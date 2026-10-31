from datetime import date
from pathlib import Path
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import (
    Attendance,
    ChartOfAccount,
    Client,
    Holiday,
    Invoice,
    JournalEntry,
    LeaveBalance,
    PayrollItem,
    PayrollRun,
    User,
)
from app.services.accounting import (
    account_balance,
    create_posted_entry,
    post_invoice,
    post_payroll_run,
    receivables,
    receive_invoice_payment,
    reverse_entry,
)
from app.services.attendance_leave import count_leave_days, decide_leave, month_summary, submit_leave
from app.services.payroll import calculate_gross_to_net, indian_currency, money


def test_attendance_summary_excludes_unverified_missing_checkout_overtime(db_session):
    db_session.add_all([
        Attendance(
            attendance_id="AT-P2-1", employee_id="EMP-1001", attendance_date=date(2026, 7, 1),
            weekday="Wednesday", status="PRESENT", hours_worked=Decimal("8.00"),
            overtime_hours=Decimal("2.00"), late_flag="Y",
        ),
        Attendance(
            attendance_id="AT-P2-2", employee_id="EMP-1001", attendance_date=date(2026, 7, 2),
            weekday="Thursday", status="WFH", hours_worked=None, overtime_hours=Decimal("4.00"),
            late_flag="N", data_quality_flag="MISSING_CHECKOUT",
        ),
        Attendance(
            attendance_id="AT-P2-3", employee_id="EMP-1001", attendance_date=date(2026, 7, 3),
            weekday="Friday", status="HALF_DAY_UNPAID", late_flag="N",
        ),
    ])
    db_session.commit()
    assert month_summary(db_session, "EMP-1001", 2026, 7) == {
        "present": 1,
        "wfh": 1,
        "absent": Decimal("0.5"),
        "late": 1,
        "overtime_hours": Decimal("2.00"),
    }


def test_attendance_record_list_and_summary_endpoints(client):
    created = client.post("/attendance", json={
        "employee_id": "EMP-1001", "attendance_date": "2026-07-08", "status": "PRESENT",
        "check_in": "09:00", "check_out": "18:00", "hours_worked": "8.00",
        "overtime_hours": "1.50", "late_flag": False,
    })
    assert created.status_code == 201
    assert created.json()["weekday"] == "Wednesday"
    rows = client.get("/attendance/EMP-1001?year=2026&month=7")
    assert rows.status_code == 200 and len(rows.json()) == 1
    summary = client.get("/attendance/EMP-1001/summary?year=2026&month=7")
    assert summary.status_code == 200
    assert summary.json()["present"] == 1
    assert summary.json()["overtime_hours"] == 1.5
    duplicate = client.post("/attendance", json={
        "employee_id": "EMP-1001", "attendance_date": "2026-07-08", "status": "PRESENT",
    })
    assert duplicate.status_code == 409


def test_leave_weekend_holiday_exclusion_and_balance_decision(db_session):
    db_session.add(Holiday(
        holiday_date=date(2026, 7, 6), holiday_name="Training holiday", holiday_type="COMPANY",
        weekday="Monday", falls_on_weekend=False,
    ))
    balance = LeaveBalance(
        employee_id="EMP-1001", leave_type_code="CL", financial_year="FY2026-27",
        as_of_date=date(2026, 7, 1), entitlement_days=Decimal("12"), used_days=Decimal("0"),
        balance_days=Decimal("12"), pending_days=Decimal("0"),
    )
    db_session.add(balance)
    db_session.commit()
    assert count_leave_days(db_session, date(2026, 7, 3), date(2026, 7, 7)) == Decimal("2")
    request = submit_leave(
        db_session, request_id="LR-TEST-01", employee_id="EMP-1001", leave_type_code="CL",
        start_date=date(2026, 7, 3), end_date=date(2026, 7, 7), reason="Family matter",
        financial_year="FY2026-27", applied_on=date(2026, 7, 1),
    )
    assert request.days == Decimal("2.00")
    assert balance.pending_days == Decimal("2.00")
    decide_leave(
        db_session, request, approve=True, financial_year="FY2026-27", approver_id="EMP-1000",
        decided_on=date(2026, 7, 2),
    )
    assert balance.balance_days == Decimal("10.00")
    assert balance.used_days == Decimal("2.00")
    assert balance.pending_days == Decimal("0.00")


