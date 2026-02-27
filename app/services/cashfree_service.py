import hmac
import hashlib
import base64
import requests
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.config import settings

class CashfreeService:
    def __init__(self):
        self.app_id = settings.CASHFREE_APP_ID
        self.secret_key = settings.CASHFREE_SECRET_KEY
        # Determine environment based on key strings or explicit setting
        is_prod = "test" not in getattr(settings, "CASHFREE_APP_ID", "").lower()
        self.base_url = "https://api.cashfree.com/pg" if is_prod else "https://sandbox.cashfree.com/pg"
        self.api_version = "2023-08-01"

    def _get_headers(self) -> Dict[str, str]:
        """Provides the standard headers required for Cashfree API requests."""
        return {
            "x-client-id": self.app_id,
            "x-client-secret": self.secret_key,
            "x-api-version": self.api_version,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def create_order(
        self, 
        order_currency: str, 
        order_amount: float, 
        customer_details: dict,
        order_note: str = "",
        order_meta: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        Creates a new order on Cashfree.
        """
        url = f"{self.base_url}/orders"
        
        # Generate dynamic order ID based on timestamp and user ID if possible
        customer_id = customer_details.get("customer_id", "unknown")
        timestamp = int(datetime.now().timestamp() * 1000)
        order_id = f"ORDER_{customer_id}_{timestamp}"

        payload = {
            "order_id": order_id,
            "order_amount": round(order_amount, 2),
            "order_currency": order_currency,
            "customer_details": customer_details,
            "order_note": order_note
        }

        if order_meta:
            payload["order_meta"] = order_meta

        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Handle specific API errors from Cashfree if possible
            error_response = e.response.json() if hasattr(e, 'response') and e.response else str(e)
            raise Exception(f"Cashfree Order Generation Failed: {error_response}")

    def verify_webhook_signature(self, signature: str, timestamp: str, raw_body: str) -> bool:
        """
        Verifies the signature sent by Cashfree in its webhooks.
        Reconstruct the signature string: timestamp + raw body
        Generate HMAC SHA256 using the client secret.
        """
        if not signature or not timestamp or not raw_body:
            return False

        signature_string = timestamp + raw_body
        
        # Calculate HMAC SHA256 correlation
        expected_signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode('utf-8'),
                signature_string.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode()

        return hmac.compare_digest(expected_signature, signature)

    def fetch_order_details(self, order_id: str) -> Dict[str, Any]:
        """
        Fetches the complete status of an order directly from Cashfree.
        """
        url = f"{self.base_url}/orders/{order_id}"
        
        try:
            response = requests.get(url, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch Cashfree Order: {str(e)}")

# Instantiate a global instance to be imported across the application
cashfree_service = CashfreeService()
