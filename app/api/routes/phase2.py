from __future__ import annotations

from datetime import date
from decimal import Decimal
from io import BytesIO

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models import Invoice, InvoiceItem, InvoicePayment, JournalEntry, LeaveRequest, PayrollItem, PayrollRun, User
from app.services.accounting import (
    account_balance,
    post_invoice,
    post_payroll_run,
    receivables,
    receive_invoice_payment,
    reverse_entry,
)
from app.services.attendance_leave import decide_leave, month_summary, submit_leave
from app.services.payroll import calculate_gross_to_net, indian_currency

router = APIRouter()


class LeaveSubmission(BaseModel):
    employee_id: str
    leave_type_code: str
    start_date: date
    end_date: date
    reason: str = Field(min_length=3)
    financial_year: str = "FY2026-27"


class Decision(BaseModel):
    financial_year: str = "FY2026-27"
    note: str | None = None


class InvoiceLineInput(BaseModel):
    description: str = Field(min_length=1)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    revenue_account: str


class InvoiceInput(BaseModel):
    invoice_id: str
    invoice_number: str
    client_id: str
    invoice_date: date
    due_date: date
    service_line_account: str
    gst_rate_percent: Decimal = Field(ge=0, le=100)
    items: list[InvoiceLineInput] = Field(min_length=1)


class PaymentInput(BaseModel):
    payment_id: str
    payment_date: date
    amount: Decimal = Field(gt=0)
    payment_mode: str
    entry_id: str
    reference_no: str | None = None


def _next_entry_id(db: Session) -> str:
    count = db.query(JournalEntry).count() + 1
    return f"JE-P2-{count:06d}"


@router.get("/attendance/{employee_id}/summary")
def attendance_summary(employee_id: str, year: int, month: int, db: Session = Depends(get_db)):
    if not 1 <= month <= 12:
        raise HTTPException(422, "month must be between 1 and 12")
    return month_summary(db, employee_id, year, month)


@router.post("/leave/requests", status_code=status.HTTP_201_CREATED)
def apply_for_leave(payload: LeaveSubmission, db: Session = Depends(get_db)):
    try:
        request = submit_leave(
            db,
            request_id=f"LR-API-{date.today():%y%m%d}-{db.query(LeaveRequest).count() + 1:04d}",
            employee_id=payload.employee_id,
            leave_type_code=payload.leave_type_code,
            start_date=payload.start_date,
            end_date=payload.end_date,
            reason=payload.reason,
            financial_year=payload.financial_year,
        )
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"leave_request_id": request.leave_request_id, "status": request.status, "days": request.days}