def test_leave_rejection_releases_pending_days_and_insufficient_balance_is_refused(db_session):
    balance = LeaveBalance(
        employee_id="EMP-1002", leave_type_code="CL", financial_year="FY2026-27",
        as_of_date=date(2026, 7, 1), entitlement_days=Decimal("1"), used_days=Decimal("0"),
        balance_days=Decimal("1"), pending_days=Decimal("0"),
    )
    db_session.add(balance)
    db_session.commit()
    with pytest.raises(ValueError, match="insufficient leave balance"):
        submit_leave(
            db_session, request_id="LR-TEST-LOW", employee_id="EMP-1002", leave_type_code="CL",
            start_date=date(2026, 7, 6), end_date=date(2026, 7, 8), reason="Too many days",
            financial_year="FY2026-27", applied_on=date(2026, 7, 1),
        )
    request = submit_leave(
        db_session, request_id="LR-TEST-REJECT", employee_id="EMP-1002", leave_type_code="CL",
        start_date=date(2026, 7, 7), end_date=date(2026, 7, 7), reason="Personal",
        financial_year="FY2026-27", applied_on=date(2026, 7, 1),
    )
    decide_leave(
        db_session, request, approve=False, financial_year="FY2026-27", approver_id="EMP-1000",
        decided_on=date(2026, 7, 2), note="Coverage unavailable",
    )
    assert request.status == "REJECTED"
    assert balance.balance_days == Decimal("1")
    assert balance.used_days == Decimal("0")
    assert balance.pending_days == Decimal("0")


def test_decimal_gross_to_net_and_indian_currency_format():
    result = calculate_gross_to_net(
        components={"BASIC": Decimal("10000.00"), "HRA": Decimal("5000.00")},
        days_employed=Decimal("30"), lop_days=Decimal("1"), calendar_days=30,
        overtime_hours=Decimal("10"), eligible_for_overtime=True, variable_pay=Decimal("0.10"),
        pf_applicable=True, esi_applicable=False,
        statutory={"PF_EMPLOYEE_RATE": Decimal("12"), "PF_EMPLOYER_RATE": Decimal("12"),
                   "PF_WAGE_CEILING": Decimal("15000"), "OT_MULTIPLIER": Decimal("2"),
                   "WORKING_HOURS_PER_MONTH": Decimal("208")},
        professional_tax_threshold=Decimal("25000"), professional_tax_monthly=Decimal("200"),
    )
    assert result["gross_pay"] == Decimal("15942.41")
    assert result["pf_employee"] == Decimal("1160.00")
    assert result["net_pay"] == Decimal("14782.41")
    assert money(Decimal("0.1") + Decimal("0.2")) == Decimal("0.30")
    assert indian_currency(Decimal("123456.7")) == "₹1,23,456.70"


def test_payroll_engine_matches_five_hand_checked_reference_rows():
    import csv

    from scripts.calculate_payroll import calculate

    data_dir = Path("data/master")
    generated = calculate(data_dir)
    actual = {(row["employee_id"], row["run_id"]): row for row in generated}
    with (data_dir / "payroll_items.csv").open(encoding="utf-8-sig", newline="") as stream:
        references = [row for row in csv.DictReader(stream) if row["run_id"] == "PR-2025-04"][:5]
    assert len(references) == 5
    for reference in references:
        result = actual[(reference["employee_id"], reference["run_id"])]
        for field in (
            "basic", "hra", "conveyance", "medical", "special_allowance", "earned_fixed_pay",
            "overtime_pay", "variable_pay", "gross_pay", "pf_employee", "esi_employee",
            "professional_tax", "tds", "other_deductions", "total_deductions", "net_pay",
            "pf_employer", "esi_employer", "employer_cost",
        ):
            assert abs(Decimal(result[field]) - Decimal(reference[field])) <= Decimal("0.01")


