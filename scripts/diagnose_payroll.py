from __future__ import annotations

import argparse
import csv
from collections import Counter
from decimal import Decimal
from pathlib import Path


def read(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return {(row["run_id"], row["employee_id"]): row for row in csv.DictReader(stream)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare engine output to the kit answer key after calculation.")
    parser.add_argument("--reference", type=Path, default=Path("data/master/payroll_items.csv"))
    parser.add_argument("--engine", type=Path, default=Path("exports/payroll_run.csv"))
    parser.add_argument("--output", type=Path, default=Path("exports/payroll_mismatch_log.csv"))
    args = parser.parse_args()
    official, calculated = read(args.reference), read(args.engine)
    records = []
    causes = Counter()
    for key, expected in official.items():
        actual = calculated.get(key)
        if actual is None:
            causes["missing_engine_row"] += 1
            records.append({"run_id": key[0], "employee_id": key[1], "cause": "missing_engine_row"})
            continue
        mismatched = [
            field for field in ("gross_pay", "total_deductions", "net_pay")
            if abs(Decimal(expected[field]) - Decimal(actual[field])) > Decimal("0.01")
        ]
        if not mismatched:
            continue
        if abs(Decimal(expected["variable_pay"]) - Decimal(actual["variable_pay"])) > Decimal("0.01"):
            cause = "variable_bonus_inputs_or_eligibility_not_specified"
        elif abs(Decimal(expected["tds"]) - Decimal(actual["tds"])) > Decimal("0.01"):
            cause = "tax_withholding_projection_or_deduction_rule_not_specified"
        elif abs(Decimal(expected["overtime_pay"]) - Decimal(actual["overtime_pay"])) > Decimal("0.01"):
            cause = "overtime_eligibility_or_rounding_rule"
        else:
            cause = "downstream_rounding_or_unmapped_deduction"
        causes[cause] += 1
        records.append({
            "run_id": key[0], "employee_id": key[1], "cause": cause,
            "mismatched_fields": ",".join(mismatched),
            "expected_gross": expected["gross_pay"], "engine_gross": actual["gross_pay"],
            "expected_deductions": expected["total_deductions"],
            "engine_deductions": actual["total_deductions"],
            "expected_net": expected["net_pay"], "engine_net": actual["net_pay"],
            "expected_variable_pay": expected["variable_pay"],
            "engine_variable_pay": actual["variable_pay"],
            "expected_tds": expected["tds"], "engine_tds": actual["tds"],
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(records[0]) if records else ["run_id", "employee_id", "cause"]
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    print(f"Answer-key rows compared after calculation: {len(official):,}")
    print(f"Rows matching within one paisa: {len(official) - len(records):,}")
    print("Mismatch causes:")
    for cause, count in sorted(causes.items()):
        print(f"  {cause}: {count:,}")
    print(f"Detailed mismatch log: {args.output.resolve()}")


if __name__ == "__main__":
    main()
