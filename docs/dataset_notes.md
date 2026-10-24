# Dataset Notes

Source workbook: `01_LedgerForge_Python_Master_Dataset.xlsx`.

The workbook describes a fictional company and states that all employees, clients, vendors, emails, and numbers are generated for training. No real personal data should be treated as present.

## Task Mapping Used

| Task | Workbook sheets |
| --- | --- |
| Task 1 | First 10 rows of `employees`, plus `departments` |
| Task 2 | `departments`, `roles`, `employees`, `employee_assignments` |
| Task 3 | `employees`, `departments`, `employee_assignments` |
| Task 4 | Workbook-derived CSVs, with database seed focused on employees, salary structures, and attendance |

## License

The assignment text asks for a public HR dataset license. The supplied workbook is a fictional training dataset and does not include a separate public license. The project therefore documents it as a provided training source. If a public Kaggle source is later required, place the downloaded file under `data/raw/`, add its license here, and map it through the same seed script.

## Repeatability

The seed command uses primary-key upserts, so running it twice updates existing rows instead of duplicating them. Any fallback generated values use a fixed Faker seed: `20261013`.
