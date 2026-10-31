# Payroll rules and accuracy notes

The payroll engine uses `Decimal` values and rounds currency with `ROUND_HALF_UP` to two decimal places. It calculates from employee, assignment, salary, attendance, statutory-rate, tax, review, and holiday inputs. `payroll_items.csv` is used only as the independent comparison key after a run.

## Rules implemented

- Loss of pay is prorated by calendar days in the payroll month. An unpaid half day is 0.5 day.
- Overtime is allowed only for roles flagged as eligible, uses monthly fixed gross / 208 x 2, and is capped at 50 hours. `MISSING_CHECKOUT` overtime is excluded.
- Employee and employer PF use 12% of basic pay, capped at a 15,000 wage base, when the employee profile marks PF applicable.
- Employee ESI uses 0.75% and employer ESI 3.25% when monthly fixed gross is at or below 21,000.
- Professional tax is 200 when gross is at least 25,000.
- TDS follows the supplied tax slabs and parameters, with the monthly projected fixed-pay tax plus incremental tax for variable pay.
- Performance bonuses are calculated in April using the employee's performance rating; October festival bonuses use the role level. The rating rates are 2%, 4.5%, and 6.5% for ratings 3, 4, and 5, based on the supplied examples.

## Decimal example

Binary floating point can produce `0.1 + 0.2 = 0.30000000000000004`. With decimal arithmetic, `Decimal("0.1") + Decimal("0.2")` equals `0.3`, so money is not affected by binary representation noise.

## Remaining comparison gaps

The provided source tables do not give the sales-performance inputs needed to calculate sales incentives, individual spot-award decisions, or employee loan/advance schedules. The current full-run checker result is 6,694 of 7,340 rows (91.20%). The 646 mismatches are logged by employee and run in `exports/payroll_mismatch_log.csv`; the main causes are variable-pay inputs or eligibility (336), TDS differences (129), loan/advance recovery inputs (126), ESI rule/base differences (34), overtime differences (2), and rounding or other components (19). The required 99% threshold is not met.
