"""
Start Handler - Handles /start command and main menu
Author: @kinva_master
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from ..database import db
from ..config import Config

logger = logging.getLogger(__name__)

class StartHandler:
    """Handler for /start command"""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Register user
        user_data = db.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        is_premium = user_data.get('is_premium', False) if user_data else False
        exports_left = user_data.get('exports_left', 3) if user_data else 3
        total_edits = user_data.get('total_edits', 0) if user_data else 0
        
        # Welcome message
        welcome_text = (
            f"🎬 <b>Welcome to Kinva Master!</b>\n\n"
            f"Hello {user.first_name}! I'm your professional video and image editing assistant.\n\n"
            f"<b>✨ Features:</b>\n"
            f"• 🎨 Canva-style design editor\n"
            f"• 🎥 Video editor with 20+ effects\n"
            f"• 🖼️ Image editor with 30+ filters\n"
            f"• ⭐ Premium: 4K, no watermark, unlimited exports\n\n"
            f"<b>📊 Your Status:</b>\n"
            f"• Account: {'⭐ Premium' if is_premium else '🆓 Free'}\n"
            f"• Exports left today: {exports_left}\n"
            f"• Total edits: {total_edits}\n\n"
            f"📱 Click the button below to open the Web App!"
        )
        
        # Main menu keyboard
        keyboard = [
            [InlineKeyboardButton("🚀 Open Web App", web_app=WebAppInfo(url=Config.WEBAPP_URL))],
            [
                InlineKeyboardButton("🎬 Edit Video", callback_data="video"),
                InlineKeyboardButton("🖼️ Edit Image", callback_data="image")
            ],
            [
                InlineKeyboardButton("🎨 Design", callback_data="design"),
                InlineKeyboardButton("📋 Templates", callback_data="templates")
            ],
            [
                InlineKeyboardButton("⭐ Premium", callback_data="premium"),
                InlineKeyboardButton("👤 Profile", callback_data="profile")
            ],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        
        # Add upgrade button for free users
        if not is_premium:
            keyboard.insert(0, [InlineKeyboardButton("⭐ UPGRADE TO PREMIUM", callback_data="premium")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        
        logger.info(f"User {user.id} (@{user.username}) started the bot")
    
    @staticmethod
    async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "❓ <b>Kinva Master Help</b>\n\n"
            "<b>📱 Commands:</b>\n"
            "/start - Start the bot\n"
            "/help - Show this help\n"
            "/editor - Open design editor\n"
            "/video - Edit a video\n"
            "/image - Edit an image\n"
            "/templates - Browse templates\n"
            "/premium - Premium plans\n"
            "/profile - Your profile\n"
            "/myworks - Your saved works\n"
            "/stats - Your statistics\n"
            "/settings - Bot settings\n"
            "/feedback - Send feedback\n"
            "/contact - Contact admin\n\n"
            "<b>🎬 Video Editing:</b>\n"
            "1. Send a video or use /video\n"
            "2. Select effects to apply\n"
            "3. Wait for processing (1-3 minutes)\n"
            "4. Download the result\n\n"
            "<b>🖼️ Image Editing:</b>\n"
            "1. Send an image or use /image\n"
            "2. Select filters to apply\n"
            "3. Wait for processing (few seconds)\n"
            "4. Download the result\n\n"
            "<b>🎨 Design Editor:</b>\n"
            "Use /editor to open the Canva-style editor\n\n"
            f"<b>📞 Need more help?</b> Contact @{Config.ADMIN_CONTACT}"
        )
        
        keyboard = [
            [InlineKeyboardButton("📚 Video Tutorial", url="https://kinva-master.com/tutorial")],
            [InlineKeyboardButton("📞 Contact Support", callback_data="contact")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    
    @staticmethod
    async def handle_editor(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /editor command"""
        user = update.effective_user
        user_data = db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        text = (
            "🎨 <b>Design Studio</b>\n\n"
            "Create stunning designs with our Canva-style editor!\n\n"
            "<b>Features:</b>\n"
            "• 100+ professional fonts\n"
            "• 500+ ready-to-use templates\n"
            "• Text effects (shadow, outline, glow)\n"
            "• Shapes, icons, and stickers\n"
            "• Layer management\n"
            "• Export as PNG, JPG, PDF\n\n"
            f"<b>⭐ Premium Features:</b>\n"
            f"• 4K export{' (available)' if is_premium else ' - Upgrade to unlock'}\n"
            f"• No watermark{' (available)' if is_premium else ' - Upgrade to unlock'}\n"
            "• Advanced effects\n"
            "• Cloud storage\n\n"
            "Click the button below to start creating!"
        )
        
        keyboard = [
            [InlineKeyboardButton("🚀 Open Editor", web_app=WebAppInfo(url=f"{Config.WEBAPP_URL}/editor"))],
            [InlineKeyboardButton("📋 Browse Templates", callback_data="templates")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        if not is_premium:
            keyboard.insert(0, [InlineKeyboardButton("⭐ Unlock Premium Features", callback_data="premium")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def handle_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /profile command"""
        user = update.effective_user
        user_data = db.get_user(user.id)
        
        if not user_data:
            await update.message.reply_text("❌ User not found. Please use /start")
            return
        
        is_premium = user_data.get('is_premium', False)
        premium_until = user_data.get('premium_until', 'Never')
        exports_today = user_data.get('exports_today', 0)
        exports_limit = user_data.get('exports_limit', 3)
        total_edits = user_data.get('total_edits', 0)
        total_designs = user_data.get('total_designs', 0)
        videos_edited = user_data.get('videos_edited', 0)
        images_edited = user_data.get('images_edited', 0)
        storage_used = user_data.get('storage_used', 0)
        storage_limit = user_data.get('storage_limit', 100 * 1024 * 1024)  # 100MB
        joined = user_data.get('created_at', datetime.now()).split('T')[0] if user_data.get('created_at') else 'Unknown'
        
        # Format storage
        storage_used_mb = storage_used / (1024 * 1024)
        storage_limit_mb = storage_limit / (1024 * 1024)
        
        text = (
            f"👤 <b>User Profile</b>\n\n"
            f"<b>Name:</b> {user.first_name} {user.last_name or ''}\n"
            f"<b>Username:</b> @{user.username or 'None'}\n"
            f"<b>User ID:</b> <code>{user.id}</code>\n"
            f"<b>Joined:</b> {joined}\n\n"
            f"<b>💰 Account Status:</b> {'⭐ Premium' if is_premium else '🆓 Free'}\n"
        )
        
        if is_premium:
            text += f"<b>Premium Until:</b> {premium_until}\n\n"
        
        text += (
            f"<b>📊 Today's Usage:</b>\n"
            f"• Exports: {exports_today}/{exports_limit}\n"
            f"• Storage: {storage_used_mb:.1f}/{storage_limit_mb:.0f} MB\n\n"
            f"<b>📈 Lifetime Statistics:</b>\n"
            f"• Total Edits: {total_edits}\n"
            f"• Videos Edited: {videos_edited}\n"
            f"• Images Edited: {images_edited}\n"
            f"• Designs Created: {total_designs}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 Full Statistics", callback_data="stats")],
            [InlineKeyboardButton("🎨 My Designs", callback_data="my_designs")],
            [InlineKeyboardButton("🎬 My Videos", callback_data="my_videos")],
            [InlineKeyboardButton("🖼️ My Images", callback_data="my_images")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        ]
        
        if not is_premium:
            keyboard.insert(0, [InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="premium")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def handle_myworks(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /myworks command"""
        user = update.effective_user
        designs = db.get_user_designs(user.id, limit=5)
        videos = db.get_user_videos(user.id, limit=5)
        images = db.get_user_images(user.id, limit=5)
        
        text = (
            f"📁 <b>My Works</b>\n\n"
            f"<b>Recent Designs:</b> {len(designs)} total\n"
        )
        
        for design in designs[:3]:
            text += f"• {design['title']} - {design['created_at'][:10]}\n"
        
        text += f"\n<b>Recent Videos:</b> {len(videos)} total\n"
        for video in videos[:3]:
            text += f"• {video['title']} - {video['created_at'][:10]}\n"
        
        text += f"\n<b>Recent Images:</b> {len(images)} total\n"
        for image in images[:3]:
            text += f"• {image['title']} - {image['created_at'][:10]}\n"
        
        keyboard = [
            [InlineKeyboardButton("🎨 View All Designs", callback_data="my_designs")],
            [InlineKeyboardButton("🎬 View All Videos", callback_data="my_videos")],
            [InlineKeyboardButton("🖼️ View All Images", callback_data="my_images")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user = update.effective_user
        stats = db.get_user_stats(user.id)
        
        text = (
            f"📊 <b>Your Statistics</b>\n\n"
            f"<b>Daily Usage:</b>\n"
            f"• Exports Today: {stats.get('exports_today', 0)}/{stats.get('exports_limit', 3)}\n"
            f"• Videos Edited: {stats.get('videos_today', 0)}\n"
            f"• Images Edited: {stats.get('images_today', 0)}\n"
            f"• Designs Created: {stats.get('designs_today', 0)}\n\n"
            f"<b>Lifetime:</b>\n"
            f"• Total Exports: {stats.get('total_exports', 0)}\n"
            f"• Total Videos: {stats.get('total_videos', 0)}\n"
            f"• Total Images: {stats.get('total_images', 0)}\n"
            f"• Total Designs: {stats.get('total_designs', 0)}\n\n"
            f"<b>Storage:</b>\n"
            f"• Used: {stats.get('storage_used', 0)} MB\n"
            f"• Limit: {stats.get('storage_limit', 100)} MB\n"
            f"• Free: {stats.get('storage_free', 100)} MB\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("📈 Weekly Activity", callback_data="weekly_activity")],
            [InlineKeyboardButton("📉 Monthly Activity", callback_data="monthly_activity")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        user = update.effective_user
        settings = db.get_user_settings(user.id)
        
        text = (
            f"⚙️ <b>Settings</b>\n\n"
            f"<b>Notifications:</b> {'✅ On' if settings.get('notifications', True) else '❌ Off'}\n"
            f"<b>Auto-save:</b> {'✅ On' if settings.get('auto_save', True) else '❌ Off'}\n"
            f"<b>Quality:</b> {settings.get('default_quality', '720p')}\n"
            f"<b>Format:</b> {settings.get('default_format', 'mp4')}\n"
            f"<b>Language:</b> {settings.get('language', 'English')}\n"
            f"<b>Theme:</b> {settings.get('theme', 'Light')}\n\n"
            f"Click below to change settings in the web app!"
        )
        
        keyboard = [
            [InlineKeyboardButton("⚙️ Open Settings", web_app=WebAppInfo(url=f"{Config.WEBAPP_URL}/settings"))],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /feedback command"""
        await update.message.reply_text(
            "📝 <b>Send Feedback</b>\n\n"
            "We value your feedback! Please send your message and we'll review it.\n\n"
            "What would you like to share?\n"
            "• Bug report\n"
            "• Feature request\n"
            "• General feedback\n"
            "• Question\n\n"
            "Just type your message below:",
            parse_mode=ParseMode.HTML
        )
        
        return 'WAITING_FOR_FEEDBACK'
    
    @staticmethod
    async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /contact command"""
        text = (
            f"📞 <b>Contact Support</b>\n\n"
            f"Need help? Reach out to us through any of these channels:\n\n"
            f"<b>Telegram:</b> @{Config.ADMIN_CONTACT}\n"
            f"<b>Email:</b> support@kinva-master.com\n"
            f"<b>Website:</b> https://kinva-master.com\n"
            f"<b>Twitter:</b> @kinva_master\n"
            f"<b>Instagram:</b> @kinva.master\n\n"
            f"<b>Support Hours:</b>\n"
            f"Monday - Friday: 9 AM - 6 PM (UTC)\n"
            f"Saturday: 10 AM - 4 PM (UTC)\n"
            f"Sunday: Closed\n\n"
            f"Average response time: 2-4 hours"
        )
        
        keyboard = [
            [InlineKeyboardButton("💬 Telegram", url=f"https://t.me/{Config.ADMIN_CONTACT}")],
            [InlineKeyboardButton("📧 Email", url="mailto:support@kinva-master.com")],
            [InlineKeyboardButton("🌐 Website", url="https://kinva-master.com")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
      )
