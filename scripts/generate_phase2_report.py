from __future__ import annotations

from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "Python_MILIND_KUMAR_Phase2_Report.pdf"
EVIDENCE = ROOT / "docs" / "phase2_evidence"
PAGE_W, PAGE_H = A4
NAVY = colors.HexColor("#10233F")
BLUE = colors.HexColor("#176B87")
PALE = colors.HexColor("#EAF3F7")
INK = colors.HexColor("#1B2733")
MUTED = colors.HexColor("#536273")
GREEN = colors.HexColor("#16734A")
AMBER = colors.HexColor("#A25A00")
RED = colors.HexColor("#A12B2B")


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 13 * mm, PAGE_W, 13 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.drawString(18 * mm, PAGE_H - 8.5 * mm, "PYTHON DEVELOPER  /  PHASE 2")
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, 10 * mm, "MILIND KUMAR  •  Python Developer  •  31 October 2026")
    canvas.drawRightString(PAGE_W - 18 * mm, 10 * mm, f"{doc.page}")
    canvas.restoreState()


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleX", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=24, leading=27, textColor=NAVY, alignment=TA_LEFT, spaceAfter=3 * mm))
styles.add(ParagraphStyle(name="NameCenteredX", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=25, textColor=NAVY, alignment=TA_CENTER, spaceAfter=1 * mm))
styles.add(ParagraphStyle(name="ReportTitleX", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=20, leading=23, textColor=NAVY, alignment=TA_CENTER, spaceAfter=1 * mm))
styles.add(ParagraphStyle(name="SubCenteredX", parent=styles["Normal"], fontSize=9, leading=12, textColor=MUTED, alignment=TA_CENTER, spaceAfter=3 * mm))
styles.add(ParagraphStyle(name="SubX", parent=styles["Normal"], fontSize=10, leading=14, textColor=MUTED, spaceAfter=3 * mm))
styles.add(ParagraphStyle(name="H1X", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=NAVY, spaceBefore=2 * mm, spaceAfter=2 * mm))
styles.add(ParagraphStyle(name="H2X", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=BLUE, spaceBefore=1.5 * mm, spaceAfter=1 * mm))
styles.add(ParagraphStyle(name="BodyX", parent=styles["BodyText"], fontSize=8.6, leading=12, textColor=INK, spaceAfter=1.7 * mm))
styles.add(ParagraphStyle(name="SmallX", parent=styles["BodyText"], fontSize=7.5, leading=10, textColor=MUTED))
styles.add(ParagraphStyle(name="CellX", parent=styles["BodyText"], fontSize=7.2, leading=9.1, textColor=INK))
styles.add(ParagraphStyle(name="CellBoldX", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=7.2, leading=9.1, textColor=NAVY))
styles.add(ParagraphStyle(name="WhiteX", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8.4, leading=11, textColor=colors.white))
styles.add(ParagraphStyle(name="MetricX", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=15, leading=17, textColor=NAVY, alignment=TA_CENTER))
styles.add(ParagraphStyle(name="MetricLabelX", parent=styles["BodyText"], fontSize=7.2, leading=9, textColor=MUTED, alignment=TA_CENTER))
styles.add(ParagraphStyle(name="CenterX", parent=styles["BodyText"], fontSize=8, leading=10, textColor=MUTED, alignment=TA_CENTER))


def P(text, style="BodyX"):
    return Paragraph(text, styles[style])


def pill(text, color):
    style = ParagraphStyle(f"pill{color.hexval()}", parent=styles["CellBoldX"], textColor=color, alignment=TA_CENTER)
    return Paragraph(text, style)


