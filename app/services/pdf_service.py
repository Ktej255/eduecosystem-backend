"""
PDF Report Generation Service

Generates professional PDF reports for analytics, revenue, and comparisons.
Uses ReportLab for PDF creation and matplotlib for chart generation.
"""

import io
from typing import Optional, Dict, Any, List
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")  # Use non-GUI backend


class PDFReportService:
    """Service for generating PDF reports"""

    @staticmethod
    def generate_revenue_report(
        data: Dict[str, Any], company_name: str = "Eduecosystem"
    ) -> bytes:
        """
        Generate a professional revenue report PDF.

        Args:
            data: Revenue data including breakdown, trends, etc.
            company_name: Company name for header

        Returns:
            PDF bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1f77b4"),
            spaceAfter=30,
            alignment=TA_CENTER,
        )

        subtitle_style = ParagraphStyle(
            "CustomSubtitle",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.grey,
            spaceAfter=12,
            alignment=TA_CENTER,
        )

        # Title
        story.append(Paragraph(f"{company_name} Revenue Report", title_style))
        story.append(
            Paragraph(
                f"Generated on {datetime.now().strftime('%B %d, %Y')}", subtitle_style
            )
        )
        story.append(Spacer(1, 0.3 * inch))

        # Revenue Summary Table
        story.append(Paragraph("Revenue Summary", styles["Heading2"]))
        if "revenue_summary" in data:
            summary = data["revenue_summary"]
            summary_data = [
                ["Metric", "Value"],
                ["Total Revenue", f"${summary.get('total', 0):,.2f}"],
                ["Monthly Revenue", f"${summary.get('monthly', 0):,.2f}"],
                ["Growth Rate", f"{summary.get('growth_rate', 0):.1f}%"],
                ["Average Order Value", f"${summary.get('avg_order', 0):,.2f}"],
            ]

            t = Table(summary_data, colWidths=[3 * inch, 3 * inch])
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            story.append(t)
            story.append(Spacer(1, 0.3 * inch))

        # Revenue Chart
        if "monthly_data" in data:
            chart_img = PDFReportService._create_revenue_chart(data["monthly_data"])
            if chart_img:
                story.append(Paragraph("Revenue Trends", styles["Heading2"]))
                story.append(Image(chart_img, width=5 * inch, height=3 * inch))
                story.append(Spacer(1, 0.3 * inch))

        # Top Courses Table
        if "top_courses" in data:
            story.append(
                Paragraph("Top Revenue Generating Courses", styles["Heading2"])
            )
            course_data = [["Rank", "Course Name", "Revenue", "Enrollments"]]

            for i, course in enumerate(data["top_courses"][:10], 1):
                course_data.append(
                    [
                        str(i),
                        course.get("name", "N/A"),
                        f"${course.get('revenue', 0):,.2f}",
                        str(course.get("enrollments", 0)),
                    ]
                )

            t = Table(
                course_data, colWidths=[0.7 * inch, 2.5 * inch, 1.5 * inch, 1.3 * inch]
            )
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2ca02c")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.lightgrey),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )
            story.append(t)

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    @staticmethod
    def generate_executive_summary(
        kpis: Dict[str, Any],
        health: Dict[str, Any],
        risks: List[Dict[str, Any]],
        company_name: str = "Eduecosystem",
    ) -> bytes:
        """
        Generate executive summary PDF.

        Args:
            kpis: Platform KPIs
            health: Health score data
            risks: List of risk indicators
            company_name: Company name

        Returns:
            PDF bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            "ExecTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#d62728"),
            spaceAfter=30,
            alignment=TA_CENTER,
        )

        story.append(Paragraph(f"{company_name} Executive Summary", title_style))
        story.append(
            Paragraph(
                f"Report Date: {datetime.now().strftime('%B %d, %Y')}", styles["Normal"]
            )
        )
        story.append(Spacer(1, 0.3 * inch))

        # KPI Summary
        story.append(Paragraph("Key Performance Indicators", styles["Heading2"]))
        kpi_data = [
            ["KPI", "Current Value", "Status"],
            [
                "Monthly Active Users",
                f"{kpis.get('active_users', {}).get('monthly', 0):,}",
                "✓",
            ],
            [
                "Monthly Revenue",
                f"${kpis.get('revenue', {}).get('monthly', 0):,.2f}",
                "✓",
            ],
            [
                "Revenue Growth",
                f"{kpis.get('revenue', {}).get('growth_rate', 0):.1f}%",
                "✓" if kpis.get("revenue", {}).get("growth_rate", 0) >= 0 else "⚠",
            ],
            [
                "Completion Rate",
                f"{kpis.get('courses', {}).get('completion_rate', 0):.1f}%",
                "✓",
            ],
            [
                "Churn Rate",
                f"{kpis.get('business_metrics', {}).get('churn_rate', 0):.1f}%",
                "✓"
                if kpis.get("business_metrics", {}).get("churn_rate", 0) < 5
                else "⚠",
            ],
        ]

        t = Table(kpi_data, colWidths=[2.5 * inch, 2 * inch, 1 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d62728")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.lightcyan),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 0.3 * inch))

        # Platform Health
        story.append(Paragraph("Platform Health Score", styles["Heading2"]))
        health_score = health.get("score", 0)
        health_grade = health.get("grade", "N/A")
        health_trend = health.get("trend", "stable")

        health_data = [
            ["Health Score", "Grade", "Trend"],
            [f"{health_score}/100", health_grade, health_trend.upper()],
        ]

        t = Table(health_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch])

        # Color code based on score
        bg_color = (
            colors.green
            if health_score >= 80
            else colors.yellow
            if health_score >= 60
            else colors.red
        )

        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("BACKGROUND", (0, 1), (-1, 1), bg_color),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 1), (-1, 1), 14),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 0.3 * inch))

        # Risk Indicators
        if risks:
            story.append(Paragraph("Risk Indicators", styles["Heading2"]))
            risk_data = [["Type", "Severity", "Value", "Recommendation"]]

            for risk in risks[:5]:  # Top 5 risks
                risk_data.append(
                    [
                        risk.get("type", "N/A"),
                        risk.get("severity", "N/A").upper(),
                        str(risk.get("value", 0)),
                        risk.get("recommendation", "N/A")[:50] + "...",
                    ]
                )

            t = Table(risk_data, colWidths=[1.2 * inch, 1 * inch, 0.8 * inch, 3 * inch])
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ff7f0e")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.lightpink),
                    ]
                )
            )
            story.append(t)

        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    @staticmethod
    def _create_revenue_chart(monthly_data: List[Dict]) -> Optional[io.BytesIO]:
        """Create revenue trend chart using matplotlib"""
        try:
            months = [d["month"] for d in monthly_data]
            revenues = [d["revenue"] for d in monthly_data]

            plt.figure(figsize=(8, 4))
            plt.plot(months, revenues, marker="o", color="#1f77b4", linewidth=2)
            plt.title("Revenue Trend", fontsize=14, fontweight="bold")
            plt.xlabel("Month")
            plt.ylabel("Revenue ($)")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()

            # Save to buffer
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight")
            plt.close()

            img_buffer.seek(0)
            return img_buffer
        except Exception as e:
            print(f"Error creating chart: {e}")
            return None
