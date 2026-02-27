from .user import User, UserCreate, UserUpdate
from .task import Task, TaskCreate, TaskUpdate
from .course import (
    Course,
    CourseCreate,
    CourseUpdate,
    Module,
    ModuleCreate,
    ModuleUpdate,
    Lesson,
    LessonCreate,
    LessonUpdate,
    Enrollment,
    EnrollmentCreate,
    EnrollmentUpdate,
    CourseReview,
    CourseReviewCreate,
)
from .course_payment import CoursePayment, CoursePaymentCreate, CoursePaymentUpdate
from .progress import (
    LessonProgress,
    LessonProgressUpdate,
    CourseProgress,
    Certificate,
    UniversalProgress,
    UniversalProgressUpdate,
)
from .coupon import (
    Coupon,
    CouponCreate,
    CouponUpdate,
    CouponValidationRequest,
    CouponValidationResponse,
    CouponUsageStats,
)
from .digital_product import DigitalProduct, DigitalProductCreate, DigitalProductUpdate
from .enquiry import Enquiry, EnquiryCreate, EnquiryUpdate
from .asset import Asset, AssetCreate, AssetUpdate
from .attendance import Attendance, AttendanceCreate
from .student_report import StudentReport, StudentReportCreate, StudentReportUpdate
from .app_config import AppConfig, AppConfigCreate, AppConfigUpdate
