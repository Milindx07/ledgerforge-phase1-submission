from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Holiday(Base):
    __tablename__ = "holidays"

    holiday_date: Mapped[date] = mapped_column(Date, primary_key=True)
    holiday_name: Mapped[str] = mapped_column(String(160), nullable=False)
    holiday_type: Mapped[str] = mapped_column(String(40), nullable=False)
    weekday: Mapped[str] = mapped_column(String(12), nullable=False)
    falls_on_weekend: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    calendar_note: Mapped[str | None] = mapped_column(String(240))


class LeaveType(Base):
    __tablename__ = "leave_types"

    leave_type_code: Mapped[str] = mapped_column(String(12), primary_key=True)
    leave_type_name: Mapped[str] = mapped_column(String(80), nullable=False)
    pay_type: Mapped[str] = mapped_column(String(20), nullable=False)
    annual_quota_days: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    prorated_for_joiners: Mapped[bool] = mapped_column(Boolean, nullable=False)
    carry_forward_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    max_carry_forward_days: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    policy_note: Mapped[str | None] = mapped_column(Text)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    __table_args__ = (
        CheckConstraint("days >= 0", name="ck_leave_requests_days_nonnegative"),
        Index("ix_leave_requests_employee_dates", "employee_id", "start_date", "end_date"),
    )

    leave_request_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.employee_id"), nullable=False)
    leave_type_code: Mapped[str] = mapped_column(ForeignKey("leave_types.leave_type_code"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    days: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    applied_on: Mapped[date] = mapped_column(Date, nullable=False)
    approver_id: Mapped[str | None] = mapped_column(ForeignKey("employees.employee_id"))
    decided_on: Mapped[date | None] = mapped_column(Date)
    decision_note: Mapped[str | None] = mapped_column(Text)


class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    __table_args__ = (
        CheckConstraint("balance_days >= 0", name="ck_leave_balances_nonnegative"),
    )

    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.employee_id"), primary_key=True
    )
    leave_type_code: Mapped[str] = mapped_column(
        ForeignKey("leave_types.leave_type_code"), primary_key=True
    )
    financial_year: Mapped[str] = mapped_column(String(12), primary_key=True)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    entitlement_days: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    used_days: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False, default=0)
    balance_days: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    pending_days: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False, default=0)


class SalaryComponent(Base):
    __tablename__ = "salary_components"

    component_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    component_name: Mapped[str] = mapped_column(String(120), nullable=False)
    component_type: Mapped[str] = mapped_column(String(40), nullable=False)
    taxable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    calculation_rule: Mapped[str] = mapped_column(Text, nullable=False)
    is_fixed: Mapped[bool] = mapped_column(Boolean, nullable=False)


class SalaryRevision(Base):
    __tablename__ = "salary_revisions"

    revision_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.employee_id"), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    revision_reason: Mapped[str] = mapped_column(String(80), nullable=False)
    previous_annual_fixed: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    new_annual_fixed: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    pct_change: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    role_id_after: Mapped[str | None] = mapped_column(ForeignKey("roles.role_id"))
    approved_by: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime | None] = mapped_column(DateTime)


class PerformanceReview(Base):
    __tablename__ = "performance_reviews"

    employee_id: Mapped[str] = mapped_column(
        ForeignKey("employees.employee_id"), primary_key=True
    )
    review_year: Mapped[int] = mapped_column(Integer, primary_key=True)
    appraisal_date: Mapped[date] = mapped_column(Date, nullable=False)
    performance_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    rating_label: Mapped[str] = mapped_column(String(80), nullable=False)


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.employee_id"), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="EMPLOYEE")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    password_policy_note: Mapped[str | None] = mapped_column(Text)


class StatutoryRate(Base):
    __tablename__ = "statutory_rates"

    parameter: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(40), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)


class TaxSlab(Base):
    __tablename__ = "tax_slabs"

    slab_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    regime: Mapped[str] = mapped_column(String(20), nullable=False)
    financial_year: Mapped[str] = mapped_column(String(12), nullable=False)
    income_from: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    income_to: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    rate_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)


class TaxParameter(Base):
    __tablename__ = "tax_parameters"

    parameter: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)


class PayrollRun(Base):
    __tablename__ = "payroll_runs"

    run_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    pay_date: Mapped[date | None] = mapped_column(Date)
    employees_paid: Mapped[int] = mapped_column(Integer, nullable=False)
    total_gross: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    total_net: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    total_employer_contributions: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    total_employer_cost: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    run_by: Mapped[str | None] = mapped_column(String(20))
    approved_by: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), unique=True)
    journal_entry_id: Mapped[str | None] = mapped_column(String(20))
    calculation_version: Mapped[str | None] = mapped_column(String(80))

    items: Mapped[list["PayrollItem"]] = relationship(back_populates="run")


