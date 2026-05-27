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

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

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
        """
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")

        # Get order for additional details
        order = db.query(Order).filter(Order.id == invoice.order_id).first()

        # Create directory if it doesn't exist
        os.makedirs("uploads/invoices", exist_ok=True)

        pdf_filename = f"invoice_{invoice.invoice_number}.pdf"
        pdf_path = f"uploads/invoices/{pdf_filename}"

        # Actual PDF generation with ReportLab
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        elements.append(Paragraph("<b>INVOICE</b>", styles['Title']))
        elements.append(Spacer(1, 20))

        # Header info (Company & Invoice Details)
        issued_str = invoice.issued_date.strftime('%Y-%m-%d') if invoice.issued_date else ""
        due_str = invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else ""

        company_addr = InvoiceService.COMPANY_ADDRESS.replace('\n', '<br/>')

        header_data = [
            [
                Paragraph(f"<b>{InvoiceService.COMPANY_NAME}</b><br/>{company_addr}<br/>Tax ID: {InvoiceService.COMPANY_TAX_ID}", styles['Normal']),
                Paragraph(f"<b>Invoice #:</b> {invoice.invoice_number}<br/><b>Date:</b> {issued_str}<br/><b>Due Date:</b> {due_str}", styles['Normal'])
            ]
        ]
        header_table = Table(header_data, colWidths=[300, 200])
        elements.append(header_table)
        elements.append(Spacer(1, 20))

        # Billing info
        billing_name = invoice.billing_name or ""
        billing_email = invoice.billing_email or ""
        billing_address = (invoice.billing_address or "").replace('\n', '<br/>')

        elements.append(Paragraph(f"<b>Bill To:</b><br/>{billing_name}<br/>{billing_address}<br/>{billing_email}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # Items
        items_data = [["Item", "Quantity", "Unit Price", "Discount", "Total"]]
        items = json.loads(invoice.items_json) if invoice.items_json else []
        for item in items:
            items_data.append([
                item.get('item_name', ''),
                str(item.get('quantity', 0)),
                f"{item.get('unit_price', 0):.2f}",
                f"{item.get('discount', 0):.2f}",
                f"{item.get('total', 0):.2f}"
            ])

        # Add totals
        items_data.append(["", "", "", "Subtotal:", f"{invoice.subtotal:.2f}"])
        items_data.append(["", "", "", "Discount:", f"{invoice.discount:.2f}"])
        items_data.append(["", "", "", "Tax:", f"{invoice.tax:.2f}"])
        items_data.append(["", "", "", "Total:", f"{invoice.currency} {invoice.total:.2f}"])

        t = Table(items_data, colWidths=[220, 60, 80, 70, 70])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -5), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (-2, -4), (-1, -1), 'Helvetica-Bold'),
        ]))
        elements.append(t)

        if invoice.notes:
            elements.append(Spacer(1, 20))
            notes_str = invoice.notes.replace('\n', '<br/>')
            elements.append(Paragraph(f"<b>Notes:</b><br/>{notes_str}", styles['Normal']))

        doc.build(elements)

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
