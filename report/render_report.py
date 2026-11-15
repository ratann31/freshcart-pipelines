from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "23bcs227_data_engineering_assignment.pdf"


def footer(canvas, document):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(18 * mm, 10 * mm, "23BCS227 | From Git to Gold")
    canvas.drawRightString(192 * mm, 10 * mm, f"Page {document.page}")
    canvas.restoreState()


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="TitleCentered", parent=styles["Title"], alignment=TA_CENTER,
    fontSize=18, leading=22, spaceAfter=12,
))
styles.add(ParagraphStyle(
    name="H1Custom", parent=styles["Heading1"], fontSize=14, leading=17,
    textColor=colors.HexColor("#174a73"), spaceBefore=8, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="H2Custom", parent=styles["Heading2"], fontSize=11, leading=14,
    textColor=colors.HexColor("#245f8f"), spaceBefore=6, spaceAfter=3,
))
styles.add(ParagraphStyle(
    name="BodyCustom", parent=styles["BodyText"], fontSize=8.5, leading=11,
    spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="Small", parent=styles["BodyText"], fontSize=7.5, leading=9,
))


def p(text, style="BodyCustom"):
    text = escape(text).replace("\n", "<br/>")
    return Paragraph(text, styles[style])


def table(data, widths=None):
    converted = []
    for row in data:
        converted.append([
            Paragraph(escape(str(value)), styles["Small"]) for value in row
        ])
    result = Table(converted, colWidths=widths, repeatRows=1)
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9eaf7")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#7f9db5")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return result