def cropped_slip(source: Path, target: Path):
    im = PILImage.open(source).convert("RGB")
    # The generated payslip has the complete itemized content in its upper region;
    # crop excess paper space so the evidence remains legible in the report.
    im.crop((40, 35, im.width - 35, min(im.height, 850))).save(target, quality=95)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    slip_png = EVIDENCE / "payslips" / "payslip_EMP-0459_PR-2025-04.png"
    slip_crop = EVIDENCE / "payslips" / "payslip_EMP-0459_PR-2025-04-report-crop.jpg"
    cropped_slip(slip_png, slip_crop)

    doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                          topMargin=20 * mm, bottomMargin=17 * mm,
                          title="LedgerForge Phase 2 Review", author="MILIND KUMAR",
                          subject="Python Developer Phase 2 tasks 6 to 10 evidence",
                          creator="LedgerForge Phase 2 report")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="main", frames=frame, onPage=header_footer)])
    story = []

    # Page 1: overview, required links, five-task evidence matrix.
    story += [Spacer(1, 1 * mm), P("MILIND KUMAR", "NameCenteredX"),
              P("LedgerForge: Core Development", "ReportTitleX"),
              P("Python Developer | Phase 2 | Days 6-10 | 31 October 2026", "SubCenteredX")]
    repo = "https://github.com/Milindx07/ledgerforge-phase1-submission"
    tag = repo + "/tree/phase-2"
    header_data = [[P("REPOSITORY", "WhiteX"), P("PHASE TAG", "WhiteX")],
                   [P(f'<link href="{repo}" color="#176B87">ledgerforge-phase1-submission</link>', "CellX"),
                    P(f'<link href="{tag}" color="#176B87">phase-2</link>', "CellX")]]
    ht = Table(header_data, colWidths=[122 * mm, 52 * mm])
    ht.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("BACKGROUND", (0, 1), (-1, 1), PALE),
                            ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#C5D5E0")),
                            ("INNERGRID", (0, 0), (-1, -1), .4, colors.HexColor("#C5D5E0")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 7),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story += [ht, Spacer(1, 3 * mm)]
    metrics = [[P("19", "MetricX"), P("5 / 5", "MetricX"), P("91.20%", "MetricX"), P("3 / 3", "MetricX")],
               [P("automated tests passed", "MetricLabelX"), P("accounting checks passed", "MetricLabelX"), P("payroll key match", "MetricLabelX"), P("sample payslips matched", "MetricLabelX")]]
    mt = Table(metrics, colWidths=[43.5 * mm] * 4)
    mt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PALE), ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#C5D5E0")),
                            ("INNERGRID", (0, 0), (-1, -1), .4, colors.white), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story += [P("Task-by-task status and evidence", "H1X")]
    def evidence_link(label, path):
        url = f"{repo}/blob/phase-2/{path}"
        return f'<link href="{url}" color="#176B87">{label}</link>'

    tasks = [
        ("Task 6 · Attendance & leave", "Implemented; checks pass", "150,155 rows loaded in 5,000-row chunks; 3 employee/month CSV-to-API hand checks match. Leave balance, rejection, weekends and holidays are tested; missing checkout earns no OT. " + evidence_link("Hand-check table", "docs/phase2_evidence/attendance_hand_check.csv"), GREEN),
        ("Task 7 · Payroll", "Implemented; target not met", "7,340 rows calculated independently with Decimal. Official checker: 6,694 / 7,340 match (91.20%); the 99% goal is unmet. " + evidence_link("Rules", "docs/phase2_evidence/payroll_rules.md") + " | " + evidence_link("Mismatch log", "exports/payroll_mismatch_log.csv"), RED),
        ("Task 8 · Payslips", "Implemented; sample checks pass", "Owner/HR access and stranger refusal are tested. Three April PDFs match the supplied reference within INR 0.01. " + evidence_link("Visible screenshot", "docs/phase2_evidence/payslips/payslip_EMP-0459_PR-2025-04.png") + " | " + evidence_link("Results", "docs/phase2_evidence/payslip_samples.csv"), GREEN),
        ("Task 9 · Accounting", "Implemented; checks pass", "Balanced entries, immutable posting, reversals, account balances and payroll posting. All 5 supplied accounting checks pass. " + evidence_link("Journal sample", "docs/phase2_evidence/journal_payroll_sample.csv") + " | " + evidence_link("Checker", "docs/phase2_evidence/phase2_check_results.txt"), GREEN),
        ("Task 10 · Invoicing", "Implemented; checks pass", "Draft, sent, part-paid, overdue, paid and cancelled states; GST posting and receivables. All 5 supplied controls pass. " + evidence_link("Three-client receivables", "docs/phase2_evidence/receivables_sample.csv"), GREEN),
    ]
    rows = [[P("TASK", "WhiteX"), P("RESULT", "WhiteX"), P("EVIDENCE", "WhiteX")]]
    for task, result, evidence, color in tasks:
        rows.append([P(task, "CellBoldX"), pill(result, color), P(evidence, "CellX")])
    table = Table(rows, colWidths=[38 * mm, 39 * mm, 98 * mm], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), BLUE), ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                               ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F8FA")]),
                               ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#CBD6DE")),
                               ("INNERGRID", (0, 0), (-1, -1), .35, colors.HexColor("#D8E0E6")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5),
                               ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 5),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story += [table, Spacer(1, 2 * mm), mt, Spacer(1, 2 * mm),
              P("Readiness note: Task 7 is below its required 99% accuracy. Remaining mismatches are recorded in the linked log; this report does not claim every acceptance criterion passed.", "SmallX")]

    # Page 2: actual output evidence and mini-challenge flow.
    story += [PageBreak(), Spacer(1, 2 * mm), P("Working proof & mini challenge", "TitleX"),
              P("Attendance → payroll → payslip → ledger", "SubX"),
              P("Mini challenge evidence · employee EMP-0126 · April 2025 (PR-2025-04) | " +
                evidence_link("full walkthrough", "docs/phase2_evidence/mini_challenge_demo.md"), "H1X")]
    lines = [
        "1. Attendance and approved leave establish paid days, loss-of-pay days, late marks and eligible overtime.",
        "2. Payroll uses salary components effective in the month and applies statutory rates to the earned amounts.",
        "3. Decimal calculations produce gross pay, PF, ESI, professional tax, TDS, deductions and net pay.",
        "4. The payslip reads the calculated payroll result and checks owner or HR access before returning JSON or PDF.",
        "5. Payroll posting debits expense accounts 5001-5005 and credits payables; the journal must balance.",
    ]
    flow = Table([[P(x, "CellX")] for x in lines], colWidths=[175 * mm])
    flow.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PALE), ("BOX", (0, 0), (-1, -1), .6, colors.HexColor("#C5D5E0")),
                              ("INNERGRID", (0, 0), (-1, -1), .4, colors.white), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story += [flow, Spacer(1, 2 * mm),
              P("CSV/API hand check: EMP-0002, EMP-0004 and EMP-0006 for April 2025 all matched. Full tests: 19 passed. Accounting/receivables checker: 5/5 passed. Payroll checker: 6,694 of 7,340 within INR 0.01 (91.20%). Full outputs are linked in the evidence table.", "BodyX"),
              P("Sample generated payslip · the original PDF is included in docs/phase2_evidence/payslips/", "H2X")]
    img = Image(str(slip_crop))
    max_w, max_h = 112 * mm, 115 * mm
    ratio = min(max_w / img.imageWidth, max_h / img.imageHeight)
    img.drawWidth = img.imageWidth * ratio
    img.drawHeight = img.imageHeight * ratio
    story += [img, Spacer(1, 1 * mm),
              P("Actual API-generated payslip screenshot. The Indian-format example shows the net amount prominently. All three checked sample totals match; this small sample does not change the full-run accuracy result.", "SmallX"),
              Spacer(1, 2 * mm),
              P("Self-check", "H1X"),
              P("I can follow the README to set up the project, migrate the database, load the data, run tests, and open the API docs. I can explain gross-to-net and why debits must equal credits using this workflow. For the no-notes self-check, I will say the five steps aloud with the notes closed.", "BodyX")]

    # Page 3: learning, issues and next phase plan.
    story += [PageBreak(), Spacer(1, 2 * mm), P("Learning, fixes & next steps", "TitleX"),
              P("Review notes for Phase 2", "SubX"), P("What I learned", "H1X"),
              P("I learned how attendance and leave rules affect payable days and payroll. Decimal arithmetic avoids binary floating-point surprises when calculating money. A payslip should be generated from a payroll result and protected by an access check. A journal entry needs equal debits and credits, and corrections should use a reversal. The supplied payroll answer key also showed me why a calculation must be checked against every row, not only a few examples.", "BodyX"),
              P("Problems I hit and how I addressed them", "H1X")]
    problems = [
        ("Schema history", "The existing phone migration conflicted with the initial schema. I made the upgrade safe to rerun and added the missing Alembic template; a fresh migration check now reports no pending model changes."),
        ("Source data", "Attendance is large, so the loader processes it in 5,000-row batches. Missing checkout rows remain visible but do not earn overtime."),
        ("Payroll source gaps", "The 646 mismatches are logged: variable-pay inputs or eligibility (336), TDS (129), loan/advance recovery inputs (126), ESI (34), overtime (2), and rounding or other components (19). I used the written workbook rules and kept the answer key out of the calculation. The official match is 91.20%, below the 99% requirement."),
        ("Demo authentication", "The sample payslip endpoint uses X-User-Id for owner/HR checks. This demonstrates authorization in tests but is not production identity/authentication."),
    ]
    pr = [[P("ISSUE", "WhiteX"), P("ACTION / RESULT", "WhiteX")]] + [[P(a, "CellBoldX"), P(b, "CellX")] for a, b in problems]
    pt = Table(pr, colWidths=[39 * mm, 136 * mm], repeatRows=1)
    pt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), BLUE), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F8FA")]),
                            ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#CBD6DE")), ("INNERGRID", (0, 0), (-1, -1), .35, colors.HexColor("#D8E0E6")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story += [pt, Spacer(1, 2 * mm), P("My plan for Phase 3", "H1X"),
              P("I will first ask for the missing bonus, incentive, loan-recovery, and tax-withholding rules or source inputs, then update the payroll engine and rerun all 7,340 rows against the checker. I will strengthen the sample identity check into proper authentication and role-based access, add audit history for payroll and invoice changes, and build Phase 3 reporting on top of the ledger. I will keep regression tests and the mismatch log while improving the accuracy toward the required 99%.", "BodyX"),
              P("Evidence files", "H2X"),
              P("Repository evidence: attendance hand checks, mini-challenge walkthrough, payslip samples and PDFs, full check output, payroll run, and mismatch log are linked in the repository. Dataset records are fictional training data; sample statutory amounts are not for real payroll use.", "SmallX"),
              Spacer(1, 3 * mm),
              P("Submitted code and evidence: <link href=\"https://github.com/Milindx07/ledgerforge-phase1-submission/tree/phase-2\" color=\"#176B87\">open the Phase 2 repository tag</link>.", "CenterX")]

    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    main()
