"""
Data Models - Database models and schemas
Author: @kinva_master
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


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
        data = self.__dict__.copy()
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data


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
    def exports_left(self) -> int:
        from ..config import Config
        limit = Config.PREMIUM_VIDEO_EXPORTS if self.is_premium_active else Config.FREE_VIDEO_EXPORTS
        return max(0, limit - self.exports_today)


@dataclass
class UserSettings:
    """User settings model"""
    user_id: int
    language: str = "en"
    theme: str = "light"
    notifications_enabled: bool = True
    auto_save: bool = True
    default_quality: str = "720p"
    default_format: str = "mp4"
    
    def to_dict(self) -> Dict:
        return self.__dict__.copy()


# ============================================
# DESIGN MODELS
# ============================================

@dataclass
class DesignElement:
    """Design element model"""
    id: str
    type: str
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0
    opacity: float = 1.0
    z_index: int = 0
    data: Dict = field(default_factory=dict)


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
    elements: List[DesignElement] = field(default_factory=list)
    layers: List[Dict] = field(default_factory=list)
    background: Dict = field(default_factory=dict)
    is_premium: bool = False
    is_public: bool = False
    views: int = 0
    likes: int = 0
    shares: int = 0
    share_url: Optional[str] = None
    
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data['elements'] = [e.__dict__ for e in self.elements]
        return data


# ============================================
# VIDEO MODELS
# ============================================

@dataclass
class VideoEffect:
    """Video effect model"""
    name: str
    type: str
    params: Dict = field(default_factory=dict)
    duration: Optional[float] = None


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
    effects: List[VideoEffect] = field(default_factory=list)
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


# ============================================
# IMAGE MODELS
# ============================================

@dataclass
class ImageFilter:
    """Image filter model"""
    name: str
    params: Dict = field(default_factory=dict)


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
    filters: List[ImageFilter] = field(default_factory=list)
    is_premium: bool = False
    is_public: bool = False
    views: int = 0
    likes: int = 0
    shares: int = 0
    
    @property
    def size_kb(self) -> float:
        return self.file_size / 1024


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
    plan_id: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    months: int = 1
    completed_at: Optional[datetime] = None
    
    @property
    def is_completed(self) -> bool:
        return self.status == PaymentStatus.COMPLETED


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
        return self.size / (1024 * 1024)


# ============================================
# NOTIFICATION MODELS
# ============================================

@dataclass
class Notification(BaseModel):
    """Notification model"""
    user_id: int
    title: str
    message: str
    type: str = "info"
    is_read: bool = False


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
