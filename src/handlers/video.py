"""
Video Handler - Handles video editing functionality
Author: @kinva_master
"""

import os
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode, ChatAction

from ..database import db
from ..config import Config
from ..processors.video_processor import video_processor
from ..processors.watermark import watermark

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_VIDEO = 1
WAITING_FOR_EFFECTS = 2
WAITING_FOR_TRANSITIONS = 3
WAITING_FOR_AUDIO = 4

class VideoHandler:
    """Handler for video editing commands"""
    
    # Available effects
    EFFECTS = {
        'vintage': {'name': '🎞️ Vintage', 'premium': False},
        'cinematic': {'name': '🎬 Cinematic', 'premium': False},
        'black_white': {'name': '⚫ Black & White', 'premium': False},
        'sepia': {'name': '🟫 Sepia', 'premium': False},
        'glitch': {'name': '💥 Glitch', 'premium': False},
        'blur': {'name': '🌀 Blur', 'premium': False},
        'sharpen': {'name': '✨ Sharpen', 'premium': False},
        'mirror': {'name': '🪞 Mirror', 'premium': False},
        'slow_motion': {'name': '🐢 Slow Motion', 'premium': False},
        'fast_motion': {'name': '⚡ Fast Motion', 'premium': False},
        'neon': {'name': '🔥 Neon', 'premium': True},
        'cartoon': {'name': '🎨 Cartoon', 'premium': True},
        '3d': {'name': '🎥 3D Effect', 'premium': True},
        'oil_paint': {'name': '🎭 Oil Paint', 'premium': True},
    }
    
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start video editing"""
        text = (
            "🎬 <b>Video Editor</b>\n\n"
            "Send me a video to start editing!\n\n"
            "<b>Supported formats:</b> MP4, AVI, MOV, MKV, WEBM\n"
            "<b>Max size:</b> 500MB\n"
            f"<b>Max length (free):</b> {Config.FREE_VIDEO_LENGTH} seconds\n"
            f"<b>Max length (premium):</b> 2 hours\n\n"
            "<b>Available Effects:</b>\n"
            "🎞️ Vintage | 🎬 Cinematic | ⚫ B&W | 🟫 Sepia | 💥 Glitch\n"
            "🌀 Blur | ✨ Sharpen | 🪞 Mirror | 🐢 Slow Mo | ⚡ Fast Mo\n\n"
            "⭐ <b>Premium Effects:</b>\n"
            "🔥 Neon | 🎨 Cartoon | 🎥 3D | 🎭 Oil Paint\n\n"
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
    
    @staticmethod
    async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video file upload"""
        user = update.effective_user
        video = update.message.video or update.message.document
        
        if not video:
            await update.message.reply_text("❌ Please send a valid video file.")
            return WAITING_FOR_VIDEO
        
        # Check file size
        if video.file_size > Config.MAX_VIDEO_SIZE:
            await update.message.reply_text(
                f"❌ File too large. Max size: {Config.MAX_VIDEO_SIZE // (1024*1024)}MB"
            )
            return WAITING_FOR_VIDEO
        
        # Check premium status
        user_data = db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        # Download video
        progress_msg = await update.message.reply_text("📥 Downloading video...")
        
        file = await context.bot.get_file(video.file_id)
        input_path = f"/tmp/video_{user.id}_{int(asyncio.get_event_loop().time())}.mp4"
        await file.download_to_drive(input_path)
        
        # Get video info
        import cv2
        cap = cv2.VideoCapture(input_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        # Check duration for free users
        if not is_premium and duration > Config.FREE_VIDEO_LENGTH:
            os.remove(input_path)
            await progress_msg.edit_text(
                f"❌ Free users can only edit videos up to {Config.FREE_VIDEO_LENGTH} seconds.\n"
                f"Your video is {int(duration)} seconds long.\n\n"
                f"Upgrade to premium to edit longer videos!\n"
                f"Use /premium to see plans."
            )
            return WAITING_FOR_VIDEO
        
        # Store in context
        context.user_data['video_path'] = input_path
        context.user_data['video_duration'] = duration
        context.user_data['video_width'] = width
        context.user_data['video_height'] = height
        
        await progress_msg.edit_text(
            f"✅ Video downloaded!\n\n"
            f"<b>Duration:</b> {int(duration)} seconds\n"
            f"<b>Resolution:</b> {width}x{height}\n"
            f"<b>Size:</b> {video.file_size // (1024*1024)} MB\n\n"
            f"Now select effects to apply:",
            parse_mode=ParseMode.HTML
        )
        
        # Show effects selection
        keyboard = []
        
        # Add effects based on premium status
        for effect_key, effect_info in VideoHandler.EFFECTS.items():
            if effect_info['premium'] and not is_premium:
                continue
            keyboard.append([InlineKeyboardButton(
                effect_info['name'], 
                callback_data=f"effect_{effect_key}"
            )])
        
        # Add action buttons
        keyboard.append([InlineKeyboardButton("✅ Process Video", callback_data="process_video")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "✨ Select effects to apply (you can select multiple):",
            reply_markup=reply_markup
        )
        
        return WAITING_FOR_EFFECTS
    
    @staticmethod
    async def select_effect(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle effect selection"""
        query = update.callback_query
        effect = query.data.replace('effect_', '')
        
        if 'selected_effects' not in context.user_data:
            context.user_data['selected_effects'] = []
        
        if effect in context.user_data['selected_effects']:
            context.user_data['selected_effects'].remove(effect)
            await query.answer(f"❌ Removed {effect}")
        else:
            context.user_data['selected_effects'].append(effect)
            await query.answer(f"✅ Added {effect}")
        
        selected = context.user_data['selected_effects']
        selected_names = [VideoHandler.EFFECTS[e]['name'] for e in selected if e in VideoHandler.EFFECTS]
        
        text = f"✨ <b>Selected Effects:</b>\n"
        if selected_names:
            text += "\n".join(f"• {name}" for name in selected_names)
        else:
            text += "None"
        
        text += "\n\nSelect more effects or click Process when ready."
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=query.message.reply_markup
        )
    
    @staticmethod
    async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process video with selected effects"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        video_path = context.user_data.get('video_path')
        effects = context.user_data.get('selected_effects', [])
        
        if not video_path:
            await query.edit_message_text("❌ No video found. Please upload again.")
            return ConversationHandler.END
        
        # Check premium status
        user_data = db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        # Check export limit
        if not is_premium:
            stats = db.get_user_stats(user.id)
            if stats.get('exports_today', 0) >= Config.FREE_VIDEO_EXPORTS:
                await query.edit_message_text(
                    "❌ You've reached your daily export limit.\n\n"
                    "Upgrade to premium for unlimited exports!\n"
                    "Use /premium to see plans."
                )
                return ConversationHandler.END
        
        # Update message
        await query.edit_message_text(
            "⏳ <b>Processing your video...</b>\n\n"
            "This may take a few moments depending on video length.\n"
            "Please wait...",
            parse_mode=ParseMode.HTML
        )
        
        try:
            # Send typing action
            await context.bot.send_chat_action(chat_id=user.id, action=ChatAction.UPLOAD_VIDEO)
            
            # Process video
            output_path = video_processor.process(
                video_path,
                effects=effects,
                quality='1080p' if is_premium else '720p'
            )
            
            # Add watermark for free users
            if not is_premium:
                output_path = watermark.add_video_watermark(output_path)
            
            # Send video
            with open(output_path, 'rb') as video_file:
                caption = (
                    f"✅ <b>Video processed successfully!</b>\n\n"
                    f"<b>Effects applied:</b> {', '.join(effects) if effects else 'None'}\n"
                    f"<b>Quality:</b> {'1080p' if is_premium else '720p'}\n"
                    f"<b>Size:</b> {os.path.getsize(output_path) // (1024*1024)} MB\n\n"
                )
                
                if not is_premium:
                    caption += (
                        f"💧 <i>Watermark: @kinva_master.com</i>\n"
                        f"⭐ Upgrade to premium to remove watermark!\n\n"
                    )
                
                caption += f"<b>Need more edits?</b> Use /video again!"
                
                await context.bot.send_video(
                    chat_id=user.id,
                    video=video_file,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    supports_streaming=True
                )
            
            # Update stats
            db.increment_exports(user.id)
            db.increment_videos_edited(user.id)
            
            # Save to history
            db.save_video_history(
                user_id=user.id,
                file_path=output_path,
                effects=effects,
                size=os.path.getsize(output_path)
            )
            
            # Send notification to admin
            for admin_id in Config.ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"📊 User {user.id} (@{user.username}) processed a video\n"
                             f"Effects: {', '.join(effects) if effects else 'None'}\n"
                             f"Quality: {'1080p' if is_premium else '720p'}"
                    )
                except:
                    pass
            
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
    
    @staticmethod
    async def compress_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video compression"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        video_path = context.user_data.get('video_path')
        
        if not video_path:
            await query.edit_message_text("❌ No video found. Please upload again.")
            return ConversationHandler.END
        
        # Check premium status
        user_data = db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        if not is_premium:
            await query.edit_message_text(
                "❌ Video compression is a premium feature.\n\n"
                "Upgrade to premium to compress videos!\n"
                "Use /premium to see plans."
            )
            return ConversationHandler.END
        
        await query.edit_message_text(
            "⏳ <b>Compressing your video...</b>\n\n"
            "This may take a few moments...",
            parse_mode=ParseMode.HTML
        )
        
        try:
            # Compress video
            output_path = video_processor.compress(video_path, level='high')
            
            # Send compressed video
            with open(output_path, 'rb') as video_file:
                original_size = os.path.getsize(video_path)
                compressed_size = os.path.getsize(output_path)
                reduction = (1 - compressed_size / original_size) * 100
                
                caption = (
                    f"✅ <b>Video compressed successfully!</b>\n\n"
                    f"<b>Original size:</b> {original_size // (1024*1024)} MB\n"
                    f"<b>Compressed size:</b> {compressed_size // (1024*1024)} MB\n"
                    f"<b>Reduction:</b> {reduction:.1f}%\n\n"
                    f"<b>Need more edits?</b> Use /video again!"
                )
                
                await context.bot.send_video(
                    chat_id=user.id,
                    video=video_file,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            
        except Exception as e:
            logger.error(f"Video compression error: {e}")
            await query.edit_message_text(
                f"❌ <b>Error compressing video</b>\n\n"
                f"{str(e)}\n\n"
                f"Please try again.",
                parse_mode=ParseMode.HTML
            )
        
        return ConversationHandler.END
    
    @staticmethod
    async def show_effects(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all available effects"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        user_data = db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        text = "✨ <b>Available Video Effects</b>\n\n"
        
        for effect_key, effect_info in VideoHandler.EFFECTS.items():
            premium_badge = " ⭐" if effect_info['premium'] else ""
            text += f"• <b>{effect_info['name']}</b>{premium_badge}\n"
            if effect_info['premium'] and not is_premium:
                text += f"  <i>Premium feature - Upgrade to unlock</i>\n"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="video")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel video editing"""
        query = update.callback_query
        await query.answer()
        
        # Cleanup
        if 'video_path' in context.user_data and os.path.exists(context.user_data['video_path']):
            os.remove(context.user_data['video_path'])
        
        context.user_data.clear()
        
        await query.edit_message_text(
            "❌ Video editing cancelled.\n\n"
            "Use /start to return to main menu."
        )
        
        return ConversationHandler.END
