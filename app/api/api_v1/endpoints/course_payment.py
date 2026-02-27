"""
Multi-Gateway Payment Integration for Courses
Supports: Cashfree (Migrated), Instamojo
Currency: INR
"""

import requests
import os
import hmac
import hashlib
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.course_payment import CoursePayment
from app.crud import course as crud_course
from app.services.cashfree_service import cashfree_service

# Initialize payment providers

INSTAMOJO_API_KEY = os.getenv("INSTAMOJO_API_KEY", "")
INSTAMOJO_AUTH_TOKEN = os.getenv("INSTAMOJO_AUTH_TOKEN", "")
INSTAMOJO_ENDPOINT = os.getenv(
    "INSTAMOJO_ENDPOINT", "https://test.instamojo.com/api/1.1/"
)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

router = APIRouter()


# ============================================================================
# SCHEMAS
# ============================================================================


class CreatePaymentRequest(BaseModel):
    course_id: int
    payment_provider: str  # cashfree, instamojo
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class PaymentResponse(BaseModel):
    payment_id: int
    provider: str
    checkout_url: Optional[str] = None
    order_id: Optional[str] = None
    payment_request_id: Optional[str] = None  # For Instamojo
    payment_session_id: Optional[str] = None  # For Cashfree

class VerifyPayment(BaseModel):
    order_id: str
    payment_id: str
    signature: str


class PaymentStatus(BaseModel):
    payment_id: int
    status: str
    amount: float
    currency: str
    provider: str
    created_at: datetime


# ============================================================================
# CASHFREE INTEGRATION
# ============================================================================

