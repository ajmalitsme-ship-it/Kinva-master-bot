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
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"


class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class ExportType(Enum):
    VIDEO = "video"
    IMAGE = "image"
    DESIGN = "design"


class NotificationType(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PREMIUM = "premium"


# ============================================
# BASE MODEL - ALL FIELDS HAVE DEFAULTS
# ============================================

@dataclass
class BaseModel:
    """Base model - all fields have defaults"""
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
# USER MODELS - ALL FIELDS HAVE DEFAULTS
# ============================================

@dataclass
class User(BaseModel):
    """User model - all fields have defaults"""
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
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.username or f"User_{self.telegram_id}"
    
    @property
    def is_premium_active(self) -> bool:
        if not self.is_premium:
            return False
        if self.premium_until and self.premium_until < datetime.now():
            return False
        return True
    
    @property
    def premium_days_left(self) -> int:
        if not self.is_premium_active or not self.premium_until:
            return 0
        delta = self.premium_until - datetime.now()
        return max(0, delta.days)
    
    @property
    def exports_left(self) -> int:
        from ..config import Config
        limit = Config.PREMIUM_VIDEO_EXPORTS if self.is_premium_active else Config.FREE_VIDEO_EXPORTS
        return max(0, limit - self.exports_today)
    
    @property
    def can_export(self) -> bool:
        return self.is_premium_active or self.exports_left > 0


@dataclass
class UserSettings:
    """User settings model - all fields have defaults"""
    user_id: Optional[int] = None
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
        return self.__dict__.copy()
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserSettings':
        return cls(**data)


# ============================================
# DESIGN MODELS - ALL FIELDS HAVE DEFAULTS
# ============================================

@dataclass
class Design(BaseModel):
    """Design model - all fields have defaults"""
    user_id: Optional[int] = None
    title: Optional[str] = None
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
        self.elements.append(element)
    
    def remove_element(self, element_id: str) -> None:
        self.elements = [e for e in self.elements if e.get('id') != element_id]
    
    def increment_views(self) -> None:
        self.views += 1
    
    def increment_likes(self) -> None:
        self.likes += 1


# ============================================
# VIDEO MODELS - ALL FIELDS HAVE DEFAULTS
# ============================================

@dataclass
class Video(BaseModel):
    """Video model - all fields have defaults"""
    user_id: Optional[int] = None
    title: Optional[str] = None
    file_path: Optional[str] = None
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
        return self.file_size / (1024 * 1024)
    
    @property
    def aspect_ratio(self) -> float:
        if self.width and self.height and self.height > 0:
            return self.width / self.height
        return 16 / 9
    
    def add_effect(self, effect: str) -> None:
        if effect not in self.effects:
            self.effects.append(effect)
    
    def remove_effect(self, effect: str) -> None:
        if effect in self.effects:
            self.effects.remove(effect)


# ============================================
# IMAGE MODELS - ALL FIELDS HAVE DEFAULTS
# ============================================

@dataclass
class Image(BaseModel):
    """Image model - all fields have defaults"""
    user_id: Optional[int] = None
    title: Optional[str] = None
    file_path: Optional[str] = None
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
        return self.file_size / 1024
    
    def add_filter(self, filter_name: str) -> None:
        if filter_name not in self.filters:
            self.filters.append(filter_name)
    
    def remove_filter(self, filter_name: str) -> None:
        if filter_name in self.filters:
            self.filters.remove(filter_name)


# ============================================
# TEMPLATE MODELS - ALL FIELDS HAVE DEFAULTS
# ============================================

@dataclass
class Template(BaseModel):
    """Template model - all fields have defaults"""
    title: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    preview_url: Optional[str] = None
    template_data: Dict = field(default_factory=dict)
    is_premium: bool = False
    downloads: int = 0
    views: int = 0
    created_by: Optional[int] = None
    
    def increment_downloads(self) -> None:
        self.downloads += 1
    
    def increment_views(self) -> None:
        self.views += 1


# ============================================
# PAYMENT MODELS - ALL FIELDS HAVE DEFAULTS
# ============================================

@dataclass
class Payment(BaseModel):
    """Payment model - all fields have defaults"""
    user_id: Optional[int] = None
    amount: float = 0.0
    payment_id: Optional[str] = None
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
        return self.status == PaymentStatus.COMPLETED
    
    def complete(self) -> None:
        self.status = PaymentStatus.COMPLETED
        self.completed_at = datetime.now()
    
    def refund(self) -> None:
        self.status = PaymentStatus.REFUNDED
        self.refunded_at = datetime.now()


# ============================================
# EXPORT MODELS - ALL FIELDS HAVE DEFAULTS
# ============================================

@dataclass
class Export(BaseModel):
    """Export model - all fields have defaults"""
    user_id: Optional[int] = None
    type: ExportType = ExportType.VIDEO
    file_path: Optional[str] = None
    size: int = 0
    format: Optional[str] = None
    
    @property
    def size_mb(self) -> float:
        return self.size / (1024 * 1024)
    
    @property
    def size_kb(self) -> float:
        return self.size / 1024


# ============================================
# NOTIFICATION MODELS - ALL FIELDS HAVE DEFAULTS
# ============================================

@dataclass
class Notification(BaseModel):
    """Notification model - all fields have defaults"""
    user_id: Optional[int] = None
    title: Optional[str] = None
    message: Optional[str] = None
    type: NotificationType = NotificationType.INFO
    is_read: bool = False
    action_url: Optional[str] = None
    
    def mark_read(self) -> None:
        self.is_read = True
    
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data['type'] = self.type.value
        return data


# ============================================
# SESSION MODELS - ALL FIELDS HAVE DEFAULTS
# ============================================

@dataclass
class Session(BaseModel):
    """User session model - all fields have defaults"""
    user_id: Optional[int] = None
    session_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return True
        return datetime.now() > self.expires_at
    
    @property
    def expires_in(self) -> int:
        if not self.expires_at or self.is_expired:
            return 0
        delta = self.expires_at - datetime.now()
        return int(delta.total_seconds())


# ============================================
# ANALYTICS MODELS - ALL FIELDS HAVE DEFAULTS
# ============================================

@dataclass
class AnalyticsEvent(BaseModel):
    """Analytics event model - all fields have defaults"""
    user_id: Optional[int] = None
    event_type: Optional[str] = None
    event_data: Dict = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def to_dict(self) -> Dict:
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
