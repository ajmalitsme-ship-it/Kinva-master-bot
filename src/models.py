"""
Kinva Master - Data Models
Defines all data structures and ORM models
Author: @kinva_master
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from enum import Enum

# ============================================
# ENUMS
# ============================================

class UserStatus(Enum):
    """User account status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"
    DELETED = "deleted"

class PaymentStatus(Enum):
    """Payment status"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class ExportType(Enum):
    """Export type"""
    VIDEO = "video"
    IMAGE = "image"
    DESIGN = "design"
    GIF = "gif"

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
        data = asdict(self)
        
        # Convert datetime to string
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BaseModel':
        """Create from dictionary"""
        # Convert datetime strings
        if 'created_at' in data and data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and data['updated_at']:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
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
        """Get full name"""
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
        if not self.is_premium_active:
            return 0
        if self.premium_until:
            delta = self.premium_until - datetime.now()
            return max(0, delta.days)
        return 0
    
    @property
    def exports_left(self) -> int:
        """Get exports left today"""
        from .config import Config
        limit = Config.PREMIUM_VIDEO_EXPORTS if self.is_premium_active else Config.FREE_VIDEO_EXPORTS
        return max(0, limit - self.exports_today)
    
    @property
    def can_export(self) -> bool:
        """Check if user can export"""
        return self.is_premium_active or self.exports_left > 0
    
    @property
    def storage_percentage(self) -> float:
        """Get storage usage percentage"""
        from .config import Config
        limit = Config.PREMIUM_MAX_STORAGE if self.is_premium_active else Config.FREE_MAX_STORAGE
        return (self.storage_used / limit) * 100 if limit > 0 else 0

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
    watermark_enabled: bool = True
    email_notifications: bool = True
    telegram_notifications: bool = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserSettings':
        """Create from dictionary"""
        return cls(**data)

# ============================================
# DESIGN MODELS
# ============================================

@dataclass
class DesignElement:
    """Design element model"""
    id: str
    type: str  # text, image, shape
    x: float
    y: float
    width: float
    height: float
    rotation: float = 0
    opacity: float = 1.0
    z_index: int = 0
    data: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class DesignLayer:
    """Design layer model"""
    id: str
    name: str
    visible: bool = True
    locked: bool = False
    elements: List[DesignElement] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['elements'] = [e.to_dict() for e in self.elements]
        return data

@dataclass
class Design(BaseModel):
    """Design model"""
    user_id: int
    title: str
    description: Optional[str] = None
    design_data: Dict = field(default_factory=dict)
    thumbnail: Optional[str] = None
    width: int = 1920
    height: int = 1080
    elements: List[DesignElement] = field(default_factory=list)
    layers: List[DesignLayer] = field(default_factory=list)
    background: Dict = field(default_factory=dict)
    is_premium: bool = False
    is_public: bool = False
    views: int = 0
    likes: int = 0
    shares: int = 0
    share_url: Optional[str] = None
    
    def add_element(self, element: DesignElement):
        """Add element to design"""
        self.elements.append(element)
    
    def remove_element(self, element_id: str):
        """Remove element by ID"""
        self.elements = [e for e in self.elements if e.id != element_id]
    
    def get_element(self, element_id: str) -> Optional[DesignElement]:
        """Get element by ID"""
        for element in self.elements:
            if element.id == element_id:
                return element
        return None
    
    def add_layer(self, layer: DesignLayer):
        """Add layer to design"""
        self.layers.append(layer)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = super().to_dict()
        data['elements'] = [e.to_dict() for e in self.elements]
        data['layers'] = [l.to_dict() for l in self.layers]
        return data

# ============================================
# VIDEO MODELS
# ============================================

@dataclass
class VideoEffect:
    """Video effect model"""
    name: str
    type: str  # filter, transition, speed
    params: Dict = field(default_factory=dict)
    duration: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class Video(BaseModel):
    """Video model"""
    user_id: int
    title: str
    description: Optional[str] = None
    file_path: str
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
    def aspect_ratio(self) -> float:
        """Get aspect ratio"""
        if self.width and self.height and self.height > 0:
            return self.width / self.height
        return 16/9
    
    @property
    def size_mb(self) -> float:
        """Get size in MB"""
        return self.file_size / (1024 * 1024)
    
    def add_effect(self, effect: VideoEffect):
        """Add effect to video"""
        self.effects.append(effect)
    
    def remove_effect(self, effect_name: str):
        """Remove effect by name"""
        self.effects = [e for e in self.effects if e.name != effect_name]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = super().to_dict()
        data['effects'] = [e.to_dict() for e in self.effects]
        return data

# ============================================
# IMAGE MODELS
# ============================================

@dataclass
class ImageFilter:
    """Image filter model"""
    name: str
    params: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class Image(BaseModel):
    """Image model"""
    user_id: int
    title: str
    description: Optional[str] = None
    file_path: str
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
        """Get size in KB"""
        return self.file_size / 1024
    
    def add_filter(self, filter: ImageFilter):
        """Add filter to image"""
        self.filters.append(filter)
    
    def remove_filter(self, filter_name: str):
        """Remove filter by name"""
        self.filters = [f for f in self.filters if f.name != filter_name]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = super().to_dict()
        data['filters'] = [f.to_dict() for f in self.filters]
        return data

# ============================================
# TEMPLATE MODELS
# ============================================

@dataclass
class Template(BaseModel):
    """Template model"""
    title: str
    description: Optional[str] = None
    category: str
    type: str
    thumbnail: Optional[str] = None
    preview_url: Optional[str] = None
    template_data: Dict = field(default_factory=dict)
    is_premium: bool = False
    downloads: int = 0
    views: int = 0
    created_by: Optional[int] = None
    
    def increment_downloads(self):
        """Increment download count"""
        self.downloads += 1
    
    def increment_views(self):
        """Increment view count"""
        self.views += 1
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = super().to_dict()
        return data

# ============================================
# PAYMENT MODELS
# ============================================

@dataclass
class Payment(BaseModel):
    """Payment model"""
    user_id: int
    amount: float
    currency: str = "USD"
    payment_id: str
    stripe_session_id: Optional[str] = None
    plan_id: Optional[str] = None
    status: PaymentStatus = PaymentStatus.PENDING
    months: int = 1
    completed_at: Optional[datetime] = None
    
    @property
    def is_completed(self) -> bool:
        """Check if payment is completed"""
        return self.status == PaymentStatus.COMPLETED
    
    def complete(self):
        """Mark payment as completed"""
        self.status = PaymentStatus.COMPLETED
        self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = super().to_dict()
        data['status'] = self.status.value
        return data

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
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = super().to_dict()
        data['type'] = self.type.value
        return data

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
        data = super().to_dict()
        return data

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
    
    def mark_read(self):
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
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = super().to_dict()
        return data

# ============================================
# STATISTICS MODELS
# ============================================

@dataclass
class DailyStats:
    """Daily statistics model"""
    date: str
    users: int = 0
    exports: int = 0
    videos: int = 0
    images: int = 0
    designs: int = 0
    revenue: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class UserStats:
    """User statistics model"""
    user_id: int
    total_exports: int = 0
    total_videos: int = 0
    total_images: int = 0
    total_designs: int = 0
    total_storage: int = 0
    exports_today: int = 0
    exports_this_week: int = 0
    exports_this_month: int = 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

# ============================================
# PREMIUM PLAN MODELS
# ============================================

@dataclass
class PremiumPlan:
    """Premium plan model"""
    id: str
    name: str
    price: float
    interval: str  # month, year, once
    features: List[str] = field(default_factory=list)
    is_popular: bool = False
    discount: int = 0
    
    @property
    def formatted_price(self) -> str:
        """Get formatted price"""
        if self.price == 0:
            return "Free"
        return f"${self.price:.2f}"
    
    @property
    def monthly_price(self) -> float:
        """Get monthly price equivalent"""
        if self.interval == "year":
            return self.price / 12
        return self.price
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        return data

# ============================================
# FACTORY METHODS
# ============================================

class ModelFactory:
    """Factory for creating model instances"""
    
    @staticmethod
    def create_user(telegram_id: int, **kwargs) -> User:
        """Create user model"""
        return User(telegram_id=telegram_id, **kwargs)
    
    @staticmethod
    def create_design(user_id: int, title: str, **kwargs) -> Design:
        """Create design model"""
        return Design(user_id=user_id, title=title, **kwargs)
    
    @staticmethod
    def create_video(user_id: int, title: str, file_path: str, **kwargs) -> Video:
        """Create video model"""
        return Video(user_id=user_id, title=title, file_path=file_path, **kwargs)
    
    @staticmethod
    def create_image(user_id: int, title: str, file_path: str, **kwargs) -> Image:
        """Create image model"""
        return Image(user_id=user_id, title=title, file_path=file_path, **kwargs)
    
    @staticmethod
    def create_template(title: str, category: str, type: str, **kwargs) -> Template:
        """Create template model"""
        return Template(title=title, category=category, type=type, **kwargs)
    
    @staticmethod
    def create_payment(user_id: int, amount: float, payment_id: str, **kwargs) -> Payment:
        """Create payment model"""
        return Payment(user_id=user_id, amount=amount, payment_id=payment_id, **kwargs)
    
    @staticmethod
    def create_export(user_id: int, type: ExportType, file_path: str, size: int, **kwargs) -> Export:
        """Create export model"""
        return Export(user_id=user_id, type=type, file_path=file_path, size=size, **kwargs)
    
    @staticmethod
    def create_notification(user_id: int, title: str, message: str, **kwargs) -> Notification:
        """Create notification model"""
        return Notification(user_id=user_id, title=title, message=message, **kwargs)

# ============================================
# VALIDATION MODELS
# ============================================

@dataclass
class ValidationError:
    """Validation error model"""
    field: str
    message: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class ValidationResult:
    """Validation result model"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    
    def add_error(self, field: str, message: str):
        """Add validation error"""
        self.errors.append(ValidationError(field=field, message=message))
        self.is_valid = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'is_valid': self.is_valid,
            'errors': [e.to_dict() for e in self.errors]
        }

