# Core Models
from app.models.user import User
from app.models.task import Task
from app.models.group import Group
from app.models.meditation import MeditationSession
from app.models.activity_log import ActivityLog
from app.models.submission import HandwritingSubmission
from app.models.reward import UserReward
from app.models.lesson_progress import LessonProgress
from app.models.lesson_drip import LessonDripSetting
from app.models.course_review import CourseReview, ReviewHelpful
from app.models.course_payment import CoursePayment
from app.models.certificate import Certificate
from app.models.category import Category, Tag
from app.models.assignment import Assignment, Submission
from app.models.discussion import (
    DiscussionCategory,
    DiscussionThread,
    DiscussionPost,
    PostVote,
)
from app.models.announcement import CourseAnnouncement, AnnouncementRead
from app.models.student_notes import LessonNote, LessonBookmark, CourseBookmark
from app.models.question_bank import QuestionBank, BankQuestion, QuizQuestionPool
from app.models.peer_review import PeerReview, PeerReviewAssignment
from app.models.live_class import LiveClass, LiveClassAttendance
from app.models.live_class_interactive import (
    LiveClassPoll,
    LiveClassPollResponse,
    LiveClassQuestion,
    LiveClassReaction,
    LiveClassChatMessage,
)
from app.models.learning_path import LearningPath, PathCourse, PathEnrollment
from app.models.certificate_template import CertificateTemplate
from app.models.bundle import CourseBundle, BundleEnrollment
from app.models.course import Course
from app.models.module import Module
from app.models.lesson import Lesson
from app.models.enrollment import Enrollment
from app.models.quiz import (
    Quiz,
    Question,
    QuestionOption,
    QuizAttempt,
    StudentAnswer,
    QuizFeedback,
    QuizAttemptAnalytics,
    AssessmentRubric,
    AIGradingResult,
)
from app.models.mood import MoodEntry
from app.models.exam import ExamSession
from app.models.shadow_mode import ShadowModeSession
from app.models.study_room import StudyRoom
from app.models.study_group import StudyGroup
from app.models.learning_group import (
    LearningGroup,
    GroupMembership,
    GroupPost,
    GroupPostComment,
)
from app.models.collaborative_project import (
    CollaborativeProject,
    ProjectTeam,
    ProjectTeamMember,
    ProjectMilestone,
    ProjectSubmission,
)

# Chatbot and Recommendations
from app.models.chat import RealtimeChatMessage, RealtimeUserPresence
from app.models.chatbot import ChatSession, ChatMessage, ChatFeedback
from app.models.recommendations import (
    UserActivity,
    CourseRecommendation,
    UserPreference,
)
from app.models.ai_conversation import AIConversation

# Permissions (RBAC)
from app.models.permissions import Role, Permission, role_permissions, user_roles

# Notifications
from app.models.notification import Notification

# Email Notifications
from app.models.email_notification import (
    UserEmailPreference,
    EmailTemplate,
    EmailLog,
    NotificationType,
    EmailStatus,
)

# Coupons
from app.models.coupon import Coupon, CouponUsage

# Shopping Cart
from app.models.cart import ShoppingCart, CartItem

# Orders
from app.models.order import Order, OrderItem, OrderStatus

# Invoices
from app.models.invoice import Invoice

# Analytics
from app.models.analytics import (
    InstructorAnalytics,
    StudentAnalytics,
    PlatformAnalytics,
    AnalyticsEvent,
)

# Translation/i18n
from app.models.translation import (
    Language,
    Translation,
    ContentTranslation,
    UserLanguagePreference,
)

# Marketplace
from app.models.marketplace import (
    RevenueShare,
    InstructorPayout,
    InstructorPaymentInfo,
    MarketplaceListing,
    RevenueTransaction,
)

# Subscriptions
from app.models.subscription import (
    SubscriptionPlan,
    UserSubscription,
    SubscriptionInvoice,
    SubscriptionCoupon,
)

# Affiliate Program
from app.models.affiliate import (
    AffiliatePartner,
    AffiliateClick,
    AffiliateReferral,
    AffiliateCommission,
    AffiliatePayout,
)

# AI Features
from app.models.ai_features import (
    ContentEmbedding,
    PlagiarismCheck,
    AIGeneratedQuiz,
    ContentDifficultyAnalysis,
    AIUsageLog,
)

# Enterprise SSO
from app.models.sso import (
    Organization,
    SSOConfig,
    SSOSession,
    SSOAuditLog,
    SSOProviderType,
)

# Two-Factor Authentication
from app.models.two_factor import TwoFactorAuth, TwoFactorBackupCode

# Gamification
from app.models.achievement import UserAchievement, Achievement
from app.models.challenge import UserChallenge, Challenge
from app.models.coin_transaction import CoinTransaction

# UPSC Platform
from app.models.upsc import (
    UPSCBatch,
    UPSCStudentProfile,
    UPSCPlan,
    UPSCQuestion,
    UPSCContent,
    UPSCDrill,
    UPSCStudentProgress,
    UPSCAttempt,
    UPSCReport,
    UPSCTimerConfig,
    UPSCRubric,
)

# Lead Management
from app.models.lead import Lead

# User Management
from app.models.user_management import DataMaskingConfig, UserPermission, UserSession

# Marketing Automation
from app.models.marketing_automation import (
    CommunicationTemplate,
    MarketingWorkflow,
    WorkflowStep,
    WorkflowExecution,
    MessageLog,
    AutomationAnalytics,
)
