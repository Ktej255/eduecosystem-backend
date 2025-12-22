"""
Order Service
Business logic for order management and processing
"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.models.order import Order, OrderItem, OrderStatus
from app.models.cart import ShoppingCart, CartItem
from app.models.course import Course
from app.models.bundle import CourseBundle
from app.models.enrollment import Enrollment
from app.models.coupon import Coupon
from app.schemas.order import OrderCreate, OrderResponse, OrderItemResponse


class OrderService:
    """Service for order operations"""

    @staticmethod
    def create_order_from_cart(
        db: Session,
        cart_id: int,
        order_data: OrderCreate,
        user_id: Optional[int] = None,
        guest_email: Optional[str] = None,
    ) -> Order:
        """
        Create an order from shopping cart.
        Converts cart items into order items with price snapshots.
        """
        # Get cart
        cart = db.query(ShoppingCart).filter(ShoppingCart.id == cart_id).first()
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        # Get cart items
        cart_items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        # Calculate totals
        subtotal = 0.0
        total_discount = 0.0

        for item in cart_items:
            subtotal += item.unit_price * item.quantity
            total_discount += item.discount_amount

        # Calculate tax (can be customized based on tax rules)
        tax = 0.0  # Implement tax calculation if needed

        total = subtotal - total_discount + tax

        # Generate order number
        order_number = Order.generate_order_number()

        # Create order
        order = Order(
            order_number=order_number,
            user_id=user_id,
            guest_email=guest_email or order_data.billing_email,
            cart_id=cart_id,
            status=OrderStatus.PENDING,
            subtotal=subtotal,
            discount=total_discount,
            tax=tax,
            total=total,
            currency="INR",
            billing_name=order_data.billing_name,
            billing_email=order_data.billing_email,
            billing_address=order_data.billing_address,
            customer_notes=order_data.customer_notes,
        )

        db.add(order)
        db.flush()  # Get order ID

        # Create order items from cart items
        for cart_item in cart_items:
            # Get item details
            if cart_item.course_id:
                course = (
                    db.query(Course).filter(Course.id == cart_item.course_id).first()
                )
                if course:
                    item_name = course.title
                    item_description = course.description
                else:
                    item_name = f"Course ID {cart_item.course_id}"
                    item_description = None
            elif cart_item.bundle_id:
                bundle = (
                    db.query(CourseBundle)
                    .filter(CourseBundle.id == cart_item.bundle_id)
                    .first()
                )
                if bundle:
                    item_name = bundle.name
                    item_description = bundle.description
                else:
                    item_name = f"Bundle ID {cart_item.bundle_id}"
                    item_description = None
            else:
                continue  # Skip invalid items

            # Get coupon code if applied
            coupon_code = None
            if cart_item.coupon_id:
                coupon = (
                    db.query(Coupon).filter(Coupon.id == cart_item.coupon_id).first()
                )
                if coupon:
                    coupon_code = coupon.code

            # Create order item
            order_item = OrderItem(
                order_id=order.id,
                course_id=cart_item.course_id,
                bundle_id=cart_item.bundle_id,
                item_name=item_name,
                item_description=item_description,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                discount=cart_item.discount_amount or 0.0,
                total=cart_item.total,
                coupon_code=coupon_code,
            )

            db.add(order_item)

        db.commit()
        db.refresh(order)

        return order

    @staticmethod
    def get_order(db: Session, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        return db.query(Order).filter(Order.id == order_id).first()

    @staticmethod
    def get_order_by_number(db: Session, order_number: str) -> Optional[Order]:
        """Get order by order number"""
        return db.query(Order).filter(Order.order_number == order_number).first()

    @staticmethod
    def get_user_orders(
        db: Session, user_id: int, skip: int = 0, limit: int = 20
    ) -> Tuple[List[Order], int]:
        """Get user's orders with pagination"""
        query = (
            db.query(Order)
            .filter(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )

        total = query.count()
        orders = query.offset(skip).limit(limit).all()

        return orders, total

    @staticmethod
    def get_guest_orders(
        db: Session, guest_email: str, skip: int = 0, limit: int = 20
    ) -> Tuple[List[Order], int]:
        """Get guest orders by email"""
        query = (
            db.query(Order)
            .filter(
                Order.guest_email == guest_email,
                Order.user_id == None,  # Only guest orders
            )
            .order_by(Order.created_at.desc())
        )

        total = query.count()
        orders = query.offset(skip).limit(limit).all()

        return orders, total

    @staticmethod
    def update_order_status(
        db: Session,
        order_id: int,
        status: OrderStatus,
        admin_notes: Optional[str] = None,
    ) -> Order:
        """Update order status"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        order.status = status

        if admin_notes:
            order.admin_notes = admin_notes

        if status == OrderStatus.COMPLETED:
            order.completed_at = datetime.utcnow()
        elif status == OrderStatus.CANCELLED:
            order.cancelled_at = datetime.utcnow()

        order.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(order)

        return order

    @staticmethod
    def process_order(
        db: Session, order_id: int, payment_id: Optional[int] = None
    ) -> Order:
        """
        Process order after successful payment.
        Creates enrollments for courses in the order.
        """
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status != OrderStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Order status is {order.status}, cannot process",
            )

        # Update order status
        order.status = OrderStatus.PROCESSING
        if payment_id:
            order.payment_id = payment_id

        db.commit()

        # Get order items
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()

        # Determine user ID (from order or guest)
        user_id = order.user_id

        if not user_id:
            # For guest orders, we can't create enrollments yet
            # They'll be created after guest converts to user
            order.status = OrderStatus.COMPLETED
            order.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(order)
            return order

        # Create enrollments for each course
        for item in order_items:
            if item.course_id:
                # Check if enrollment already exists
                existing_enrollment = (
                    db.query(Enrollment)
                    .filter(
                        Enrollment.user_id == user_id,
                        Enrollment.course_id == item.course_id,
                    )
                    .first()
                )

                if not existing_enrollment:
                    enrollment = Enrollment(
                        user_id=user_id,
                        course_id=item.course_id,
                        status="active",
                        price_paid=item.total,
                        progress_percentage=0,
                    )
                    db.add(enrollment)

                    # Update course enrollment count
                    course = (
                        db.query(Course).filter(Course.id == item.course_id).first()
                    )
                    if course:
                        course.total_enrollments += 1

            elif item.bundle_id:
                # Handle bundle enrollment (create enrollments for all courses in bundle)
                bundle = (
                    db.query(CourseBundle)
                    .filter(CourseBundle.id == item.bundle_id)
                    .first()
                )
                if bundle and bundle.courses:
                    for course in bundle.courses:
                        existing_enrollment = (
                            db.query(Enrollment)
                            .filter(
                                Enrollment.user_id == user_id,
                                Enrollment.course_id == course.id,
                            )
                            .first()
                        )

                        if not existing_enrollment:
                            enrollment = Enrollment(
                                user_id=user_id,
                                course_id=course.id,
                                status="active",
                                price_paid=item.total
                                / len(bundle.courses),  # Split price
                                progress_percentage=0,
                            )
                            db.add(enrollment)

                            # Update course enrollment count
                            course.total_enrollments += 1

        # Mark order as completed
        order.status = OrderStatus.COMPLETED
        order.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(order)

        return order

    @staticmethod
    def cancel_order(db: Session, order_id: int, reason: Optional[str] = None) -> Order:
        """Cancel pending order"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status != OrderStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel order with status {order.status}",
            )

        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.utcnow()

        if reason:
            order.admin_notes = f"Cancellation reason: {reason}"

        db.commit()
        db.refresh(order)

        return order

    @staticmethod
    def build_order_response(db: Session, order: Order) -> OrderResponse:
        """Build complete order response with items"""
        # Get order items
        order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()

        item_responses = []
        for item in order_items:
            # Get course thumbnail if applicable
            course_thumbnail = None
            if item.course_id:
                course = db.query(Course).filter(Course.id == item.course_id).first()
                if course:
                    course_thumbnail = course.thumbnail_url

            item_response = OrderItemResponse(
                id=item.id,
                order_id=item.order_id,
                course_id=item.course_id,
                bundle_id=item.bundle_id,
                item_name=item.item_name,
                item_description=item.item_description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount=item.discount,
                total=item.total,
                coupon_code=item.coupon_code,
                created_at=item.created_at,
                course_thumbnail=course_thumbnail,
            )
            item_responses.append(item_response)

        return OrderResponse(
            id=order.id,
            order_number=order.order_number,
            user_id=order.user_id,
            guest_email=order.guest_email,
            status=order.status.value,
            subtotal=order.subtotal,
            discount=order.discount,
            tax=order.tax,
            total=order.total,
            currency=order.currency,
            billing_name=order.billing_name,
            billing_email=order.billing_email,
            customer_notes=order.customer_notes,
            created_at=order.created_at,
            updated_at=order.updated_at,
            completed_at=order.completed_at,
            items=item_responses,
        )
