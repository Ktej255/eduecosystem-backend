"""
Invoice Schemas
Pydantic models for invoice validation and serialization
"""

from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class InvoiceCreate(BaseModel):
    """Schema for creating invoice from order"""

    order_id: int
    notes: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Full invoice response"""

    id: int
    order_id: int
    invoice_number: str
    issued_date: datetime
    due_date: Optional[datetime] = None
    pdf_url: Optional[str] = None
    pdf_generated: bool
    status: str
    billing_name: Optional[str] = None
    billing_email: Optional[str] = None
    billing_address: Optional[str] = None
    subtotal: float
    discount: float
    tax: float
    total: float
    currency: str
    notes: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    # Order details
    order_number: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InvoiceListResponse(BaseModel):
    """Paginated invoice list"""

    invoices: List[InvoiceResponse] = []
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


class InvoiceSendRequest(BaseModel):
    """Request to send invoice via email"""

    recipient_email: Optional[str] = None  # If None, use billing email
    message: Optional[str] = None