def test_posted_journal_balances_is_read_only_and_reverse_posts(db_session):
    db_session.add_all([
        ChartOfAccount(account_code="5001", account_name="Salaries", account_type="EXPENSE",
                       normal_balance="DEBIT", statement="Income Statement", is_group=False,
                       is_active=True),
        ChartOfAccount(account_code="2100", account_name="Salaries Payable", account_type="LIABILITY",
                       normal_balance="CREDIT", statement="Balance Sheet", is_group=False,
                       is_active=True),
    ])
    db_session.commit()
    with pytest.raises(ValueError, match="equal positive debit and credit totals"):
        create_posted_entry(
            db_session, entry_id="JE-P2-UNBALANCED", entry_date=date(2026, 7, 31),
            posting_period="2026-07", financial_year="FY2026-27", description="Bad entry",
            source_type="TEST", source_id="unbalanced",
            lines=[{"account_code": "5001", "debit": Decimal("100"), "credit": Decimal("0")},
                   {"account_code": "2100", "debit": Decimal("0"), "credit": Decimal("99")}],
        )
    assert db_session.query(JournalEntry).count() == 0
    entry = create_posted_entry(
        db_session, entry_id="JE-P2-TEST-01", entry_date=date(2026, 7, 31),
        posting_period="2026-07", financial_year="FY2026-27", description="Payroll test",
        source_type="TEST", source_id="payroll-1",
        lines=[{"account_code": "5001", "debit": Decimal("100"), "credit": Decimal("0")},
               {"account_code": "2100", "debit": Decimal("0"), "credit": Decimal("100")}],
    )
    db_session.commit()
    assert account_balance(db_session, "5001", date(2026, 7, 31)) == Decimal("100.00")
    entry.description = "attempted edit"
    with pytest.raises(ValueError, match="immutable"):
        db_session.commit()
    db_session.rollback()
    entry = db_session.scalar(select(JournalEntry).options(selectinload(JournalEntry.lines)).where(
        JournalEntry.entry_id == "JE-P2-TEST-01"
    ))
    reversal = reverse_entry(db_session, entry, reversal_id="JE-P2-TEST-02", actor_id="EMP-1000")
    db_session.commit()
    assert reversal.reversal_of_source_id == entry.entry_id
    assert account_balance(db_session, "5001", date.today()) == Decimal("0.00")


