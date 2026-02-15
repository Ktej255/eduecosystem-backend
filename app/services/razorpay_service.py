"""
Razorpay Integration Service for Meditation Level Purchases
"""
import razorpay
import hmac
import hashlib
from typing import Dict, Optional
from app.core.config import settings


class RazorpayService:
    """Service for handling Razorpay payment operations"""
    
    def __init__(self):
        """Initialize Razorpay client"""
        self.client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
    
    def create_order(self, amount: float, currency: str = "INR", receipt: str = None, notes: Dict = None) -> Dict:
        """
        Create a Razorpay order
        
        Args:
            amount: Amount in rupees (will be converted to paise)
            currency: Currency code (default: INR)
            receipt: Receipt ID for reference
            notes: Additional notes/metadata
            
        Returns:
            Order details from Razorpay
        """
        # Convert amount to paise (Razorpay uses smallest currency unit)
        amount_in_paise = int(amount * 100)
        
        order_data = {
            "amount": amount_in_paise,
            "currency": currency,
            "payment_capture": 1  # Auto capture payment
        }
        
        if receipt:
            order_data["receipt"] = receipt
        if notes:
            order_data["notes"] = notes
            
        order = self.client.order.create(data=order_data)
        return order
    
    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> bool:
        """
        Verify Razorpay payment signature
        
        Args:
            razorpay_order_id: Order ID from Razorpay
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_signature: Signature from Razorpay
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Create signature string
            message = f"{razorpay_order_id}|{razorpay_payment_id}"
            
            # Generate expected signature
            expected_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, razorpay_signature)
        except Exception as e:
            print(f"Error verifying signature: {e}")
            return False
    
    def fetch_payment(self, payment_id: str) -> Optional[Dict]:
        """
        Fetch payment details from Razorpay
        
        Args:
            payment_id: Razorpay payment ID
            
        Returns:
            Payment details or None if not found
        """
        try:
            payment = self.client.payment.fetch(payment_id)
            return payment
        except Exception as e:
            print(f"Error fetching payment: {e}")
            return None
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature from Razorpay
        
        Args:
            payload: Webhook payload (raw body)
            signature: X-Razorpay-Signature header
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            expected_signature = hmac.new(
                settings.RAZORPAY_WEBHOOK_SECRET.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            print(f"Error verifying webhook signature: {e}")
            return False


# Singleton instance
razorpay_service = RazorpayService()
