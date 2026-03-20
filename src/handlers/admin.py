"""
Admin Handler - Handles admin commands and panel
Author: @kinva_master
Updated: 2026 - Enhanced Broadcast Features
"""

import logging
import json
import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from ..database import db
from ..config import Config
from ..utils import format_file_size, get_video_info, get_image_info

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_BROADCAST = 1
WAITING_FOR_BAN_REASON = 2
WAITING_FOR_ANNOUNCEMENT = 3
WAITING_FOR_PROMO_CODE = 4
WAITING_FOR_BROADCAST_MEDIA = 5
WAITING_FOR_BROADCAST_SCHEDULE = 6
WAITING_FOR_BROADCAST_TARGET = 7

class AdminHandler:
    """Handler for admin commands and panel"""
    
    # Broadcast types
    BROADCAST_TYPES = {
        'all': {'name': 'All Users', 'icon': '🌍'},
        'premium': {'name': 'Premium Users', 'icon': '⭐'},
        'free': {'name': 'Free Users', 'icon': '🆓'},
        'active': {'name': 'Active (Last 7 days)', 'icon': '📊'},
        'inactive': {'name': 'Inactive (>30 days)', 'icon': '💤'},
        'new': {'name': 'New (Last 7 days)', 'icon': '🆕'},
        'test': {'name': 'Test Users (Admins)', 'icon': '🧪'}
    }
    
    @staticmethod
    async def check_admin(user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in Config.ADMIN_IDS
    
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start admin panel"""
        user = update.effective_user
        
        if not await AdminHandler.check_admin(user.id):
            await update.message.reply_text(
                "❌ You don't have permission to access admin panel.",
                parse_mode=ParseMode.HTML
            )
            return
        
        text = (
            "👑 <b>Admin Panel</b>\n\n"
            "Welcome to the admin dashboard!\n\n"
            "<b>📊 Quick Stats:</b>\n"
            f"• Total Users: {db.get_total_users():,}\n"
            f"• Premium Users: {db.get_premium_users():,}\n"
            f"• Active Today: {db.get_active_today():,}\n"
            f"• Total Exports: {db.get_total_exports():,}\n"
            f"• Revenue (Month): ₹{db.get_monthly_revenue():,.0f}\n\n"
            "Select an option below:"
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 Dashboard", callback_data="admin_dashboard")],
            [InlineKeyboardButton("👥 User Management", callback_data="admin_users")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton("📈 Analytics", callback_data="admin_analytics")],
            [InlineKeyboardButton("🎨 Templates", callback_data="admin_templates")],
            [InlineKeyboardButton("💰 Payments", callback_data="admin_payments")],
            [InlineKeyboardButton("🎁 Promo Codes", callback_data="admin_promo")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")],
            [InlineKeyboardButton("📝 Logs", callback_data="admin_logs")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def broadcast_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show broadcast menu"""
        query = update.callback_query
        user = update.effective_user
        
        if not await AdminHandler.check_admin(user.id):
            await query.answer("Unauthorized", show_alert=True)
            return
        
        # Get broadcast stats
        last_broadcast = db.get_last_broadcast()
        
        text = (
            "📢 <b>Broadcast Center</b>\n\n"
            "Send messages to your users with powerful targeting options!\n\n"
            "<b>📊 Last Broadcast:</b>\n"
        )
        
        if last_broadcast:
            text += f"• Date: {last_broadcast['created_at'][:16]}\n"
            text += f"• Target: {last_broadcast['target']}\n"
            text += f"• Sent: {last_broadcast['sent']:,} users\n"
            text += f"• Delivered: {last_broadcast['delivered']:,}\n"
            text += f"• Failed: {last_broadcast['failed']:,}\n"
        else:
            text += "No broadcasts sent yet\n"
        
        text += "\n<b>🎯 Target Options:</b>\n"
        for key, target in AdminHandler.BROADCAST_TYPES.items():
            text += f"• {target['icon']} {target['name']}\n"
        
        text += "\n<b>📝 Message Types:</b>\n"
        text += "• Text Message\n"
        text += "• Photo + Caption\n"
        text += "• Video + Caption\n"
        text += "• Media Album (Multiple photos/videos)\n"
        text += "• Scheduled Broadcast\n\n"
        
        text += "<b>Choose an option:</b>"
        
        keyboard = [
            [InlineKeyboardButton("📝 Text Message", callback_data="broadcast_text")],
            [InlineKeyboardButton("🖼️ Photo Message", callback_data="broadcast_photo")],
            [InlineKeyboardButton("🎬 Video Message", callback_data="broadcast_video")],
            [InlineKeyboardButton("📚 Media Album", callback_data="broadcast_album")],
            [InlineKeyboardButton("⏰ Schedule Broadcast", callback_data="broadcast_schedule")],
            [InlineKeyboardButton("📊 Broadcast Stats", callback_data="broadcast_stats")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def select_broadcast_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Select broadcast target"""
        query = update.callback_query
        broadcast_type = query.data.replace('broadcast_', '')
        
        context.user_data['broadcast_type'] = broadcast_type
        
        text = (
            "🎯 <b>Select Target Audience</b>\n\n"
            "Choose who should receive this broadcast:\n\n"
        )
        
        keyboard = []
        for key, target in AdminHandler.BROADCAST_TYPES.items():
            count = db.get_user_count_by_type(key)
            keyboard.append([InlineKeyboardButton(
                f"{target['icon']} {target['name']} ({count:,} users)", 
                callback_data=f"broadcast_target_{key}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_broadcast")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get counts for each target type
        for key in AdminHandler.BROADCAST_TYPES.keys():
            count = db.get_user_count_by_type(key)
            text += f"{AdminHandler.BROADCAST_TYPES[key]['icon']} {AdminHandler.BROADCAST_TYPES[key]['name']}: {count:,} users\n"
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def set_broadcast_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set broadcast target"""
        query = update.callback_query
        target = query.data.replace('broadcast_target_', '')
        
        context.user_data['broadcast_target'] = target
        context.user_data['broadcast_users'] = db.get_users_by_type(target)
        
        user_count = len(context.user_data['broadcast_users'])
        
        text = (
            f"✅ <b>Target Selected: {AdminHandler.BROADCAST_TYPES[target]['name']}</b>\n\n"
            f"<b>Users to receive:</b> {user_count:,}\n\n"
            f"Now send your broadcast message.\n\n"
            f"<b>Tips:</b>\n"
            f"• You can use HTML formatting\n"
            f"• Send a photo/video for media broadcast\n"
            f"• Type /cancel to cancel\n\n"
            f"Send your message now:"
        )
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML
        )
        
        return WAITING_FOR_BROADCAST
    
    @staticmethod
    async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send broadcast message"""
        message_text = update.message.text
        user = update.effective_user
        broadcast_type = context.user_data.get('broadcast_type', 'text')
        target = context.user_data.get('broadcast_target', 'all')
        users = context.user_data.get('broadcast_users', [])
        
        if not users:
            users = db.get_users_by_type(target)
        
        total_users = len(users)
        
        # Create progress message
        progress_msg = await update.message.reply_text(
            f"⏳ <b>Sending Broadcast...</b>\n\n"
            f"Target: {AdminHandler.BROADCAST_TYPES[target]['name']}\n"
            f"Total: {total_users:,} users\n"
            f"Progress: 0/{total_users}\n"
            f"Success: 0\n"
            f"Failed: 0\n\n"
            f"<i>This may take several minutes...</i>",
            parse_mode=ParseMode.HTML
        )
        
        success_count = 0
        fail_count = 0
        blocked_count = 0
        
        # Send to users in batches
        batch_size = 50
        for i in range(0, total_users, batch_size):
            batch = users[i:i+batch_size]
            
            for user_data in batch:
                try:
                    await context.bot.send_message(
                        chat_id=user_data['telegram_id'],
                        text=message_text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True
                    )
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    if "blocked" in str(e).lower():
                        blocked_count += 1
                
                # Update progress every 10 users
                if (success_count + fail_count) % 10 == 0:
                    await progress_msg.edit_text(
                        f"⏳ <b>Sending Broadcast...</b>\n\n"
                        f"Target: {AdminHandler.BROADCAST_TYPES[target]['name']}\n"
                        f"Total: {total_users:,} users\n"
                        f"Progress: {success_count + fail_count}/{total_users}\n"
                        f"Success: {success_count}\n"
                        f"Failed: {fail_count}\n"
                        f"Blocked: {blocked_count}\n\n"
                        f"<i>Estimated time: {((total_users - (success_count + fail_count)) / 10):.0f} seconds</i>",
                        parse_mode=ParseMode.HTML
                    )
            
            # Small delay between batches
            await asyncio.sleep(1)
        
        # Save broadcast record
        db.save_broadcast(
            admin_id=user.id,
            target=target,
            message=message_text,
            sent=success_count + fail_count,
            delivered=success_count,
            failed=fail_count
        )
        
        # Final message
        await progress_msg.edit_text(
            f"✅ <b>Broadcast Complete!</b>\n\n"
            f"<b>Target:</b> {AdminHandler.BROADCAST_TYPES[target]['name']}\n"
            f"<b>Total Users:</b> {total_users:,}\n"
            f"<b>Successfully Delivered:</b> {success_count:,}\n"
            f"<b>Failed:</b> {fail_count:,}\n"
            f"<b>Blocked Users:</b> {blocked_count:,}\n\n"
            f"<b>Message Preview:</b>\n"
            f"{message_text[:200]}...",
            parse_mode=ParseMode.HTML
        )
        
        return ConversationHandler.END
    
    @staticmethod
    async def send_photo_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send photo broadcast"""
        user = update.effective_user
        target = context.user_data.get('broadcast_target', 'all')
        users = context.user_data.get('broadcast_users', [])
        
        if not users:
            users = db.get_users_by_type(target)
        
        photo = update.message.photo[-1] if update.message.photo else None
        caption = update.message.caption
        
        if not photo:
            await update.message.reply_text(
                "❌ Please send a photo to broadcast.",
                parse_mode=ParseMode.HTML
            )
            return WAITING_FOR_BROADCAST_MEDIA
        
        total_users = len(users)
        
        # Create progress message
        progress_msg = await update.message.reply_text(
            f"⏳ <b>Sending Photo Broadcast...</b>\n\n"
            f"Target: {AdminHandler.BROADCAST_TYPES[target]['name']}\n"
            f"Total: {total_users:,} users\n"
            f"Progress: 0/{total_users}\n"
            f"Success: 0\n"
            f"Failed: 0\n\n"
            f"<i>This may take several minutes...</i>",
            parse_mode=ParseMode.HTML
        )
        
        success_count = 0
        fail_count = 0
        
        # Get file
        file = await context.bot.get_file(photo.file_id)
        file_path = f"/tmp/broadcast_{user.id}_{int(datetime.now().timestamp())}.jpg"
        await file.download_to_drive(file_path)
        
        # Send to users in batches
        batch_size = 30
        for i in range(0, total_users, batch_size):
            batch = users[i:i+batch_size]
            
            for user_data in batch:
                try:
                    with open(file_path, 'rb') as photo_file:
                        await context.bot.send_photo(
                            chat_id=user_data['telegram_id'],
                            photo=photo_file,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                
                # Update progress
                if (success_count + fail_count) % 10 == 0:
                    await progress_msg.edit_text(
                        f"⏳ <b>Sending Photo Broadcast...</b>\n\n"
                        f"Target: {AdminHandler.BROADCAST_TYPES[target]['name']}\n"
                        f"Total: {total_users:,} users\n"
                        f"Progress: {success_count + fail_count}/{total_users}\n"
                        f"Success: {success_count}\n"
                        f"Failed: {fail_count}\n\n"
                        f"<i>Estimated time: {((total_users - (success_count + fail_count)) / 5):.0f} seconds</i>",
                        parse_mode=ParseMode.HTML
                    )
            
            await asyncio.sleep(1)
        
        # Cleanup
        os.remove(file_path)
        
        # Save broadcast record
        db.save_broadcast(
            admin_id=user.id,
            target=target,
            message=caption,
            media_type='photo',
            sent=success_count + fail_count,
            delivered=success_count,
            failed=fail_count
        )
        
        await progress_msg.edit_text(
            f"✅ <b>Photo Broadcast Complete!</b>\n\n"
            f"<b>Target:</b> {AdminHandler.BROADCAST_TYPES[target]['name']}\n"
            f"<b>Total Users:</b> {total_users:,}\n"
            f"<b>Successfully Delivered:</b> {success_count:,}\n"
            f"<b>Failed:</b> {fail_count:,}\n\n"
            f"<b>Caption Preview:</b>\n"
            f"{caption[:200] if caption else 'No caption'}...",
            parse_mode=ParseMode.HTML
        )
        
        return ConversationHandler.END
    
    @staticmethod
    async def schedule_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Schedule a broadcast for later"""
        query = update.callback_query
        
        text = (
            "⏰ <b>Schedule Broadcast</b>\n\n"
            "Enter the date and time for your broadcast in the following format:\n\n"
            "<code>YYYY-MM-DD HH:MM</code>\n\n"
            "<b>Example:</b>\n"
            "<code>2026-01-15 18:30</code>\n\n"
            "<b>Note:</b>\n"
            "• Time is in IST (Indian Standard Time)\n"
            "• Minimum 5 minutes from now\n"
            "• Maximum 30 days from now\n\n"
            "Enter the scheduled time:"
        )
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML
        )
        
        return WAITING_FOR_BROADCAST_SCHEDULE
    
    @staticmethod
    async def process_schedule_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process scheduled broadcast"""
        try:
            schedule_time = datetime.strptime(update.message.text, '%Y-%m-%d %H:%M')
            
            # Check if time is in the future
            if schedule_time <= datetime.now():
                await update.message.reply_text(
                    "❌ Schedule time must be in the future.\n\n"
                    "Please enter a future date and time.",
                    parse_mode=ParseMode.HTML
                )
                return WAITING_FOR_BROADCAST_SCHEDULE
            
            # Check if within 30 days
            if schedule_time > datetime.now() + timedelta(days=30):
                await update.message.reply_text(
                    "❌ Schedule time cannot be more than 30 days from now.\n\n"
                    "Please enter a date within 30 days.",
                    parse_mode=ParseMode.HTML
                )
                return WAITING_FOR_BROADCAST_SCHEDULE
            
            context.user_data['broadcast_schedule'] = schedule_time
            
            # Show target selection for scheduled broadcast
            text = (
                f"✅ <b>Schedule Set!</b>\n\n"
                f"<b>Scheduled for:</b> {schedule_time.strftime('%Y-%m-%d %H:%M')} IST\n\n"
                f"Now select the target audience:\n\n"
            )
            
            keyboard = []
            for key, target in AdminHandler.BROADCAST_TYPES.items():
                count = db.get_user_count_by_type(key)
                keyboard.append([InlineKeyboardButton(
                    f"{target['icon']} {target['name']} ({count:,} users)", 
                    callback_data=f"schedule_target_{key}"
                )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid format.\n\n"
                "Please use the format: <code>YYYY-MM-DD HH:MM</code>\n"
                "Example: <code>2026-01-15 18:30</code>",
                parse_mode=ParseMode.HTML
            )
            return WAITING_FOR_BROADCAST_SCHEDULE
        
        return ConversationHandler.END
    
    @staticmethod
    async def schedule_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set target for scheduled broadcast"""
        query = update.callback_query
        target = query.data.replace('schedule_target_', '')
        
        schedule_time = context.user_data.get('broadcast_schedule')
        
        # Save scheduled broadcast
        db.save_scheduled_broadcast(
            admin_id=update.effective_user.id,
            target=target,
            scheduled_time=schedule_time,
            message=context.user_data.get('broadcast_message', '')
        )
        
        await query.edit_message_text(
            f"✅ <b>Broadcast Scheduled!</b>\n\n"
            f"<b>Target:</b> {AdminHandler.BROADCAST_TYPES[target]['name']}\n"
            f"<b>Scheduled for:</b> {schedule_time.strftime('%Y-%m-%d %H:%M')} IST\n\n"
            f"Your broadcast will be sent automatically at the scheduled time.\n\n"
            f"<b>Note:</b> You can view scheduled broadcasts in the stats.",
            parse_mode=ParseMode.HTML
        )
        
        return ConversationHandler.END
    
    @staticmethod
    async def broadcast_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show broadcast statistics"""
        query = update.callback_query
        
        # Get broadcast stats
        stats = db.get_broadcast_stats()
        recent_broadcasts = db.get_recent_broadcasts(limit=10)
        scheduled_broadcasts = db.get_scheduled_broadcasts()
        
        text = (
            "📊 <b>Broadcast Statistics</b>\n\n"
            f"<b>📈 Overall Stats:</b>\n"
            f"• Total Broadcasts: {stats['total_broadcasts']}\n"
            f"• Total Users Reached: {stats['total_reached']:,}\n"
            f"• Average Success Rate: {stats['avg_success_rate']:.1f}%\n"
            f"• Total Blocked Users: {stats['total_blocked']:,}\n\n"
            f"<b>⏰ Scheduled Broadcasts:</b> {len(scheduled_broadcasts)}\n\n"
            f"<b>📋 Recent Broadcasts:</b>\n"
        )
        
        for broadcast in recent_broadcasts:
            text += f"• {broadcast['created_at'][:16]} - {broadcast['target']}\n"
            text += f"  Sent: {broadcast['sent']} | Delivered: {broadcast['delivered']} | Failed: {broadcast['failed']}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("📊 Export Stats", callback_data="broadcast_export")],
            [InlineKeyboardButton("⏰ View Scheduled", callback_data="broadcast_scheduled")],
            [InlineKeyboardButton("🔙 Back", callback_data="admin_broadcast")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel broadcast"""
        await update.message.reply_text(
            "❌ Broadcast cancelled.\n\n"
            "Use /admin to return to admin panel.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    # ============================================
    # Enhanced Broadcast Features
    # ============================================
    
    @staticmethod
    async def send_video_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send video broadcast"""
        user = update.effective_user
        target = context.user_data.get('broadcast_target', 'all')
        users = context.user_data.get('broadcast_users', [])
        
        if not users:
            users = db.get_users_by_type(target)
        
        video = update.message.video
        caption = update.message.caption
        
        if not video:
            await update.message.reply_text(
                "❌ Please send a video to broadcast.",
                parse_mode=ParseMode.HTML
            )
            return WAITING_FOR_BROADCAST_MEDIA
        
        total_users = len(users)
        
        progress_msg = await update.message.reply_text(
            f"⏳ <b>Sending Video Broadcast...</b>\n\n"
            f"Target: {AdminHandler.BROADCAST_TYPES[target]['name']}\n"
            f"Total: {total_users:,} users\n"
            f"Progress: 0/{total_users}\n\n"
            f"<i>This may take a while...</i>",
            parse_mode=ParseMode.HTML
        )
        
        success_count = 0
        fail_count = 0
        
        file = await context.bot.get_file(video.file_id)
        file_path = f"/tmp/broadcast_{user.id}_{int(datetime.now().timestamp())}.mp4"
        await file.download_to_drive(file_path)
        
        batch_size = 20
        for i in range(0, total_users, batch_size):
            batch = users[i:i+batch_size]
            
            for user_data in batch:
                try:
                    with open(file_path, 'rb') as video_file:
                        await context.bot.send_video(
                            chat_id=user_data['telegram_id'],
                            video=video_file,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                            supports_streaming=True
                        )
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                
                if (success_count + fail_count) % 5 == 0:
                    await progress_msg.edit_text(
                        f"⏳ <b>Sending Video Broadcast...</b>\n\n"
                        f"Target: {AdminHandler.BROADCAST_TYPES[target]['name']}\n"
                        f"Total: {total_users:,} users\n"
                        f"Progress: {success_count + fail_count}/{total_users}\n"
                        f"Success: {success_count}\n"
                        f"Failed: {fail_count}",
                        parse_mode=ParseMode.HTML
                    )
            
            await asyncio.sleep(2)
        
        os.remove(file_path)
        
        db.save_broadcast(
            admin_id=user.id,
            target=target,
            message=caption,
            media_type='video',
            sent=success_count + fail_count,
            delivered=success_count,
            failed=fail_count
        )
        
        await progress_msg.edit_text(
            f"✅ <b>Video Broadcast Complete!</b>\n\n"
            f"<b>Target:</b> {AdminHandler.BROADCAST_TYPES[target]['name']}\n"
            f"<b>Successfully Delivered:</b> {success_count:,}\n"
            f"<b>Failed:</b> {fail_count:,}",
            parse_mode=ParseMode.HTML
        )
        
        return ConversationHandler.END
    
    @staticmethod
    async def send_album_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send media album broadcast"""
        user = update.effective_user
        target = context.user_data.get('broadcast_target', 'all')
        users = context.user_data.get('broadcast_users', [])
        
        if not users:
            users = db.get_users_by_type(target)
        
        # Check if message contains multiple media
        media_group = update.message.media_group
        caption = update.message.caption
        
        if not media_group or len(media_group) < 2:
            await update.message.reply_text(
                "❌ Please send at least 2 photos/videos as an album.\n\n"
                "Send them together as a media group.",
                parse_mode=ParseMode.HTML
            )
            return WAITING_FOR_BROADCAST_MEDIA
        
        total_users = len(users)
        
        progress_msg = await update.message.reply_text(
            f"⏳ <b>Sending Album Broadcast...</b>\n\n"
            f"Target: {AdminHandler.BROADCAST_TYPES[target]['name']}\n"
            f"Total: {total_users:,} users\n"
            f"Media: {len(media_group)} items\n"
            f"Progress: 0/{total_users}\n\n"
            f"<i>This may take a while...</i>",
            parse_mode=ParseMode.HTML
        )
        
        success_count = 0
        fail_count = 0
        
        # Download all media
        media_files = []
        for media in media_group:
            if media.photo:
                file = await context.bot.get_file(media.photo[-1].file_id)
                file_path = f"/tmp/broadcast_{user.id}_{int(datetime.now().timestamp())}_{media.photo[-1].file_id}.jpg"
                await file.download_to_drive(file_path)
                media_files.append(('photo', file_path))
            elif media.video:
                file = await context.bot.get_file(media.video.file_id)
                file_path = f"/tmp/broadcast_{user.id}_{int(datetime.now().timestamp())}_{media.video.file_id}.mp4"
                await file.download_to_drive(file_path)
                media_files.append(('video', file_path))
        
        batch_size = 15
        for i in range(0, total_users, batch_size):
            batch = users[i:i+batch_size]
            
            for user_data in batch:
                try:
                    # Create media group
                    media_group_list = []
                    for idx, (media_type, file_path) in enumerate(media_files):
                        with open(file_path, 'rb') as f:
                            if media_type == 'photo':
                                if idx == 0:
                                    media_group_list.append(InputMediaPhoto(f, caption=caption))
                                else:
                                    media_group_list.append(InputMediaPhoto(f))
                            else:
                                if idx == 0:
                                    media_group_list.append(InputMediaVideo(f, caption=caption))
                                else:
                                    media_group_list.append(InputMediaVideo(f))
                    
                    await context.bot.send_media_group(
                        chat_id=user_data['telegram_id'],
                        media=media_group_list
                    )
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                
                if (success_count + fail_count) % 5 == 0:
                    await progress_msg.edit_text(
                        f"⏳ <b>Sending Album Broadcast...</b>\n\n"
                        f"Target: {AdminHandler.BROADCAST_TYPES[target]['name']}\n"
                        f"Total: {total_users:,} users\n"
                        f"Progress: {success_count + fail_count}/{total_users}\n"
                        f"Success: {success_count}\n"
                        f"Failed: {fail_count}",
                        parse_mode=ParseMode.HTML
                    )
            
            await asyncio.sleep(2)
        
        # Cleanup media files
        for _, file_path in media_files:
            os.remove(file_path)
        
        db.save_broadcast(
            admin_id=user.id,
            target=target,
            message=caption,
            media_type='album',
            media_count=len(media_files),
            sent=success_count + fail_count,
            delivered=success_count,
            failed=fail_count
        )
        
        await progress_msg.edit_text(
            f"✅ <b>Album Broadcast Complete!</b>\n\n"
            f"<b>Target:</b> {AdminHandler.BROADCAST_TYPES[target]['name']}\n"
            f"<b>Media Items:</b> {len(media_files)}\n"
            f"<b>Successfully Delivered:</b> {success_count:,}\n"
            f"<b>Failed:</b> {fail_count:,}",
            parse_mode=ParseMode.HTML
        )
        
        return ConversationHandler.END
