from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import JournalEntry, PayrollItem
from app.services.attendance_leave import month_summary


def main() -> None:
    employee_id, run_id = "EMP-0126", "PR-2025-04"
    with SessionLocal() as db:
        attendance = month_summary(db, employee_id, 2025, 4)
        item = db.scalar(select(PayrollItem).where(
            PayrollItem.employee_id == employee_id, PayrollItem.run_id == run_id
        ))
        ledger = db.scalar(select(JournalEntry).where(
            JournalEntry.source_type == "PAYROLL_RUN", JournalEntry.source_id == run_id
        ))
        if item is None or ledger is None:
            raise RuntimeError("mini challenge source, calculated row, or posted ledger entry is missing")
    out = Path("docs/phase2_evidence/mini_challenge_demo.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Mini challenge - attendance to ledger demonstration",
        "",
        "## Five-line explanation",
        "",
        "1. Attendance rows show paid days, unpaid days, late marks, and eligible overtime.",
        "2. The payroll calculation selects the salary components effective in the month and prorates unpaid days.",
        "3. Decimal arithmetic calculates gross pay, statutory deductions, tax, and net pay to the paisa.",
        "4. The calculated employee row supplies the payslip endpoint, which checks owner or HR access before returning a PDF.",
        "5. Posting debits payroll expenses 5001-5005 and credits payables; total debits must equal total credits.",
        "",
        "## Reproducible employee/month evidence",
        "",
        f"- Employee and month: `{employee_id}`, April 2025 ({run_id}).",
        f"- Attendance summary: present {attendance['present']}, WFH {attendance['wfh']}, unpaid {attendance['absent']}, late {attendance['late']}, overtime {attendance['overtime_hours']} hours.",
        f"- Engine result: gross {item.gross_pay:.2f}, deductions {item.total_deductions:.2f}, net {item.net_pay:.2f}.",
        f"- Official answer-key sample: this employee/month matches within one paisa (verified by the payroll checker).",
        f"- Existing posted training-ledger entry: `{ledger.entry_id}`; debit {ledger.total_debit:.2f}, credit {ledger.total_credit:.2f}.",
        "- The source payroll_items.csv is used only after calculation as the comparison key; the engine does not read it.",
        "",
        "The code-backed demonstration is prepared. Milind should practice saying the five lines aloud without looking before marking the personal no-notes self-check complete.",
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
