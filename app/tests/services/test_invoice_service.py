import pytest
import os
import json
from datetime import datetime
from unittest.mock import MagicMock

def test_generate_pdf():
    # Because of dependency hell with mocking and missing pydantic internal imports,
    # we import locally to avoid loading module level mocks incorrectly.
    import sys

    # Temporarily mock fastapi if needed during the test execution
    original_modules = {}
    for mod in ['fastapi', 'motor', 'motor.motor_asyncio']:
        if mod in sys.modules:
            original_modules[mod] = sys.modules[mod]
        else:
            sys.modules[mod] = MagicMock()

    try:
        from app.services.invoice_service import InvoiceService
        from app.models.invoice import Invoice
        from app.models.order import Order

        # Setup mock db and models
        mock_db = MagicMock()

        mock_invoice = MagicMock(spec=Invoice)
        mock_invoice.id = 1
        mock_invoice.invoice_number = "INV-2023-00001"
        mock_invoice.issued_date = datetime.now()
        mock_invoice.due_date = datetime.now()
        mock_invoice.billing_name = "Jane Doe"
        mock_invoice.billing_email = "jane@example.com"
        mock_invoice.billing_address = "456 Test Ave"
        mock_invoice.items_json = json.dumps([
            {"item_name": "Test Course", "quantity": 1, "unit_price": 99.99, "discount": 0.0, "total": 99.99}
        ])
        mock_invoice.currency = "USD"
        mock_invoice.subtotal = 99.99
        mock_invoice.discount = 0.0
        mock_invoice.tax = 0.0
        mock_invoice.total = 99.99
        mock_invoice.notes = "Thanks for your purchase"

        mock_order = MagicMock(spec=Order)
        mock_order.id = 1
        mock_order.billing_name = "Jane Doe"
        mock_order.billing_email = "jane@example.com"
        mock_order.billing_address = "456 Test Ave"

        # Configure mock query
        def mock_query(model):
            query_mock = MagicMock()
            if model == Invoice:
                query_mock.filter.return_value.first.return_value = mock_invoice
            elif model == Order:
                query_mock.filter.return_value.first.return_value = mock_order
            return query_mock

        mock_db.query.side_effect = mock_query

        # Run the function
        pdf_path = InvoiceService.generate_pdf(mock_db, 1)

        # Assertions
        assert pdf_path == f"uploads/invoices/invoice_{mock_invoice.invoice_number}.pdf"
        assert os.path.exists(pdf_path)

        # Clean up generated file
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    finally:
        for mod in ['fastapi', 'motor', 'motor.motor_asyncio']:
            if mod in original_modules:
                sys.modules[mod] = original_modules[mod]
            elif mod in sys.modules and isinstance(sys.modules[mod], MagicMock):
                sys.modules.pop(mod)