def build():
    doc = BaseDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=16 * mm,
        title="23bcs227 Data Engineering Assignment",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                  id="normal")
    doc.addPageTemplates([PageTemplate(id="main", frames=frame, onPage=footer)])

    story = [
        p("From Git to Gold – Data Engineering Assignment", "TitleCentered"),
        p("Roll number: 23BCS227", "BodyCustom"),
        p("Repository: https://github.com/ratann31/freshcart-pipelines", "BodyCustom"),
        p("Evidence note: this report uses verified notebook outputs, repository code, and local tests. It does not invent RabbitMQ runtime or bonus results.", "BodyCustom"),
        p("A. Git and CI/CD (15 marks)", "H1Custom"),
        p("The repository contains FreshCart ELT, Mage material, RabbitMQ code, tests, requirements, and GitHub Actions. Meaningful commits cover setup, ELT, B3–B5, Mage experiments, quality evidence, and RabbitMQ implementation. A local commit is visible only locally until it is pushed."),
        table([
            ["Command", "Purpose"],
            ["git init", "Creates a local repository."],
            ["git add train.py", "Stages a file."],
            ["git commit -m \"message\"", "Saves a staged snapshot locally."],
            ["git remote add origin URL", "Names the GitHub remote."],
            ["git push -u origin main", "Uploads main and sets upstream."],
            ["git pull origin main", "Downloads and merges remote main."],
        ], [55 * mm, 115 * mm]),
        p("The CI workflow runs on pushes and pull requests, installs requirements, and runs pytest. A deliberately false split assertion produced the red experiment; restoring it produced the final green run. Stream tests cover valid, malformed, and invalid-every-tenth payloads."),
        p("B. FreshCart ELT on Snowflake (30 marks)", "H1Custom"),
        p("Credentials are supplied through Google Colab Secrets and are not stored in the repository. The verified baseline is:"),
        table([
            ["Check", "Actual result"],
            ["Bronze raw orders", "8"],
            ["Silver cleaned / Quarantine", "6 / 2"],
            ["Deduplicated / Gold orders", "4 / 4"],
            ["Gold revenue", "INR 7,785.00"],
            ["Loyalty points / rejection rate", "126 / 25%"],
        ], [80 * mm, 90 * mm]),
        p("Gold rows were ORD-1001 (Silver, INR 1,250, 12 points), ORD-1002 (Silver, INR 3,536 after USD conversion, 35 points), ORD-1003 (Platinum, INR 2,100, 63 points), and ORD-1005 (Gold, INR 899, 16 points)."),
        p("API adapters standardize source field names. ORD-1003 is duplicated and the latest valid record survives the ROW_NUMBER() ordering. ORD-1005 joins the Gold SCD2 interval while ORD-1001 joins the earlier Silver interval."),
        p("B3: before validation, ORD-1006 had bad_email and bad_pincode; after the change it also had unsupported_currency. It stayed quarantined. Repeated runs displayed nine raw copies but one distinct order."),
        p("B4 prediction and actual: CUST-02 became Gold on 2026-08-15; ORD-1002 points changed 35→70; total points changed 126→161; four Gold orders and INR 7,785 revenue stayed unchanged. All predictions matched actual results. row_hash plus a business-key MERGE makes Gold reruns idempotent."),
        p("B5: a mock order made the quality gate fail with PROBLEM output. Cleanup removed it from Bronze, Gold, and Quarantine; the rebuilt Silver and Gold checks passed and the mock count was zero. ELT is preferred because raw data remains auditable and Snowflake performs scalable SQL transformations; ETL wins when data must be transformed before loading for privacy or target-system limitations."),
        p("C. Mage Iris ML pipeline (20 marks)", "H1Custom"),
        p("The graph is load_iris → prepare_data → train_model, with parallel save_results and evaluate_model branches. Iris has 150 rows (120 train, 30 test). max_depth=3 achieved 1.000 accuracy and created 30 predictions. The intentional depth-1 gate failed at 0.633 and did not create iris_predictions.csv."),
        Preformatted("[[10, 0, 0],\\n [ 0, 9, 0],\\n [ 0, 0,11]]", styles["Code"]),
        p("The updated metadata connects train_model to both downstream blocks and a Mage tunnel URL was generated. The custom source contains @custom and @test, but one run still reported that Mage could not discover a decorated function. C4 must be rerun after a clean Mage restart before it is claimed complete."),
        p("D. RabbitMQ food-order streaming (20 marks)", "H1Custom"),
        p("stream/dispatcher.py and stream/driver.py implement the durable topic exchange rapido-dispatch, JSON fields id/city/zone/type/ts, an invalid message every tenth message, private exclusive queues, manual basic_ack, and basic_nack(requeue=False) for invalid data. The local payload-validation tests pass."),
        p("For the implemented four-word keys, # matches all keys; ride.# all rides; ride.delhi.# Delhi rides; ride.*.north.# north-zone rides; ride.*.*.premium premium rides; and ride.mumbai.# Mumbai rides. A crash before ACK causes redelivery after connection close. requeue=True can loop permanently invalid messages. A live two-minute run with three drivers and one dispatcher, plus screenshots, remains pending."),
        p("Bonus (+10)", "H1Custom"),
        p("The bonus setup is implemented in stream/bonus_consumer.py and stream/bonus_producer.py. The consumer buffers FreshCart-style messages for one minute, reuses the existing landing/load and transformation functions, and uses the Gold MERGE. It still must be run twice against RabbitMQ and Snowflake to verify unchanged Gold totals; no live bonus result is claimed yet."),
        p("E. Report and viva (15 marks)", "H1Custom"),
        Preformatted("GitHub → GitHub Actions / pytest\n       ├→ Colab APIs → Landing → Snowflake Bronze → Silver → Gold\n       ├→ Mage: load → prepare → train → predictions/evaluation\n       └→ RabbitMQ dispatcher → topic exchange → drivers\n                                      └→ bonus consumer → landing", styles["Code"]),
        p("Reflection: The main debugging issue was separating notebook state from pipeline logic. Closed Snowflake connections caused later SQL cells to fail, while repeated extraction runs accumulated raw records. Fresh connections, an explicit SQL-file runner, Silver deduplication, and a Gold MERGE fixed the root causes. The same evidence-first method verified unsupported-currency validation and the Mage depth-1 quality gate."),
        p("Screenshot appendix checklist", "H1Custom"),
        p("Attach actual screenshots for repository structure, Git log and CI states; Snowflake connection and B1–B5 outputs; Mage graph, depth 1–5 experiments, metrics, metadata and custom test; RabbitMQ management, dispatcher, drivers and ACK/NACK; and bonus landing/Bronze/Gold idempotency. Never include credentials."),
    ]
    doc.build(story)
    print(OUTPUT)


if __name__ == "__main__":
    build()
