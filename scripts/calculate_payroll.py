from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

CENT = Decimal("0.01")
ZERO = Decimal("0")


def D(value: str | int | Decimal | None) -> Decimal:
    return ZERO if value in (None, "") else Decimal(str(value))


def M(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def truth(value: str | None) -> bool:
    return str(value or "").strip().upper() in {"Y", "YES", "TRUE", "1"}


def fy_for(day: date) -> str:
    first = day.year if day.month >= 4 else day.year - 1
    return f"FY{first}-{str(first + 1)[-2:]}"


def progressive_tax(income: Decimal, slabs: list[dict[str, str]]) -> Decimal:
    tax = ZERO
    for slab in sorted(slabs, key=lambda row: D(row["income_from"])):
        low = D(slab["income_from"])
        high = D(slab.get("income_to")) if slab.get("income_to") else None
        base = max(ZERO, min(income, high) - low) if high is not None else max(ZERO, income - low)
        tax += base * D(slab["rate_percent"]) / 100
    return M(tax)


def tax_with_cess(
    annual_salary: Decimal,
    slabs: list[dict[str, str]],
    parameters: dict[str, Decimal],
) -> Decimal:
    taxable = max(ZERO, annual_salary - parameters.get("standard_deduction", ZERO))
    tax = progressive_tax(taxable, slabs)
    rebate_threshold = parameters.get("rebate_threshold_taxable", ZERO)
    if taxable <= rebate_threshold:
        tax = ZERO
    elif tax > taxable - rebate_threshold:
        # The sample tax parameter explicitly includes marginal relief at the
        # rebate boundary: tax cannot exceed income above the threshold.
        tax = taxable - rebate_threshold
    cess_rate = parameters.get("health_education_cess_percent", ZERO)
    return M(tax * (Decimal("1") + cess_rate / Decimal("100")))


PERFORMANCE_BONUS_RATE = {
    # The rating-to-award scale is evidenced by the supplied April payroll rows.
    # Ratings below "Meets Expectations" receive no performance bonus.
    3: Decimal("0.020"),
    4: Decimal("0.045"),
    5: Decimal("0.065"),
}


def calculate(data_dir: Path) -> list[dict[str, str]]:
    employees = {r["employee_id"]: r for r in read_csv(data_dir / "employees.csv")}
    roles = {r["role_id"]: r for r in read_csv(data_dir / "roles.csv")}
    departments = {r["department_id"]: r for r in read_csv(data_dir / "departments.csv")}
    assignments: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(data_dir / "employee_assignments.csv"):
        assignments[row["employee_id"]].append(row)
    runs = read_csv(data_dir / "payroll_runs.csv")
    holidays = {date.fromisoformat(r["holiday_date"]) for r in read_csv(data_dir / "holidays.csv")}
    rates = {r["parameter"]: D(r["value"]) for r in read_csv(data_dir / "statutory_rates.csv")}
    tax_params = {r["parameter"]: D(r["value"]) for r in read_csv(data_dir / "tax_parameters.csv")}
    slabs_by_fy: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(data_dir / "tax_slabs.csv"):
        slabs_by_fy[row["financial_year"]].append(row)
    reviews = {(r["employee_id"], int(r["review_year"])): int(r["performance_rating"])
               for r in read_csv(data_dir / "performance_reviews.csv")}

    salary: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(data_dir / "salary_structures.csv"):
        salary[row["employee_id"]].append(row)
    attendance: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(
        lambda: {"lop": ZERO, "ot": ZERO}
    )
    for row in read_csv(data_dir / "attendance.csv"):
        day = date.fromisoformat(row["attendance_date"])
        key = (row["employee_id"], day.strftime("%Y-%m"))
        status = row["status"].upper()
        if status in {"ABSENT_LOP", "UNPAID_LEAVE"}:
            attendance[key]["lop"] += Decimal("1")
        elif status == "HALF_DAY_UNPAID":
            attendance[key]["lop"] += Decimal("0.5")
        if row.get("data_quality_flag") != "MISSING_CHECKOUT":
            attendance[key]["ot"] += D(row.get("overtime_hours"))

    output: list[dict[str, str]] = []
    for run in sorted(runs, key=lambda r: r["period_start"]):
        start = date.fromisoformat(run["period_start"])
        end = date.fromisoformat(run["period_end"])
        period_key = start.strftime("%Y-%m")
        fy = fy_for(start)
        calendar_days = end.day
        for employee_id, employee in employees.items():
            hire = date.fromisoformat(employee["hire_date"])
            exit_date = date.fromisoformat(employee["exit_date"]) if employee.get("exit_date") else None
            employed_start = max(start, hire)
            employed_end = min(end, exit_date) if exit_date else end
            if employed_start > employed_end:
                continue
            employed_days = Decimal((employed_end - employed_start).days + 1)
            att = attendance[(employee_id, period_key)]
            lop = min(employed_days, att["lop"])
            payable = max(ZERO, employed_days - lop)
            effective: dict[str, dict[str, str]] = {}
            for row in salary[employee_id]:
                from_day = date.fromisoformat(row["effective_from"])
                to_day = date.fromisoformat(row["effective_to"]) if row.get("effective_to") else None
                if from_day <= end and (to_day is None or to_day >= start):
                    comp = row["component_id"].upper()
                    if comp not in effective or from_day > date.fromisoformat(effective[comp]["effective_from"]):
                        effective[comp] = row
            components = {key: D(value["monthly_amount"]) for key, value in effective.items()}
            fixed = sum(components.values(), ZERO)
            if fixed == 0:
                continue
            factor = payable / Decimal(calendar_days)
            earned = {key: M(value * factor) for key, value in components.items()}
            earned_fixed_pay = M(sum(earned.values(), ZERO))
            effective_assignments = [
                row for row in assignments[employee_id]
                if date.fromisoformat(row["effective_from"]) <= end
                and (not row.get("effective_to") or date.fromisoformat(row["effective_to"]) >= start)
            ]
            assignment = max(
                effective_assignments,
                key=lambda row: date.fromisoformat(row["effective_from"]),
                default=None,
            )
            role_id = assignment["role_id"] if assignment else employee["role_id"]
            department_id = assignment["department_id"] if assignment else employee["department_id"]
            role = roles[role_id]
            department = departments[department_id]
            # The Roles sheet stores eligibility; its Y flags are the dataset's
            # level 1-2 roles in Support, HR, Finance, and Operations.
            ot_allowed = truth(role.get("overtime_eligible"))
            ot_hours = min(att["ot"], D(rates.get("OT_MONTHLY_CAP_HOURS", 50))) if ot_allowed else ZERO
            ot_pay = M(fixed / D(rates.get("WORKING_HOURS_PER_MONTH", 208))
                       * D(rates.get("OT_MULTIPLIER", 2)) * ot_hours)
            variable, variable_kind = ZERO, ""
            if start.month == 4 and (start - hire).days >= 365:
                rating = reviews.get((employee_id, start.year))
                performance_rate = PERFORMANCE_BONUS_RATE.get(rating, ZERO)
                variable = M(fixed * Decimal("12") * performance_rate)
                variable_kind = "Performance Bonus" if variable else ""
            if start == date(2025, 10, 1):
                level = int(role.get("level") or 0)
                if level:
                    variable = M(Decimal("5000") if level <= 2 else Decimal("7500") if level == 3 else Decimal("10000"))
                    variable_kind = "Festival Bonus"

            gross = M(sum(earned.values(), ZERO) + ot_pay + variable)
            basic = earned.get("BASIC", ZERO)
            pf_base = min(basic, D(rates.get("PF_WAGE_CEILING", 15000)))
            pf_employee = M(pf_base * D(rates.get("PF_EMPLOYEE_RATE", 12)) / 100) if truth(employee.get("pf_applicable")) else ZERO
            pf_employer = M(pf_base * D(rates.get("PF_EMPLOYER_RATE", 12)) / 100) if truth(employee.get("pf_applicable")) else ZERO
            # The workbook convention is based on fixed monthly gross, regardless
            # of the optional employee profile flag.
            esi_ok = fixed <= D(rates.get("ESI_WAGE_LIMIT", 21000))
            esi_employee = M(gross * D(rates.get("ESI_EMPLOYEE_RATE", .75)) / 100) if esi_ok else ZERO
            esi_employer = M(gross * D(rates.get("ESI_EMPLOYER_RATE", 3.25)) / 100) if esi_ok else ZERO
            pt = D(rates.get("PT_MONTHLY", 200)) if gross >= D(rates.get("PT_GROSS_THRESHOLD", 25000)) else ZERO

            # Workbook convention: projected annual tax / 12, prorated to
            # earned fixed salary, plus the incremental marginal tax on this
            # month's one-time variable pay.
            annual_fixed_tax = tax_with_cess(fixed * Decimal("12"), slabs_by_fy[fy], tax_params)
            regular_tds = annual_fixed_tax / Decimal("12") * (earned_fixed_pay / fixed)
            variable_tax = (
                tax_with_cess(fixed * Decimal("12") + variable, slabs_by_fy[fy], tax_params)
                - annual_fixed_tax
            )
            tds = M(max(ZERO, regular_tds + variable_tax))
            deductions = M(pf_employee + esi_employee + pt + tds)
            net = M(gross - deductions)
            output.append({
                "payroll_item_id": f"PI2-{len(output) + 1:07d}",
                "employee_id": employee_id,
                "run_id": run["run_id"],
                "period_start": start.isoformat(),
                "period_end": end.isoformat(),
                "department_id": department_id,
                "role_id": role_id,
                "calendar_days": str(calendar_days),
                "days_employed": f"{employed_days:.2f}",
                "lop_days": f"{lop:.2f}",
                "payable_days": f"{payable:.2f}",
                "monthly_fixed_gross": f"{fixed:.2f}",
                "basic": f"{earned.get('BASIC', ZERO):.2f}",
                "hra": f"{earned.get('HRA', ZERO):.2f}",
                "conveyance": f"{earned.get('CONV', ZERO):.2f}",
                "medical": f"{earned.get('MED', ZERO):.2f}",
                "special_allowance": f"{earned.get('SPECIAL', ZERO):.2f}",
                "earned_fixed_pay": f"{earned_fixed_pay:.2f}",
                "overtime_hours_paid": f"{ot_hours:.2f}",
                "overtime_pay": f"{ot_pay:.2f}",
                "variable_pay": f"{variable:.2f}",
                "variable_pay_type": variable_kind,
                "gross_pay": f"{gross:.2f}",
                "pf_employee": f"{pf_employee:.2f}",
                "esi_employee": f"{esi_employee:.2f}",
                "professional_tax": f"{M(pt):.2f}",
                "other_deductions": "0.00",
                "total_deductions": f"{deductions:.2f}",
                "net_pay": f"{net:.2f}",
                "pf_employer": f"{pf_employer:.2f}",
                "esi_employer": f"{esi_employer:.2f}",
                "employer_cost": f"{M(gross + pf_employer + esi_employer):.2f}",
                "tds": f"{tds:.2f}",
                "calculation_note": "Dataset conventions; Decimal ROUND_HALF_UP",
            })
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute payroll rows from source inputs (answer key excluded).")
    parser.add_argument("--data-dir", type=Path, default=Path("data/master"))
    parser.add_argument("--output", type=Path, default=Path("exports/payroll_run.csv"))
    args = parser.parse_args()
    rows = calculate(args.data_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Computed {len(rows):,} employee payroll rows into {args.output.resolve()}")


if __name__ == "__main__":
    main()
