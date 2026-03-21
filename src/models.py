"""
Data Models - Database models and schemas
Author: @kinva_master
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


# ============================================
# ENUMS
# ============================================

class UserStatus(Enum):
    """User account status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"


class PaymentStatus(Enum):
    """Payment status"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class ExportType(Enum):
    """Export type"""
    VIDEO = "video"
    IMAGE = "image"
    DESIGN = "design"


class NotificationType(Enum):
    """Notification type"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PREMIUM = "premium"


# ============================================
# BASE MODEL
# ============================================

@dataclass
class BaseModel:
    """Base model with common fields"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, Enum):
                data[key] = value.value
            else:
                data[key] = value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BaseModel':
        """Create from dictionary"""
        return cls(**data)


# ============================================
# USER MODELS
# ============================================

@dataclass
class User(BaseModel):
    """User model"""
    telegram_id: Optional[int] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    password_hash: Optional[str] = None
    avatar: Optional[str] = None
    is_premium: bool = False
    premium_until: Optional[datetime] = None
    trial_used: bool = False
    exports_today: int = 0
    exports_total: int = 0
    videos_edited: int = 0
    images_edited: int = 0
    designs_created: int = 0
    storage_used: int = 0
    status: UserStatus = UserStatus.ACTIVE
    settings: Dict = field(default_factory=dict)
    last_active: Optional[datetime] = None
    
    @property
    def full_name(self) -> str:
        """Get user full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.username or f"User_{self.telegram_id}"
    
    @property
    def is_premium_active(self) -> bool:
        """Check if premium is active"""
        if not self.is_premium:
            return False
        if self.premium_until and self.premium_until < datetime.now():
            return False
        return True
    
    @property
    def premium_days_left(self) -> int:
        """Get days left in premium"""
        if not self.is_premium_active or not self.premium_until:
            return 0
        delta = self.premium_until - datetime.now()
        return max(0, delta.days)
    
    @property
    def exports_left(self) -> int:
        """Get exports left today"""
        from ..config import Config
        limit = Config.PREMIUM_VIDEO_EXPORTS if self.is_premium_active else Config.FREE_VIDEO_EXPORTS
        return max(0, limit - self.exports_today)
    
    @property
    def can_export(self) -> bool:
        """Check if user can export"""
        return self.is_premium_active or self.exports_left > 0


@dataclass
class UserSettings:
    """User settings model"""
    user_id: int
    language: str = "en"
    theme: str = "light"
    notifications_enabled: bool = True
    email_notifications: bool = True
    telegram_notifications: bool = True
    auto_save: bool = True
    default_quality: str = "720p"
    default_format: str = "mp4"
    watermark_enabled: bool = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return self.__dict__.copy()
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserSettings':
        """Create from dictionary"""
        return cls(**data)


# ============================================
# DESIGN MODELS
# ============================================

@dataclass
class Design(BaseModel):
    """Design model"""
    user_id: int
    title: str
    design_data: Dict = field(default_factory=dict)
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    width: int = 1920
    height: int = 1080
    elements: List[Dict] = field(default_factory=list)
    layers: List[Dict] = field(default_factory=list)
    background: Dict = field(default_factory=dict)
    is_premium: bool = False
    is_public: bool = False
    views: int = 0
    likes: int = 0
    shares: int = 0
    share_url: Optional[str] = None
    
    def add_element(self, element: Dict) -> None:
        """Add element to design"""
        self.elements.append(element)
    
    def remove_element(self, element_id: str) -> None:
        """Remove element by ID"""
        self.elements = [e for e in self.elements if e.get('id') != element_id]
    
    def increment_views(self) -> None:
        """Increment view count"""
        self.views += 1
    
    def increment_likes(self) -> None:
        """Increment like count"""
        self.likes += 1


# ============================================
# VIDEO MODELS
# ============================================

@dataclass
class Video(BaseModel):
    """Video model"""
    user_id: int
    title: str
    file_path: str
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: int = 0
    format: Optional[str] = None
    effects: List[str] = field(default_factory=list)
    filters: List[str] = field(default_factory=list)
    transitions: List[str] = field(default_factory=list)
    is_premium: bool = False
    is_public: bool = False
    views: int = 0
    likes: int = 0
    shares: int = 0
    
    @property
    def size_mb(self) -> float:
        """Get size in MB"""
        return self.file_size / (1024 * 1024)
    
    @property
    def aspect_ratio(self) -> float:
        """Get aspect ratio"""
        if self.width and self.height and self.height > 0:
            return self.width / self.height
        return 16 / 9
    
    def add_effect(self, effect: str) -> None:
        """Add effect to video"""
        if effect not in self.effects:
            self.effects.append(effect)
    
    def remove_effect(self, effect: str) -> None:
        """Remove effect from video"""
        if effect in self.effects:
            self.effects.remove(effect)