def _decide(request_id: str, approve: bool, payload: Decision, db: Session):
    request = db.get(LeaveRequest, request_id)
    if request is None:
        raise HTTPException(404, "leave request not found")
    try:
        result = decide_leave(
            db, request, approve=approve, financial_year=payload.financial_year,
            approver_id="API-HR", note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    return {"leave_request_id": result.leave_request_id, "status": result.status,
            "days": result.days, "balance_updated": approve}


@router.post("/leave/requests/{request_id}/approve")
def approve_leave(request_id: str, payload: Decision, db: Session = Depends(get_db)):
    return _decide(request_id, True, payload, db)


@router.post("/leave/requests/{request_id}/reject")
def reject_leave(request_id: str, payload: Decision, db: Session = Depends(get_db)):
    return _decide(request_id, False, payload, db)


@router.get("/payslips/{employee_id}/{run_id}")
def get_payslip(
    employee_id: str,
    run_id: str,
    x_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.user_id == x_user_id, User.is_active.is_(True))) if x_user_id else None
    if user is None or (user.role.upper() not in {"HR", "ADMIN"} and user.employee_id != employee_id):
        raise HTTPException(403, "only the employee or HR may view this payslip")
    item = db.scalar(select(PayrollItem).where(
        PayrollItem.employee_id == employee_id,
        PayrollItem.run_id == run_id,
    ))
    if item is None:
        raise HTTPException(404, "payslip not found")
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle(f"Payslip {employee_id} {run_id}")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(48, 800, "LedgerForge Payslip")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(48, 780, f"Employee: {employee_id}    Payroll run: {run_id}")
    pdf.drawString(48, 765, f"Period: {item.period_start:%d %b %Y} to {item.period_end:%d %b %Y}")
    y = 725
    entries = [
        ("Basic", item.basic), ("HRA", item.hra), ("Conveyance", item.conveyance),
        ("Medical", item.medical), ("Special allowance", item.special_allowance),
        ("Overtime", item.overtime_pay), ("Variable pay", item.variable_pay),
        ("Gross pay", item.gross_pay), ("Employee PF", item.pf_employee),
        ("Employee ESI", item.esi_employee), ("Professional tax", item.professional_tax),
        ("TDS", item.tds), ("Other deductions", item.other_deductions),
        ("Total deductions", item.total_deductions), ("Net pay", item.net_pay),
    ]
    for label, amount in entries:
        pdf.drawString(55, y, label)
        pdf.drawRightString(540, y, indian_currency(amount))
        y -= 24
    pdf.setFont("Helvetica-Oblique", 8)
    pdf.drawString(48, 70, "Training dataset payslip; sample statutory values are not for real payroll use.")
    pdf.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={
        "Content-Disposition": f"inline; filename=payslip-{employee_id}-{run_id}.pdf"
    })


@router.get("/ledger/accounts/{account_code}/balance")
def get_account_balance(account_code: str, as_of: date, db: Session = Depends(get_db)):
    try:
        value = account_balance(db, account_code, as_of)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"account_code": account_code, "as_of": as_of, "balance": value}


@router.post("/payroll/runs/{run_id}/post", status_code=status.HTTP_201_CREATED)
def post_payroll_to_ledger(run_id: str, db: Session = Depends(get_db)):
    run = db.get(PayrollRun, run_id)
    if run is None:
        raise HTTPException(404, "payroll run not found")
    items = db.scalars(select(PayrollItem).where(PayrollItem.run_id == run_id)).all()
    try:
        entry = post_payroll_run(db, run, items, entry_id=_next_entry_id(db))
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
    return {"run_id": run_id, "journal_entry_id": entry.entry_id,
            "total_debit": entry.total_debit, "total_credit": entry.total_credit}


@router.get("/payroll/runs/{run_id}/items")
def list_calculated_payroll(run_id: str, db: Session = Depends(get_db)):
    items = db.scalars(
        select(PayrollItem).where(PayrollItem.run_id == run_id).order_by(PayrollItem.employee_id)
    ).all()
    if not items:
        raise HTTPException(404, "calculated payroll rows not found")
    return [
        {"employee_id": item.employee_id, "run_id": item.run_id,
         "gross_pay": item.gross_pay, "total_deductions": item.total_deductions,
         "net_pay": item.net_pay, "calculation_note": item.calculation_note}
        for item in items
    ]


@router.get("/payroll/runs/{run_id}/items/{employee_id}")
def get_calculated_payroll(run_id: str, employee_id: str, db: Session = Depends(get_db)):
    item = db.scalar(select(PayrollItem).where(
        PayrollItem.run_id == run_id, PayrollItem.employee_id == employee_id
    ))
    if item is None:
        raise HTTPException(404, "calculated payroll row not found")
    return {
        "employee_id": item.employee_id,
        "run_id": item.run_id,
        "period_start": item.period_start,
        "period_end": item.period_end,
        "days_employed": item.days_employed,
        "lop_days": item.lop_days,
        "gross_pay": item.gross_pay,
        "total_deductions": item.total_deductions,
        "net_pay": item.net_pay,
        "calculation_note": item.calculation_note,
    }