def test_invoice_posting_and_payment_lifecycle(client, db_session):
    db_session.add_all([
        ChartOfAccount(account_code="1100", account_name="AR", account_type="ASSET",
                       normal_balance="DEBIT", statement="Balance Sheet", is_group=False, is_active=True),
        ChartOfAccount(account_code="4101", account_name="Revenue", account_type="INCOME",
                       normal_balance="CREDIT", statement="Income Statement", is_group=False, is_active=True),
        ChartOfAccount(account_code="2200", account_name="GST", account_type="LIABILITY",
                       normal_balance="CREDIT", statement="Balance Sheet", is_group=False, is_active=True),
        ChartOfAccount(account_code="1001", account_name="Bank", account_type="ASSET",
                       normal_balance="DEBIT", statement="Balance Sheet", is_group=False, is_active=True),
        Client(client_id="CLIENT-1", client_name="Training Client", country="IN",
               client_type="COMPANY", payment_terms_days=30, primary_service_line="CONSULTING",
               is_active=True),
    ])
    db_session.commit()
    draft = client.post("/invoices", json={
        "invoice_id": "INV-P2-DRAFT", "invoice_number": "LF-P2-DRAFT", "client_id": "CLIENT-1",
        "invoice_date": "2026-07-01", "due_date": "2026-07-31", "service_line_account": "4101",
        "gst_rate_percent": "18", "items": [{"description": "Advisory", "quantity": "1",
                                                "unit_price": "1000", "revenue_account": "4101"}],
    })
    assert draft.status_code == 201 and draft.json()["status"] == "DRAFT"
    cancelled = client.post("/invoices/INV-P2-DRAFT/cancel")
    assert cancelled.status_code == 200 and cancelled.json()["posted"] is False
    assert db_session.query(JournalEntry).count() == 0
    invoice = Invoice(
        invoice_id="INV-P2-1", invoice_number="LF-P2-001", client_id="CLIENT-1",
        invoice_date=date(2026, 7, 1), due_date=date(2026, 7, 31), service_line_account="4101",
        currency="INR", subtotal=Decimal("1000"), gst_rate_percent=Decimal("18"),
        gst_amount=Decimal("180"), total_amount=Decimal("1180"), amount_paid=Decimal("0"),
        balance_due=Decimal("1180"), status="DRAFT",
    )
    db_session.add(invoice)
    db_session.commit()
    assert db_session.query(JournalEntry).count() == 0
    posted = post_invoice(db_session, invoice, entry_id="JE-P2-INV-01")
    db_session.commit()
    assert posted.total_debit == posted.total_credit == Decimal("1180.00")
    payment = receive_invoice_payment(
        db_session, invoice, payment_id="PAY-P2-1", payment_date=date(2026, 7, 10),
        amount=Decimal("500"), payment_mode="BANK", entry_id="JE-P2-PAY-01",
    )
    db_session.commit()
    assert payment.amount == Decimal("500.00")
    assert invoice.status == "PARTIALLY_PAID" and invoice.balance_due == Decimal("680.00")
    payment = receive_invoice_payment(
        db_session, invoice, payment_id="PAY-P2-2", payment_date=date(2026, 7, 15),
        amount=Decimal("680"), payment_mode="BANK", entry_id="JE-P2-PAY-02",
    )
    db_session.commit()
    assert payment.amount == Decimal("680.00")
    assert invoice.status == "PAID" and invoice.balance_due == Decimal("0.00")


def test_overdue_invoice_status_and_receivables_balance(db_session):
    db_session.add_all([
        ChartOfAccount(account_code="4101", account_name="Revenue", account_type="INCOME",
                       normal_balance="CREDIT", statement="Income Statement", is_group=False,
                       is_active=True),
        Client(client_id="CLIENT-OVERDUE", client_name="Overdue Training Client", country="IN",
               client_type="COMPANY", payment_terms_days=30, primary_service_line="CONSULTING",
               is_active=True),
    ])
    db_session.commit()
    invoice = Invoice(
        invoice_id="INV-P2-OVERDUE", invoice_number="LF-P2-OVERDUE", client_id="CLIENT-OVERDUE",
        invoice_date=date(2026, 6, 1), due_date=date(2026, 6, 30), service_line_account="4101",
        currency="INR", subtotal=Decimal("1000"), gst_rate_percent=Decimal("18"),
        gst_amount=Decimal("180"), total_amount=Decimal("1180"), amount_paid=Decimal("200"),
        balance_due=Decimal("980"), status="PARTIALLY_PAID",
    )
    db_session.add(invoice)
    db_session.commit()
    result = receivables(db_session, as_of=date(2026, 7, 1))
    assert invoice.status == "OVERDUE"
    assert len(result) == 1
    assert result[0]["amount_due"] == Decimal("980.00")


