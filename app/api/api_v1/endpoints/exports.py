"""
Export API Endpoints

API endpoints for data export functionality.
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services.export_service import ExportService

router = APIRouter()


@router.get("/analytics")
def export_analytics(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    format: str = Query("csv", pattern="^(csv|pdf|json)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """
    Export user analytics data.

    - **format**: Export format (csv, pdf, json)
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    """
    try:
        data = ExportService.export_analytics(
            db=db,
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date,
            format=format,
        )

        # Set appropriate content type
        content_type_map = {
            "csv": "text/csv",
            "pdf": "application/pdf",
            "json": "application/json",
        }

        filename_map = {
            "csv": f"analytics_{current_user.id}.csv",
            "pdf": f"analytics_{current_user.id}.pdf",
            "json": f"analytics_{current_user.id}.json",
        }

        return Response(
            content=data if isinstance(data, bytes) else data.encode("utf-8"),
            media_type=content_type_map[format],
            headers={
                "Content-Disposition": f'attachment; filename="{filename_map[format]}"'
            },
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/course/{course_id}")
def export_course(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    course_id: int,
    format: str = Query("json", pattern="^(json|pdf)$"),
):
    """
    Export course content for backup.

    - **course_id**: Course ID to export
    - **format**: Export format (json, pdf)

    Note: Only course creator or admin can export course content.
    """
    try:
        # TODO: Add permission check - only course creator or admin

        data = ExportService.export_course_content(
            db=db, course_id=course_id, format=format
        )

        content_type_map = {"json": "application/json", "pdf": "application/pdf"}

        filename_map = {
            "json": f"course_{course_id}.json",
            "pdf": f"course_{course_id}.pdf",
        }

        return Response(
            content=data if isinstance(data, bytes) else data.encode("utf-8"),
            media_type=content_type_map[format],
            headers={
                "Content-Disposition": f'attachment; filename="{filename_map[format]}"'
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user-data")
def export_user_data(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    format: str = Query("json", pattern="^(json|pdf)$"),
):
    """
    Export user's personal data (GDPR compliance).

    - **format**: Export format (json, pdf)

    Returns all personal data associated with the user's account.
    """
    try:
        data = ExportService.export_user_data(
            db=db, user_id=current_user.id, format=format
        )

        content_type_map = {"json": "application/json", "pdf": "application/pdf"}

        filename_map = {
            "json": f"user_data_{current_user.id}.json",
            "pdf": f"user_data_{current_user.id}.pdf",
        }

        return Response(
            content=data if isinstance(data, bytes) else data.encode("utf-8"),
            media_type=content_type_map[format],
            headers={
                "Content-Disposition": f'attachment; filename="{filename_map[format]}"'
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/admin/all-users")
def export_all_users(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
    format: str = Query("csv", pattern="^(csv|pdf)$"),
):
    """
    Export all users list (admin only).

    - **format**: Export format (csv, pdf)
    """
    try:
        users = db.query(User).all()

        data = []
        for user in users:
            data.append(
                {
                    "id": user.id,
                    "email": user.email,
                    "full_name": user.full_name or "",
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat()
                    if user.created_at
                    else "",
                }
            )

        if format == "csv":
            csv_data = ExportService.generate_csv(data)
            return Response(
                content=csv_data.encode("utf-8"),
                media_type="text/csv",
                headers={"Content-Disposition": 'attachment; filename="users.csv"'},
            )
        elif format == "pdf":
            pdf_data = ExportService.generate_pdf(data, "Users List")
            return Response(
                content=pdf_data,
                media_type="application/pdf",
                headers={"Content-Disposition": 'attachment; filename="users.pdf"'},
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
