"""
Invoice Model
Invoices for orders with PDF generation support
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Invoice(Base):
    """
    Invoice model for orders.
    Stores invoice details and PDF reference.
    """

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)

    # Order relationship
    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Invoice identification
    invoice_number = Column(String(50), unique=True, index=True, nullable=False)

    # Dates
    issued_date = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    due_date = Column(DateTime(timezone=True), nullable=True)

    # PDF storage
    pdf_url = Column(String(500), nullable=True)  # Path to PDF file
    pdf_generated = Column(Integer, default=0)  # Boolean flag (SQLite compatible)

    # Status
    status = Column(
        String(20), default="draft", nullable=False
    )  # draft, sent, paid, void

    # Billing information snapshot (from order)
    billing_name = Column(String(255), nullable=True)
    billing_email = Column(String(255), nullable=True)
    billing_address = Column(Text, nullable=True)

    # Invoice items snapshot (JSON stored as Text for SQLite compatibility)
    items_json = Column(Text, nullable=True)

    # Totals snapshot
    subtotal = Column(Float, nullable=False, default=0.0)
    discount = Column(Float, nullable=False, default=0.0)
    tax = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)
    currency = Column(String(3), default="INR", nullable=False)

    # Notes
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="invoice")

    def __repr__(self):
        return f"<Invoice(invoice_number={self.invoice_number}, status={self.status}, total={self.total})>"

    @staticmethod
    def generate_invoice_number(year: int, sequence: int) -> str:
        """Generate invoice number: INV-{year}-{sequence}"""
        return f"INV-{year}-{sequence:05d}"
