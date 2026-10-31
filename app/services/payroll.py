from __future__ import annotations

from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")
ZERO = Decimal("0.00")


def money(value: Decimal | str | int | float) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def indian_currency(value: Decimal | str | int | float) -> str:
    amount = money(value)
    sign = "-" if amount < 0 else ""
    whole, fraction = f"{abs(amount):.2f}".split(".")
    if len(whole) > 3:
        last_three, prefix = whole[-3:], whole[:-3]
        groups = []
        while prefix:
            groups.insert(0, prefix[-2:])
            prefix = prefix[:-2]
        whole = ",".join(groups + [last_three])
    return f"{sign}₹{whole}.{fraction}"


def progressive_tax(annual_taxable_income: Decimal, slabs: list[dict[str, Decimal | None]]) -> Decimal:
    income = max(Decimal("0"), Decimal(annual_taxable_income))
    tax = Decimal("0")
    for slab in sorted(slabs, key=lambda item: Decimal(item["income_from"])):
        low = Decimal(slab["income_from"])
        high = Decimal(slab["income_to"]) if slab.get("income_to") is not None else None
        rate = Decimal(slab["rate_percent"]) / Decimal("100")
        taxable = max(Decimal("0"), min(income, high) - low) if high is not None else max(Decimal("0"), income - low)
        tax += taxable * rate
    return money(tax)


def calculate_gross_to_net(
    *,
    components: dict[str, Decimal],
    days_employed: Decimal,
    lop_days: Decimal,
    calendar_days: int,
    overtime_hours: Decimal,
    eligible_for_overtime: bool,
    variable_pay: Decimal,
    pf_applicable: bool,
    esi_applicable: bool,
    statutory: dict[str, Decimal],
    professional_tax_threshold: Decimal,
    professional_tax_monthly: Decimal,
    monthly_tds: Decimal = ZERO,
) -> dict[str, Decimal]:
    if calendar_days <= 0:
        raise ValueError("calendar_days must be positive")
    if lop_days < 0 or lop_days > days_employed:
        raise ValueError("LOP days must be between zero and employed days")
    payable_days = max(Decimal("0"), days_employed - lop_days)
    factor = payable_days / Decimal(calendar_days)
    earned = {name: money(amount * factor) for name, amount in components.items()}
    basic = earned.get("BASIC", ZERO)
    monthly_fixed = sum(components.values(), Decimal("0"))
    ot_hours = min(Decimal("50"), max(Decimal("0"), Decimal(overtime_hours))) if eligible_for_overtime else ZERO
    ot_pay = money(monthly_fixed / statutory.get("WORKING_HOURS_PER_MONTH", Decimal("208"))
                    * statutory.get("OT_MULTIPLIER", Decimal("2")) * ot_hours)
    variable = money(variable_pay)
    gross = money(sum(earned.values(), ZERO) + ot_pay + variable)
    pf_base = min(basic, statutory.get("PF_WAGE_CEILING", Decimal("15000"))) if pf_applicable else ZERO
    pf_employee = money(pf_base * statutory.get("PF_EMPLOYEE_RATE", Decimal("12")) / 100)
    pf_employer = money(pf_base * statutory.get("PF_EMPLOYER_RATE", Decimal("12")) / 100)
    esi_eligible = esi_applicable and monthly_fixed <= statutory.get("ESI_WAGE_LIMIT", Decimal("21000"))
    esi_employee = money(gross * statutory.get("ESI_EMPLOYEE_RATE", Decimal("0.75")) / 100) if esi_eligible else ZERO
    esi_employer = money(gross * statutory.get("ESI_EMPLOYER_RATE", Decimal("3.25")) / 100) if esi_eligible else ZERO
    pt = professional_tax_monthly if gross >= professional_tax_threshold else ZERO
    deductions = money(pf_employee + esi_employee + pt + monthly_tds)
    return {
        **{name.lower(): amount for name, amount in earned.items()},
        "earned_fixed_pay": money(sum(earned.values(), ZERO)),
        "monthly_fixed_gross": money(monthly_fixed),
        "payable_days": payable_days,
        "lop_days": Decimal(lop_days),
        "overtime_hours_paid": ot_hours,
        "overtime_pay": ot_pay,
        "variable_pay": variable,
        "gross_pay": gross,
        "pf_employee": pf_employee,
        "esi_employee": esi_employee,
        "professional_tax": money(pt),
        "tds": money(monthly_tds),
        "total_deductions": deductions,
        "net_pay": money(gross - deductions),
        "pf_employer": pf_employer,
        "esi_employer": esi_employer,
        "employer_cost": money(gross + pf_employer + esi_employer),
    }


def run_period_bounds(period_start: date) -> tuple[date, date, int]:
    last_day = monthrange(period_start.year, period_start.month)[1]
    return period_start, date(period_start.year, period_start.month, last_day), last_day