def test_payslip_owner_access_and_stranger_refusal(client, db_session):
    db_session.add_all([
        User(user_id="U-OWNER", employee_id="EMP-1001", username="owner@example.com", role="EMPLOYEE",
             is_active=True, mfa_enabled=False),
        User(user_id="U-STRANGER", employee_id="EMP-1000", username="stranger@example.com", role="EMPLOYEE",
             is_active=True, mfa_enabled=False),
        User(user_id="U-HR", employee_id="EMP-1002", username="hr@example.com", role="HR",
             is_active=True, mfa_enabled=False),
    ])
    for code, name, kind, normal in (
        ("5001", "Salary", "EXPENSE", "DEBIT"), ("5002", "Overtime", "EXPENSE", "DEBIT"),
        ("5003", "Incentives", "EXPENSE", "DEBIT"), ("5004", "Employer PF", "EXPENSE", "DEBIT"),
        ("5005", "Employer ESI", "EXPENSE", "DEBIT"), ("2100", "Salaries payable", "LIABILITY", "CREDIT"),
        ("2110", "PF payable", "LIABILITY", "CREDIT"), ("2120", "ESI payable", "LIABILITY", "CREDIT"),
        ("2130", "TDS payable", "LIABILITY", "CREDIT"), ("2140", "PT payable", "LIABILITY", "CREDIT"),
    ):
        db_session.add(ChartOfAccount(account_code=code, account_name=name, account_type=kind,
                                      normal_balance=normal, statement="Test", is_group=False,
                                      is_active=True))
    run = PayrollRun(
        run_id="PR-P2-TEST", period_start=date(2026, 7, 1), period_end=date(2026, 7, 31),
        pay_date=date(2026, 8, 1), employees_paid=1, total_gross=Decimal("1000"),
        total_deductions=Decimal("100"), total_net=Decimal("900"),
        total_employer_contributions=Decimal("100"), total_employer_cost=Decimal("1100"),
        status="CALCULATED",
    )
    item = PayrollItem(
        payroll_item_id="PI-P2-TEST", run_id="PR-P2-TEST", employee_id="EMP-1001",
        period_start=date(2026, 7, 1), period_end=date(2026, 7, 31), department_id="D01", role_id="R001",
        calendar_days=31, days_employed=Decimal("31"), lop_days=Decimal("0"), payable_days=Decimal("31"),
        monthly_fixed_gross=Decimal("1000"), basic=Decimal("500"), hra=Decimal("200"),
        conveyance=Decimal("100"), medical=Decimal("100"), special_allowance=Decimal("100"),
        earned_fixed_pay=Decimal("1000"), overtime_hours_paid=Decimal("0"), overtime_pay=Decimal("0"),
        variable_pay=Decimal("0"), gross_pay=Decimal("1000"), pf_employee=Decimal("100"),
        esi_employee=Decimal("0"), professional_tax=Decimal("0"), tds=Decimal("0"),
        other_deductions=Decimal("0"), total_deductions=Decimal("100"), net_pay=Decimal("900"),
        pf_employer=Decimal("100"), esi_employer=Decimal("0"), employer_cost=Decimal("1100"),
    )
    db_session.add_all([run, item])
    db_session.commit()
    denied = client.get("/payslips/EMP-1001/PR-P2-TEST", headers={"X-User-Id": "U-STRANGER"})
    assert denied.status_code == 403
    allowed = client.get("/payslips/EMP-1001/PR-P2-TEST", headers={"X-User-Id": "U-OWNER"})
    assert allowed.status_code == 200
    assert allowed.json()["net_pay"] == "900.00"
    assert allowed.json()["net_pay_formatted"] == "₹900.00"
    hr_allowed = client.get("/payslips/EMP-1001/PR-P2-TEST", headers={"X-User-Id": "U-HR"})
    assert hr_allowed.status_code == 200
    denied_pdf = client.get("/payslips/EMP-1001/PR-P2-TEST/pdf", headers={"X-User-Id": "U-STRANGER"})
    assert denied_pdf.status_code == 403
    pdf_response = client.get("/payslips/EMP-1001/PR-P2-TEST/pdf", headers={"X-User-Id": "U-OWNER"})
    assert pdf_response.headers["content-type"].startswith("application/pdf")
    assert pdf_response.content.startswith(b"%PDF")
    hr_pdf = client.get("/payslips/EMP-1001/PR-P2-TEST/pdf", headers={"X-User-Id": "U-HR"})
    assert hr_pdf.status_code == 200 and hr_pdf.content.startswith(b"%PDF")
    calculated = client.get("/payroll/runs/PR-P2-TEST/items/EMP-1001")
    assert calculated.status_code == 200
    assert calculated.json()["gross_pay"] == 1000
    posted = client.post("/payroll/runs/PR-P2-TEST/post")
    assert posted.status_code == 201
    assert posted.json()["total_debit"] == posted.json()["total_credit"] == 1100