# ============================================
# IMAGE MODELS
# ============================================

@dataclass
class Image(BaseModel):
    """Image model"""
    user_id: int
    title: str
    file_path: str
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: int = 0
    format: Optional[str] = None
    filters: List[str] = field(default_factory=list)
    is_premium: bool = False
    is_public: bool = False
    views: int = 0
    likes: int = 0
    shares: int = 0
    
    @property
    def size_kb(self) -> float:
        """Get size in KB"""
        return self.file_size / 1024
    
    def add_filter(self, filter_name: str) -> None:
        """Add filter to image"""
        if filter_name not in self.filters:
            self.filters.append(filter_name)
    
    def remove_filter(self, filter_name: str) -> None:
        """Remove filter from image"""
        if filter_name in self.filters:
            self.filters.remove(filter_name)


# ============================================
# TEMPLATE MODELS
# ============================================

@dataclass
class Template(BaseModel):
    """Template model"""
    title: str
    category: str
    type: str
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    preview_url: Optional[str] = None
    template_data: Dict = field(default_factory=dict)
    is_premium: bool = False
    downloads: int = 0
    views: int = 0
    created_by: Optional[int] = None
    
    def increment_downloads(self) -> None:
        """Increment download count"""
        self.downloads += 1
    
    def increment_views(self) -> None:
        """Increment view count"""
        self.views += 1


# ============================================
# PAYMENT MODELS
# ============================================

@dataclass
class Payment(BaseModel):
    """Payment model"""
    user_id: int
    amount: float
    payment_id: str
    currency: str = "USD"
    stripe_session_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    plan_id: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    months: int = 1
    completed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    
    @property
    def is_completed(self) -> bool:
        """Check if payment is completed"""
        return self.status == PaymentStatus.COMPLETED
    
    def complete(self) -> None:
        """Mark payment as completed"""
        self.status = PaymentStatus.COMPLETED
        self.completed_at = datetime.now()
    
    def refund(self) -> None:
        """Mark payment as refunded"""
        self.status = PaymentStatus.REFUNDED
        self.refunded_at = datetime.now()


# ============================================
# EXPORT MODELS
# ============================================

@dataclass
class Export(BaseModel):
    """Export model"""
    user_id: int
    type: ExportType
    file_path: str
    size: int
    format: Optional[str] = None
    
    @property
    def size_mb(self) -> float:
        """Get size in MB"""
        return self.size / (1024 * 1024)
    
    @property
    def size_kb(self) -> float:
        """Get size in KB"""
        return self.size / 1024


# ============================================
# NOTIFICATION MODELS
# ============================================

@dataclass
class Notification(BaseModel):
    """Notification model"""
    user_id: int
    title: str
    message: str
    type: NotificationType = NotificationType.INFO
    is_read: bool = False
    action_url: Optional[str] = None
    
    def mark_read(self) -> None:
        """Mark notification as read"""
        self.is_read = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = super().to_dict()
        data['type'] = self.type.value
        return data


# ============================================
# SESSION MODELS
# ============================================

@dataclass
class Session(BaseModel):
    """User session model"""
    user_id: int
    session_token: str
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now() > self.expires_at
    
    @property
    def expires_in(self) -> int:
        """Get seconds until expiration"""
        if self.is_expired:
            return 0
        delta = self.expires_at - datetime.now()
        return int(delta.total_seconds())


# ============================================
# ANALYTICS MODELS
# ============================================

@dataclass
class AnalyticsEvent(BaseModel):
    """Analytics event model"""
    user_id: Optional[int] = None
    event_type: str
    event_data: Dict = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return self.__dict__.copy()


# ============================================
# FACTORY FUNCTIONS
# ============================================

def create_user(telegram_id: int, **kwargs) -> User:
    """Create user instance"""
    return User(telegram_id=telegram_id, **kwargs)


