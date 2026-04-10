import pytest
from unittest.mock import MagicMock
import os
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.services.invoice_service import InvoiceService
from app.models.invoice import Invoice
from app.models.order import Order

def test_generate_pdf_success():
    """Test generating a PDF for an existing invoice successfully"""
    # 1. Setup mock session and data
    mock_db = MagicMock(spec=Session)

    # Create mock objects
    mock_invoice = MagicMock(spec=Invoice)
    mock_invoice.id = 1
    mock_invoice.order_id = 100
    mock_invoice.invoice_number = "INV-2023-00001"
    mock_invoice.pdf_url = None
    mock_invoice.pdf_generated = 0

    mock_order = MagicMock(spec=Order)
    mock_order.id = 100

    # Configure the query mock
    mock_query_invoice = MagicMock()
    mock_query_invoice.filter.return_value.first.return_value = mock_invoice

    mock_query_order = MagicMock()
    mock_query_order.filter.return_value.first.return_value = mock_order

    def side_effect_query(model):
        if model == Invoice:
            return mock_query_invoice
        elif model == Order:
            return mock_query_order
        return mock_query_invoice # default

    mock_db.query.side_effect = side_effect_query

    # 2. Action
    pdf_path = InvoiceService.generate_pdf(mock_db, 1)

    # 3. Assert
    expected_path = "uploads/invoices/invoice_INV-2023-00001.pdf"
    assert pdf_path == expected_path

    # Check invoice object updates
    assert mock_invoice.pdf_url == expected_path
    assert mock_invoice.pdf_generated == 1

    # Check db interactions
    mock_db.commit.assert_called_once()

def test_generate_pdf_not_found():
    """Test generating a PDF for a non-existent invoice raises HTTPException"""
    # 1. Setup mock session
    mock_db = MagicMock(spec=Session)

    mock_query_invoice = MagicMock()
    mock_query_invoice.filter.return_value.first.return_value = None

    mock_db.query.return_value = mock_query_invoice

    # 2 & 3. Action and Assert
    with pytest.raises(HTTPException) as exc_info:
        InvoiceService.generate_pdf(mock_db, 999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Invoice not found"

    # db.commit should not be called
    mock_db.commit.assert_not_called()
