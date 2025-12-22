"""
Invoice Service
Business logic for invoice generation and management
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timedelta
import os
import json

from app.models.invoice import Invoice
from app.models.order import Order, OrderItem
from app.schemas.invoice import InvoiceResponse


class InvoiceService:
    """Service for invoice operations"""

    # Company details (should be in config)
    COMPANY_NAME = os.getenv("COMPANY_NAME", "Eduecosystem")
    COMPANY_ADDRESS = os.getenv(
        "COMPANY_ADDRESS", "123 Education Street, Learning City"
    )
    COMPANY_TAX_ID = os.getenv("COMPANY_TAX_ID", "TAX-123456")
    INVOICE_START_NUMBER = int(os.getenv("INVOICE_START_NUMBER", "1000"))

    @staticmethod
    def create_invoice(
        db: Session, order_id: int, notes: Optional[str] = None
    ) -> Invoice:
        """
        Create invoice from order.
        Snapshots order details and generates invoice number.
        """
        # Get order
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Check if invoice already exists
        existing_invoice = (
            db.query(Invoice).filter(Invoice.order_id == order_id).first()
        )
        if existing_invoice:
            return existing_invoice

        # Generate invoice number
        current_year = datetime.utcnow().year

        # Get last invoice number for this year
        last_invoice = (
            db.query(Invoice)
            .filter(Invoice.invoice_number.like(f"INV-{current_year}-%"))
            .order_by(Invoice.id.desc())
            .first()
        )

        if last_invoice:
            # Extract sequence number and increment
            try:
                last_seq = int(last_invoice.invoice_number.split("-")[-1])
                sequence = last_seq + 1
            except (ValueError, IndexError):
                sequence = InvoiceService.INVOICE_START_NUMBER
        else:
            sequence = InvoiceService.INVOICE_START_NUMBER

        invoice_number = Invoice.generate_invoice_number(current_year, sequence)

        # Get order items for JSON snapshot
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        items_data = [
            {
                "item_name": item.item_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "discount": item.discount,
                "total": item.total,
            }
            for item in order_items
        ]

        # Create invoice
        invoice = Invoice(
            order_id=order_id,
            invoice_number=invoice_number,
            issued_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30),  # 30 days payment term
            status="draft",
            billing_name=order.billing_name,
            billing_email=order.billing_email,
            billing_address=order.billing_address,
            items_json=json.dumps(items_data),
            subtotal=order.subtotal,
            discount=order.discount,
            tax=order.tax,
            total=order.total,
            currency=order.currency,
            notes=notes,
            pdf_generated=0,
        )

        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        return invoice

    @staticmethod
    def get_invoice(db: Session, invoice_id: int) -> Optional[Invoice]:
        """Get invoice by ID"""
        return db.query(Invoice).filter(Invoice.id == invoice_id).first()

    @staticmethod
    def get_invoice_by_order(db: Session, order_id: int) -> Optional[Invoice]:
        """Get invoice by order ID"""
        return db.query(Invoice).filter(Invoice.order_id == order_id).first()

    @staticmethod
    def generate_pdf(db: Session, invoice_id: int) -> str:
        """
        Generate PDF for invoice.
        Returns path to PDF file.

        Note: This is a placeholder implementation.
        Full implementation would use ReportLab or similar library.
        """
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        # Get order for additional details
        order = db.query(Order).filter(Order.id == invoice.order_id).first()

        # In a real implementation, you would:
        # 1. Use ReportLab to generate PDF
        # 2. Add company logo and branding
        # 3. Format invoice details nicely
        # 4. Save to uploads directory
        # 5. Return file path

        # For now, create placeholder path
        pdf_filename = f"invoice_{invoice.invoice_number}.pdf"
        pdf_path = f"uploads/invoices/{pdf_filename}"

        # Create directory if it doesn't exist
        os.makedirs("uploads/invoices", exist_ok=True)

        # TODO: Actual PDF generation with ReportLab
        # This is a placeholder - in production, implement proper PDF generation

        # Update invoice
        invoice.pdf_url = pdf_path
        invoice.pdf_generated = 1
        db.commit()

        return pdf_path

    @staticmethod
    def mark_as_sent(db: Session, invoice_id: int) -> Invoice:
        """Mark invoice as sent"""
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        invoice.status = "sent"
        invoice.sent_at = datetime.utcnow()
        db.commit()
        db.refresh(invoice)

        return invoice

    @staticmethod
    def mark_as_paid(db: Session, invoice_id: int) -> Invoice:
        """Mark invoice as paid"""
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        invoice.status = "paid"
        invoice.paid_at = datetime.utcnow()
        db.commit()
        db.refresh(invoice)

        return invoice

    @staticmethod
    def build_invoice_response(db: Session, invoice: Invoice) -> InvoiceResponse:
        """Build complete invoice response"""
        # Get order number
        order = db.query(Order).filter(Order.id == invoice.order_id).first()
        order_number = order.order_number if order else None

        return InvoiceResponse(
            id=invoice.id,
            order_id=invoice.order_id,
            invoice_number=invoice.invoice_number,
            issued_date=invoice.issued_date,
            due_date=invoice.due_date,
            pdf_url=invoice.pdf_url,
            pdf_generated=bool(invoice.pdf_generated),
            status=invoice.status,
            billing_name=invoice.billing_name,
            billing_email=invoice.billing_email,
            billing_address=invoice.billing_address,
            subtotal=invoice.subtotal,
            discount=invoice.discount,
            tax=invoice.tax,
            total=invoice.total,
            currency=invoice.currency,
            notes=invoice.notes,
            created_at=invoice.created_at,
            sent_at=invoice.sent_at,
            paid_at=invoice.paid_at,
            order_number=order_number,
        )

    @staticmethod
    def send_invoice_email(
        db: Session,
        invoice_id: int,
        recipient_email: Optional[str] = None,
        message: Optional[str] = None,
    ):
        """
        Send invoice via email.

        Note: This is a placeholder implementation.
        Full implementation would integrate with email service.
        """
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        # Use billing email if no recipient specified
        to_email = recipient_email or invoice.billing_email
        if not to_email:
            raise HTTPException(status_code=400, detail="No recipient email available")

        # Generate PDF if not already generated
        if not invoice.pdf_generated:
            InvoiceService.generate_pdf(db, invoice_id)

        # TODO: Actual email sending implementation
        # This would integrate with your EmailService or similar
        # For now, just mark as sent

        InvoiceService.mark_as_sent(db, invoice_id)

        return {"status": "success", "message": "Invoice sent", "recipient": to_email}
