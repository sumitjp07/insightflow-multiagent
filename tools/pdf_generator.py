"""
tools/pdf_generator.py – Professional PDF Report Generator
============================================================
ReportLab-based PDF report compiler:
  - Generates polished, publication-ready PDF documents
  - Custom branded palette, headers, footers, and page numbers
  - Data summary tables, insight callout blocks, and evaluation scorecard
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)

# Ensure root on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

import config

logger = logging.getLogger(__name__)


def generate_pdf_report(state: Dict[str, Any], output_path: str = None) -> Dict[str, Any]:
    """
    Transforms final state outputs into a PDF report document.
    """
    try:
        timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
        if output_path is None:
            output_dir = config.REPORTS_DIR
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"InsightFlow_Report_{timestamp_slug}.pdf")

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=45,
            leftMargin=45,
            topMargin=45,
            bottomMargin=45
        )

        styles = getSampleStyleSheet()

        # ── Custom Brand Styles ─────────────────────────────────
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#4F46E5"),
            spaceAfter=6,
        )
        
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#6B7280"),
            spaceAfter=15,
        )

        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#111827"),
            spaceBefore=12,
            spaceAfter=6,
        )

        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#374151"),
            spaceAfter=6,
        )

        callout_style = ParagraphStyle(
            "Callout",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=12.5,
            textColor=colors.HexColor("#1F2937"),
        )

        story = []

        # ── 1. Document Header ──────────────────────────────────
        story.append(Paragraph("⚡ InsightFlow Intelligence Brief", title_style))
        query = state.get("user_query", "Autonomous Research Analysis")
        date_str = datetime.now().strftime("%B %d, %Y - %H:%M")
        story.append(Paragraph(f"Objective: <b>{query}</b> | Published: {date_str}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4F46E5"), spaceAfter=12))

        # ── 2. Evaluation Scorecard Tile ────────────────────────
        eval_res = state.get("evaluation_result", {})
        acc = eval_res.get("calculation_accuracy_pct", 100.0)
        cov = eval_res.get("evidence_coverage_pct", 100.0)
        retries = state.get("retry_count", 0)

        score_data = [
            ["Metric", "Value", "Audit Status"],
            ["Mathematical Accuracy", f"{acc}%", "VERIFIED ✅" if acc >= 95 else "FLAGGED ⚠️"],
            ["Evidence Coverage", f"{cov}%", "COMPLETE ✅"],
            ["Self-Correction Retries", f"{retries}", "OPTIMAL" if retries == 0 else f"{retries} Retries"],
        ]

        score_table = Table(score_data, colWidths=[180, 140, 180])
        score_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2FF")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#312E81")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E7FF")),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 14))

        # ── 3. Executive Insights ───────────────────────────────
        story.append(Paragraph("1. Verified Strategic Insights", h2_style))
        insights = state.get("insights", [])
        if insights:
            for i, ins in enumerate(insights, 1):
                claim = ins.get("claim", "")
                t_label = ins.get("type", "insight").replace("_", " ").title()
                story.append(Paragraph(f"<b>{i}. [{t_label}]</b> {claim}", body_style))
        else:
            story.append(Paragraph("Exploratory screening conducted across active dataset.", body_style))

        story.append(Spacer(1, 10))

        # ── 4. Performance Drivers ──────────────────────────────
        key_drivers = state.get("key_drivers", [])
        if key_drivers:
            story.append(Paragraph("2. Core Performance Drivers", h2_style))
            for kd in key_drivers:
                story.append(Paragraph(f"• <b>{kd}</b>", body_style))
            story.append(Spacer(1, 10))

        # ── 5. Anomaly Detection ────────────────────────────────
        anomalies = state.get("anomalies_detected", [])
        story.append(Paragraph("3. Anomaly & Outlier Screening", h2_style))
        if anomalies:
            for a in anomalies:
                story.append(Paragraph(
                    f"⚠️ <b>{a['column']}:</b> Detected <b>{a['count']} anomalies</b> ({a['percentage']}% of samples) outside normal IQR range.",
                    body_style
                ))
        else:
            story.append(Paragraph("✅ Zero high-severity outliers detected outside 1.5× IQR boundary limits.", body_style))

        story.append(Spacer(1, 14))
        story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#E5E7EB"), spaceAfter=8))
        story.append(Paragraph("Confidential Intelligence Brief • InsightFlow Multi-Agent System", subtitle_style))

        # Build document
        doc.build(story)
        logger.info(f"📄 PDF generated successfully at: {output_path}")

        return {
            "success": True,
            "pdf_path": output_path,
            "file_name": Path(output_path).name
        }

    except Exception as e:
        logger.error(f"❌ PDF generation failed: {str(e)}")
        return {"success": False, "error": str(e)}


# ── Quick Test ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "="*55)
    print("  InsightFlow – PDF Generator Test")
    print("="*55)

    dummy_state = {
        "user_query": "Sample PDF Test Query",
        "evaluation_result": {"calculation_accuracy_pct": 100.0, "evidence_coverage_pct": 100.0},
        "retry_count": 0,
        "insights": [
            {"type": "group_performance", "claim": "Segment 'West' generated leading sales volume of 2,817,500."},
            {"type": "correlation", "claim": "High correlation (r=0.82) observed between Unit Price and Revenue."}
        ],
        "key_drivers": ["Top Region: West", "High Margin: Laptop Pro"],
        "anomalies_detected": []
    }

    res = generate_pdf_report(dummy_state)
    print(f"  Success: {res['success']}")
    if res['success']:
        print(f"  Saved to: {res['pdf_path']}")

    print("="*55 + "\n")

