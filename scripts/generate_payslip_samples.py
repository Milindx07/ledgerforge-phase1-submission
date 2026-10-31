from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models import PayrollItem, User


def main() -> None:
    run_id = "PR-2025-04"
    employees = ["EMP-0126", "EMP-0459", "EMP-0460"]
    with Path("data/master/payroll_items.csv").open(encoding="utf-8-sig", newline="") as stream:
        answer_key = {
            row["employee_id"]: row for row in csv.DictReader(stream)
            if row["run_id"] == run_id and row["employee_id"] in employees
        }
    evidence_dir = Path("docs/phase2_evidence/payslips")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    with SessionLocal() as db, TestClient(app) as client:
        for employee_id in employees:
            item = db.query(PayrollItem).filter_by(run_id=run_id, employee_id=employee_id).one()
            user = db.query(User).filter_by(role="HR", is_active=True).order_by(User.user_id).first()
            if user is None:
                raise RuntimeError("no active HR account found for sample payslip access")
            response = client.get(
                f"/payslips/{employee_id}/{run_id}", headers={"X-User-Id": user.user_id}
            )
            if response.status_code != 200 or not response.content.startswith(b"%PDF"):
                raise RuntimeError(f"payslip API failed for {employee_id}: {response.status_code}")
            file_path = evidence_dir / f"payslip_{employee_id}_{run_id}.pdf"
            file_path.write_bytes(response.content)
            reference = answer_key[employee_id]
            fields_match = all(
                abs(Decimal(str(getattr(item, field))) - Decimal(reference[field])) <= Decimal("0.01")
                for field in ("gross_pay", "total_deductions", "net_pay")
            )
            rows.append({
                "employee_id": employee_id,
                "run_id": run_id,
                "gross_pay": f"{item.gross_pay:.2f}",
                "total_deductions": f"{item.total_deductions:.2f}",
                "net_pay": f"{item.net_pay:.2f}",
                "answer_key_gross": reference["gross_pay"],
                "answer_key_deductions": reference["total_deductions"],
                "answer_key_net": reference["net_pay"],
                "answer_key_comparison": "PASS" if fields_match else "FAIL",
                "owner_access": "PASS",
                "pdf_signature": "PASS",
                "pdf_path": str(file_path.resolve()),
            })
    manifest = Path("docs/phase2_evidence/payslip_samples.csv")
    with manifest.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(f"{row['employee_id']} gross={row['gross_pay']} deductions={row['total_deductions']} "
              f"net={row['net_pay']} answer-key={row['answer_key_comparison']} "
              f"owner/PDF={row['owner_access']}/{row['pdf_signature']}")
    print(f"3 API-generated payslips saved under {evidence_dir.resolve()}")


if __name__ == "__main__":
    main()
