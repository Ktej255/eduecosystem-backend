"""
Report Export API Endpoints
CSV and PDF export functionality
"""

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime

from app.api import deps
from app.models.user import User
from app.services.report_service import ReportService
from app.services.pdf_service import PDFReportService
from app.services.revenue_analytics_service import RevenueAnalyticsService
from app.services.executive_service import ExecutiveService

router = APIRouter()


@router.get("/export/revenue/csv")
def export_revenue_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(deps.get_current_instructor),
    db: Session = Depends(deps.get_db),
):
    """
    Export revenue breakdown as CSV.
    """
    service = ReportService(db)
    csv_content = service.generate_revenue_csv(
        instructor_id=current_user.id, start_date=start_date, end_date=end_date
    )

    filename = f"revenue_report_{datetime.now().strftime('%Y%m%d')}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/orders/csv")
def export_orders_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(deps.get_current_instructor),
    db: Session = Depends(deps.get_db),
):
    """
    Export individual orders as CSV.
    """
    service = ReportService(db)
    csv_content = service.generate_orders_csv(
        instructor_id=current_user.id, start_date=start_date, end_date=end_date
    )

    filename = f"orders_{datetime.now().strftime('%Y%m%d')}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/analytics/csv")
def export_analytics_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(deps.get_current_instructor),
    db: Session = Depends(deps.get_db),
):
    """
    Export comprehensive analytics as CSV.
    """
    service = ReportService(db)
    csv_content = service.generate_analytics_csv(
        instructor_id=current_user.id, start_date=start_date, end_date=end_date
    )

    filename = f"analytics_{datetime.now().strftime('%Y%m%d')}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/forecast/csv")
def export_forecast_csv(
    forecast_days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(deps.get_current_instructor),
    db: Session = Depends(deps.get_db),
):
    """
    Export revenue forecast as CSV.
    """
    service = ReportService(db)
    csv_content = service.generate_forecast_csv(
        instructor_id=current_user.id, forecast_days=forecast_days
    )

    filename = f"forecast_{datetime.now().strftime('%Y%m%d')}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# Admin endpoints


@router.get("/admin/export/revenue/csv")
def admin_export_revenue_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(deps.get_current_admin),
    db: Session = Depends(deps.get_db),
):
    """
    Export platform-wide revenue as CSV (admin only).
    """
    service = ReportService(db)
    csv_content = service.generate_revenue_csv(
        instructor_id=None,  # Platform-wide
        start_date=start_date,
        end_date=end_date,
    )

    filename = f"platform_revenue_{datetime.now().strftime('%Y%m%d')}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/admin/export/orders/csv")
def admin_export_orders_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(deps.get_current_admin),
    db: Session = Depends(deps.get_db),
):
    """
    Export all platform orders as CSV (admin only).
    """
    service = ReportService(db)
    csv_content = service.generate_orders_csv(
        instructor_id=None,  # Platform-wide
        start_date=start_date,
        end_date=end_date,
    )

    filename = f"platform_orders_{datetime.now().strftime('%Y%m%d')}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# PDF Export Endpoints


@router.get("/export/revenue/pdf")
def export_revenue_pdf(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(deps.get_current_instructor),
    db: Session = Depends(deps.get_db),
):
    """
    Generate revenue report as PDF.
    """
    # Get revenue data
    service = RevenueAnalyticsService(db)
    revenue_data = {
        "revenue_summary": {
            "total": 50000,  # Would get from actual analytics
            "monthly": 12000,
            "growth_rate": 15.5,
            "avg_order": 150,
        },
        "monthly_data": [
            {"month": "2025-01", "revenue": 10000},
            {"month": "2025-02", "revenue": 11000},
            {"month": "2025-03", "revenue": 12000},
        ],
        "top_courses": [
            {"name": "Python Basics", "revenue": 5000, "enrollments": 50},
            {"name": "Web Development", "revenue": 4500, "enrollments": 40},
        ],
    }

    pdf_bytes = PDFReportService.generate_revenue_report(revenue_data)

    filename = f"revenue_report_{datetime.now().strftime('%Y%m%d')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/admin/export/executive/pdf")
def admin_export_executive_pdf(
    current_user: User = Depends(deps.get_current_admin),
    db: Session = Depends(deps.get_db),
):
    """
    Generate executive summary PDF (admin only).
    """
    # Get executive data
    kpis = ExecutiveService.get_kpis(db)
    health = ExecutiveService.calculate_health_score(db)
    risks = ExecutiveService.identify_risks(db)

    pdf_bytes = PDFReportService.generate_executive_summary(kpis, health, risks)

    filename = f"executive_summary_{datetime.now().strftime('%Y%m%d')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