@router.post("/ledger/entries/{entry_id}/reverse", status_code=status.HTTP_201_CREATED)
def reverse_ledger_entry(entry_id: str, db: Session = Depends(get_db)):
    entry = db.scalar(select(JournalEntry).options(selectinload(JournalEntry.lines)).where(
        JournalEntry.entry_id == entry_id
    ))
    if entry is None:
        raise HTTPException(404, "journal entry not found")
    try:
        reversal = reverse_entry(db, entry, reversal_id=_next_entry_id(db), actor_id="API-HR")
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
    return {"reversal_entry_id": reversal.entry_id, "status": reversal.status,
            "reversal_of": entry.entry_id}


@router.get("/invoices/receivables")
def list_receivables(db: Session = Depends(get_db)):
    return receivables(db)


@router.post("/invoices", status_code=status.HTTP_201_CREATED)
def create_invoice(payload: InvoiceInput, db: Session = Depends(get_db)):
    if db.get(Invoice, payload.invoice_id):
        raise HTTPException(409, "invoice id already exists")
    subtotal = sum((line.quantity * line.unit_price for line in payload.items), Decimal("0"))
    subtotal = subtotal.quantize(Decimal("0.01"))
    gst = (subtotal * payload.gst_rate_percent / 100).quantize(Decimal("0.01"))
    invoice = Invoice(
        invoice_id=payload.invoice_id,
        invoice_number=payload.invoice_number,
        client_id=payload.client_id,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        service_line_account=payload.service_line_account,
        currency="INR",
        subtotal=subtotal,
        gst_rate_percent=payload.gst_rate_percent,
        gst_amount=gst,
        total_amount=subtotal + gst,
        amount_paid=Decimal("0"),
        balance_due=subtotal + gst,
        status="DRAFT",
        items=[InvoiceItem(
            invoice_item_id=f"{payload.invoice_id}-L{index:02d}",
            line_no=index,
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            amount=(line.quantity * line.unit_price).quantize(Decimal("0.01")),
            revenue_account=line.revenue_account,
        ) for index, line in enumerate(payload.items, 1)],
    )
    db.add(invoice)
    db.commit()
    return {"invoice_id": invoice.invoice_id, "status": invoice.status,
            "total_amount": invoice.total_amount, "balance_due": invoice.balance_due}


@router.post("/invoices/{invoice_id}/post")
def send_invoice(invoice_id: str, db: Session = Depends(get_db)):
    invoice = db.scalar(select(Invoice).options(selectinload(Invoice.items)).where(
        Invoice.invoice_id == invoice_id
    ))
    if invoice is None:
        raise HTTPException(404, "invoice not found")
    try:
        entry = post_invoice(db, invoice, entry_id=_next_entry_id(db))
        invoice.ledger_entry_id = entry.entry_id
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
    return {"invoice_id": invoice_id, "status": invoice.status, "journal_entry_id": entry.entry_id}


@router.post("/invoices/{invoice_id}/cancel")
def cancel_invoice(invoice_id: str, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(404, "invoice not found")
    if invoice.status != "DRAFT":
        raise HTTPException(409, "only draft invoices can be cancelled")
    invoice.status = "CANCELLED"
    db.commit()
    return {"invoice_id": invoice_id, "status": invoice.status, "posted": False}


@router.post("/invoices/{invoice_id}/payments", status_code=status.HTTP_201_CREATED)
def add_payment(invoice_id: str, payload: PaymentInput, db: Session = Depends(get_db)):
    invoice = db.get(Invoice, invoice_id)
    if invoice is None:
        raise HTTPException(404, "invoice not found")
    try:
        payment = receive_invoice_payment(
            db, invoice, payment_id=payload.payment_id, payment_date=payload.payment_date,
            amount=payload.amount, payment_mode=payload.payment_mode, entry_id=payload.entry_id,
            reference_no=payload.reference_no,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
    return {"payment_id": payment.payment_id, "status": invoice.status,
            "balance_due": invoice.balance_due}
