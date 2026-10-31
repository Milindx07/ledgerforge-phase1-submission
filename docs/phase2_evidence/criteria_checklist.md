# Phase 2 criteria verification

Status labels refer to the supplied Phase 2 task guidance. Evidence files live in this repository.

## Task 6 - Attendance and leave

- **PASS** - Attendance, leave, holiday, and leave-balance models are in the Phase 2 migration and full data loader.
- **PASS** - Attendance imports in batches of 5,000; the full source contains 150,155 attendance rows.
- **PASS** - Monthly summary returns present, work from home, unpaid absence, late count, and overtime hours.
- **PASS** - `MISSING_CHECKOUT` records stay visible and do not earn unverified overtime; README documents the rule.
- **PASS** - Leave can be submitted, approved, and rejected. Pending/used/balance days update, and insufficient balance is refused.
- **PASS** - Weekends and company holidays are excluded from leave-day counts; an unpaid half day is 0.5 loss-of-pay day.
- **PASS** - Three April 2025 employee summaries were counted from CSV and compared with the API in `attendance_hand_check.csv`.
- **PASS** - Half-day leave and its 0.5 balance change are described in the README design notes.

## Task 7 - Payroll calculation

- **PASS** - Plain-language rule notes and a Decimal/floating-point example are in `payroll_rules.md`.
- **PASS** - The engine uses Decimal arithmetic and independently creates 7,340 payroll rows in `exports/payroll_run.csv`.
- **PASS** - Real reference rows compare component, gross, deduction, net, and employer-cost fields in the regression test.
- **PASS** - A row-level cause log is generated at `exports/payroll_mismatch_log.csv`.
- **NOT MET** - The required 99% match is not reached: 6,694 / 7,340 rows (91.20%) match within the official one-paisa tolerance.
- **PARTIAL** - Remaining causes are explicitly grouped in the mismatch log. Source data does not supply sales incentive inputs, spot-award decisions, or employee loan/advance schedules; additional tax/ESI differences remain.

## Task 8 - Payslips

- **PASS** - `GET /payslips/{employee_id}/{run_id}` returns JSON; its `/pdf` route returns the generated PDF.
- **PASS** - Payslips use Indian currency grouping and show net pay prominently.
- **PASS** - Owner/HR access is allowed and a stranger is refused; tests cover JSON and PDF access.
- **PASS** - Three April 2025 PDF samples match the supplied reference totals; values are recorded in `payslip_samples.csv`.
- **PASS** - The report contains a clear screenshot of the generated EMP-0459 payslip.

## Task 9 - Double-entry ledger

- **PASS** - Chart of accounts, journal entries, and journal lines are loaded.
- **PASS** - Unbalanced entries are refused with a clear error.
- **PASS** - Posted journals cannot be edited; corrections create a reversing entry.
- **PASS** - Account balances are calculated by date.
- **PASS** - Payroll debits expense accounts 5001-5005 and credits payables; a journal sample is in `journal_payroll_sample.csv`.
- **PASS** - The supplied accounting checker passes all five controls, including balanced journals and payroll-ledger equality.

## Task 10 - Invoices and payments

- **PASS** - Client, invoice, item, and payment models are included in the migration and data loader.
- **PASS** - Draft, sent, part-paid, overdue, paid, and cancelled states are handled; overdue status is derived when an open invoice passes its due date.
- **PASS** - Invoice posting debits receivables and credits revenue/GST; receipts debit bank and credit receivables.
- **PASS** - Draft/cancelled invoices do not post; posting and payment debits/credits are tested.
- **PASS** - The receivables check passes, and a three-client sample is in `receivables_sample.csv`.
- **PASS** - README documents the credit-note/reversal design for cancelling an already-posted invoice; the current cancel endpoint is draft-only.

## Mini challenge and report

- **PASS** - Five-line attendance-to-payroll-to-payslip-to-ledger explanation is in `mini_challenge_demo.md`.
- **PASS** - The demonstration uses EMP-0126 for April 2025 and includes its attendance summary, payroll values, payslip, and posted journal.
- **PERSONAL SELF-CHECK** - The report provides prompts for explaining gross-to-net and debit/credit without notes; only the learner can verify that aloud.
- **PASS** - The 3-page PDF has name, track, phase, clickable repository/tag links, a five-task evidence table, test/checker results, learning notes, problems/solutions, and a Phase 3 plan.
- **PASS** - The PDF embeds an actual payslip screenshot and its task evidence links are clickable.
- **PENDING** - Upload the PDF to the programme submission form after reviewing the unmet payroll accuracy requirement.
