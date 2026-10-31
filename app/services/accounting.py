from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import event, func, select
from sqlalchemy.orm import Session, object_session, selectinload

from app.models import (
    ChartOfAccount,
    Invoice,
    InvoiceItem,
    InvoicePayment,
    JournalEntry,
    JournalLine,
)

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


@event.listens_for(Session, "before_flush")
def _keep_posted_journals_immutable(session: Session, _flush_context, _instances) -> None:
    for obj in session.dirty | session.deleted:
        if isinstance(obj, JournalEntry) and obj.status == "POSTED":
            raise ValueError("posted journal entries are immutable; create a reversing entry")
        if isinstance(obj, JournalLine):
            parent = object_session(obj)
            entry = parent.get(JournalEntry, obj.entry_id) if parent is not None else None
            if entry is not None and entry.status == "POSTED":
                raise ValueError("posted journal lines are immutable; create a reversing entry")


def money(value: Decimal | str | int | float) -> Decimal:
    return Decimal(str(value)).quantize(CENT)


def create_posted_entry(
    db: Session,
    *,
    entry_id: str,
    entry_date: date,
    posting_period: str,
    financial_year: str,
    description: str,
    source_type: str,
    source_id: str,
    lines: list[dict[str, Decimal | str]],
    reversal_of_source_id: str | None = None,
) -> JournalEntry:
    debit = sum((money(line.get("debit", ZERO)) for line in lines), ZERO)
    credit = sum((money(line.get("credit", ZERO)) for line in lines), ZERO)
    if debit <= ZERO or debit != credit:
        raise ValueError("journal entry must have equal positive debit and credit totals")
    if db.scalar(select(JournalEntry.entry_id).where(
        JournalEntry.source_type == source_type,
        JournalEntry.source_id == source_id,
    )):
        raise ValueError("a journal entry already exists for this source")
    entry = JournalEntry(
        entry_id=entry_id,
        entry_date=entry_date,
        posting_period=posting_period,
        financial_year=financial_year,
        description=description,
        source_type=source_type,
        source_id=source_id,
        status="POSTED",
        total_debit=debit,
        total_credit=credit,
        reversal_of_source_id=reversal_of_source_id,
        lines=[
            JournalLine(
                line_id=f"{entry_id}-L{number:02d}",
                line_no=number,
                account_code=str(line["account_code"]),
                debit=money(line.get("debit", ZERO)),
                credit=money(line.get("credit", ZERO)),
                line_description=str(line.get("description", description)),
                cost_center_department_id=line.get("department_id"),
            )
            for number, line in enumerate(lines, start=1)
        ],
    )
    db.add(entry)
    db.flush()
    return entry


def reverse_entry(db: Session, entry: JournalEntry, *, reversal_id: str, actor_id: str) -> JournalEntry:
    if entry.status != "POSTED":
        raise ValueError("only posted journal entries can be reversed")
    if entry.reversal_of_source_id:
        raise ValueError("a reversing journal entry cannot itself be reversed")
    return create_posted_entry(
        db,
        entry_id=reversal_id,
        entry_date=date.today(),
        posting_period=date.today().strftime("%Y-%m"),
        financial_year=f"FY{date.today().year}-{str(date.today().year + 1)[-2:]}",
        description=f"Reversal of {entry.entry_id}",
        source_type="REVERSAL",
        source_id=entry.entry_id,
        reversal_of_source_id=entry.entry_id,
        lines=[
            {
                "account_code": line.account_code,
                "debit": line.credit,
                "credit": line.debit,
                "description": f"Reversal: {line.line_description}",
                "department_id": line.cost_center_department_id,
            }
            for line in entry.lines
        ],
    )


def account_balance(db: Session, account_code: str, as_of: date) -> Decimal:
    account = db.get(ChartOfAccount, account_code)
    if account is None:
        raise ValueError("account not found")
    debit, credit = db.execute(
        select(
            func.coalesce(func.sum(JournalLine.debit), 0),
            func.coalesce(func.sum(JournalLine.credit), 0),
        )
        .join(JournalEntry, JournalEntry.entry_id == JournalLine.entry_id)
        .where(
            JournalLine.account_code == account_code,
            JournalEntry.status == "POSTED",
            JournalEntry.entry_date <= as_of,
        )
    ).one()
    delta = money(Decimal(str(debit)) - Decimal(str(credit)))
    return delta if account.normal_balance.upper() == "DEBIT" else -delta


def post_invoice(db: Session, invoice: Invoice, *, entry_id: str) -> JournalEntry:
    if invoice.status not in {"DRAFT", "SENT"}:
        raise ValueError("only draft or sent invoices can be posted")
    if invoice.status == "DRAFT":
        invoice.status = "SENT"
    return create_posted_entry(
        db,
        entry_id=entry_id,
        entry_date=invoice.invoice_date,
        posting_period=invoice.invoice_date.strftime("%Y-%m"),
        financial_year=f"FY{invoice.invoice_date.year}-{str(invoice.invoice_date.year + 1)[-2:]}",
        description=f"Invoice {invoice.invoice_number}",
        source_type="INVOICE",
        source_id=invoice.invoice_id,
        lines=[
            {"account_code": "1100", "debit": invoice.total_amount, "credit": ZERO,
             "description": f"Receivable {invoice.invoice_number}"},
            {"account_code": invoice.service_line_account, "debit": ZERO,
             "credit": invoice.subtotal, "description": f"Revenue {invoice.invoice_number}"},
            {"account_code": "2200", "debit": ZERO, "credit": invoice.gst_amount,
             "description": f"Output GST {invoice.invoice_number}"},
        ],
    )


