"""
Error Handler - Handles all bot errors and exceptions
Author: @kinva_master
"""

import logging
import traceback
import sys
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from ..config import Config
from ..database import db
from ..utils import format_file_size

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Handler for all bot errors and exceptions"""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main error handler - logs and sends error reports"""
        
        # Get error details
        error = context.error
        error_type = type(error).__name__
        error_message = str(error)
        error_traceback = traceback.format_exc()
        
        # Log error
        logger.error(f"Error in update {update}: {error}")
        logger.error(error_traceback)
        
        # Get user info if available
        user = None
        user_id = None
        username = None
        if update and update.effective_user:
            user = update.effective_user
            user_id = user.id
            username = user.username
        
        # Save error to database
        try:
            db.log_error(
                error_type=error_type,
                error_message=error_message,
                stack_trace=error_traceback[:5000],  # Limit length
                user_id=user_id,
                context={
                    'update': str(update)[:1000] if update else None,
                    'chat_id': update.effective_chat.id if update and update.effective_chat else None,
                    'message_text': update.effective_message.text if update and update.effective_message else None
                }
            )
        except Exception as e:
            logger.error(f"Failed to log error to database: {e}")
        
        # Send error message to user
        await ErrorHandler.send_error_message(update, context, error)
        
        # Send error report to admins
        await ErrorHandler.send_error_report(update, context, error, error_traceback, user)
        
        # Handle specific error types
        await ErrorHandler.handle_specific_errors(update, context, error)
    
    @staticmethod
    async def send_error_message(update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception):
        """Send user-friendly error message"""
        try:
            error_message = str(error).lower()
            
            # User-friendly error messages
            if "blocked" in error_message:
                text = (
                    "⚠️ <b>Unable to send message</b>\n\n"
                    "It seems you have blocked the bot. Please unblock to continue using features.\n\n"
                    "To unblock:\n"
                    "1. Open Telegram settings\n"
                    "2. Go to Privacy & Security → Blocked Users\n"
                    "3. Find and unblock this bot\n\n"
                    "Then restart the bot with /start"
                )
            elif "chat not found" in error_message:
                text = (
                    "⚠️ <b>Chat not found</b>\n\n"
                    "Please start a chat with the bot first.\n\n"
                    "Click /start to begin."
                )
            elif "timeout" in error_message:
                text = (
                    "⏰ <b>Request timeout</b>\n\n"
                    "The request took too long to process. Please try again.\n\n"
                    "If this persists, please contact support."
                )
            elif "rate limit" in error_message or "too many requests" in error_message:
                text = (
                    "🚦 <b>Rate limit exceeded</b>\n\n"
                    "You're sending too many requests. Please wait a moment and try again.\n\n"
                    "Rate limits help ensure fair usage for all users."
                )
            elif "file too large" in error_message or "file is too big" in error_message:
                text = (
                    "📁 <b>File too large</b>\n\n"
                    f"Maximum file size is {format_file_size(Config.MAX_FILE_SIZE)}.\n\n"
                    "Please compress your file and try again."
                )
            elif "video" in error_message and "format" in error_message:
                text = (
                    "🎬 <b>Unsupported video format</b>\n\n"
                    f"Supported formats: {', '.join(Config.ALLOWED_VIDEOS)}\n\n"
                    "Please convert your video and try again."
                )
            elif "image" in error_message and "format" in error_message:
                text = (
                    "🖼️ <b>Unsupported image format</b>\n\n"
                    f"Supported formats: {', '.join(Config.ALLOWED_IMAGES)}\n\n"
                    "Please convert your image and try again."
                )
            elif "premium" in error_message:
                text = (
                    "⭐ <b>Premium feature</b>\n\n"
                    "This feature requires a premium subscription.\n\n"
                    f"Upgrade to premium to unlock all features!\n"
                    f"Use /premium to see plans."
                )
            elif "limit" in error_message and "export" in error_message:
                text = (
                    "📊 <b>Daily limit reached</b>\n\n"
                    "You've reached your daily export limit.\n\n"
                    "Upgrade to premium for unlimited exports!\n"
                    f"Use /premium to see plans."
                )
            else:
                text = (
                    "❌ <b>Something went wrong</b>\n\n"
                    "An unexpected error occurred. Please try again.\n\n"
                    f"<b>Error:</b> {str(error)[:200]}\n\n"
                    f"If the problem persists, please contact @{Config.ADMIN_CONTACT}"
                )
            
            # Try to send error message
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
            elif update and update.callback_query:
                await update.callback_query.answer(
                    "An error occurred. Please try again.",
                    show_alert=True
                )
                
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    @staticmethod
    async def send_error_report(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                error: Exception, traceback_str: str, user):
        """Send detailed error report to admins"""
        try:
            # Prepare error report
            error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            error_type = type(error).__name__
            error_message = str(error)
            
            report = (
                f"🔥 <b>ERROR REPORT</b>\n\n"
                f"<b>Time:</b> {error_time}\n"
                f"<b>Type:</b> <code>{error_type}</code>\n"
                f"<b>Message:</b> {error_message[:500]}\n\n"
                f"<b>User:</b> {user.full_name if user else 'Unknown'}\n"
                f"<b>User ID:</b> <code>{user.id if user else 'Unknown'}</code>\n"
                f"<b>Username:</b> @{user.username if user else 'Unknown'}\n\n"
            )
            
            # Add update info
            if update:
                if update.effective_chat:
                    report += f"<b>Chat ID:</b> <code>{update.effective_chat.id}</code>\n"
                if update.effective_message:
                    report += f"<b>Message:</b> {update.effective_message.text[:200] if update.effective_message.text else 'No text'}\n"
                if update.callback_query:
                    report += f"<b>Callback:</b> {update.callback_query.data}\n"
            
            report += f"\n<b>Traceback:</b>\n<pre>{traceback_str[:1500]}</pre>"
            
            # Split long messages
            if len(report) > 4000:
                report = report[:4000] + "\n\n... (truncated)"
            
            # Send to all admins
            for admin_id in Config.ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=report,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                except Exception as e:
                    logger.error(f"Failed to send error report to admin {admin_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to send error report: {e}")
    
    @staticmethod
    async def handle_specific_errors(update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception):
        """Handle specific error types with custom responses"""
        error_message = str(error).lower()
        
        # Conversation timeout
        if "conversation" in error_message and "timeout" in error_message:
            context.user_data.clear()
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "⏰ <b>Session timed out</b>\n\n"
                    "Your session has expired. Please start over.\n\n"
                    "Use /start to begin again.",
                    parse_mode=ParseMode.HTML
                )
        
        # File not found
        elif "no file" in error_message or "file not found" in error_message:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "📁 <b>File not found</b>\n\n"
                    "The file you were trying to process is no longer available.\n\n"
                    "Please upload the file again.",
                    parse_mode=ParseMode.HTML
                )
        
        # Permission denied
        elif "permission" in error_message or "unauthorized" in error_message:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "🔒 <b>Permission denied</b>\n\n"
                    "You don't have permission to perform this action.\n\n"
                    "If you think this is an error, please contact support.",
                    parse_mode=ParseMode.HTML
                )
        
        # Network error
        elif "network" in error_message or "connection" in error_message:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "🌐 <b>Network error</b>\n\n"
                    "Unable to connect to the server. Please check your internet connection and try again.\n\n"
                    "If the problem persists, please try again later.",
                    parse_mode=ParseMode.HTML
                )
        
        # Database error
        elif "database" in error_message or "sql" in error_message:
            logger.critical(f"Database error: {error}")
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "🗄️ <b>Database error</b>\n\n"
                    "A database error occurred. Our team has been notified.\n\n"
                    "Please try again later.",
                    parse_mode=ParseMode.HTML
                )
        
        # Video processing error
        elif "video" in error_message and ("process" in error_message or "ffmpeg" in error_message):
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "🎬 <b>Video processing error</b>\n\n"
                    "Failed to process the video. This could be due to:\n"
                    "• Corrupted video file\n"
                    "• Unsupported codec\n"
                    "• File too large\n\n"
                    "Please try with a different video file.",
                    parse_mode=ParseMode.HTML
                )
        
        # Image processing error
        elif "image" in error_message and ("process" in error_message or "pil" in error_message):
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "🖼️ <b>Image processing error</b>\n\n"
                    "Failed to process the image. This could be due to:\n"
                    "• Corrupted image file\n"
                    "• Unsupported format\n"
                    "• File too large\n\n"
                    "Please try with a different image file.",
                    parse_mode=ParseMode.HTML
                )
    
    @staticmethod
    async def log_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception):
        """Log error with full details"""
        error_time = datetime.now().isoformat()
        error_type = type(error).__name__
        error_message = str(error)
        error_traceback = traceback.format_exc()
        
        # Log to file
        logger.error(f"[{error_time}] {error_type}: {error_message}")
        logger.error(error_traceback)
        
        # Log to console
        print(f"[{error_time}] ERROR: {error_type}: {error_message}", file=sys.stderr)
        print(error_traceback, file=sys.stderr)
        
        # Log to database
        try:
            user_id = update.effective_user.id if update and update.effective_user else None
            db.log_error(
                error_type=error_type,
                error_message=error_message,
                stack_trace=error_traceback[:5000],
                user_id=user_id,
                context={
                    'update': str(update)[:1000] if update else None,
                    'chat_id': update.effective_chat.id if update and update.effective_chat else None,
                    'message': update.effective_message.text if update and update.effective_message else None,
                    'callback_data': update.callback_query.data if update and update.callback_query else None
                }
            )
        except Exception as e:
            logger.error(f"Failed to log error to database: {e}")
    
    @staticmethod
    async def critical_error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle critical errors that might crash the bot"""
        try:
            error = context.error
            logger.critical(f"CRITICAL ERROR: {error}")
            
            # Attempt to restart conversation
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "⚠️ <b>Critical Error</b>\n\n"
                    "The bot encountered a critical error and is restarting.\n\n"
                    "Please wait a moment and try again.\n\n"
                    f"If the problem persists, contact @{Config.ADMIN_CONTACT}",
                    parse_mode=ParseMode.HTML
                )
            
            # Clear user data
            if context and context.user_data:
                context.user_data.clear()
            
            # Log to admins
            for admin_id in Config.ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"🚨 <b>CRITICAL ERROR</b>\n\n{error}\n\n{traceback.format_exc()[:3000]}",
                        parse_mode=ParseMode.HTML
                    )
                except:
                    pass
                    
        except Exception as e:
            logger.critical(f"Failed to handle critical error: {e}")
    
    @staticmethod
    async def startup_error_handler(context: ContextTypes.DEFAULT_TYPE):
        """Handle errors during bot startup"""
        try:
            # Log startup error
            logger.error("Bot startup error occurred")
            
            # Try to notify admins
            for admin_id in Config.ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text="⚠️ <b>Bot Startup Warning</b>\n\nSome features may be unavailable. Please check logs.",
                        parse_mode=ParseMode.HTML
                    )
                except:
                    pass
        except Exception as e:
            logger.error(f"Failed to send startup error notification: {e}")

# Create global error handler instance
error_handler = ErrorHandler()