def create_design(user_id: int, title: str, **kwargs) -> Design:
    """Create design instance"""
    return Design(user_id=user_id, title=title, **kwargs)


def create_video(user_id: int, title: str, file_path: str, **kwargs) -> Video:
    """Create video instance"""
    return Video(user_id=user_id, title=title, file_path=file_path, **kwargs)


def create_image(user_id: int, title: str, file_path: str, **kwargs) -> Image:
    """Create image instance"""
    return Image(user_id=user_id, title=title, file_path=file_path, **kwargs)


def create_template(title: str, category: str, type: str, **kwargs) -> Template:
    """Create template instance"""
    return Template(title=title, category=category, type=type, **kwargs)


def create_payment(user_id: int, amount: float, payment_id: str, **kwargs) -> Payment:
    """Create payment instance"""
    return Payment(user_id=user_id, amount=amount, payment_id=payment_id, **kwargs)


def create_export(user_id: int, type: ExportType, file_path: str, size: int, **kwargs) -> Export:
    """Create export instance"""
    return Export(user_id=user_id, type=type, file_path=file_path, size=size, **kwargs)


def create_notification(user_id: int, title: str, message: str, **kwargs) -> Notification:
    """Create notification instance"""
    return Notification(user_id=user_id, title=title, message=message, **kwargs)


# ============================================
# VALIDATORS
# ============================================

class ModelValidator:
    """Model validator class"""
    
    @staticmethod
    def validate_user(user: User) -> List[str]:
        """Validate user model"""
        errors = []
        
        if not user.telegram_id and not user.email:
            errors.append("Either telegram_id or email is required")
        
        if user.email and '@' not in user.email:
            errors.append("Invalid email format")
        
        if user.username and (len(user.username) < 3 or len(user.username) > 30):
            errors.append("Username must be between 3 and 30 characters")
        
        return errors
    
    @staticmethod
    def validate_design(design: Design) -> List[str]:
        """Validate design model"""
        errors = []
        
        if not design.user_id:
            errors.append("user_id is required")
        
        if not design.title:
            errors.append("title is required")
        
        if design.width <= 0 or design.height <= 0:
            errors.append("Invalid dimensions")
        
        return errors
    
    @staticmethod
    def validate_video(video: Video) -> List[str]:
        """Validate video model"""
        errors = []
        
        if not video.user_id:
            errors.append("user_id is required")
        
        if not video.title:
            errors.append("title is required")
        
        if not video.file_path:
            errors.append("file_path is required")
        
        return errors
    
    @staticmethod
    def validate_payment(payment: Payment) -> List[str]:
        """Validate payment model"""
        errors = []
        
        if not payment.user_id:
            errors.append("user_id is required")
        
        if payment.amount <= 0:
            errors.append("amount must be positive")
        
        if not payment.payment_id:
            errors.append("payment_id is required")
        
        return errors


# ============================================
# DTOs (Data Transfer Objects)
# ============================================

@dataclass
class UserDTO:
    """User data transfer object"""
    id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    avatar: Optional[str]
    is_premium: bool
    exports_left: int
    storage_used: int
    total_exports: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'avatar': self.avatar,
            'is_premium': self.is_premium,
            'exports_left': self.exports_left,
            'storage_used': self.storage_used,
            'total_exports': self.total_exports
        }


@dataclass
class DesignDTO:
    """Design data transfer object"""
    id: int
    title: str
    thumbnail: Optional[str]
    created_at: str
    views: int
    likes: int
    is_premium: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'thumbnail': self.thumbnail,
            'created_at': self.created_at,
            'views': self.views,
            'likes': self.likes,
            'is_premium': self.is_premium
        }


@dataclass
class VideoDTO:
    """Video data transfer object"""
    id: int
    title: str
    duration: Optional[float]
    thumbnail: Optional[str]
    created_at: str
    views: int
    size_mb: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'duration': self.duration,
            'thumbnail': self.thumbnail,
            'created_at': self.created_at,
            'views': self.views,
            'size_mb': self.size_mb
        }


@dataclass
class TemplateDTO:
    """Template data transfer object"""
    id: int
    title: str
    category: str
    type: str
    thumbnail: Optional[str]
    is_premium: bool
    downloads: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'type': self.type,
            'thumbnail': self.thumbnail,
            'is_premium': self.is_premium,
            'downloads': self.downloads
}
