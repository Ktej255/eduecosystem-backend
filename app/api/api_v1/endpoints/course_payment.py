"""
Multi-Gateway Payment Integration for Courses
Supports: Stripe, Razorpay, Instamojo
Currency: INR
"""

import stripe
import razorpay
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

# Initialize payment providers
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

razorpay_client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID", ""), os.getenv("RAZORPAY_KEY_SECRET", ""))
)

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
    payment_provider: str  # stripe, razorpay, instamojo
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class PaymentResponse(BaseModel):
    payment_id: int
    provider: str
    checkout_url: Optional[str] = None
    order_id: Optional[str] = None  # For Razorpay
    razorpay_key: Optional[str] = None  # For frontend
    payment_request_id: Optional[str] = None  # For Instamojo


class VerifyRazorpayPayment(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentStatus(BaseModel):
    payment_id: int
    status: str
    amount: float
    currency: str
    provider: str
    created_at: datetime


# ============================================================================
# STRIPE INTEGRATION
# ============================================================================


@router.post("/create-stripe-checkout", response_model=PaymentResponse)
async def create_stripe_checkout(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Create Stripe checkout session (INR)"""
    course = crud_course.course.get(db=db, id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.price <= 0:
        raise HTTPException(status_code=400, detail="Course is free")

    try:
        # Convert INR to paise (smallest currency unit)
        amount_in_paise = int(course.price * 100)

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "inr",
                        "unit_amount": amount_in_paise,
                        "product_data": {
                            "name": course.title,
                            "description": course.description,
                            "images": [course.thumbnail_url]
                            if course.thumbnail_url
                            else [],
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{FRONTEND_URL}/lms/courses/{course_id}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/lms/courses/{course_id}",
            customer_email=current_user.email,
            metadata={
                "user_id": str(current_user.id),
                "course_id": str(course_id),
            },
        )

        # Create payment record
        payment = CoursePayment(
            user_id=current_user.id,
            course_id=course_id,
            amount=course.price,
            currency="INR",
            status="pending",
            payment_provider="stripe",
            stripe_checkout_session_id=session.id,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        return PaymentResponse(
            payment_id=payment.id, provider="stripe", checkout_url=session.url
        )

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# RAZORPAY INTEGRATION
# ============================================================================


@router.post("/create-razorpay-order", response_model=PaymentResponse)
async def create_razorpay_order(
    course_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Create Razorpay order (INR)"""
    course = crud_course.course.get(db=db, id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if course.price <= 0:
        raise HTTPException(status_code=400, detail="Course is free")

    try:
        # Convert INR to paise
        amount_in_paise = int(course.price * 100)

        # Create Razorpay order
        order = razorpay_client.order.create(
            {
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": f"course_{course_id}_user_{current_user.id}",
                "notes": {
                    "course_id": str(course_id),
                    "user_id": str(current_user.id),
                    "course_title": course.title,
                },
            }
        )

        # Create payment record
        payment = CoursePayment(
            user_id=current_user.id,
            course_id=course_id,
            amount=course.price,
            currency="INR",
            status="pending",
            payment_provider="razorpay",
            razorpay_order_id=order["id"],
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        return PaymentResponse(
            payment_id=payment.id,
            provider="razorpay",
            order_id=order["id"],
            razorpay_key=os.getenv("RAZORPAY_KEY_ID", ""),
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/verify-razorpay-payment")
async def verify_razorpay_payment(
    data: VerifyRazorpayPayment,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Verify Razorpay payment signature"""

    # Find payment record
    payment = (
        db.query(CoursePayment)
        .filter(
            CoursePayment.razorpay_order_id == data.razorpay_order_id,
            CoursePayment.user_id == current_user.id,
        )
        .first()
    )

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Verify signature
    generated_signature = hmac.new(
        os.getenv("RAZORPAY_KEY_SECRET", "").encode(),
        f"{data.razorpay_order_id}|{data.razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if generated_signature != data.razorpay_signature:
        payment.status = "failed"
        payment.failure_reason = "Invalid signature"
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # Update payment
    payment.status = "succeeded"
    payment.razorpay_payment_id = data.razorpay_payment_id
    payment.razorpay_signature = data.razorpay_signature
    payment.succeeded_at = datetime.utcnow()

    # Create enrollment
    enrollment = Enrollment(
        user_id=payment.user_id,
        course_id=payment.course_id,
        status="active",
        payment_id=data.razorpay_payment_id,
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
# WEBHOOK HANDLERS (Stripe)
# ============================================================================


@router.post("/stripe-webhook")
async def stripe_webhook(request: Request, db: Session = Depends(deps.get_db)):
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        # Get payment record
        payment = (
            db.query(CoursePayment)
            .filter(CoursePayment.stripe_checkout_session_id == session.id)
            .first()
        )

        if payment and payment.status != "succeeded":
            payment.status = "succeeded"
            payment.stripe_payment_intent_id = session.payment_intent
            payment.succeeded_at = datetime.utcnow()

            # Create enrollment
            enrollment = Enrollment(
                user_id=payment.user_id,
                course_id=payment.course_id,
                status="active",
                payment_id=session.payment_intent,
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

    return {"status": "success"}


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
