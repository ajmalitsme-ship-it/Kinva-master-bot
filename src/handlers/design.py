"""
Design Handler - Handles Canva-style design creation
Author: @kinva_master
"""

import os
import logging
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from ..database import db
from ..config import Config
from ..editors.canva_editor import canva_editor
from ..processors.watermark import watermark

logger = logging.getLogger(__name__)

class DesignHandler:
    """Handler for Canva-style design commands"""
    
    # Design templates
    TEMPLATES = {
        'youtube_thumbnail': {
            'name': '🎬 YouTube Thumbnail',
            'size': (1280, 720),
            'premium': False
        },
        'instagram_post': {
            'name': '📱 Instagram Post',
            'size': (1080, 1080),
            'premium': False
        },
        'instagram_story': {
            'name': '📖 Instagram Story',
            'size': (1080, 1920),
            'premium': False
        },
        'facebook_post': {
            'name': '👍 Facebook Post',
            'size': (1200, 630),
            'premium': False
        },
        'twitter_header': {
            'name': '🐦 Twitter Header',
            'size': (1500, 500),
            'premium': False
        },
        'linkedin_banner': {
            'name': '💼 LinkedIn Banner',
            'size': (1584, 396),
            'premium': False
        },
        'business_card': {
            'name': '💳 Business Card',
            'size': (1050, 600),
            'premium': True
        },
        'presentation': {
            'name': '📊 Presentation',
            'size': (1920, 1080),
            'premium': True
        },
        'flyer': {
            'name': '📄 Flyer',
            'size': (2550, 3300),
            'premium': True
        },
        'poster': {
            'name': '🎨 Poster',
            'size': (3300, 5100),
            'premium': True
        }
    }
    
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start design creation"""
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
            f"• 50+ premium templates{' (available)' if is_premium else ' - Upgrade to unlock'}\n"
            "• Advanced effects\n"
            "• Cloud storage\n\n"
            "Click the button below to start creating!"
        )
        
        keyboard = [
            [InlineKeyboardButton("🚀 Open Editor", web_app=WebAppInfo(url=f"{Config.WEBAPP_URL}/editor"))],
            [InlineKeyboardButton("📋 Templates", callback_data="design_templates")],
            [InlineKeyboardButton("📁 My Designs", callback_data="my_designs")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        if not is_premium:
            keyboard.insert(1, [InlineKeyboardButton("⭐ Unlock Premium Features", callback_data="premium")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def show_templates(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show available design templates"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        user_data = db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        text = "📋 <b>Design Templates</b>\n\n"
        
        # Group templates by premium status
        free_templates = []
        premium_templates = []
        
        for key, template in DesignHandler.TEMPLATES.items():
            if template['premium']:
                premium_templates.append((key, template))
            else:
                free_templates.append((key, template))
        
        text += "<b>Free Templates:</b>\n"
        for key, template in free_templates:
            size = f"{template['size'][0]}x{template['size'][1]}"
            text += f"• {template['name']} - {size}\n"
        
        if is_premium:
            text += "\n<b>⭐ Premium Templates:</b>\n"
            for key, template in premium_templates:
                size = f"{template['size'][0]}x{template['size'][1]}"
                text += f"• {template['name']} - {size}\n"
        else:
            text += f"\n⭐ <b>Premium Templates:</b> {len(premium_templates)} templates available\n"
            text += f"Upgrade to premium to unlock all templates!\n"
        
        # Create keyboard with template buttons
        keyboard = []
        for key, template in free_templates:
            keyboard.append([InlineKeyboardButton(
                template['name'], 
                callback_data=f"use_template_{key}"
            )])
        
        if is_premium:
            for key, template in premium_templates:
                keyboard.append([InlineKeyboardButton(
                    f"⭐ {template['name']}", 
                    callback_data=f"use_template_{key}"
                )])
        else:
            keyboard.append([InlineKeyboardButton("⭐ Upgrade to Premium", callback_data="premium")])
        
        keyboard.append([InlineKeyboardButton("🎨 Create Custom", callback_data="design")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="design")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def use_template(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Use a template for new design"""
        query = update.callback_query
        template_key = query.data.replace('use_template_', '')
        
        user = update.effective_user
        user_data = db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        template = DesignHandler.TEMPLATES.get(template_key)
        
        if not template:
            await query.answer("Template not found")
            return
        
        if template['premium'] and not is_premium:
            await query.answer("This template requires premium subscription!", show_alert=True)
            return
        
        # Store template in context
        context.user_data['current_template'] = template_key
        
        text = (
            f"✅ <b>Template selected: {template['name']}</b>\n\n"
            f"<b>Size:</b> {template['size'][0]}x{template['size'][1]}\n\n"
            f"Click the button below to open the editor with this template!\n\n"
            f"<b>What would you like to do next?</b>"
        )
        
        keyboard = [
            [InlineKeyboardButton("🚀 Open in Editor", web_app=WebAppInfo(url=f"{Config.WEBAPP_URL}/editor?template={template_key}"))],
            [InlineKeyboardButton("📋 Browse More Templates", callback_data="design_templates")],
            [InlineKeyboardButton("🎨 Custom Design", callback_data="design")],
            [InlineKeyboardButton("🔙 Back", callback_data="design")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def my_designs(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's saved designs"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        designs = db.get_user_designs(user.id, limit=10)
        
        if not designs:
            text = "📁 <b>My Designs</b>\n\nYou haven't created any designs yet.\n\nUse /editor to create your first design!"
            
            keyboard = [
                [InlineKeyboardButton("🎨 Create Design", callback_data="design")],
                [InlineKeyboardButton("📋 Browse Templates", callback_data="design_templates")],
                [InlineKeyboardButton("🔙 Back", callback_data="design")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            return
        
        text = "📁 <b>My Designs</b>\n\n"
        
        for i, design in enumerate(designs[:10], 1):
            text += f"{i}. <b>{design['title']}</b>\n"
            text += f"   📅 {design['created_at'][:10]}\n"
            text += f"   📐 {design.get('width', 1920)}x{design.get('height', 1080)}\n"
            text += f"   👁️ {design.get('views', 0)} views | ❤️ {design.get('likes', 0)} likes\n"
            text += f"   🔗 <a href='{design.get('share_url', '#')}'>View</a>\n\n"
        
        # Create keyboard with design buttons
        keyboard = []
        for i, design in enumerate(designs[:5]):
            keyboard.append([InlineKeyboardButton(
                f"✏️ Edit: {design['title'][:30]}", 
                callback_data=f"edit_design_{design['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("🎨 Create New", callback_data="design")])
        keyboard.append([InlineKeyboardButton("📋 Browse Templates", callback_data="design_templates")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="design")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    
    @staticmethod
    async def edit_design(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Edit existing design"""
        query = update.callback_query
        design_id = int(query.data.replace('edit_design_', ''))
        
        user = update.effective_user
        design = db.get_design(design_id)
        
        if not design or design['user_id'] != user.id:
            await query.answer("Design not found")
            return
        
        text = (
            f"✏️ <b>Editing: {design['title']}</b>\n\n"
            f"<b>Created:</b> {design['created_at'][:10]}\n"
            f"<b>Size:</b> {design.get('width', 1920)}x{design.get('height', 1080)}\n\n"
            f"Click the button below to open the editor with your design!"
        )
        
        keyboard = [
            [InlineKeyboardButton("✏️ Open in Editor", web_app=WebAppInfo(url=f"{Config.WEBAPP_URL}/editor?design={design_id}"))],
            [InlineKeyboardButton("📥 Export Design", callback_data=f"export_design_{design_id}")],
            [InlineKeyboardButton("🗑️ Delete Design", callback_data=f"delete_design_{design_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data="my_designs")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def export_design(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Export design as image"""
        query = update.callback_query
        design_id = int(query.data.replace('export_design_', ''))
        
        user = update.effective_user
        design = db.get_design(design_id)
        
        if not design or design['user_id'] != user.id:
            await query.answer("Design not found")
            return
        
        # Check premium status
        user_data = db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        # Check export limit
        if not is_premium:
            stats = db.get_user_stats(user.id)
            if stats.get('exports_today', 0) >= Config.FREE_DESIGN_EXPORTS:
                await query.answer(
                    "You've reached your daily export limit! Upgrade to premium for unlimited exports.",
                    show_alert=True
                )
                return
        
        await query.edit_message_text(
            "⏳ <b>Exporting design...</b>\n\n"
            "Please wait...",
            parse_mode=ParseMode.HTML
        )
        
        try:
            # Render design
            design_data = json.loads(design['design_data']) if isinstance(design['design_data'], str) else design['design_data']
            image = canva_editor.render(design_data)
            
            # Add watermark for free users
            if not is_premium:
                image = watermark.add_text_watermark(image)
            
            # Save to temporary file
            output_path = f"/tmp/design_{user.id}_{int(datetime.now().timestamp())}.png"
            image.save(output_path, format='PNG')
            
            # Send image
            with open(output_path, 'rb') as image_file:
                caption = (
                    f"✅ <b>Design exported successfully!</b>\n\n"
                    f"<b>Title:</b> {design['title']}\n"
                    f"<b>Size:</b> {image.width}x{image.height}\n"
                )
                
                if not is_premium:
                    caption += f"\n💧 <i>Watermark: @kinva_master.com</i>\n"
                    caption += f"⭐ Upgrade to premium to remove watermark!\n"
                
                await context.bot.send_photo(
                    chat_id=user.id,
                    photo=image_file,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            
            # Update stats
            db.increment_exports(user.id)
            
            # Cleanup
            os.remove(output_path)
            
        except Exception as e:
            logger.error(f"Design export error: {e}")
            await query.edit_message_text(
                f"❌ <b>Error exporting design</b>\n\n"
                f"{str(e)}\n\n"
                f"Please try again.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Return to design menu
        keyboard = [
            [InlineKeyboardButton("✏️ Edit Again", callback_data=f"edit_design_{design_id}")],
            [InlineKeyboardButton("🎨 Create New", callback_data="design")],
            [InlineKeyboardButton("🔙 Back", callback_data="my_designs")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "✅ <b>Design exported successfully!</b>\n\n"
            "What would you like to do next?",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def delete_design(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete design"""
        query = update.callback_query
        design_id = int(query.data.replace('delete_design_', ''))
        
        user = update.effective_user
        design = db.get_design(design_id)
        
        if not design or design['user_id'] != user.id:
            await query.answer("Design not found")
            return
        
        # Confirm deletion
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, Delete", callback_data=f"confirm_delete_{design_id}"),
                InlineKeyboardButton("❌ No, Cancel", callback_data=f"edit_design_{design_id}")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"⚠️ <b>Delete Design</b>\n\n"
            f"Are you sure you want to delete '{design['title']}'?\n\n"
            f"This action cannot be undone.",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm design deletion"""
        query = update.callback_query
        design_id = int(query.data.replace('confirm_delete_', ''))
        
        user = update.effective_user
        design = db.get_design(design_id)
        
        if not design or design['user_id'] != user.id:
            await query.answer("Design not found")
            return
        
        # Delete design
        db.delete_design(design_id)
        
        await query.answer("Design deleted successfully!")
        
        # Show my designs
        await DesignHandler.my_designs(update, context)
    
    @staticmethod
    async def share_design(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Share design link"""
        query = update.callback_query
        design_id = int(query.data.replace('share_design_', ''))
        
        user = update.effective_user
        design = db.get_design(design_id)
        
        if not design or design['user_id'] != user.id:
            await query.answer("Design not found")
            return
        
        # Generate share link
        share_url = f"{Config.WEBAPP_URL}/design/{design_id}"
        
        # Update share count
        db.increment_design_shares(design_id)
        
        text = (
            f"🔗 <b>Share Your Design</b>\n\n"
            f"<b>Title:</b> {design['title']}\n\n"
            f"Share this link with others:\n"
            f"<code>{share_url}</code>\n\n"
            f"Or copy and share the text below:\n\n"
            f"<b>Check out my design on Kinva Master!</b>\n"
            f"{share_url}"
        )
        
        keyboard = [
            [InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_link_{design_id}")],
            [InlineKeyboardButton("📱 Share on Telegram", switch_inline_query=f"Check out my design: {share_url}")],
            [InlineKeyboardButton("🔙 Back", callback_data=f"edit_design_{design_id}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def create_from_webapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create design from web app callback"""
        # This is called when user creates a design in web app
        # Web app sends design data via callback
        data = update.callback_query.data
        
        if data.startswith("design_saved_"):
            design_id = int(data.replace("design_saved_", ""))
            user = update.effective_user
            
            await update.callback_query.answer("Design saved successfully!")
            
            # Send confirmation
            text = (
                f"✅ <b>Design Saved!</b>\n\n"
                f"Your design has been saved successfully.\n\n"
                f"You can view it in <b>My Designs</b> or continue editing."
            )
            
            keyboard = [
                [InlineKeyboardButton("🎨 Continue Editing", web_app=WebAppInfo(url=f"{Config.WEBAPP_URL}/editor?design={design_id}"))],
                [InlineKeyboardButton("📁 View My Designs", callback_data="my_designs")],
                [InlineKeyboardButton("🔙 Main Menu", callback_data="back")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
