"""
Kinva Master - Telegram Bot
Handles all bot commands, video/image processing, and user interactions
Author: @kinva_master
"""

import os
import sys
import json
import asyncio
import logging
import tempfile
import time
import uuid
import hashlib
import hmac
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import traceback

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, 
    WebAppInfo, InputMediaPhoto, InputMediaVideo,
    ChatAction, BotCommand, BotCommandScopeDefault
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler,
    PreCheckoutQueryHandler, ShippingQueryHandler, ChatMemberHandler,
    PicklePersistence
)
from telegram.constants import ParseMode
from telegram.error import TelegramError

# Import local modules
from .config import Config
from .database import Database
from .processors.video_processor import VideoProcessor
from .processors.image_processor import ImageProcessor
from .processors.watermark import Watermark
from .editors.canva_editor import CanvaEditor
from .payment.stripe_handler import StripeHandler
from .utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

# Conversation states
WAITING_FOR_VIDEO = 1
WAITING_FOR_IMAGE = 2
WAITING_FOR_EFFECTS = 3
WAITING_FOR_FILTERS = 4
WAITING_FOR_PREMIUM_PAYMENT = 5

class KinvaBot:
    """Main Telegram Bot Class"""
    
    def __init__(self):
        self.config = Config()
        self.db = Database()
        self.video_processor = VideoProcessor()
        self.image_processor = ImageProcessor()
        self.watermark = Watermark()
        self.canva_editor = CanvaEditor()
        self.stripe_handler = StripeHandler()
        self.application = None
        
    async def setup_commands(self):
        """Setup bot commands"""
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Show help menu"),
            BotCommand("editor", "Open design editor"),
            BotCommand("video", "Edit a video"),
            BotCommand("image", "Edit an image"),
            BotCommand("templates", "Browse templates"),
            BotCommand("premium", "Premium plans"),
            BotCommand("profile", "Your profile"),
            BotCommand("myworks", "Your saved works"),
            BotCommand("stats", "Your statistics"),
            BotCommand("settings", "Bot settings"),
            BotCommand("feedback", "Send feedback"),
            BotCommand("contact", "Contact admin"),
        ]
        
        await self.application.bot.set_my_commands(commands, scope=BotCommandScopeDefault())
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Register user
        self.db.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Check premium status
        user_data = self.db.get_user(user.id)
        is_premium = user_data['is_premium'] if user_data else False
        
        welcome_text = (
            f"🎬 <b>Welcome to Kinva Master!</b>\n\n"
            f"Hello {user.first_name}! I'm your professional video and image editing assistant.\n\n"
            f"<b>✨ Features:</b>\n"
            f"• 🎨 Canva-style design editor\n"
            f"• 🎥 Video editor with 20+ effects\n"
            f"• 🖼️ Image editor with 30+ filters\n"
            f"• ⭐ Premium: 4K, no watermark, unlimited exports\n\n"
            f"<b>📊 Your Stats:</b>\n"
            f"• Status: {'⭐ Premium' if is_premium else '🆓 Free'}\n"
            f"• Exports today: {user_data.get('exports_today', 0)}/{user_data.get('exports_limit', 3)}\n"
            f"• Total edits: {user_data.get('total_edits', 0)}\n\n"
            f"📱 Click the button below to open the Web App!"
        )
        
        keyboard = [
            [InlineKeyboardButton("🚀 Open Web App", web_app=WebAppInfo(url=self.config.WEBAPP_URL))],
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
        
        if not is_premium:
            keyboard.insert(0, [InlineKeyboardButton("⭐ UPGRADE TO PREMIUM", callback_data="premium")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        
        # Send welcome sticker (optional)
        try:
            await update.message.reply_sticker("CAACAgIAAxkBAAEB")
        except:
            pass
            
        logger.info(f"User {user.id} (@{user.username}) started the bot")
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        text = (
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
            "3. Wait for processing\n"
            "4. Download the result\n\n"
            "<b>🖼️ Image Editing:</b>\n"
            "1. Send an image or use /image\n"
            "2. Select filters to apply\n"
            "3. Wait for processing\n"
            "4. Download the result\n\n"
            "<b>🎨 Design Editor:</b>\n"
            "Use /editor to open the Canva-style editor\n\n"
            f"<b>💬 Need more help?</b> Contact @{self.config.ADMIN_CONTACT}"
        )
        
        keyboard = [
            [InlineKeyboardButton("📚 Video Tutorial", url="https://kinva-master.com/tutorial")],
            [InlineKeyboardButton("📞 Contact Support", callback_data="contact")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    async def editor_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /editor command"""
        user = update.effective_user
        
        text = (
            "🎨 <b>Design Editor</b>\n\n"
            "Create stunning designs with our Canva-style editor!\n\n"
            "<b>Features:</b>\n"
            "• 100+ professional fonts\n"
            "• 500+ ready-to-use templates\n"
            "• Text effects (shadow, outline, glow)\n"
            "• Shapes, icons, and stickers\n"
            "• Layer management\n"
            "• Export as PNG, JPG, PDF\n\n"
            "<b>⭐ Premium Features:</b>\n"
            "• 4K export\n"
            "• No watermark\n"
            "• Advanced effects\n"
            "• Cloud storage\n\n"
            "Click the button below to start creating!"
        )
        
        keyboard = [
            [InlineKeyboardButton("🚀 Open Editor", web_app=WebAppInfo(url=f"{self.config.WEBAPP_URL}/editor"))],
            [InlineKeyboardButton("📋 Templates", callback_data="templates")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    async def video_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /video command"""
        text = (
            "🎬 <b>Video Editor</b>\n\n"
            "Send me a video to start editing!\n\n"
            "<b>Supported formats:</b> MP4, AVI, MOV, MKV, WEBM\n"
            "<b>Max size:</b> 500MB\n"
            f"<b>Max length (free):</b> {self.config.FREE_VIDEO_LENGTH} seconds\n"
            f"<b>Max length (premium):</b> 2 hours\n\n"
            "<b>Available Effects:</b>\n"
            "🎞️ Vintage | 🎬 Cinematic | ⚫ B&W | 🟫 Sepia | 💥 Glitch\n"
            "🌀 Blur | ✨ Sharpen | 🪞 Mirror | 🐢 Slow Mo | ⚡ Fast Mo\n\n"
            "<b>⭐ Premium Effects:</b>\n"
            "🔥 Neon | 🎭 Oil Paint | ✏️ Sketch | 🌈 3D\n\n"
            "Send me a video file to get started!"
        )
        
        keyboard = [
            [InlineKeyboardButton("📤 Upload Video", callback_data="upload_video")],
            [InlineKeyboardButton("✨ View All Effects", callback_data="effects_list")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
        return WAITING_FOR_VIDEO
        
    async def image_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /image command"""
        text = (
            "🖼️ <b>Image Editor</b>\n\n"
            "Send me an image to start editing!\n\n"
            "<b>Supported formats:</b> JPG, PNG, GIF, WebP, BMP\n"
            "<b>Max size:</b> 50MB\n\n"
            "<b>Available Filters:</b>\n"
            "Grayscale | Sepia | Invert | Vintage | Cinematic | Glitch\n"
            "Blur | Sharpen | Edge | Emboss | Contour | Smooth\n\n"
            "<b>⭐ Premium Filters:</b>\n"
            "Neon | Sketch | Oil Paint | Watercolor | 3D\n\n"
            "<b>⭐ Premium Tools:</b>\n"
            "• Background Removal\n"
            "• Object Removal\n"
            "• Face Detection\n"
            "• Skin Smoothing\n\n"
            "Send me an image to get started!"
        )
        
        keyboard = [
            [InlineKeyboardButton("📤 Upload Image", callback_data="upload_image")],
            [InlineKeyboardButton("✨ View All Filters", callback_data="filters_list")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
        return WAITING_FOR_IMAGE
        
    async def templates_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /templates command"""
        user = update.effective_user
        user_data = self.db.get_user(user.id)
        is_premium = user_data['is_premium'] if user_data else False
        
        text = (
            "📋 <b>Templates Gallery</b>\n\n"
            "Browse our collection of ready-to-use templates!\n\n"
            "<b>Categories:</b>\n"
            "📱 Social Media | 💼 Business | 🎓 Education\n"
            "🎉 Events | 🎬 Video Thumbnails | 📰 Posters\n\n"
            f"<b>Available templates:</b> 500+ (including {100 if not is_premium else 500}+ premium)\n\n"
            "Click the button below to browse templates in the web app!"
        )
        
        keyboard = [
            [InlineKeyboardButton("📋 Browse Templates", web_app=WebAppInfo(url=f"{self.config.WEBAPP_URL}/templates"))],
            [InlineKeyboardButton("🎨 Create Custom", callback_data="design")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        if not is_premium:
            keyboard.insert(0, [InlineKeyboardButton("⭐ Unlock Premium Templates", callback_data="premium")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    async def premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /premium command"""
        user = update.effective_user
        user_data = self.db.get_user(user.id)
        is_premium = user_data['is_premium'] if user_data else False
        
        if is_premium:
            text = (
                "⭐ <b>Premium Member</b>\n\n"
                f"Thank you for supporting Kinva Master!\n\n"
                f"<b>Premium until:</b> {user_data.get('premium_until', 'Active')}\n\n"
                "<b>Your Benefits:</b>\n"
                "✓ 4K Video Export\n"
                "✓ No Watermark\n"
                "✓ All Filters & Effects\n"
                "✓ Unlimited Exports\n"
                "✓ Priority Support\n"
                "✓ 10GB Cloud Storage\n"
                "✓ API Access\n\n"
                "Need to renew? Contact support for special offers!"
            )
            
            keyboard = [
                [InlineKeyboardButton("📞 Contact Support", callback_data="contact")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ]
        else:
            text = (
                "⭐ <b>Upgrade to Premium</b>\n\n"
                "Get unlimited access to all professional features!\n\n"
                "<b>📊 Plans:</b>\n\n"
                "<b>🎯 Pro Plan - $14.99/month</b>\n"
                "• 4K Video Export\n"
                "• No Watermark\n"
                "• All Filters & Effects\n"
                "• Unlimited Exports\n"
                "• Priority Support\n"
                "• 10GB Storage\n\n"
                "<b>🚀 Business Plan - $29.99/month</b>\n"
                "• Everything in Pro\n"
                "• Team Collaboration\n"
                "• Custom Branding\n"
                "• API Access\n"
                "• Dedicated Support\n"
                "• 100GB Storage\n\n"
                "<b>💎 Lifetime Plan - $299.99</b>\n"
                "• One-time payment\n"
                "• Lifetime access\n"
                "• All future updates\n\n"
                f"Contact @{self.config.ADMIN_CONTACT} to upgrade or click below!"
            )
            
            keyboard = [
                [InlineKeyboardButton("💳 Buy Premium", callback_data="buy_premium")],
                [InlineKeyboardButton("🎁 Free Trial", callback_data="free_trial")],
                [InlineKeyboardButton("📞 Contact Admin", callback_data="contact")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /profile command"""
        user = update.effective_user
        user_data = self.db.get_user(user.id)
        
        if not user_data:
            await update.message.reply_text("❌ User not found. Please use /start")
            return
            
        is_premium = user_data.get('is_premium', False)
        premium_until = user_data.get('premium_until', 'Never')
        exports_today = user_data.get('exports_today', 0)
        exports_limit = user_data.get('exports_limit', 3)
        total_edits = user_data.get('total_edits', 0)
        total_designs = user_data.get('total_designs', 0)
        joined = user_data.get('created_at', datetime.now()).split('T')[0]
        
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
            f"<b>📊 Usage Statistics:</b>\n"
            f"• Exports Today: {exports_today}/{exports_limit}\n"
            f"• Total Edits: {total_edits}\n"
            f"• Designs Created: {total_designs}\n\n"
            f"<b>✨ Features:</b>\n"
            f"• Video Editing: {'✅' if is_premium or exports_today < exports_limit else '⚠️ Limit reached'}\n"
            f"• Image Editing: {'✅' if is_premium or exports_today < exports_limit else '⚠️ Limit reached'}\n"
            f"• Design Editor: ✅ Free\n"
            f"• 4K Export: {'✅ Premium' if not is_premium else '✅'}\n"
            f"• No Watermark: {'✅ Premium' if not is_premium else '✅'}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 Full Statistics", callback_data="stats")],
            [InlineKeyboardButton("🎨 My Designs", callback_data="my_designs")],
            [InlineKeyboardButton("🎬 My Videos", callback_data="my_videos")],
            [InlineKeyboardButton("🖼️ My Images", callback_data="my_images")],
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
        
    async def myworks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /myworks command"""
        user = update.effective_user
        designs = self.db.get_user_designs(user.id, limit=5)
        videos = self.db.get_user_videos(user.id, limit=5)
        images = self.db.get_user_images(user.id, limit=5)
        
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
        
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        user = update.effective_user
        stats = self.db.get_user_stats(user.id)
        
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
        
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        user = update.effective_user
        settings = self.db.get_user_settings(user.id)
        
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
            [InlineKeyboardButton("⚙️ Open Settings", web_app=WebAppInfo(url=f"{self.config.WEBAPP_URL}/settings"))],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    async def feedback_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        return WAITING_FOR_FEEDBACK
        
    async def contact_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /contact command"""
        text = (
            f"📞 <b>Contact Support</b>\n\n"
            f"Need help? Reach out to us through any of these channels:\n\n"
            f"<b>Telegram:</b> @{self.config.ADMIN_CONTACT}\n"
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
            [InlineKeyboardButton("💬 Telegram", url=f"https://t.me/{self.config.ADMIN_CONTACT}")],
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
        
    # ============================================
    # CALLBACK HANDLERS
    # ============================================
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user = update.effective_user
        
        if data == "back":
            await self.start_callback(query, context)
            
        elif data == "video":
            await self.video_menu(query, context)
            
        elif data == "image":
            await self.image_menu(query, context)
            
        elif data == "design":
            await self.design_menu(query, context)
            
        elif data == "templates":
            await self.templates_menu(query, context)
            
        elif data == "premium":
            await self.premium_menu(query, context)
            
        elif data == "profile":
            await self.profile_menu(query, context)
            
        elif data == "stats":
            await self.stats_menu(query, context)
            
        elif data == "help":
            await self.help_menu(query, context)
            
        elif data == "contact":
            await self.contact_menu(query, context)
            
        elif data == "my_designs":
            await self.my_designs(query, context)
            
        elif data == "my_videos":
            await self.my_videos(query, context)
            
        elif data == "my_images":
            await self.my_images(query, context)
            
        elif data == "upload_video":
            await self.upload_video(query, context)
            
        elif data == "upload_image":
            await self.upload_image(query, context)
            
        elif data == "effects_list":
            await self.show_effects(query, context)
            
        elif data == "filters_list":
            await self.show_filters(query, context)
            
        elif data == "buy_premium":
            await self.buy_premium(query, context)
            
        elif data == "free_trial":
            await self.free_trial(query, context)
            
        elif data.startswith("effect_"):
            await self.select_effect(query, context, data[7:])
            
        elif data.startswith("filter_"):
            await self.select_filter(query, context, data[7:])
            
        elif data == "process_video":
            await self.process_video(query, context)
            
        elif data == "process_image":
            await self.process_image(query, context)
            
        elif data == "cancel":
            await self.cancel_operation(query, context)
            
        elif data == "weekly_activity":
            await self.weekly_activity(query, context)
            
        elif data == "monthly_activity":
            await self.monthly_activity(query, context)
            
    async def start_callback(self, query, context):
        """Return to main menu"""
        user = query.from_user
        user_data = self.db.get_user(user.id)
        is_premium = user_data['is_premium'] if user_data else False
        
        text = (
            f"🎬 <b>Kinva Master</b>\n\n"
            f"Hello {user.first_name}! What would you like to do?\n\n"
            f"<b>Status:</b> {'⭐ Premium' if is_premium else '🆓 Free'}\n"
            f"<b>Exports left today:</b> {user_data.get('exports_left', 3) if user_data else 3}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🚀 Open Web App", web_app=WebAppInfo(url=self.config.WEBAPP_URL))],
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
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    async def video_menu(self, query, context):
        """Show video editing menu"""
        text = (
            "🎬 <b>Video Editor</b>\n\n"
            "Send me a video to start editing!\n\n"
            "<b>Supported formats:</b> MP4, AVI, MOV, MKV, WEBM\n"
            "<b>Max size:</b> 500MB\n\n"
            "<b>Available Effects:</b>\n"
            "• Vintage - Old film look\n"
            "• Cinematic - Movie colors\n"
            "• Black & White - Classic\n"
            "• Sepia - Vintage brown\n"
            "• Glitch - Digital distortion\n"
            "• Blur - Gaussian blur\n"
            "• Sharpen - Edge enhancement\n"
            "• Mirror - Reflection\n"
            "• Slow Motion - 0.5x speed\n"
            "• Fast Motion - 2x speed\n\n"
            "⭐ Premium Effects:\n"
            "• Neon - Glow effect\n"
            "• Cartoon - Comic style\n"
            "• 3D - 3D effect\n"
            "• Oil Paint - Artistic\n\n"
            "Send me a video file!"
        )
        
        keyboard = [
            [InlineKeyboardButton("📤 Upload Video", callback_data="upload_video")],
            [InlineKeyboardButton("✨ View All Effects", callback_data="effects_list")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    async def image_menu(self, query, context):
        """Show image editing menu"""
        text = (
            "🖼️ <b>Image Editor</b>\n\n"
            "Send me an image to start editing!\n\n"
            "<b>Supported formats:</b> JPG, PNG, GIF, WebP, BMP\n"
            "<b>Max size:</b> 50MB\n\n"
            "<b>Available Filters:</b>\n"
            "• Grayscale - Black & white\n"
            "• Sepia - Vintage brown\n"
            "• Invert - Negative colors\n"
            "• Vintage - Old photo look\n"
            "• Cinematic - Movie colors\n"
            "• Glitch - Digital glitch\n"
            "• Blur - Soft focus\n"
            "• Sharpen - Crisp details\n"
            "• Edge - Outline effect\n\n"
            "⭐ Premium Filters:\n"
            "• Neon - Glow effect\n"
            "• Sketch - Drawing look\n"
            "• Oil Paint - Artistic\n"
            "• Watercolor - Painting\n\n"
            "⭐ Premium Tools:\n"
            "• Background Removal\n"
            "• Object Removal\n"
            "• Face Detection\n\n"
            "Send me an image!"
        )
        
        keyboard = [
            [InlineKeyboardButton("📤 Upload Image", callback_data="upload_image")],
            [InlineKeyboardButton("✨ View All Filters", callback_data="filters_list")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    async def design_menu(self, query, context):
        """Show design menu"""
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
            "<b>Popular Templates:</b>\n"
            "• YouTube Thumbnails\n"
            "• Instagram Stories\n"
            "• Facebook Posts\n"
            "• Business Cards\n"
            "• Flyers & Posters\n"
            "• Presentations\n\n"
            "Click the button below to start creating!"
        )
        
        keyboard = [
            [InlineKeyboardButton("🚀 Open Editor", web_app=WebAppInfo(url=f"{self.config.WEBAPP_URL}/editor"))],
            [InlineKeyboardButton("📋 Templates", callback_data="templates")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    async def templates_menu(self, query, context):
        """Show templates menu"""
        user = query.from_user
        user_data = self.db.get_user(user.id)
        is_premium = user_data['is_premium'] if user_data else False
        
        text = (
            "📋 <b>Templates Gallery</b>\n\n"
            "Browse our collection of ready-to-use templates!\n\n"
            "<b>Categories:</b>\n"
            "📱 Social Media - Instagram, Facebook, Twitter\n"
            "💼 Business - Presentations, Reports, Proposals\n"
            "🎓 Education - Lessons, Worksheets, Posters\n"
            "🎉 Events - Weddings, Parties, Invitations\n"
            "🎬 Video - Thumbnails, Intros, Outros\n"
            "📰 Marketing - Flyers, Brochures, Ads\n\n"
            f"<b>Available:</b> 500+ templates"
        )
        
        if not is_premium:
            text += "\n\n⭐ <b>100+ premium templates available with subscription!</b>"
        
        keyboard = [
            [InlineKeyboardButton("📋 Browse All", web_app=WebAppInfo(url=f"{self.config.WEBAPP_URL}/templates"))],
            [InlineKeyboardButton("🎨 Create Custom", callback_data="design")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        if not is_premium:
            keyboard.insert(0, [InlineKeyboardButton("⭐ Unlock Premium Templates", callback_data="premium")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    async def premium_menu(self, query, context):
        """Show premium menu"""
        user = query.from_user
        user_data = self.db.get_user(user.id)
        is_premium = user_data['is_premium'] if user_data else False
        
        if is_premium:
            text = (
                "⭐ <b>Premium Member</b>\n\n"
                f"Thank you for supporting Kinva Master!\n\n"
                f"<b>Premium until:</b> {user_data.get('premium_until', 'Active')}\n\n"
                "<b>Your Benefits:</b>\n"
                "✓ 4K Video Export\n"
                "✓ No Watermark\n"
                "✓ All Filters & Effects\n"
                "✓ Unlimited Exports\n"
                "✓ Priority Support\n"
                "✓ 10GB Cloud Storage\n"
                "✓ API Access\n\n"
                "Need help? Contact support for assistance!"
            )
            
            keyboard = [
                [InlineKeyboardButton("📞 Contact Support", callback_data="contact")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ]
        else:
            text = (
                "⭐ <b>Upgrade to Premium</b>\n\n"
                "Get unlimited access to all professional features!\n\n"
                "<b>📊 Pro Plan - $14.99/month</b>\n"
                "✓ 4K Video Export\n"
                "✓ No Watermark\n"
                "✓ All Filters & Effects\n"
                "✓ Unlimited Exports\n"
                "✓ Priority Support\n"
                "✓ 10GB Storage\n\n"
                "<b>🚀 Business Plan - $29.99/month</b>\n"
                "✓ Everything in Pro\n"
                "✓ Team Collaboration\n"
                "✓ Custom Branding\n"
                "✓ API Access\n"
                "✓ Dedicated Support\n"
                "✓ 100GB Storage\n\n"
                "<b>💎 Lifetime Plan - $299.99</b>\n"
                "✓ One-time payment\n"
                "✓ Lifetime access\n"
                "✓ All future updates\n\n"
                f"<b>💰 Special Offer:</b> First month 50% off!\n\n"
                f"Click below to upgrade or contact @{self.config.ADMIN_CONTACT}"
            )
            
            keyboard = [
                [InlineKeyboardButton("💳 Buy Premium", callback_data="buy_premium")],
                [InlineKeyboardButton("🎁 Free Trial (7 days)", callback_data="free_trial")],
                [InlineKeyboardButton("📞 Contact Admin", callback_data="contact")],
                [InlineKeyboardButton("🔙 Back", callback_data="back")]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    async def profile_menu(self, query, context):
        """Show profile menu"""
        user = query.from_user
        user_data = self.db.get_user(user.id)
        
        if not user_data:
            await query.edit_message_text("❌ User not found. Please use /start")
            return
            
        is_premium = user_data.get('is_premium', False)
        premium_until = user_data.get('premium_until', 'Never')
        exports_today = user_data.get('exports_today', 0)
        exports_limit = user_data.get('exports_limit', 3)
        total_edits = user_data.get('total_edits', 0)
        total_designs = user_data.get('total_designs', 0)
        joined = user_data.get('created_at', datetime.now()).split('T')[0]
        
        text = (
            f"👤 <b>User Profile</b>\n\n"
            f"<b>Name:</b> {user.first_name} {user.last_name or ''}\n"
            f"<b>Username:</b> @{user.username or 'None'}\n"
            f"<b>User ID:</b> <code>{user.id}</code>\n"
            f"<b>Joined:</b> {joined}\n\n"
            f"<b>💰 Status:</b> {'⭐ Premium' if is_premium else '🆓 Free'}\n"
        )
        
        if is_premium:
            text += f"<b>Valid until:</b> {premium_until}\n\n"
        
        text += (
            f"<b>📊 Today's Usage:</b>\n"
            f"• Exports: {exports_today}/{exports_limit}\n"
            f"• Videos: {user_data.get('videos_today', 0)}\n"
            f"• Images: {user_data.get('images_today', 0)}\n"
            f"• Designs: {user_data.get('designs_today', 0)}\n\n"
            f"<b>📈 Lifetime:</b>\n"
            f"• Total Edits: {total_edits}\n"
            f"• Designs Created: {total_designs}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 Full Statistics", callback_data="stats")],
            [InlineKeyboardButton("🎨 My Designs", callback_data="my_designs")],
            [InlineKeyboardButton("🎬 My Videos", callback_data="my_videos")],
            [InlineKeyboardButton("🖼️ My Images", callback_data="my_images")],
        ]
        
        if not is_premium:
            keyboard.insert(0, [InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="premium")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        
    async def help_menu(self, query, context):
        """Show help menu"""
        text = (
            "❓ <b>Help & Support</b>\n\n"
            "<b>📱 Commands:</b>\n"
            "/start - Restart the bot\n"
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
            "<b>⭐ Premium Features:</b>\n"
            "• 4K video export\n"
            "• No watermark\n"
            "• All filters & effects\n"
            "• Unlimited exports\n"
            "• Priority support\n"
            "• Cloud storage\n\n"
            f"<b>📞 Need more help?</b> Contact @{self.config.ADMIN_CONTACT}\n\n"
            f"<b>📚 Video Tutorial:</b> https://kinva-master.com/tutorial"
        )
        
        keyboard = [
            [InlineKeyboardButton("📚 Video Tutorial", url="https://kinva-master.com/tutorial")],
            [InlineKeyboardButton("📞 Contact Support", callback_data="contact")],
            [InlineKeyboardButton("❓ FAQ", url="https://kinva-master.com/faq")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        
    # ============================================
    # FILE HANDLERS
    # ============================================
    
    async def handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video file upload"""
        user = update.effective_user
        video = update.message.video or update.message.document
        
        if not video:
            await update.message.reply_text("❌ Please send a valid video file.")
            return WAITING_FOR_VIDEO
            
        # Check file size
        if video.file_size > self.config.MAX_VIDEO_SIZE:
            await update.message.reply_text(
                f"❌ File too large. Max size: {self.config.MAX_VIDEO_SIZE // (1024*1024)}MB"
            )
            return WAITING_FOR_VIDEO
            
        # Check premium status
        user_data = self.db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        # Download video
        progress_msg = await update.message.reply_text("📥 Downloading video...")
        
        file = await context.bot.get_file(video.file_id)
        input_path = f"/tmp/video_{user.id}_{int(time.time())}.mp4"
        await file.download_to_drive(input_path)
        
        # Get video duration
        import cv2
        cap = cv2.VideoCapture(input_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        cap.release()
        
        # Check duration for free users
        if not is_premium and duration > self.config.FREE_VIDEO_LENGTH:
            os.remove(input_path)
            await progress_msg.edit_text(
                f"❌ Free users can only edit videos up to {self.config.FREE_VIDEO_LENGTH} seconds.\n"
                f"Your video is {int(duration)} seconds long.\n\n"
                f"Upgrade to premium to edit longer videos!\n"
                f"Use /premium to see plans."
            )
            return WAITING_FOR_VIDEO
            
        # Store in context
        context.user_data['video_path'] = input_path
        context.user_data['video_duration'] = duration
        
        await progress_msg.edit_text(
            f"✅ Video downloaded!\n\n"
            f"<b>Duration:</b> {int(duration)} seconds\n"
            f"<b>Size:</b> {video.file_size // (1024*1024)} MB\n\n"
            f"Now select effects to apply:",
            parse_mode=ParseMode.HTML
        )
        
        # Show effects selection
        keyboard = []
        effects = [
            ('vintage', '🎞️ Vintage'),
            ('cinematic', '🎬 Cinematic'),
            ('black_white', '⚫ B&W'),
            ('sepia', '🟫 Sepia'),
            ('glitch', '💥 Glitch'),
            ('blur', '🌀 Blur'),
            ('sharpen', '✨ Sharpen'),
            ('mirror', '🪞 Mirror'),
            ('slow_motion', '🐢 Slow Mo'),
            ('fast_motion', '⚡ Fast Mo'),
        ]
        
        # Add premium effects for premium users
        if is_premium:
            effects.extend([
                ('neon', '🔥 Neon'),
                ('cartoon', '🎨 Cartoon'),
                ('3d', '🎥 3D'),
                ('oil_paint', '🎭 Oil Paint'),
            ])
        
        # Create buttons in rows of 3
        for i in range(0, len(effects), 3):
            row = []
            for effect in effects[i:i+3]:
                row.append(InlineKeyboardButton(effect[1], callback_data=f"effect_{effect[0]}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("✅ Process Video", callback_data="process_video")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "✨ Select effects to apply (you can select multiple):",
            reply_markup=reply_markup
        )
        
        return WAITING_FOR_EFFECTS
        
    async def handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle image file upload"""
        user = update.effective_user
        photo = update.message.photo[-1] if update.message.photo else None
        document = update.message.document
        
        if photo:
            file_id = photo.file_id
        elif document:
            file_id = document.file_id
        else:
            await update.message.reply_text("❌ Please send a valid image file.")
            return WAITING_FOR_IMAGE
            
        # Download image
        progress_msg = await update.message.reply_text("📥 Downloading image...")
        
        file = await context.bot.get_file(file_id)
        input_path = f"/tmp/image_{user.id}_{int(time.time())}.jpg"
        await file.download_to_drive(input_path)
        
        # Get image info
        from PIL import Image
        img = Image.open(input_path)
        
        await progress_msg.edit_text(
            f"✅ Image downloaded!\n\n"
            f"<b>Size:</b> {img.width}x{img.height}\n"
            f"<b>Format:</b> {img.format}\n\n"
            f"Now select filters to apply:",
            parse_mode=ParseMode.HTML
        )
        
        # Check premium status
        user_data = self.db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        # Store in context
        context.user_data['image_path'] = input_path
        
        # Show filters selection
        keyboard = []
        filters = [
            ('grayscale', '⚫ Grayscale'),
            ('sepia', '🟫 Sepia'),
            ('invert', '🔄 Invert'),
            ('vintage', '🎞️ Vintage'),
            ('cinematic', '🎬 Cinematic'),
            ('glitch', '💥 Glitch'),
            ('blur', '🌀 Blur'),
            ('sharpen', '✨ Sharpen'),
            ('edge', '✏️ Edge'),
            ('emboss', '⛰️ Emboss'),
        ]
        
        # Add premium filters for premium users
        if is_premium:
            filters.extend([
                ('neon', '🔥 Neon'),
                ('sketch', '✏️ Sketch'),
                ('oil_paint', '🎭 Oil Paint'),
                ('watercolor', '🎨 Watercolor'),
            ])
        
        # Create buttons in rows of 3
        for i in range(0, len(filters), 3):
            row = []
            for filter_item in filters[i:i+3]:
                row.append(InlineKeyboardButton(filter_item[1], callback_data=f"filter_{filter_item[0]}"))
            keyboard.append(row)
        
        # Add premium tools
        if is_premium:
            keyboard.append([
                InlineKeyboardButton("🖼️ Remove Background", callback_data="remove_bg"),
                InlineKeyboardButton("🧹 Remove Object", callback_data="remove_object"),
            ])
        
        keyboard.append([InlineKeyboardButton("✅ Process Image", callback_data="process_image")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "✨ Select filters to apply (you can select multiple):",
            reply_markup=reply_markup
        )
        
        return WAITING_FOR_FILTERS
        
    async def select_effect(self, query, context, effect):
        """Handle effect selection"""
        if 'selected_effects' not in context.user_data:
            context.user_data['selected_effects'] = []
            
        if effect in context.user_data['selected_effects']:
            context.user_data['selected_effects'].remove(effect)
            await query.answer(f"❌ Removed {effect}")
        else:
            context.user_data['selected_effects'].append(effect)
            await query.answer(f"✅ Added {effect}")
            
        selected = context.user_data['selected_effects']
        
        # Update message
        text = f"✨ <b>Selected Effects:</b> {', '.join(selected) if selected else 'None'}\n\n"
        text += "Select more effects or click Process when ready."
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=query.message.reply_markup
        )
        
    async def select_filter(self, query, context, filter_name):
        """Handle filter selection"""
        if 'selected_filters' not in context.user_data:
            context.user_data['selected_filters'] = []
            
        if filter_name in context.user_data['selected_filters']:
            context.user_data['selected_filters'].remove(filter_name)
            await query.answer(f"❌ Removed {filter_name}")
        else:
            context.user_data['selected_filters'].append(filter_name)
            await query.answer(f"✅ Added {filter_name}")
            
        selected = context.user_data['selected_filters']
        
        # Update message
        text = f"✨ <b>Selected Filters:</b> {', '.join(selected) if selected else 'None'}\n\n"
        text += "Select more filters or click Process when ready."
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=query.message.reply_markup
        )
        
    async def process_video(self, query, context):
        """Process video with selected effects"""
        await query.answer()
        
        user = query.from_user
        video_path = context.user_data.get('video_path')
        effects = context.user_data.get('selected_effects', [])
        
        if not video_path:
            await query.edit_message_text("❌ No video found. Please upload again.")
            return ConversationHandler.END
            
        # Check premium status
        user_data = self.db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        # Update message
        await query.edit_message_text(
            "⏳ <b>Processing your video...</b>\n\n"
            "This may take a few moments depending on video length.\n"
            "Please wait...",
            parse_mode=ParseMode.HTML
        )
        
        try:
            # Process video
            output_path = self.video_processor.process(
                video_path,
                effects=effects,
                quality='1080p' if is_premium else '720p'
            )
            
            # Add watermark for free users
            if not is_premium:
                output_path = self.watermark.add_video_watermark(output_path)
                
            # Send video
            await context.bot.send_chat_action(chat_id=user.id, action=ChatAction.UPLOAD_VIDEO)
            
            with open(output_path, 'rb') as video_file:
                caption = (
                    f"✅ <b>Video processed successfully!</b>\n\n"
                    f"<b>Effects applied:</b> {', '.join(effects) if effects else 'None'}\n"
                    f"<b>Quality:</b> {'1080p' if is_premium else '720p'}\n"
                    f"<b>Size:</b> {os.path.getsize(output_path) // (1024*1024)} MB\n\n"
                )
                
                if not is_premium:
                    caption += f"💧 <i>Watermark: @kinva_master.com</i>\n"
                    caption += f"⭐ Upgrade to premium to remove watermark!\n\n"
                
                caption += f"<b>Need more edits?</b> Use /video again!"
                
                await context.bot.send_video(
                    chat_id=user.id,
                    video=video_file,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    supports_streaming=True
                )
                
            # Update stats
            self.db.increment_exports(user.id)
            self.db.increment_videos_edited(user.id)
            
            # Save to history
            self.db.save_video_history(
                user_id=user.id,
                file_path=output_path,
                effects=effects,
                size=os.path.getsize(output_path)
            )
            
        except Exception as e:
            logger.error(f"Video processing error: {e}")
            await query.edit_message_text(
                f"❌ <b>Error processing video</b>\n\n"
                f"{str(e)}\n\n"
                f"Please try again or contact support.",
                parse_mode=ParseMode.HTML
            )
            
        finally:
            # Cleanup
            if os.path.exists(video_path):
                os.remove(video_path)
            if 'output_path' in locals() and os.path.exists(output_path):
                os.remove(output_path)
                
            # Clear context
            context.user_data.clear()
                
        return ConversationHandler.END
        
    async def process_image(self, query, context):
        """Process image with selected filters"""
        await query.answer()
        
        user = query.from_user
        image_path = context.user_data.get('image_path')
        filters = context.user_data.get('selected_filters', [])
        
        if not image_path:
            await query.edit_message_text("❌ No image found. Please upload again.")
            return ConversationHandler.END
            
        # Check premium status
        user_data = self.db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        # Update message
        await query.edit_message_text(
            "⏳ <b>Processing your image...</b>\n\n"
            "Applying filters...",
            parse_mode=ParseMode.HTML
        )
        
        try:
            # Process image
            output_path = self.image_processor.process(image_path, filters=filters)
            
            # Add watermark for free users
            if not is_premium:
                output_path = self.watermark.add_image_watermark(output_path)
                
            # Send image
            await context.bot.send_chat_action(chat_id=user.id, action=ChatAction.UPLOAD_PHOTO)
            
            with open(output_path, 'rb') as image_file:
                caption = (
                    f"✅ <b>Image processed successfully!</b>\n\n"
                    f"<b>Filters applied:</b> {', '.join(filters) if filters else 'None'}\n"
                    f"<b>Size:</b> {os.path.getsize(output_path) // 1024} KB\n\n"
                )
                
                if not is_premium:
                    caption += f"💧 <i>Watermark: @kinva_master.com</i>\n"
                    caption += f"⭐ Upgrade to premium to remove watermark!\n\n"
                
                caption += f"<b>Need more edits?</b> Use /image again!"
                
                await context.bot.send_photo(
                    chat_id=user.id,
                    photo=image_file,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
                
            # Update stats
            self.db.increment_exports(user.id)
            self.db.increment_images_edited(user.id)
            
            # Save to history
            self.db.save_image_history(
                user_id=user.id,
                file_path=output_path,
                filters=filters,
                size=os.path.getsize(output_path)
            )
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            await query.edit_message_text(
                f"❌ <b>Error processing image</b>\n\n"
                f"{str(e)}\n\n"
                f"Please try again or contact support.",
                parse_mode=ParseMode.HTML
            )
            
        finally:
            # Cleanup
            if os.path.exists(image_path):
                os.remove(image_path)
            if 'output_path' in locals() and os.path.exists(output_path):
                os.remove(output_path)
                
            # Clear context
            context.user_data.clear()
                
        return ConversationHandler.END
        
    async def cancel_operation(self, query, context):
        """Cancel current operation"""
        await query.answer()
        
        # Cleanup files
        if 'video_path' in context.user_data and os.path.exists(context.user_data['video_path']):
            os.remove(context.user_data['video_path'])
        if 'image_path' in context.user_data and os.path.exists(context.user_data['image_path']):
            os.remove(context.user_data['image_path'])
            
        context.user_data.clear()
        
        await query.edit_message_text(
            "❌ Operation cancelled.\n\n"
            "Use /start to return to main menu."
        )
        
        return ConversationHandler.END
        
    # ============================================
    # PREMIUM HANDLERS
    # ============================================
    
    async def buy_premium(self, query, context):
        """Handle buy premium button"""
        user = query.from_user
        
        # Create payment link
        payment_url = self.stripe_handler.create_checkout_session(
            user_id=user.id,
            amount=1499,  # $14.99
            currency='usd',
            success_url=f"{self.config.WEBAPP_URL}/payment/success",
            cancel_url=f"{self.config.WEBAPP_URL}/payment/cancel"
        )
        
        text = (
            "💳 <b>Upgrade to Premium</b>\n\n"
            "<b>Pro Plan - $14.99/month</b>\n\n"
            "You'll get:\n"
            "✓ 4K Video Export\n"
            "✓ No Watermark\n"
            "✓ All Filters & Effects\n"
            "✓ Unlimited Exports\n"
            "✓ Priority Support\n"
            "✓ 10GB Cloud Storage\n\n"
            "Click the button below to complete payment."
        )
        
        keyboard = [
            [InlineKeyboardButton("💳 Pay with Stripe", url=payment_url)],
            [InlineKeyboardButton("📞 Contact for Crypto Payment", callback_data="contact")],
            [InlineKeyboardButton("🔙 Back", callback_data="premium")]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    async def free_trial(self, query, context):
        """Handle free trial request"""
        user = query.from_user
        user_data = self.db.get_user(user.id)
        
        if user_data.get('trial_used', False):
            await query.answer("You've already used your free trial!")
            return
            
        # Activate 7-day trial
        self.db.activate_premium(
            user_id=user.id,
            months=0,
            trial_days=7
        )
        
        await query.edit_message_text(
            "🎉 <b>Free Trial Activated!</b>\n\n"
            "You now have 7 days of premium access!\n\n"
            "<b>Enjoy these features:</b>\n"
            "✓ 4K Video Export\n"
            "✓ No Watermark\n"
            "✓ All Filters & Effects\n"
            "✓ Unlimited Exports\n"
            "✓ Priority Support\n\n"
            "Your trial will expire in 7 days.\n"
            "Upgrade to keep premium benefits!",
            parse_mode=ParseMode.HTML
        )
        
    # ============================================
    # MY WORKS HANDLERS
    # ============================================
    
    async def my_designs(self, query, context):
        """Show user's designs"""
        user = query.from_user
        designs = self.db.get_user_designs(user.id, limit=10)
        
        if not designs:
            text = "📁 <b>My Designs</b>\n\nYou haven't created any designs yet.\n\nUse /editor to create your first design!"
        else:
            text = "📁 <b>My Designs</b>\n\n"
            for design in designs[:10]:
                text += f"🎨 <b>{design['title']}</b>\n"
                text += f"   📅 {design['created_at'][:10]}\n"
                text += f"   🔗 <a href='{design['share_url']}'>View</a>\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🎨 Create New", callback_data="design")],
            [InlineKeyboardButton("🔙 Back", callback_data="profile")]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
        
    async def my_videos(self, query, context):
        """Show user's videos"""
        user = query.from_user
        videos = self.db.get_user_videos(user.id, limit=10)
        
        if not videos:
            text = "🎬 <b>My Videos</b>\n\nYou haven't edited any videos yet.\n\nUse /video to edit your first video!"
        else:
            text = "🎬 <b>My Videos</b>\n\n"
            for video in videos[:10]:
                text += f"🎥 <b>{video['title']}</b>\n"
                text += f"   📅 {video['created_at'][:10]}\n"
                text += f"   🎨 Effects: {video['effects'][:50]}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🎬 Edit New", callback_data="video")],
            [InlineKeyboardButton("🔙 Back", callback_data="profile")]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    async def my_images(self, query, context):
        """Show user's images"""
        user = query.from_user
        images = self.db.get_user_images(user.id, limit=10)
        
        if not images:
            text = "🖼️ <b>My Images</b>\n\nYou haven't edited any images yet.\n\nUse /image to edit your first image!"
        else:
            text = "🖼️ <b>My Images</b>\n\n"
            for image in images[:10]:
                text += f"📸 <b>{image['title']}</b>\n"
                text += f"   📅 {image['created_at'][:10]}\n"
                text += f"   🎨 Filters: {image['filters'][:50]}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("🖼️ Edit New", callback_data="image")],
            [InlineKeyboardButton("🔙 Back", callback_data="profile")]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    # ============================================
    # STATISTICS HANDLERS
    # ============================================
    
    async def weekly_activity(self, query, context):
        """Show weekly activity chart"""
        user = query.from_user
        stats = self.db.get_weekly_stats(user.id)
        
        text = "📈 <b>Weekly Activity</b>\n\n"
        
        for day in stats:
            text += f"<b>{day['day']}:</b> "
            bar = "█" * (day['count'] // 5)
            text += f"{bar} {day['count']}\n"
        
        keyboard = [
            [InlineKeyboardButton("📊 Monthly", callback_data="monthly_activity")],
            [InlineKeyboardButton("🔙 Back", callback_data="stats")]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    async def monthly_activity(self, query, context):
        """Show monthly activity chart"""
        user = query.from_user
        stats = self.db.get_monthly_stats(user.id)
        
        text = "📈 <b>Monthly Activity</b>\n\n"
        
        for month in stats:
            text += f"<b>{month['month']}:</b> "
            bar = "█" * (month['count'] // 20)
            text += f"{bar} {month['count']}\n"
        
        keyboard = [
            [InlineKeyboardButton("📊 Weekly", callback_data="weekly_activity")],
            [InlineKeyboardButton("🔙 Back", callback_data="stats")]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    # ============================================
    # ERROR HANDLER
    # ============================================
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        # Send error message to user
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "❌ <b>Something went wrong!</b>\n\n"
                    "Please try again later.\n\n"
                    f"If the problem persists, contact @{self.config.ADMIN_CONTACT}",
                    parse_mode=ParseMode.HTML
                )
        except:
            pass
            
        # Send error to admin
        try:
            for admin_id in self.config.ADMIN_IDS:
                await self.application.bot.send_message(
                    chat_id=admin_id,
                    text=f"⚠️ <b>Bot Error</b>\n\n{str(context.error)[:500]}",
                    parse_mode=ParseMode.HTML
                )
        except:
            pass
            
    # ============================================
    # MAIN
    # ============================================
    
    def run(self):
        """Run the bot"""
        # Create application with persistence
        persistence = PicklePersistence(filepath='bot_data.pickle')
        
        self.application = Application.builder() \
            .token(self.config.BOT_TOKEN) \
            .persistence(persistence) \
            .build()
            
        # Add handlers
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("editor", self.editor_command))
        self.application.add_handler(CommandHandler("video", self.video_command))
        self.application.add_handler(CommandHandler("image", self.image_command))
        self.application.add_handler(CommandHandler("templates", self.templates_command))
        self.application.add_handler(CommandHandler("premium", self.premium_command))
        self.application.add_handler(CommandHandler("profile", self.profile_command))
        self.application.add_handler(CommandHandler("myworks", self.myworks_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("settings", self.settings_command))
        self.application.add_handler(CommandHandler("feedback", self.feedback_command))
        self.application.add_handler(CommandHandler("contact", self.contact_command))
        
        # Conversation handlers
        video_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.upload_video, pattern="upload_video")],
            states={
                WAITING_FOR_VIDEO: [MessageHandler(filters.VIDEO | filters.Document.VIDEO, self.handle_video)],
                WAITING_FOR_EFFECTS: [CallbackQueryHandler(self.select_effect, pattern="effect_"),
                                     CallbackQueryHandler(self.process_video, pattern="process_video"),
                                     CallbackQueryHandler(self.cancel_operation, pattern="cancel")]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_operation)]
        )
        
        image_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.upload_image, pattern="upload_image")],
            states={
                WAITING_FOR_IMAGE: [MessageHandler(filters.PHOTO | filters.Document.IMAGE, self.handle_image)],
                WAITING_FOR_FILTERS: [CallbackQueryHandler(self.select_filter, pattern="filter_"),
                                     CallbackQueryHandler(self.process_image, pattern="process_image"),
                                     CallbackQueryHandler(self.cancel_operation, pattern="cancel")]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_operation)]
        )
        
        # Add conversation handlers
        self.application.add_handler(video_conv)
        self.application.add_handler(image_conv)
        
        # Callback handlers
        self.application.add_handler(CallbackQueryHandler(self.button_callback, pattern="^(back|video|image|design|templates|premium|profile|stats|help|contact|my_designs|my_videos|my_images|upload_video|upload_image|effects_list|filters_list|buy_premium|free_trial|process_video|process_image|cancel|weekly_activity|monthly_activity)$"))
        self.application.add_handler(CallbackQueryHandler(self.select_effect, pattern="^effect_"))
        self.application.add_handler(CallbackQueryHandler(self.select_filter, pattern="^filter_"))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
        
        # Set bot commands
        self.application.job_queue.run_once(self.setup_commands, 1)
        
        # Start bot
        logger.info("Starting Kinva Master Bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        
# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == '__main__':
    bot = KinvaBot()
    bot.run()
