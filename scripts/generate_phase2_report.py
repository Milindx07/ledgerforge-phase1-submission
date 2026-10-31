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
    canvas.drawString(18 * mm, PAGE_H - 8.5 * mm, "LEDGERFORGE  /  PHASE 2 REVIEW")
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18 * mm, 10 * mm, "MILIND KUMAR  •  Python Developer  •  31 October 2026")
    canvas.drawRightString(PAGE_W - 18 * mm, 10 * mm, f"{doc.page}")
    canvas.restoreState()


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleX", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=24, leading=27, textColor=NAVY, alignment=TA_LEFT, spaceAfter=3 * mm))
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
    slip_png = EVIDENCE / "payslips" / "payslip_EMP-0126_PR-2025-04.png"
    slip_crop = EVIDENCE / "payslips" / "payslip_EMP-0126_PR-2025-04-report-crop.jpg"
    cropped_slip(slip_png, slip_crop)

    doc = BaseDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                          topMargin=20 * mm, bottomMargin=17 * mm, title="LedgerForge Phase 2 Review")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="main", frames=frame, onPage=header_footer)])
    story = []

    # Page 1: overview, required links, five-task evidence matrix.
    story += [Spacer(1, 3 * mm), P("Phase 2 review", "TitleX"),
              P("Core development  |  Tasks 6–10  |  Python Developer", "SubX")]
    repo = "https://github.com/Milindx07/ledgerforge-phase1-submission"
    tag = repo + "/tree/phase-2"
    header_data = [[P("MILIND KUMAR", "WhiteX"), P("REPOSITORY", "WhiteX"), P("PHASE TAG", "WhiteX")],
                   [P("Track: Python Developer<br/>Phase: 2<br/>Report date: 31 October 2026", "CellX"),
                    P(f'<link href="{repo}" color="#176B87">ledgerforge-phase1-submission</link>', "CellX"),
                    P(f'<link href="{tag}" color="#176B87">phase-2</link>', "CellX")]]
    ht = Table(header_data, colWidths=[56 * mm, 70 * mm, 48 * mm])
    ht.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("BACKGROUND", (0, 1), (-1, 1), PALE),
                            ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#C5D5E0")),
                            ("INNERGRID", (0, 0), (-1, -1), .4, colors.HexColor("#C5D5E0")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 7),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story += [ht, Spacer(1, 3 * mm)]
    metrics = [[P("15", "MetricX"), P("5 / 5", "MetricX"), P("55.46%", "MetricX"), P("3 / 3", "MetricX")],
               [P("automated tests passed", "MetricLabelX"), P("accounting checks passed", "MetricLabelX"), P("payroll key match", "MetricLabelX"), P("sample payslips matched", "MetricLabelX")]]
    mt = Table(metrics, colWidths=[43.5 * mm] * 4)
    mt.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PALE), ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#C5D5E0")),
                            ("INNERGRID", (0, 0), (-1, -1), .4, colors.white), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story += [mt, Spacer(1, 2 * mm),
              P("Task-by-task status and evidence", "H1X")]
    tasks = [
        ("Task 6 · Attendance & leave", "Implemented; checks pass", "150,155 attendance rows loaded in 5,000-row chunks; 3 employee/month CSV-to-API hand checks match. MISSING_CHECKOUT is retained and excluded from overtime. Leave tests cover balance, weekends and holidays.", GREEN),
        ("Task 7 · Payroll", "Implemented; target not met", "7,340 rows generated independently with Decimal. Official checker: 4,071 / 7,340 match within INR 0.01 (55.46%); acceptance goal 99% is unmet. See mismatch log.", RED),
        ("Task 8 · Payslips", "Implemented; sample checks pass", "Owner/HR gate and stranger refusal are tested. Three generated April 2025 PDFs match answer-key totals within ₹0.01; see payslip samples and PDFs.", GREEN),
        ("Task 9 · Accounting", "Implemented; checks pass", "Balanced posted entries, read-only posting, reversal, account balances and monthly payroll posting. Official accounting checker passes all 5 controls.", GREEN),
        ("Task 10 · Invoicing", "Implemented; checks pass", "Draft/cancel/post/payment lifecycle and receivables; posting/payment debit-credit directions tested. Official receivables check passes.", GREEN),
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
    story += [table, Spacer(1, 2 * mm),
              P("Readiness note: the build and control checks are in place, but Task 7 does not meet the 99% payroll accuracy requirement. This report records the measured result; it should not be submitted as proof that every acceptance criterion passed.", "SmallX")]

    # Page 2: actual output evidence and mini-challenge flow.
    story += [PageBreak(), Spacer(1, 2 * mm), P("Working proof & mini challenge", "TitleX"),
              P("Attendance → payroll → payslip → ledger", "SubX"),
              P("Mini challenge evidence · employee EMP-0126 · April 2025 (PR-2025-04)", "H1X")]
    lines = [
        "1. Attendance rows show paid days, unpaid days, late marks and eligible overtime.",
        "2. Payroll selects salary components effective in the month and prorates unpaid days.",
        "3. Decimal arithmetic calculates gross, deductions, tax and net pay to the paisa.",
        "4. The calculated row supplies the payslip endpoint; owner/HR access is checked before PDF delivery.",
        "5. Posting debits payroll expense accounts 5001–5005 and credits payables; total debits equal credits.",
    ]
    flow = Table([[P(x, "CellX")] for x in lines], colWidths=[175 * mm])
    flow.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PALE), ("BOX", (0, 0), (-1, -1), .6, colors.HexColor("#C5D5E0")),
                              ("INNERGRID", (0, 0), (-1, -1), .4, colors.white), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story += [flow, Spacer(1, 2 * mm),
              P("CSV/API hand check: EMP-0002, EMP-0004 and EMP-0006 for April 2025 all matched. Full tests: 15 passed. Accounting/receivables checker: 5/5 passed. Payroll checker: 4,071 of 7,340 within INR 0.01 (55.46%).", "BodyX"),
              P("Sample generated payslip · the original PDF is included in docs/phase2_evidence/payslips/", "H2X")]
    img = Image(str(slip_crop))
    max_w, max_h = 112 * mm, 115 * mm
    ratio = min(max_w / img.imageWidth, max_h / img.imageHeight)
    img.drawWidth = img.imageWidth * ratio
    img.drawHeight = img.imageHeight * ratio
    story += [img, Spacer(1, 1 * mm),
              P("Actual API-generated PDF screenshot. Sample employee totals match the supplied reference; this three-row sample does not change the full-run payroll accuracy result.", "SmallX"),
              Spacer(1, 2 * mm),
              P("Self-check", "H1X"),
              P("I can use the README to set up the project, migrate the database, load the data, run the tests, and open the API docs. I can explain that a migration is a versioned change to the database structure. I still need to practise explaining the five mini-challenge steps aloud without looking at the notes.", "BodyX")]

    # Page 3: learning, issues and next phase plan.
    story += [PageBreak(), Spacer(1, 2 * mm), P("Learning, fixes & next steps", "TitleX"),
              P("Review notes for Phase 2", "SubX"), P("What I learned", "H1X"),
              P("I learned how attendance and leave rules affect payable days and payroll. Decimal arithmetic avoids binary floating-point surprises when calculating money. A payslip should be generated from a payroll result and protected by an access check. A journal entry needs equal debits and credits, and corrections should use a reversal. The supplied payroll answer key also showed me why a calculation must be checked against every row, not only a few examples.", "BodyX"),
              P("Problems I hit and how I addressed them", "H1X")]
    problems = [
        ("Schema history", "The existing phone migration conflicted with the initial schema. I made the upgrade safe to rerun and added the missing Alembic template; a fresh migration check now reports no pending model changes."),
        ("Source data", "Attendance is large, so the loader processes it in 5,000-row batches. Missing checkout rows remain visible but do not earn overtime."),
        ("Payroll policy gap", "The kit inputs do not specify the variable-pay matrix/eligibility or complete TDS method. I wrote an independent Decimal engine and a row-level mismatch log rather than loading the answer key as calculation data. The measured 55.46% match remains below the 99% requirement."),
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
              P("I will first confirm the official bonus eligibility/rate table and the TDS projection rules, then update the payroll engine and rerun all 7,340 rows until the checker reaches the required 99%. I will replace the demo identity header with proper authentication and role-based access, add audit logging for payroll and invoice changes, and build the Phase 3 reporting workflows on top of the verified payroll and ledger data. I will keep the mismatch log and regression tests so future changes do not lower the accuracy.", "BodyX"),
              P("Evidence files", "H2X"),
              P("Repository evidence: docs/phase2_evidence/attendance_hand_check.csv, docs/phase2_evidence/payslip_samples.csv, generated sample payslip PDFs, docs/phase2_evidence/mini_challenge_demo.md, exports/payroll_run.csv, and exports/payroll_mismatch_log.csv. Dataset records are fictional training data; sample statutory amounts are not for real payroll use.", "SmallX"),
              Spacer(1, 3 * mm),
              P("Submitted code and evidence: <link href=\"https://github.com/Milindx07/ledgerforge-phase1-submission/tree/phase-2\" color=\"#176B87\">open the Phase 2 repository tag</link>.", "CenterX")]

    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    main()