def post_payroll_run(db: Session, run, items: list, *, entry_id: str) -> JournalEntry:
    if not items:
        raise ValueError("payroll run has no calculated employee rows")
    fixed = money(sum((Decimal(item.earned_fixed_pay) for item in items), ZERO))
    overtime = money(sum((Decimal(item.overtime_pay) for item in items), ZERO))
    variable = money(sum((Decimal(item.variable_pay) for item in items), ZERO))
    employer_pf = money(sum((Decimal(item.pf_employer) for item in items), ZERO))
    employer_esi = money(sum((Decimal(item.esi_employer) for item in items), ZERO))
    lines: list[dict[str, Decimal | str]] = [
        {"account_code": "5001", "debit": fixed, "credit": ZERO, "description": "Fixed payroll"},
        {"account_code": "5002", "debit": overtime, "credit": ZERO, "description": "Overtime payroll"},
        {"account_code": "5003", "debit": variable, "credit": ZERO, "description": "Payroll incentives"},
        {"account_code": "5004", "debit": employer_pf, "credit": ZERO, "description": "Employer PF"},
        {"account_code": "5005", "debit": employer_esi, "credit": ZERO, "description": "Employer ESI"},
    ]
    for account_code, field in (
        ("2100", "net_pay"), ("2110", "pf_employee"), ("2120", "esi_employee"),
        ("2130", "tds"), ("2140", "professional_tax"),
    ):
        amount = money(sum((Decimal(getattr(item, field)) for item in items), ZERO))
        lines.append({"account_code": account_code, "debit": ZERO, "credit": amount,
                      "description": f"Payroll payable: {field}"})
    for account_code, amount, label in (
        ("2110", employer_pf, "Employer PF payable"),
        ("2120", employer_esi, "Employer ESI payable"),
    ):
        lines.append({"account_code": account_code, "debit": ZERO, "credit": amount,
                      "description": label})
    other = money(sum((Decimal(item.other_deductions) for item in items), ZERO))
    if other:
        lines.append({"account_code": "2130", "debit": ZERO, "credit": other,
                      "description": "Other employee deductions payable"})
    entry = create_posted_entry(
        db,
        entry_id=entry_id,
        entry_date=run.pay_date or run.period_end,
        posting_period=run.period_end.strftime("%Y-%m"),
        financial_year=f"FY{run.period_end.year if run.period_end.month >= 4 else run.period_end.year - 1}-{str((run.period_end.year if run.period_end.month >= 4 else run.period_end.year - 1) + 1)[-2:]}",
        description=f"Payroll posting for {run.run_id}",
        source_type="ENGINE_PAYROLL",
        source_id=run.run_id,
        lines=lines,
    )
    run.journal_entry_id = entry.entry_id
    return entry


def receive_invoice_payment(
    db: Session,
    invoice: Invoice,
    *,
    payment_id: str,
    payment_date: date,
    amount: Decimal,
    payment_mode: str,
    entry_id: str,
    reference_no: str | None = None,
) -> InvoicePayment:
    amount = money(amount)
    if invoice.status not in {"SENT", "PARTIALLY_PAID", "OVERDUE"}:
        raise ValueError("invoice is not open for payment")
    if amount <= ZERO or amount > money(invoice.balance_due):
        raise ValueError("payment must be positive and cannot exceed the balance due")
    payment = InvoicePayment(
        payment_id=payment_id,
        invoice_id=invoice.invoice_id,
        payment_date=payment_date,
        amount=amount,
        payment_mode=payment_mode,
        reference_no=reference_no,
        ledger_entry_id=entry_id,
    )
    entry = create_posted_entry(
        db,
        entry_id=entry_id,
        entry_date=payment_date,
        posting_period=payment_date.strftime("%Y-%m"),
        financial_year=f"FY{payment_date.year}-{str(payment_date.year + 1)[-2:]}",
        description=f"Payment for {invoice.invoice_number}",
        source_type="INVOICE_PAYMENT",
        source_id=payment_id,
        lines=[
            {"account_code": "1001", "debit": amount, "credit": ZERO,
             "description": f"Bank receipt {invoice.invoice_number}"},
            {"account_code": "1100", "debit": ZERO, "credit": amount,
             "description": f"Settle receivable {invoice.invoice_number}"},
        ],
    )
    db.add(payment)
    invoice.amount_paid = money(invoice.amount_paid) + amount
    invoice.balance_due = money(invoice.balance_due) - amount
    invoice.last_payment_date = payment_date
    invoice.status = "PAID" if invoice.balance_due == ZERO else "PARTIALLY_PAID"
    invoice.ledger_entry_id = entry.entry_id
    return payment


def receivables(db: Session) -> list[dict[str, object]]:
    open_invoices = db.scalars(
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(Invoice.status.in_(["SENT", "PARTIALLY_PAID", "OVERDUE"]))
        .order_by(Invoice.due_date, Invoice.invoice_number)
    ).all()
    return [
        {
            "invoice_id": inv.invoice_id,
            "invoice_number": inv.invoice_number,
            "client_id": inv.client_id,
            "due_date": inv.due_date,
            "status": inv.status,
            "amount_due": money(inv.balance_due),
        }
        for inv in open_invoices
    ]
