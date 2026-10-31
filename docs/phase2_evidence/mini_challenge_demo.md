# Mini challenge - attendance to ledger demonstration

## Five-line explanation

1. Attendance rows show paid days, unpaid days, late marks, and eligible overtime.
2. The payroll calculation selects the salary components effective in the month and prorates unpaid days.
3. Decimal arithmetic calculates gross pay, statutory deductions, tax, and net pay to the paisa.
4. The calculated employee row supplies the payslip endpoint, which checks owner or HR access before returning a PDF.
5. Posting debits payroll expenses 5001-5005 and credits payables; total debits must equal total credits.

## Reproducible employee/month evidence

- Employee and month: `EMP-0126`, April 2025 (PR-2025-04).
- Attendance summary: present 12, WFH 8, unpaid 0, late 0, overtime 0.00 hours.
- Engine result: gross 80195.76, deductions 2000.00, net 78195.76.
- Official answer-key sample: this employee/month matches within one paisa (verified by the payroll checker).
- Existing posted training-ledger entry: `JE-000105`; debit 53363392.08, credit 53363392.08.
- The source payroll_items.csv is used only after calculation as the comparison key; the engine does not read it.

The five steps and employee/month output are documented for the mini challenge. For the personal no-notes self-check, I should be able to explain the flow aloud with this document closed.
