"""
Image Handler - Handles image editing functionality
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
from ..processors.image_processor import image_processor
from ..processors.watermark import watermark

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_IMAGE = 1
WAITING_FOR_FILTERS = 2
WAITING_FOR_TEXT = 3
WAITING_FOR_CROP = 4

class ImageHandler:
    """Handler for image editing commands"""
    
    # Available filters
    FILTERS = {
        'grayscale': {'name': '⚫ Grayscale', 'premium': False},
        'sepia': {'name': '🟫 Sepia', 'premium': False},
        'invert': {'name': '🔄 Invert', 'premium': False},
        'vintage': {'name': '🎞️ Vintage', 'premium': False},
        'cinematic': {'name': '🎬 Cinematic', 'premium': False},
        'glitch': {'name': '💥 Glitch', 'premium': False},
        'blur': {'name': '🌀 Blur', 'premium': False},
        'sharpen': {'name': '✨ Sharpen', 'premium': False},
        'edge': {'name': '✏️ Edge', 'premium': False},
        'emboss': {'name': '⛰️ Emboss', 'premium': False},
        'neon': {'name': '🔥 Neon', 'premium': True},
        'sketch': {'name': '✏️ Sketch', 'premium': True},
        'oil_paint': {'name': '🎭 Oil Paint', 'premium': True},
        'watercolor': {'name': '🎨 Watercolor', 'premium': True},
        'pixelate': {'name': '🔲 Pixelate', 'premium': True},
    }
    
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start image editing"""
        text = (
            "🖼️ <b>Image Editor</b>\n\n"
            "Send me an image to start editing!\n\n"
            "<b>Supported formats:</b> JPG, PNG, GIF, WebP, BMP\n"
            "<b>Max size:</b> 50MB\n\n"
            "<b>Available Filters:</b>\n"
            "⚫ Grayscale | 🟫 Sepia | 🔄 Invert | 🎞️ Vintage | 🎬 Cinematic\n"
            "💥 Glitch | 🌀 Blur | ✨ Sharpen | ✏️ Edge | ⛰️ Emboss\n\n"
            "⭐ <b>Premium Filters:</b>\n"
            "🔥 Neon | ✏️ Sketch | 🎭 Oil Paint | 🎨 Watercolor | 🔲 Pixelate\n\n"
            "⭐ <b>Premium Tools:</b>\n"
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
    
    @staticmethod
    async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle image file upload"""
        user = update.effective_user
        photo = update.message.photo[-1] if update.message.photo else None
        document = update.message.document
        
        if photo:
            file_id = photo.file_id
            file_size = photo.file_size
        elif document:
            file_id = document.file_id
            file_size = document.file_size
        else:
            await update.message.reply_text("❌ Please send a valid image file.")
            return WAITING_FOR_IMAGE
        
        # Check file size
        if file_size > Config.MAX_IMAGE_SIZE:
            await update.message.reply_text(
                f"❌ File too large. Max size: {Config.MAX_IMAGE_SIZE // (1024*1024)}MB"
            )
            return WAITING_FOR_IMAGE
        
        # Check premium status
        user_data = db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        # Download image
        progress_msg = await update.message.reply_text("📥 Downloading image...")
        
        file = await context.bot.get_file(file_id)
        input_path = f"/tmp/image_{user.id}_{int(asyncio.get_event_loop().time())}.jpg"
        await file.download_to_drive(input_path)
        
        # Get image info
        from PIL import Image
        img = Image.open(input_path)
        width, height = img.size
        format = img.format
        
        await progress_msg.edit_text(
            f"✅ Image downloaded!\n\n"
            f"<b>Size:</b> {width}x{height}\n"
            f"<b>Format:</b> {format}\n"
            f"<b>File size:</b> {file_size // 1024} KB\n\n"
            f"Now select filters to apply:",
            parse_mode=ParseMode.HTML
        )
        
        # Store in context
        context.user_data['image_path'] = input_path
        context.user_data['image_width'] = width
        context.user_data['image_height'] = height
        
        # Show filters selection
        keyboard = []
        
        # Add filters based on premium status
        for filter_key, filter_info in ImageHandler.FILTERS.items():
            if filter_info['premium'] and not is_premium:
                continue
            keyboard.append([InlineKeyboardButton(
                filter_info['name'], 
                callback_data=f"filter_{filter_key}"
            )])
        
        # Add premium tools for premium users
        if is_premium:
            keyboard.append([
                InlineKeyboardButton("🖼️ Remove Background", callback_data="remove_bg"),
                InlineKeyboardButton("🧹 Remove Object", callback_data="remove_object"),
            ])
        
        # Add action buttons
        keyboard.append([InlineKeyboardButton("✅ Process Image", callback_data="process_image")])
        keyboard.append([InlineKeyboardButton("✏️ Add Text", callback_data="add_text")])
        keyboard.append([InlineKeyboardButton("✂️ Crop", callback_data="crop_image")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "✨ Select filters to apply (you can select multiple):",
            reply_markup=reply_markup
        )
        
        return WAITING_FOR_FILTERS
    
    @staticmethod
    async def select_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle filter selection"""
        query = update.callback_query
        filter_name = query.data.replace('filter_', '')
        
        if 'selected_filters' not in context.user_data:
            context.user_data['selected_filters'] = []
        
        if filter_name in context.user_data['selected_filters']:
            context.user_data['selected_filters'].remove(filter_name)
            await query.answer(f"❌ Removed {filter_name}")
        else:
            context.user_data['selected_filters'].append(filter_name)
            await query.answer(f"✅ Added {filter_name}")
        
        selected = context.user_data['selected_filters']
        selected_names = [ImageHandler.FILTERS[f]['name'] for f in selected if f in ImageHandler.FILTERS]
        
        text = f"✨ <b>Selected Filters:</b>\n"
        if selected_names:
            text += "\n".join(f"• {name}" for name in selected_names)
        else:
            text += "None"
        
        text += "\n\nSelect more filters or click Process when ready."
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=query.message.reply_markup
        )
    
    @staticmethod
    async def process_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process image with selected filters"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        image_path = context.user_data.get('image_path')
        filters = context.user_data.get('selected_filters', [])
        
        if not image_path:
            await query.edit_message_text("❌ No image found. Please upload again.")
            return ConversationHandler.END
        
        # Check premium status
        user_data = db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        # Check export limit
        if not is_premium:
            stats = db.get_user_stats(user.id)
            if stats.get('exports_today', 0) >= Config.FREE_IMAGE_EXPORTS:
                await query.edit_message_text(
                    "❌ You've reached your daily export limit.\n\n"
                    "Upgrade to premium for unlimited exports!\n"
                    "Use /premium to see plans."
                )
                return ConversationHandler.END
        
        # Update message
        await query.edit_message_text(
            "⏳ <b>Processing your image...</b>\n\n"
            "Applying filters...",
            parse_mode=ParseMode.HTML
        )
        
        try:
            # Send typing action
            await context.bot.send_chat_action(chat_id=user.id, action=ChatAction.UPLOAD_PHOTO)
            
            # Process image
            output_path = image_processor.process(image_path, filters=filters)
            
            # Add watermark for free users
            if not is_premium:
                output_path = watermark.add_image_watermark(output_path)
            
            # Send image
            with open(output_path, 'rb') as image_file:
                caption = (
                    f"✅ <b>Image processed successfully!</b>\n\n"
                    f"<b>Filters applied:</b> {', '.join(filters) if filters else 'None'}\n"
                    f"<b>Size:</b> {os.path.getsize(output_path) // 1024} KB\n\n"
                )
                
                if not is_premium:
                    caption += (
                        f"💧 <i>Watermark: @kinva_master.com</i>\n"
                        f"⭐ Upgrade to premium to remove watermark!\n\n"
                    )
                
                caption += f"<b>Need more edits?</b> Use /image again!"
                
                await context.bot.send_photo(
                    chat_id=user.id,
                    photo=image_file,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            
            # Update stats
            db.increment_exports(user.id)
            db.increment_images_edited(user.id)
            
            # Save to history
            db.save_image_history(
                user_id=user.id,
                file_path=output_path,
                filters=filters,
                size=os.path.getsize(output_path)
            )
            
            # Send notification to admin
            for admin_id in Config.ADMIN_IDS:
                try:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=f"📊 User {user.id} (@{user.username}) processed an image\n"
                             f"Filters: {', '.join(filters) if filters else 'None'}"
                    )
                except:
                    pass
            
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
    
    @staticmethod
    async def remove_background(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove image background (premium feature)"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        image_path = context.user_data.get('image_path')
        
        if not image_path:
            await query.edit_message_text("❌ No image found. Please upload again.")
            return ConversationHandler.END
        
        # Check premium status
        user_data = db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        if not is_premium:
            await query.edit_message_text(
                "❌ Background removal is a premium feature.\n\n"
                "Upgrade to premium to remove backgrounds!\n"
                "Use /premium to see plans."
            )
            return ConversationHandler.END
        
        await query.edit_message_text(
            "⏳ <b>Removing background...</b>\n\n"
            "This may take a few moments...",
            parse_mode=ParseMode.HTML
        )
        
        try:
            # Remove background
            output_path = image_processor.remove_background(image_path)
            
            # Send result
            with open(output_path, 'rb') as image_file:
                caption = (
                    f"✅ <b>Background removed successfully!</b>\n\n"
                    f"<b>Size:</b> {os.path.getsize(output_path) // 1024} KB\n\n"
                    f"<b>Need more edits?</b> Use /image again!"
                )
                
                await context.bot.send_photo(
                    chat_id=user.id,
                    photo=image_file,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            
        except Exception as e:
            logger.error(f"Background removal error: {e}")
            await query.edit_message_text(
                f"❌ <b>Error removing background</b>\n\n"
                f"{str(e)}\n\n"
                f"Please try again.",
                parse_mode=ParseMode.HTML
            )
        
        return ConversationHandler.END
    
    @staticmethod
    async def add_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add text to image"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "✏️ <b>Add Text to Image</b>\n\n"
            "Please send me the text you want to add:\n\n"
            "You can format your text with:\n"
            "• /bold - Bold text\n"
            "• /italic - Italic text\n"
            "• /color #RRGGBB - Text color\n"
            "• /size 24 - Font size\n\n"
            "Example: /color #ff0000 /size 32 Hello World!",
            parse_mode=ParseMode.HTML
        )
        
        return WAITING_FOR_TEXT
    
    @staticmethod
    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text input for adding to image"""
        user = update.effective_user
        text = update.message.text
        image_path = context.user_data.get('image_path')
        
        if not image_path:
            await update.message.reply_text("❌ No image found. Please upload again.")
            return ConversationHandler.END
        
        # Parse text formatting
        import re
        color = '#ffffff'
        size = 32
        content = text
        
        # Extract color
        color_match = re.search(r'/color (#[0-9a-fA-F]{6})', text)
        if color_match:
            color = color_match.group(1)
            content = re.sub(r'/color #[0-9a-fA-F]{6}', '', content).strip()
        
        # Extract size
        size_match = re.search(r'/size (\d+)', text)
        if size_match:
            size = int(size_match.group(1))
            content = re.sub(r'/size \d+', '', content).strip()
        
        # Remove formatting commands
        content = re.sub(r'/bold|/italic', '', content).strip()
        
        if not content:
            await update.message.reply_text("❌ Please enter some text to add.")
            return WAITING_FOR_TEXT
        
        await update.message.reply_text("⏳ Adding text to image...")
        
        try:
            # Add text to image
            output_path = image_processor.add_text(
                image_path, content, 
                font_size=size, 
                font_color=color
            )
            
            # Send result
            with open(output_path, 'rb') as image_file:
                await context.bot.send_photo(
                    chat_id=user.id,
                    photo=image_file,
                    caption=f"✅ Text added successfully!\n\nText: {content}",
                    parse_mode=ParseMode.HTML
                )
            
        except Exception as e:
            logger.error(f"Add text error: {e}")
            await update.message.reply_text(
                f"❌ Error adding text: {str(e)}\n\nPlease try again."
            )
        
        return ConversationHandler.END
    
    @staticmethod
    async def crop_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Crop image"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "✂️ <b>Crop Image</b>\n\n"
            "Please send me the crop coordinates in format:\n"
            "<code>x y width height</code>\n\n"
            "Example: <code>100 100 500 500</code>\n\n"
            "Where:\n"
            "• x - starting X coordinate\n"
            "• y - starting Y coordinate\n"
            "• width - crop width\n"
            "• height - crop height",
            parse_mode=ParseMode.HTML
        )
        
        return WAITING_FOR_CROP
    
    @staticmethod
    async def handle_crop(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle crop coordinates"""
        user = update.effective_user
        coords = update.message.text.split()
        image_path = context.user_data.get('image_path')
        
        if not image_path:
            await update.message.reply_text("❌ No image found. Please upload again.")
            return ConversationHandler.END
        
        if len(coords) != 4:
            await update.message.reply_text(
                "❌ Invalid coordinates. Please use format: x y width height\n"
                "Example: 100 100 500 500"
            )
            return WAITING_FOR_CROP
        
        try:
            x, y, width, height = map(int, coords)
        except ValueError:
            await update.message.reply_text("❌ Invalid numbers. Please use integers.")
            return WAITING_FOR_CROP
        
        await update.message.reply_text("⏳ Cropping image...")
        
        try:
            # Crop image
            output_path = image_processor.crop(image_path, x, y, width, height)
            
            # Send result
            with open(output_path, 'rb') as image_file:
                await context.bot.send_photo(
                    chat_id=user.id,
                    photo=image_file,
                    caption=f"✅ Image cropped successfully!\n\nCrop area: {x},{y} {width}x{height}",
                    parse_mode=ParseMode.HTML
                )
            
        except Exception as e:
            logger.error(f"Crop error: {e}")
            await update.message.reply_text(
                f"❌ Error cropping image: {str(e)}\n\nPlease try again."
            )
        
        return ConversationHandler.END
    
    @staticmethod
    async def show_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all available filters"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        user_data = db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        text = "✨ <b>Available Image Filters</b>\n\n"
        
        for filter_key, filter_info in ImageHandler.FILTERS.items():
            premium_badge = " ⭐" if filter_info['premium'] else ""
            text += f"• <b>{filter_info['name']}</b>{premium_badge}\n"
            if filter_info['premium'] and not is_premium:
                text += f"  <i>Premium feature - Upgrade to unlock</i>\n"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="image")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel image editing"""
        query = update.callback_query
        await query.answer()
        
        # Cleanup
        if 'image_path' in context.user_data and os.path.exists(context.user_data['image_path']):
            os.remove(context.user_data['image_path'])
        
        context.user_data.clear()
        
        await query.edit_message_text(
            "❌ Image editing cancelled.\n\n"
            "Use /start to return to main menu."
        )
        
        return ConversationHandler.END