class PayrollItem(Base):
    __tablename__ = "payroll_items"
    __table_args__ = (
        UniqueConstraint("run_id", "employee_id", name="uq_payroll_item_run_employee"),
        CheckConstraint("calendar_days > 0", name="ck_payroll_item_calendar_days"),
        Index("ix_payroll_items_employee_period", "employee_id", "period_start"),
    )

    payroll_item_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("payroll_runs.run_id"), nullable=False)
    employee_id: Mapped[str] = mapped_column(ForeignKey("employees.employee_id"), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    department_id: Mapped[str] = mapped_column(ForeignKey("departments.department_id"), nullable=False)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.role_id"), nullable=False)
    calendar_days: Mapped[int] = mapped_column(Integer, nullable=False)
    days_employed: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    lop_days: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    payable_days: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    monthly_fixed_gross: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    basic: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    hra: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    conveyance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    medical: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    special_allowance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    earned_fixed_pay: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    overtime_hours_paid: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    overtime_pay: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    variable_pay: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    variable_pay_type: Mapped[str | None] = mapped_column(String(60))
    gross_pay: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    pf_employee: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    esi_employee: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    professional_tax: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tds: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    other_deductions: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    net_pay: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    pf_employer: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    esi_employer: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    employer_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    calculation_note: Mapped[str | None] = mapped_column(Text)

    run: Mapped[PayrollRun] = relationship(back_populates="items")


class ChartOfAccount(Base):
    __tablename__ = "chart_of_accounts"

    account_code: Mapped[str] = mapped_column(String(12), primary_key=True)
    account_name: Mapped[str] = mapped_column(String(120), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)
    normal_balance: Mapped[str] = mapped_column(String(10), nullable=False)
    parent_code: Mapped[str | None] = mapped_column(ForeignKey("chart_of_accounts.account_code"))
    is_group: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    statement: Mapped[str] = mapped_column(String(40), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    entry_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    posting_period: Mapped[str] = mapped_column(String(7), nullable=False)
    financial_year: Mapped[str] = mapped_column(String(7), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_id: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="POSTED")
    total_debit: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    total_credit: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    reversal_of_source_id: Mapped[str | None] = mapped_column(String(40))
    created_by: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime | None] = mapped_column(DateTime)

    lines: Mapped[list["JournalLine"]] = relationship(
        back_populates="entry", cascade="all, delete-orphan", order_by="JournalLine.line_no"
    )


class JournalLine(Base):
    __tablename__ = "journal_lines"
    __table_args__ = (
        CheckConstraint("debit >= 0 AND credit >= 0", name="ck_journal_lines_nonnegative"),
        CheckConstraint("NOT (debit > 0 AND credit > 0)", name="ck_journal_line_one_side"),
        Index("ix_journal_lines_account", "account_code"),
    )

    line_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    entry_id: Mapped[str] = mapped_column(ForeignKey("journal_entries.entry_id"), nullable=False)
    line_no: Mapped[int] = mapped_column(Integer, nullable=False)
    account_code: Mapped[str] = mapped_column(
        ForeignKey("chart_of_accounts.account_code"), nullable=False
    )
    debit: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False, default=0)
    credit: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False, default=0)
    cost_center_department_id: Mapped[str | None] = mapped_column(ForeignKey("departments.department_id"))
    line_description: Mapped[str] = mapped_column(Text, nullable=False)

    entry: Mapped[JournalEntry] = relationship(back_populates="lines")


class Client(Base):
    __tablename__ = "clients"

    client_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    client_name: Mapped[str] = mapped_column(String(160), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(80))
    city: Mapped[str | None] = mapped_column(String(80))
    state_or_region: Mapped[str | None] = mapped_column(String(80))
    country: Mapped[str] = mapped_column(String(4), nullable=False)
    client_type: Mapped[str] = mapped_column(String(30), nullable=False)
    gst_registration: Mapped[str | None] = mapped_column(String(30))
    payment_terms_days: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_behaviour: Mapped[str | None] = mapped_column(String(40))
    primary_service_line: Mapped[str] = mapped_column(String(12), nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    onboarded_on: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint("subtotal >= 0 AND gst_amount >= 0 AND total_amount >= 0", name="ck_invoice_amounts_nonnegative"),
        CheckConstraint("amount_paid >= 0 AND balance_due >= 0", name="ck_invoice_balances_nonnegative"),
        Index("ix_invoices_client_status", "client_id", "status"),
    )

    invoice_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    invoice_number: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.client_id"), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    service_line_account: Mapped[str] = mapped_column(
        ForeignKey("chart_of_accounts.account_code"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    gst_rate_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False, default=0)
    balance_due: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT")
    last_payment_date: Mapped[date | None] = mapped_column(Date)
    po_number: Mapped[str | None] = mapped_column(String(40))
    carried_in_from_prior_period: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    ledger_entry_id: Mapped[str | None] = mapped_column(String(20))

    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan", order_by="InvoiceItem.line_no"
    )
    payments: Mapped[list["InvoicePayment"]] = relationship(back_populates="invoice")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    __table_args__ = (
        CheckConstraint("quantity > 0 AND unit_price >= 0 AND amount >= 0", name="ck_invoice_item_amounts"),
    )

    invoice_item_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.invoice_id"), nullable=False)
    line_no: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    revenue_account: Mapped[str] = mapped_column(
        ForeignKey("chart_of_accounts.account_code"), nullable=False
    )

    invoice: Mapped[Invoice] = relationship(back_populates="items")


class InvoicePayment(Base):
    __tablename__ = "invoice_payments"

    payment_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.invoice_id"), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    payment_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    reference_no: Mapped[str | None] = mapped_column(String(40))
    received_by: Mapped[str | None] = mapped_column(String(20))
    ledger_entry_id: Mapped[str | None] = mapped_column(String(20))

    invoice: Mapped[Invoice] = relationship(back_populates="payments")


__all__ = [
    "ChartOfAccount",
    "Client",
    "Holiday",
    "Invoice",
    "InvoiceItem",
    "InvoicePayment",
    "JournalEntry",
    "JournalLine",
    "LeaveBalance",
    "LeaveRequest",
    "LeaveType",
    "PayrollItem",
    "PayrollRun",
    "PerformanceReview",
    "SalaryComponent",
    "SalaryRevision",
    "StatutoryRate",
    "TaxParameter",
    "TaxSlab",
    "User",
]
