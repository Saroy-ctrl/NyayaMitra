"""
services/pdf_generator.py -- ReportLab PDF generation for NyayaMitra.

Converts the DrafterAgent's plain-text draft into a print-ready A4 PDF.

Output path: backend/generated_pdfs/nyayamitra_{session_id}.pdf

Note about Devanagari:
    For Devanagari support, download NotoSansDevanagari-Regular.ttf from
    fonts.google.com/noto and place it at backend/fonts/NotoSansDevanagari-Regular.ttf.
    Register with:
        pdfmetrics.registerFont(TTFont('NotoSansDevanagari', 'fonts/NotoSansDevanagari-Regular.ttf'))
    For now Helvetica is used as fallback since the font file may not be present.
"""

import logging
from datetime import date
from pathlib import Path

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

logger = logging.getLogger(__name__)

PDF_OUTPUT_DIR = Path(__file__).parent.parent / "generated_pdfs"

# Heuristic: lines shorter than this that are ALL CAPS (or start with #)
# are treated as headings rather than body text
_HEADING_MIN_LEN = 3
_HEADING_MAX_LEN = 120


def _is_heading(line: str) -> bool:
    """Return True if the line looks like a section heading."""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("#"):
        return True
    # ALL-CAPS line of reasonable length (allow spaces, colons, digits)
    clean = stripped.replace(" ", "").replace(":", "").replace("/", "").replace("-", "")
    if (
        _HEADING_MIN_LEN <= len(stripped) <= _HEADING_MAX_LEN
        and clean.isupper()
        and len(clean) >= 3
    ):
        return True
    return False


def _build_styles() -> dict[str, ParagraphStyle]:
    """Build and return the ReportLab paragraph style set."""
    base = getSampleStyleSheet()

    styles: dict[str, ParagraphStyle] = {
        "title": ParagraphStyle(
            "NMTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "heading": ParagraphStyle(
            "NMHeading",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            alignment=TA_LEFT,
            spaceAfter=6,
            spaceBefore=10,
        ),
        "body": ParagraphStyle(
            "NMBody",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            alignment=TA_LEFT,
            spaceAfter=6,
        ),
        "footer": ParagraphStyle(
            "NMFooter",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
        ),
    }
    return styles


def _safe_para(text: str, style: ParagraphStyle) -> Paragraph:
    """
    Create a ReportLab Paragraph, escaping characters that break XML parsing.
    Replaces bare & with &amp; and strips any NUL bytes.
    """
    # ReportLab uses a subset of XML internally
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("\x00", "")
    return Paragraph(text, style)


async def generate_pdf(draft_text: str, session_id: str) -> str:
    """
    Render a plain-text legal document draft to an A4 PDF.

    Args:
        draft_text: Full document text from DrafterAgent (plain text, newline-delimited).
        session_id: Used to name the output file.

    Returns:
        Absolute path (str) to the generated PDF file.
    """
    PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = PDF_OUTPUT_DIR / f"nyayamitra_{session_id}.pdf"

    styles = _build_styles()

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    story = []

    lines = draft_text.splitlines()

    # --- Title: use first non-empty line ---
    title_text = "Legal Document"
    first_content_idx = 0
    for idx, line in enumerate(lines):
        if line.strip():
            title_text = line.strip().lstrip("#").strip()
            first_content_idx = idx + 1
            break

    story.append(_safe_para(title_text, styles["title"]))
    story.append(HRFlowable(width="100%", thickness=1, spaceAfter=10))

    # --- Body: remaining lines ---
    for line in lines[first_content_idx:]:
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 0.3 * cm))
            continue
        if _is_heading(stripped):
            clean_heading = stripped.lstrip("#").strip()
            story.append(_safe_para(clean_heading, styles["heading"]))
        else:
            story.append(_safe_para(stripped, styles["body"]))

    # --- Footer ---
    story.append(Spacer(1, 0.8 * cm))
    today = date.today().strftime("%d-%m-%Y")
    footer_text = f"Generated by NyayaMitra | {today} | For informational purposes only"
    story.append(HRFlowable(width="100%", thickness=0.5, spaceAfter=6))
    story.append(_safe_para(footer_text, styles["footer"]))

    doc.build(story)
    logger.info("PDF written: %s (%d bytes)", pdf_path, pdf_path.stat().st_size)
    return str(pdf_path)