@router.post("/create-cashfree-order", response_model=PaymentResponse)
async def create_cashfree_order(
    request: CreatePaymentRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Create a Cashfree order (INR)"""
    course = crud_course.course.get(db=db, id=request.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.price <= 0:
        raise HTTPException(status_code=400, detail="Course is free")

    try:
        customer_details = {
            "customer_id": str(current_user.id),
            "customer_email": current_user.email,
            "customer_phone": getattr(current_user, "phone", "9999999999") or "9999999999",
            "customer_name": getattr(current_user, "full_name", current_user.email.split("@")[0]) or "Student"
        }

        # Use the unified Cashfree service
        cashfree_order = cashfree_service.create_order(
            order_amount=course.price,
            order_currency="INR",
            customer_details=customer_details,
            order_note=f"Enrollment: {course.title}",
            order_meta={
                "return_url": request.success_url or f"{FRONTEND_URL}/lms/courses/{course.id}/success",
                "notify_url": f"{os.getenv('BASE_URL')}/api/v1/course-payments/cashfree-webhook"
            }
        )

        # Create payment record
        payment = CoursePayment(
            user_id=current_user.id,
            course_id=course.id,
            amount=course.price,
            currency="INR",
            status="pending",
            payment_provider="cashfree",
            cashfree_order_id=cashfree_order.get("order_id"), # Storing standard ID in a placeholder if needed, otherwise rely on order_id natively
            # You might need to add cashfree_order_id to CoursePayment model if it doesn't exist,
            # or map it to a generic order_id column.
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        return PaymentResponse(
            payment_id=payment.id,
            provider="cashfree",
            order_id=cashfree_order.get("order_id"),
            payment_session_id=cashfree_order.get("payment_session_id")
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/cashfree-webhook")
async def cashfree_webhook(request: Request, db: Session = Depends(deps.get_db)):
    """Server-to-Server Webhook handler for Cashfree"""
    try:
        raw_body = await request.body()
        signature = request.headers.get("x-webhook-signature")
        timestamp = request.headers.get("x-webhook-timestamp")

        if not signature or not timestamp:
            raise HTTPException(status_code=400, detail="Missing Cashfree headers")

        # Verify signature
        if not cashfree_service.verify_webhook_signature(signature, timestamp, raw_body.decode("utf-8")):
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Parse Event
        event = await request.json()
        
        if event.get("type") == "PAYMENT_SUCCESS_WEBHOOK":
            order = event.get("data", {}).get("order", {})
            order_id = order.get("order_id")
            
            # Find payment record
            payment = db.query(CoursePayment).filter(CoursePayment.cashfree_order_id == order_id).first()
            
            if payment and payment.status != "succeeded":
                # Mark as succeeded
                payment.status = "succeeded"
                payment.cashfree_payment_id = event.get("data", {}).get("payment", {}).get("cf_payment_id")
                payment.succeeded_at = datetime.utcnow()
                
                # Create enrollment to unlock access
                enrollment = Enrollment(
                    user_id=payment.user_id,
                    course_id=payment.course_id,
                    status="active",
                    payment_id=payment.cashfree_payment_id,
                    price_paid=payment.amount,
                    progress_percentage=0,
                )
                db.add(enrollment)
                db.flush()
                
                payment.enrollment_id = enrollment.id
                
                # Update course enrollment count
                course = db.query(Course).filter(Course.id == payment.course_id).first()
                if course:
                    course.total_enrollments = (course.total_enrollments or 0) + 1
                    
                db.commit()
                print(f"WEBHOOK SUCCESS: Confirmed unlocked bundle for Order ID {order_id}")
            else:
                print(f"WEBHOOK INFO: Payment {order_id} already processed or not found.")
            
        return {"status": "OK"}

    except Exception as e:
        print(f"Webhook processing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# INSTAMOJO INTEGRATION
# ============================================================================


@router.post("/create-instamojo-payment", response_model=PaymentResponse)
async def create_instamojo_payment(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Create Instamojo payment request (INR)"""
    course = crud_course.course.get(db=db, id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.price <= 0:
        raise HTTPException(status_code=400, detail="Course is free")

    try:
        # Create Instamojo payment request
        headers = {"X-Api-Key": INSTAMOJO_API_KEY, "X-Auth-Token": INSTAMOJO_AUTH_TOKEN}

        payload = {
            "purpose": f"Enrollment: {course.title}",
            "amount": str(course.price),
            "buyer_name": current_user.email.split("@")[0],
            "email": current_user.email,
            "redirect_url": f"{FRONTEND_URL}/lms/courses/{course_id}/success",
            "send_email": False,
            "send_sms": False,
            "allow_repeated_payments": False,
        }

        response = requests.post(
            f"{INSTAMOJO_ENDPOINT}payment-requests/", data=payload, headers=headers
        )

        if response.status_code != 201:
            raise HTTPException(
                status_code=400, detail="Failed to create payment request"
            )

        result = response.json()
        payment_request = result["payment_request"]

        # Create payment record
        payment = CoursePayment(
            user_id=current_user.id,
            course_id=course_id,
            amount=course.price,
            currency="INR",
            status="pending",
            payment_provider="instamojo",
            instamojo_payment_request_id=payment_request["id"],
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        return PaymentResponse(
            payment_id=payment.id,
            provider="instamojo",
            checkout_url=payment_request["longurl"],
            payment_request_id=payment_request["id"],
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verify-instamojo-payment/{payment_request_id}")
async def verify_instamojo_payment(
    payment_request_id: str,
    payment_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Verify Instamojo payment"""

    # Find payment record
    payment = (
        db.query(CoursePayment)
        .filter(
            CoursePayment.instamojo_payment_request_id == payment_request_id,
            CoursePayment.user_id == current_user.id,
        )
        .first()
    )

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    try:
        # Verify with Instamojo
        headers = {"X-Api-Key": INSTAMOJO_API_KEY, "X-Auth-Token": INSTAMOJO_AUTH_TOKEN}

        response = requests.get(
            f"{INSTAMOJO_ENDPOINT}payments/{payment_id}/", headers=headers
        )

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to verify payment")

        result = response.json()
        payment_data = result["payment"]

        if payment_data["status"] == "Credit":
            # Update payment
            payment.status = "succeeded"
            payment.instamojo_payment_id = payment_id
            payment.succeeded_at = datetime.utcnow()

            # Create enrollment
            enrollment = Enrollment(
                user_id=payment.user_id,
                course_id=payment.course_id,
                status="active",
                payment_id=payment_id,
                price_paid=payment.amount,
                progress_percentage=0,
            )
            db.add(enrollment)
            db.flush()

            payment.enrollment_id = enrollment.id

            # Update course enrollment count
            course = db.query(Course).filter(Course.id == payment.course_id).first()
            if course:
                course.total_enrollments += 1

            db.commit()

            return {"status": "success", "enrollment_id": enrollment.id}
        else:
            payment.status = "failed"
            payment.failure_reason = payment_data.get("failure", {}).get(
                "message", "Payment failed"
            )
            db.commit()
            raise HTTPException(status_code=400, detail="Payment not completed")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))





# ============================================================================
# COMMON ENDPOINTS
# ============================================================================


@router.get("/payment-status/{course_id}", response_model=Optional[PaymentStatus])
async def get_payment_status(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Get payment status for a course"""
    payment = (
        db.query(CoursePayment)
        .filter(
            CoursePayment.user_id == current_user.id,
            CoursePayment.course_id == course_id,
        )
        .order_by(CoursePayment.created_at.desc())
        .first()
    )

    if not payment:
        return None

    return PaymentStatus(
        payment_id=payment.id,
        status=payment.status,
        amount=payment.amount,
        currency=payment.currency,
        provider=payment.payment_provider,
        created_at=payment.created_at,
    )
