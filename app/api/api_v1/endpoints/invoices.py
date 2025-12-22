"""
Invoice API Endpoints
Manage invoices, PDF generation, and email delivery
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.api import deps
from app.models.user import User
from app.models.invoice import Invoice
from app.models.order import Order
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceSendRequest,
)
from app.services.invoice_service import InvoiceService

router = APIRouter()


@router.post("/invoices", response_model=InvoiceResponse)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Create invoice from an order.
    Automatically called when order is completed.
    """
    # Verify user owns the order
    order = db.query(Order).filter(Order.id == invoice_data.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    # Create invoice
    invoice = InvoiceService.create_invoice(
        db=db, order_id=invoice_data.order_id, notes=invoice_data.notes
    )

    return InvoiceService.build_invoice_response(db, invoice)


@router.get("/invoices", response_model=InvoiceListResponse)
def get_user_invoices(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get user's invoices with pagination.
    """
    skip = (page - 1) * page_size

    # Get user's orders
    user_orders = db.query(Order).filter(Order.user_id == current_user.id).all()
    order_ids = [order.id for order in user_orders]

    # Get invoices for these orders
    query = (
        db.query(Invoice)
        .filter(Invoice.order_id.in_(order_ids))
        .order_by(Invoice.created_at.desc())
    )

    total = query.count()
    invoices = query.offset(skip).limit(page_size).all()

    invoice_responses = [
        InvoiceService.build_invoice_response(db, inv) for inv in invoices
    ]

    return InvoiceListResponse(
        invoices=invoice_responses, total=total, page=page, page_size=page_size
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice_details(
    invoice_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get invoice details by ID.
    """
    invoice = InvoiceService.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Verify user owns the invoice's order
    order = db.query(Order).filter(Order.id == invoice.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    return InvoiceService.build_invoice_response(db, invoice)


@router.get("/invoices/order/{order_id}", response_model=InvoiceResponse)
def get_invoice_by_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Get invoice for a specific order.
    """
    # Verify user owns the order
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    invoice = InvoiceService.get_invoice_by_order(db, order_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found for this order")

    return InvoiceService.build_invoice_response(db, invoice)


@router.post("/invoices/{invoice_id}/generate-pdf")
def generate_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Generate PDF for invoice.
    """
    invoice = InvoiceService.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Verify ownership
    order = db.query(Order).filter(Order.id == invoice.order_id).first()
    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    pdf_path = InvoiceService.generate_pdf(db, invoice_id)

    return {"status": "success", "message": "PDF generated", "pdf_url": pdf_path}


@router.get("/invoices/{invoice_id}/download")
def download_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Download invoice PDF.
    """
    invoice = InvoiceService.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Verify ownership
    order = db.query(Order).filter(Order.id == invoice.order_id).first()
    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    # Generate PDF if not exists
    if not invoice.pdf_generated:
        InvoiceService.generate_pdf(db, invoice_id)
        db.refresh(invoice)

    # Check if file exists
    if not invoice.pdf_url or not os.path.exists(invoice.pdf_url):
        raise HTTPException(status_code=404, detail="PDF file not found")

    return FileResponse(
        path=invoice.pdf_url,
        filename=f"{invoice.invoice_number}.pdf",
        media_type="application/pdf",
    )


@router.post("/invoices/{invoice_id}/send")
def send_invoice_email(
    invoice_id: int,
    send_request: InvoiceSendRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """
    Send invoice via email.
    """
    invoice = InvoiceService.get_invoice(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Verify ownership or admin
    order = db.query(Order).filter(Order.id == invoice.order_id).first()
    if order.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    result = InvoiceService.send_invoice_email(
        db=db,
        invoice_id=invoice_id,
        recipient_email=send_request.recipient_email,
        message=send_request.message,
    )

    return result


@router.post("/invoices/{invoice_id}/mark-paid")
def mark_invoice_paid(
    invoice_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_admin_user),
):
    """
    Mark invoice as paid (admin only).
    """
    invoice = InvoiceService.mark_as_paid(db, invoice_id)

    return {
        "status": "success",
        "message": "Invoice marked as paid",
        "invoice_number": invoice.invoice_number,
    }