class Validator:
    """Model validator"""
    
    @staticmethod
    def validate_user(user: User) -> ValidationResult:
        """Validate user model"""
        result = ValidationResult(is_valid=True)
        
        if not user.telegram_id:
            result.add_error('telegram_id', 'Telegram ID is required')
        
        if user.email and '@' not in user.email:
            result.add_error('email', 'Invalid email format')
        
        if user.username and len(user.username) < 3:
            result.add_error('username', 'Username must be at least 3 characters')
        
        return result
    
    @staticmethod
    def validate_design(design: Design) -> ValidationResult:
        """Validate design model"""
        result = ValidationResult(is_valid=True)
        
        if not design.title:
            result.add_error('title', 'Title is required')
        
        if not design.user_id:
            result.add_error('user_id', 'User ID is required')
        
        if design.width <= 0 or design.height <= 0:
            result.add_error('dimensions', 'Invalid dimensions')
        
        return result
    
    @staticmethod
    def validate_video(video: Video) -> ValidationResult:
        """Validate video model"""
        result = ValidationResult(is_valid=True)
        
        if not video.title:
            result.add_error('title', 'Title is required')
        
        if not video.file_path:
            result.add_error('file_path', 'File path is required')
        
        if video.duration and video.duration <= 0:
            result.add_error('duration', 'Invalid duration')
        
        return result
    
    @staticmethod
    def validate_image(image: Image) -> ValidationResult:
        """Validate image model"""
        result = ValidationResult(is_valid=True)
        
        if not image.title:
            result.add_error('title', 'Title is required')
        
        if not image.file_path:
            result.add_error('file_path', 'File path is required')
        
        return result

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
    is_premium: bool
    exports_left: int
    storage_used: int
    total_exports: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class DesignDTO:
    """Design data transfer object"""
    id: int
    title: str
    thumbnail: Optional[str]
    created_at: str
    views: int
    likes: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class VideoDTO:
    """Video data transfer object"""
    id: int
    title: str
    duration: Optional[float]
    thumbnail: Optional[str]
    created_at: str
    views: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class ImageDTO:
    """Image data transfer object"""
    id: int
    title: str
    width: Optional[int]
    height: Optional[int]
    thumbnail: Optional[str]
    created_at: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)

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
        return asdict(self)

# ============================================
# EXPORTS
# ============================================

__all__ = [
    # Enums
    'UserStatus', 'PaymentStatus', 'ExportType', 'NotificationType',
    
    # Models
    'User', 'UserSettings', 'Design', 'DesignElement', 'DesignLayer',
    'Video', 'VideoEffect', 'Image', 'ImageFilter',
    'Template', 'Payment', 'Export', 'AnalyticsEvent',
    'Notification', 'Session',
    
    # Statistics
    'DailyStats', 'UserStats', 'PremiumPlan',
    
    # Factory
    'ModelFactory',
    
    # Validation
    'Validator', 'ValidationResult', 'ValidationError',
    
    # DTOs
    'UserDTO', 'DesignDTO', 'VideoDTO', 'ImageDTO', 'TemplateDTO'
]
