from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.core.database import SessionLocal
from app.services.attendance_leave import month_summary


def main() -> None:
    people = ["EMP-0002", "EMP-0004", "EMP-0006"]
    month_start = date(2025, 4, 1)
    month_end = date(2025, 4, 30)
    tally = {
        person: {"present": 0, "wfh": 0, "absent": Decimal("0"), "late": 0,
                 "overtime_hours": Decimal("0")}
        for person in people
    }
    with Path("data/master/attendance.csv").open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["employee_id"] not in tally:
                continue
            day = date.fromisoformat(row["attendance_date"])
            if not month_start <= day <= month_end:
                continue
            status = row["status"].upper()
            out = tally[row["employee_id"]]
            if status == "PRESENT":
                out["present"] += 1
            elif status == "WFH":
                out["wfh"] += 1
            elif status in {"ABSENT_LOP", "UNPAID_LEAVE"}:
                out["absent"] += Decimal("1")
            elif status == "HALF_DAY_UNPAID":
                out["absent"] += Decimal("0.5")
            if row.get("late_flag", "").upper() in {"Y", "YES", "TRUE"}:
                out["late"] += 1
            if row.get("data_quality_flag") != "MISSING_CHECKOUT" and row.get("overtime_hours"):
                out["overtime_hours"] += Decimal(row["overtime_hours"])
    result = []
    with SessionLocal() as db:
        for person in people:
            api = month_summary(db, person, 2025, 4)
            csv_values = tally[person]
            result.append({
                "employee_id": person,
                "month": "2025-04",
                **{f"csv_{key}": value for key, value in csv_values.items()},
                **{f"api_{key}": api[key] for key in api},
                "all_fields_match": str(all(csv_values[key] == api[key] for key in csv_values)).upper(),
            })
    output = Path("docs/phase2_evidence/attendance_hand_check.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = list(result[0])
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result)
    for row in result:
        print(f"{row['employee_id']} {row['month']}: CSV/API match={row['all_fields_match']} "
              f"present={row['csv_present']} WFH={row['csv_wfh']} absent={row['csv_absent']} "
              f"late={row['csv_late']} OT={row['csv_overtime_hours']}")
    print(f"Evidence saved to {output.resolve()}")


if __name__ == "__main__":
    main()
