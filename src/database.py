"""
Kinva Master - Database Manager
Handles all database operations, queries, and data management
Author: @kinva_master
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from contextlib import contextmanager

from .config import Config

logger = logging.getLogger(__name__)

class Database:
    """Main Database Manager Class"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_URL.replace('sqlite:///', '')
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    is_premium BOOLEAN DEFAULT 0,
                    premium_until TIMESTAMP,
                    trial_used BOOLEAN DEFAULT 0,
                    exports_today INTEGER DEFAULT 0,
                    exports_total INTEGER DEFAULT 0,
                    videos_edited INTEGER DEFAULT 0,
                    images_edited INTEGER DEFAULT 0,
                    designs_created INTEGER DEFAULT 0,
                    storage_used INTEGER DEFAULT 0,
                    settings TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_export_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Designs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS designs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT,
                    description TEXT,
                    design_data TEXT,
                    thumbnail TEXT,
                    width INTEGER,
                    height INTEGER,
                    elements TEXT,
                    layers TEXT,
                    background TEXT,
                    is_premium BOOLEAN DEFAULT 0,
                    is_public BOOLEAN DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    share_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Videos table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT,
                    description TEXT,
                    file_path TEXT,
                    thumbnail TEXT,
                    duration REAL,
                    width INTEGER,
                    height INTEGER,
                    file_size INTEGER,
                    format TEXT,
                    effects TEXT,
                    filters TEXT,
                    transitions TEXT,
                    is_premium BOOLEAN DEFAULT 0,
                    is_public BOOLEAN DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Images table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT,
                    description TEXT,
                    file_path TEXT,
                    thumbnail TEXT,
                    width INTEGER,
                    height INTEGER,
                    file_size INTEGER,
                    format TEXT,
                    filters TEXT,
                    is_premium BOOLEAN DEFAULT 0,
                    is_public BOOLEAN DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Templates table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    description TEXT,
                    category TEXT,
                    type TEXT,
                    thumbnail TEXT,
                    preview_url TEXT,
                    template_data TEXT,
                    is_premium BOOLEAN DEFAULT 0,
                    downloads INTEGER DEFAULT 0,
                    views INTEGER DEFAULT 0,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Payments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    currency TEXT DEFAULT 'USD',
                    payment_id TEXT UNIQUE,
                    stripe_session_id TEXT,
                    plan_id TEXT,
                    status TEXT DEFAULT 'pending',
                    months INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Exports table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    type TEXT,
                    file_path TEXT,
                    size INTEGER,
                    format TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Analytics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    event_type TEXT,
                    event_data TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_token TEXT UNIQUE,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Notifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT,
                    message TEXT,
                    type TEXT,
                    is_read BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
            
            # Create indexes
            self.create_indexes()
            
            logger.info("Database initialized successfully")
    
    def create_indexes(self):
        """Create database indexes for performance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)",
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_users_premium ON users(is_premium)",
                "CREATE INDEX IF NOT EXISTS idx_designs_user_id ON designs(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_images_user_id ON images(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)",
                "CREATE INDEX IF NOT EXISTS idx_exports_user_id ON exports(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_analytics_user_id ON analytics(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read)"
            ]
            
            for index in indexes:
                cursor.execute(index)
            
            conn.commit()
    
    # ============================================
    # USER OPERATIONS
    # ============================================
    
    def get_or_create_user(self, telegram_id: int, **kwargs) -> Dict:
        """Get existing user or create new one"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            user = cursor.fetchone()
            
            if user:
                # Update last active
                cursor.execute('''
                    UPDATE users 
                    SET last_active = CURRENT_TIMESTAMP,
                        username = COALESCE(?, username),
                        first_name = COALESCE(?, first_name),
                        last_name = COALESCE(?, last_name)
                    WHERE telegram_id = ?
                ''', (
                    kwargs.get('username'),
                    kwargs.get('first_name'),
                    kwargs.get('last_name'),
                    telegram_id
                ))
                conn.commit()
                
                # Reset exports if needed
                self.check_reset_exports(telegram_id)
                
                # Get updated user
                cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
                user = cursor.fetchone()
            else:
                # Create new user
                cursor.execute('''
                    INSERT INTO users (
                        telegram_id, username, first_name, last_name,
                        email, is_premium, settings
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    telegram_id,
                    kwargs.get('username'),
                    kwargs.get('first_name'),
                    kwargs.get('last_name'),
                    kwargs.get('email'),
                    0,
                    json.dumps({'language': 'en', 'theme': 'light'})
                ))
                conn.commit()
                
                # Get new user
                cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
                user = cursor.fetchone()
            
            return dict(user) if user else None
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def get_user_by_telegram(self, telegram_id: int) -> Optional[Dict]:
        """Get user by Telegram ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def update_user(self, user_id: int, data: Dict) -> Dict:
        """Update user data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            fields = []
            values = []
            
            for key, value in data.items():
                if key in ['username', 'first_name', 'last_name', 'email', 'settings']:
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if fields:
                values.append(user_id)
                cursor.execute(f'''
                    UPDATE users 
                    SET {', '.join(fields)}, last_active = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', values)
                conn.commit()
            
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            return dict(cursor.fetchone())
    
    def update_user_premium(self, user_id: int, is_premium: bool = True, months: int = 1) -> bool:
        """Update user premium status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if is_premium:
                # Get current premium_until
                cursor.execute('SELECT premium_until FROM users WHERE id = ?', (user_id,))
                result = cursor.fetchone()
                
                if result and result['premium_until']:
                    current = datetime.fromisoformat(result['premium_until'])
                    if current > datetime.now():
                        new_date = current + timedelta(days=30 * months)
                    else:
                        new_date = datetime.now() + timedelta(days=30 * months)
                else:
                    new_date = datetime.now() + timedelta(days=30 * months)
                
                cursor.execute('''
                    UPDATE users 
                    SET is_premium = 1, premium_until = ?
                    WHERE id = ?
                ''', (new_date.isoformat(), user_id))
            else:
                cursor.execute('''
                    UPDATE users 
                    SET is_premium = 0, premium_until = NULL
                    WHERE id = ?
                ''', (user_id,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def activate_premium(self, user_id: int, months: int = 1, trial: bool = False) -> bool:
        """Activate premium subscription"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if trial:
                # 7-day trial
                premium_until = datetime.now() + timedelta(days=7)
                cursor.execute('''
                    UPDATE users 
                    SET is_premium = 1, premium_until = ?, trial_used = 1
                    WHERE id = ?
                ''', (premium_until.isoformat(), user_id))
            else:
                # Regular subscription
                cursor.execute('SELECT premium_until FROM users WHERE id = ?', (user_id,))
                result = cursor.fetchone()
                
                if result and result['premium_until']:
                    current = datetime.fromisoformat(result['premium_until'])
                    if current > datetime.now():
                        new_date = current + timedelta(days=30 * months)
                    else:
                        new_date = datetime.now() + timedelta(days=30 * months)
                else:
                    new_date = datetime.now() + timedelta(days=30 * months)
                
                cursor.execute('''
                    UPDATE users 
                    SET is_premium = 1, premium_until = ?
                    WHERE id = ?
                ''', (new_date.isoformat(), user_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def check_reset_exports(self, user_id: int):
        """Reset daily exports if needed"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT last_export_reset FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            
            if result:
                last_reset = datetime.fromisoformat(result['last_export_reset'])
                today = datetime.now().date()
                
                if last_reset.date() < today:
                    cursor.execute('''
                        UPDATE users 
                        SET exports_today = 0, last_export_reset = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (user_id,))
                    conn.commit()
    
    def increment_exports(self, user_id: int) -> bool:
        """Increment export counter"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET exports_today = exports_today + 1,
                    exports_total = exports_total + 1
                WHERE id = ?
            ''', (user_id,))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def increment_videos_edited(self, user_id: int) -> bool:
        """Increment videos edited counter"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET videos_edited = videos_edited + 1 WHERE id = ?
            ''', (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def increment_images_edited(self, user_id: int) -> bool:
        """Increment images edited counter"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET images_edited = images_edited + 1 WHERE id = ?
            ''', (user_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    exports_today,
                    exports_total,
                    videos_edited,
                    images_edited,
                    designs_created,
                    storage_used
                FROM users WHERE id = ?
            ''', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return {}
            
            limits = Config.get_user_limits(user['is_premium'])
            
            return {
                'exports_today': user['exports_today'],
                'exports_left': limits['video_exports'] - user['exports_today'],
                'exports_total': user['exports_total'],
                'videos_edited': user['videos_edited'],
                'images_edited': user['images_edited'],
                'designs_created': user['designs_created'],
                'storage_used': user['storage_used'],
                'storage_limit': limits['storage'],
                'storage_free': limits['storage'] - user['storage_used'],
                'video_limit': limits['video_length'],
                'export_limit': limits['video_exports']
            }
    
    def get_user_settings(self, user_id: int) -> Dict:
        """Get user settings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT settings FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            
            if result:
                return json.loads(result['settings'])
            return {}
    
    def update_user_settings(self, user_id: int, settings: Dict) -> Dict:
        """Update user settings"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            current = self.get_user_settings(user_id)
            current.update(settings)
            
            cursor.execute('''
                UPDATE users SET settings = ? WHERE id = ?
            ''', (json.dumps(current), user_id))
            conn.commit()
            
            return current
    
    # ============================================
    # DESIGN OPERATIONS
    # ============================================
    
    def create_design(self, user_id: int, title: str, design_data: Dict,
                     thumbnail: str = None, width: int = 1920, height: int = 1080) -> int:
        """Create new design"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO designs (
                    user_id, title, design_data, thumbnail,
                    width, height, elements, layers, background
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, title, json.dumps(design_data), thumbnail,
                width, height, '[]', '[]', '{}'
            ))
            conn.commit()
            
            # Update user stats
            cursor.execute('''
                UPDATE users SET designs_created = designs_created + 1 WHERE id = ?
            ''', (user_id,))
            conn.commit()
            
            return cursor.lastrowid
    
    def get_design(self, design_id: int) -> Optional[Dict]:
        """Get design by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM designs WHERE id = ?', (design_id,))
            design = cursor.fetchone()
            
            if design:
                design = dict(design)
                design['design_data'] = json.loads(design['design_data'])
                design['elements'] = json.loads(design['elements'])
                design['layers'] = json.loads(design['layers'])
                design['background'] = json.loads(design['background'])
                return design
            return None
    
    def get_user_designs(self, user_id: int, page: int = 1, limit: int = 20) -> List[Dict]:
        """Get user designs with pagination"""
        offset = (page - 1) * limit
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM designs 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (user_id, limit, offset))
            
            designs = []
            for row in cursor.fetchall():
                design = dict(row)
                design['design_data'] = json.loads(design['design_data'])
                designs.append(design)
            
            return designs
    
    def update_design(self, design_id: int, data: Dict) -> bool:
        """Update design"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            fields = []
            values = []
            
            if 'title' in data:
                fields.append('title = ?')
                values.append(data['title'])
            if 'design_data' in data:
                fields.append('design_data = ?')
                values.append(json.dumps(data['design_data']))
            if 'thumbnail' in data:
                fields.append('thumbnail = ?')
                values.append(data['thumbnail'])
            if 'elements' in data:
                fields.append('elements = ?')
                values.append(json.dumps(data['elements']))
            if 'layers' in data:
                fields.append('layers = ?')
                values.append(json.dumps(data['layers']))
            
            if fields:
                fields.append('updated_at = CURRENT_TIMESTAMP')
                values.append(design_id)
                cursor.execute(f'''
                    UPDATE designs 
                    SET {', '.join(fields)} 
                    WHERE id = ?
                ''', values)
                conn.commit()
                return cursor.rowcount > 0
            
            return False
    
    def delete_design(self, design_id: int) -> bool:
        """Delete design"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM designs WHERE id = ?', (design_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ============================================
    # VIDEO OPERATIONS
    # ============================================
    
    def save_video(self, user_id: int, title: str, file_path: str,
                  duration: float = None, width: int = None, height: int = None,
                  file_size: int = None, format: str = None,
                  effects: List = None) -> int:
        """Save video metadata"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO videos (
                    user_id, title, file_path, duration,
                    width, height, file_size, format, effects
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, title, file_path, duration,
                width, height, file_size, format,
                json.dumps(effects or [])
            ))
            conn.commit()
            
            return cursor.lastrowid
    
    def get_video(self, video_id: int) -> Optional[Dict]:
        """Get video by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM videos WHERE id = ?', (video_id,))
            video = cursor.fetchone()
            
            if video:
                video = dict(video)
                video['effects'] = json.loads(video['effects']) if video['effects'] else []
                return video
            return None
    
    def get_user_videos(self, user_id: int, page: int = 1, limit: int = 20) -> List[Dict]:
        """Get user videos"""
        offset = (page - 1) * limit
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM videos 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (user_id, limit, offset))
            
            videos = []
            for row in cursor.fetchall():
                video = dict(row)
                video['effects'] = json.loads(video['effects']) if video['effects'] else []
                videos.append(video)
            
            return videos
    
    def delete_video(self, video_id: int) -> bool:
        """Delete video"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM videos WHERE id = ?', (video_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ============================================
    # IMAGE OPERATIONS
    # ============================================
    
    def save_image(self, user_id: int, title: str, file_path: str,
                  width: int = None, height: int = None,
                  file_size: int = None, format: str = None,
                  filters: List = None) -> int:
        """Save image metadata"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO images (
                    user_id, title, file_path, width,
                    height, file_size, format, filters
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, title, file_path, width,
                height, file_size, format,
                json.dumps(filters or [])
            ))
            conn.commit()
            
            return cursor.lastrowid
    
    def get_image(self, image_id: int) -> Optional[Dict]:
        """Get image by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM images WHERE id = ?', (image_id,))
            image = cursor.fetchone()
            
            if image:
                image = dict(image)
                image['filters'] = json.loads(image['filters']) if image['filters'] else []
                return image
            return None
    
    def get_user_images(self, user_id: int, page: int = 1, limit: int = 20) -> List[Dict]:
        """Get user images"""
        offset = (page - 1) * limit
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM images 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (user_id, limit, offset))
            
            images = []
            for row in cursor.fetchall():
                image = dict(row)
                image['filters'] = json.loads(image['filters']) if image['filters'] else []
                images.append(image)
            
            return images
    
    def delete_image(self, image_id: int) -> bool:
        """Delete image"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM images WHERE id = ?', (image_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ============================================
    # TEMPLATE OPERATIONS
    # ============================================
    
    def create_template(self, title: str, category: str, template_type: str,
                       template_data: Dict, is_premium: bool = False,
                       thumbnail: str = None) -> int:
        """Create new template"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO templates (
                    title, category, type, template_data,
                    is_premium, thumbnail
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                title, category, template_type,
                json.dumps(template_data), is_premium, thumbnail
            ))
            conn.commit()
            
            return cursor.lastrowid
    
    def get_templates(self, category: str = None, type: str = None,
                     include_premium: bool = False, limit: int = 50) -> List[Dict]:
        """Get templates with filters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM templates WHERE 1=1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if type:
                query += " AND type = ?"
                params.append(type)
            
            if not include_premium:
                query += " AND is_premium = 0"
            
            query += " ORDER BY downloads DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            templates = []
            for row in cursor.fetchall():
                template = dict(row)
                template['template_data'] = json.loads(template['template_data'])
                templates.append(template)
            
            return templates
    
    def get_template(self, template_id: int) -> Optional[Dict]:
        """Get template by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM templates WHERE id = ?', (template_id,))
            template = cursor.fetchone()
            
            if template:
                template = dict(template)
                template['template_data'] = json.loads(template['template_data'])
                return template
            return None
    
    def increment_template_usage(self, template_id: int) -> bool:
        """Increment template download count"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE templates SET downloads = downloads + 1 WHERE id = ?
            ''', (template_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ============================================
    # PAYMENT OPERATIONS
    # ============================================
    
    def create_payment(self, user_id: int, amount: float, months: int = 1,
                      plan_id: str = None) -> Dict:
        """Create payment record"""
        import uuid
        
        payment_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO payments (
                    user_id, amount, payment_id, months, plan_id
                ) VALUES (?, ?, ?, ?, ?)
            ''', (user_id, amount, payment_id, months, plan_id))
            conn.commit()
            
            cursor.execute('SELECT * FROM payments WHERE payment_id = ?', (payment_id,))
            return dict(cursor.fetchone())
    
    def get_payment(self, payment_id: str) -> Optional[Dict]:
        """Get payment by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM payments WHERE payment_id = ?', (payment_id,))
            payment = cursor.fetchone()
            return dict(payment) if payment else None
    
    def update_payment_status(self, payment_id: str, status: str,
                             stripe_session_id: str = None) -> bool:
        """Update payment status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status == 'completed':
                cursor.execute('''
                    UPDATE payments 
                    SET status = ?, stripe_session_id = ?,
                        completed_at = CURRENT_TIMESTAMP
                    WHERE payment_id = ?
                ''', (status, stripe_session_id, payment_id))
            else:
                cursor.execute('''
                    UPDATE payments 
                    SET status = ?, stripe_session_id = ?
                    WHERE payment_id = ?
                ''', (status, stripe_session_id, payment_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    # ============================================
    # EXPORT OPERATIONS
    # ============================================
    
    def save_export(self, user_id: int, type: str, file_path: str,
                   size: int, format: str = None) -> int:
        """Save export record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO exports (user_id, type, file_path, size, format)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, type, file_path, size, format))
            conn.commit()
            return cursor.lastrowid
    
    def get_user_exports(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user export history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM exports 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    # ============================================
    # ANALYTICS OPERATIONS
    # ============================================
    
    def log_event(self, user_id: int, event_type: str,
                 event_data: Dict = None, ip: str = None,
                 user_agent: str = None) -> int:
        """Log analytics event"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO analytics (user_id, event_type, event_data, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, event_type, json.dumps(event_data or {}), ip, user_agent))
            conn.commit()
            return cursor.lastrowid
    
    def get_weekly_stats(self, user_id: int) -> List[Dict]:
        """Get weekly user statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    DATE(created_at) as day,
                    COUNT(*) as count
                FROM exports
                WHERE user_id = ? 
                    AND created_at >= DATE('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY day
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_monthly_stats(self, user_id: int) -> List[Dict]:
        """Get monthly user statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    strftime('%Y-%m', created_at) as month,
                    COUNT(*) as count
                FROM exports
                WHERE user_id = ? 
                    AND created_at >= DATE('now', '-6 months')
                GROUP BY strftime('%Y-%m', created_at)
                ORDER BY month
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ============================================
    # NOTIFICATION OPERATIONS
    # ============================================
    
    def create_notification(self, user_id: int, title: str,
                           message: str, type: str = 'info') -> int:
        """Create notification"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notifications (user_id, title, message, type)
                VALUES (?, ?, ?, ?)
            ''', (user_id, title, message, type))
            conn.commit()
            return cursor.lastrowid
    
    def get_notifications(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user notifications"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM notifications 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_notification_read(self, notification_id: int) -> bool:
        """Mark notification as read"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE notifications SET is_read = 1 WHERE id = ?
            ''', (notification_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # ============================================
    # ADMIN OPERATIONS
    # ============================================
    
    def get_admin_stats(self) -> Dict:
        """Get admin statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total users
            cursor.execute('SELECT COUNT(*) as count FROM users')
            total_users = cursor.fetchone()['count']
            
            # Premium users
            cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_premium = 1')
            premium_users = cursor.fetchone()['count']
            
            # Active today
            cursor.execute('''
                SELECT COUNT(*) as count FROM users 
                WHERE date(last_active) = date('now')
            ''')
            active_today = cursor.fetchone()['count']
            
            # Total designs
            cursor.execute('SELECT COUNT(*) as count FROM designs')
            total_designs = cursor.fetchone()['count']
            
            # Total videos
            cursor.execute('SELECT COUNT(*) as count FROM videos')
            total_videos = cursor.fetchone()['count']
            
            # Total images
            cursor.execute('SELECT COUNT(*) as count FROM images')
            total_images = cursor.fetchone()['count']
            
            # Total exports
            cursor.execute('SELECT COUNT(*) as count, SUM(size) as total_size FROM exports')
            exports = cursor.fetchone()
            
            # Total revenue
            cursor.execute('''
                SELECT COUNT(*) as count, SUM(amount) as total 
                FROM payments WHERE status = 'completed'
            ''')
            payments = cursor.fetchone()
            
            return {
                'total_users': total_users,
                'premium_users': premium_users,
                'free_users': total_users - premium_users,
                'active_today': active_today,
                'total_designs': total_designs,
                'total_videos': total_videos,
                'total_images': total_images,
                'total_exports': exports['count'] or 0,
                'total_storage': exports['total_size'] or 0,
                'total_payments': payments['count'] or 0,
                'total_revenue': float(payments['total'] or 0)
            }
    
    def get_all_users(self, page: int = 1, limit: int = 50,
                     search: str = None) -> List[Dict]:
        """Get all users (admin)"""
        offset = (page - 1) * limit
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM users WHERE 1=1"
            params = []
            
            if search:
                query += " AND (username LIKE ? OR first_name LIKE ? OR last_name LIKE ? OR email LIKE ?)"
                search_pattern = f"%{search}%"
                params.extend([search_pattern] * 4)
            
            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_user(self, user_id: int) -> bool:
        """Delete user and all associated data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            return cursor.rowcount > 0

# Create database instance
db = Database()
