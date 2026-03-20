"""
Callback Handler - Handles all callback queries from inline keyboards
Author: @kinva_master
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from ..database import db
from ..config import Config
from ..handlers.start import StartHandler
from ..handlers.video import VideoHandler
from ..handlers.image import ImageHandler
from ..handlers.design import DesignHandler
from ..handlers.premium import PremiumHandler
from ..handlers.admin import AdminHandler

logger = logging.getLogger(__name__)

class CallbackHandler:
    """Handler for all callback queries"""
    
    @staticmethod
    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main callback handler - routes to appropriate handlers"""
        query = update.callback_query
        data = query.data
        user = update.effective_user
        
        logger.info(f"Callback received: {data} from user {user.id}")
        
        # ============================================
        # Navigation Callbacks
        # ============================================
        
        if data == "back":
            await CallbackHandler.back_to_main(update, context)
        
        elif data == "main_menu":
            await CallbackHandler.main_menu(update, context)
        
        elif data == "help":
            await StartHandler.handle_help(update, context)
        
        elif data == "contact":
            await StartHandler.handle_contact(update, context)
        
        # ============================================
        # Editor Callbacks
        # ============================================
        
        elif data == "video":
            await VideoHandler.start(update, context)
        
        elif data == "image":
            await ImageHandler.start(update, context)
        
        elif data == "design":
            await DesignHandler.start(update, context)
        
        elif data == "templates":
            await DesignHandler.show_templates(update, context)
        
        elif data.startswith("use_template_"):
            await DesignHandler.use_template(update, context)
        
        # ============================================
        # Design Management Callbacks
        # ============================================
        
        elif data == "my_designs":
            await DesignHandler.my_designs(update, context)
        
        elif data.startswith("edit_design_"):
            await DesignHandler.edit_design(update, context)
        
        elif data.startswith("export_design_"):
            await DesignHandler.export_design(update, context)
        
        elif data.startswith("delete_design_"):
            await DesignHandler.delete_design(update, context)
        
        elif data.startswith("confirm_delete_"):
            await DesignHandler.confirm_delete(update, context)
        
        elif data.startswith("share_design_"):
            await DesignHandler.share_design(update, context)
        
        # ============================================
        # Premium Callbacks
        # ============================================
        
        elif data == "premium":
            await PremiumHandler.start(update, context)
        
        elif data == "free_trial":
            await PremiumHandler.free_trial(update, context)
        
        elif data == "enter_promo":
            await PremiumHandler.enter_promo(update, context)
        
        elif data == "redeem_code":
            await PremiumHandler.redeem_code(update, context)
        
        elif data == "referral":
            await PremiumHandler.referral(update, context)
        
        elif data == "extend_premium":
            await PremiumHandler.extend_premium(update, context)
        
        elif data.startswith("select_plan_"):
            await PremiumHandler.select_plan(update, context)
        
        elif data.startswith("pay_upi_"):
            await PremiumHandler.process_upi_payment(update, context)
        
        elif data.startswith("pay_card_"):
            await PremiumHandler.process_razorpay_payment(update, context)
        
        elif data.startswith("pay_stripe_"):
            await PremiumHandler.process_stripe_payment(update, context)
        
        elif data.startswith("pay_paypal_"):
            await PremiumHandler.process_paypal_payment(update, context)
        
        elif data.startswith("pay_crypto_"):
            await PremiumHandler.process_crypto_payment(update, context)
        
        elif data.startswith("show_qr_"):
            await PremiumHandler.show_upi_qr(update, context)
        
        elif data.startswith("confirm_upi_"):
            await PremiumHandler.confirm_upi_payment(update, context)
        
        elif data.startswith("buy_with_discount_"):
            await PremiumHandler.buy_with_discount(update, context)
        
        # ============================================
        # Video Editor Callbacks
        # ============================================
        
        elif data == "upload_video":
            await VideoHandler.start(update, context)
        
        elif data == "effects_list":
            await VideoHandler.show_effects(update, context)
        
        elif data.startswith("effect_"):
            await VideoHandler.select_effect(update, context)
        
        elif data == "process_video":
            await VideoHandler.process_video(update, context)
        
        elif data == "compress_video":
            await VideoHandler.compress_video(update, context)
        
        # ============================================
        # Image Editor Callbacks
        # ============================================
        
        elif data == "upload_image":
            await ImageHandler.start(update, context)
        
        elif data == "filters_list":
            await ImageHandler.show_filters(update, context)
        
        elif data.startswith("filter_"):
            await ImageHandler.select_filter(update, context)
        
        elif data == "process_image":
            await ImageHandler.process_image(update, context)
        
        elif data == "remove_bg":
            await ImageHandler.remove_background(update, context)
        
        elif data == "remove_object":
            await ImageHandler.remove_object(update, context)
        
        elif data == "add_text":
            await ImageHandler.add_text(update, context)
        
        elif data == "crop_image":
            await ImageHandler.crop_image(update, context)
        
        # ============================================
        # Profile & Stats Callbacks
        # ============================================
        
        elif data == "profile":
            await StartHandler.handle_profile(update, context)
        
        elif data == "stats":
            await StartHandler.handle_stats(update, context)
        
        elif data == "settings":
            await StartHandler.handle_settings(update, context)
        
        elif data == "my_videos":
            await CallbackHandler.my_videos(update, context)
        
        elif data == "my_images":
            await CallbackHandler.my_images(update, context)
        
        elif data == "weekly_activity":
            await StartHandler.weekly_activity(update, context)
        
        elif data == "monthly_activity":
            await StartHandler.monthly_activity(update, context)
        
        # ============================================
        # Admin Callbacks
        # ============================================
        
        elif data.startswith("admin"):
            await AdminHandler.handle_admin_callback(update, context)
        
        # ============================================
        # General Callbacks
        # ============================================
        
        elif data == "cancel":
            await CallbackHandler.cancel_operation(update, context)
        
        elif data.startswith("copy_link_"):
            await CallbackHandler.copy_link(update, context)
        
        elif data.startswith("copy_upi_"):
            await CallbackHandler.copy_upi(update, context)
        
        elif data == "share":
            await CallbackHandler.share(update, context)
        
        elif data == "rate":
            await CallbackHandler.rate_bot(update, context)
        
        elif data == "feedback":
            await CallbackHandler.feedback(update, context)
        
        # ============================================
        # Unknown Callback
        # ============================================
        
        else:
            logger.warning(f"Unknown callback: {data}")
            await query.answer("Action not recognized", show_alert=True)
    
    @staticmethod
    async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Return to main menu"""
        query = update.callback_query
        user = update.effective_user
        
        # Clear context
        context.user_data.clear()
        
        # Get user data
        user_data = db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        exports_left = user_data.get('exports_left', 3) if user_data else 3
        
        text = (
            f"🎬 <b>Kinva Master</b>\n\n"
            f"Hello {user.first_name}! What would you like to do?\n\n"
            f"<b>Status:</b> {'⭐ Premium' if is_premium else '🆓 Free'}\n"
            f"<b>Exports left today:</b> {exports_left}\n"
        )
        
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
        
        if not is_premium:
            keyboard.insert(0, [InlineKeyboardButton("⭐ UPGRADE TO PREMIUM", callback_data="premium")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show main menu"""
        await CallbackHandler.back_to_main(update, context)
    
    @staticmethod
    async def my_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's videos"""
        query = update.callback_query
        user = update.effective_user
        
        videos = db.get_user_videos(user.id, limit=10)
        
        if not videos:
            text = "🎬 <b>My Videos</b>\n\nYou haven't edited any videos yet.\n\nUse /video to edit your first video!"
            
            keyboard = [
                [InlineKeyboardButton("🎬 Edit Video", callback_data="video")],
                [InlineKeyboardButton("🔙 Back", callback_data="profile")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            return
        
        text = "🎬 <b>My Videos</b>\n\n"
        
        for video in videos[:10]:
            text += f"🎥 <b>{video['title']}</b>\n"
            text += f"   📅 {video['created_at'][:10]}\n"
            if video.get('duration'):
                text += f"   ⏱️ {int(video['duration'])} seconds\n"
            if video.get('effects'):
                effects = json.loads(video['effects']) if isinstance(video['effects'], str) else video['effects']
                text += f"   🎨 Effects: {', '.join(effects[:3])}\n"
            text += "\n"
        
        keyboard = [
            [InlineKeyboardButton("🎬 Edit New", callback_data="video")],
            [InlineKeyboardButton("🔙 Back", callback_data="profile")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def my_images(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's images"""
        query = update.callback_query
        user = update.effective_user
        
        images = db.get_user_images(user.id, limit=10)
        
        if not images:
            text = "🖼️ <b>My Images</b>\n\nYou haven't edited any images yet.\n\nUse /image to edit your first image!"
            
            keyboard = [
                [InlineKeyboardButton("🖼️ Edit Image", callback_data="image")],
                [InlineKeyboardButton("🔙 Back", callback_data="profile")]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            return
        
        text = "🖼️ <b>My Images</b>\n\n"
        
        for image in images[:10]:
            text += f"📸 <b>{image['title']}</b>\n"
            text += f"   📅 {image['created_at'][:10]}\n"
            if image.get('width') and image.get('height'):
                text += f"   📐 {image['width']}x{image['height']}\n"
            if image.get('filters'):
                filters = json.loads(image['filters']) if isinstance(image['filters'], str) else image['filters']
                text += f"   🎨 Filters: {', '.join(filters[:3])}\n"
            text += "\n"
        
        keyboard = [
            [InlineKeyboardButton("🖼️ Edit New", callback_data="image")],
            [InlineKeyboardButton("🔙 Back", callback_data="profile")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel current operation"""
        query = update.callback_query
        await query.answer()
        
        # Cleanup any files in context
        if 'video_path' in context.user_data and os.path.exists(context.user_data['video_path']):
            os.remove(context.user_data['video_path'])
        if 'image_path' in context.user_data and os.path.exists(context.user_data['image_path']):
            os.remove(context.user_data['image_path'])
        
        context.user_data.clear()
        
        await query.edit_message_text(
            "❌ Operation cancelled.\n\n"
            "Use /start to return to main menu.",
            parse_mode=ParseMode.HTML
        )
    
    @staticmethod
    async def copy_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Copy link to clipboard"""
        query = update.callback_query
        link = query.data.replace('copy_link_', '')
        
        await query.answer("Link copied to clipboard!", show_alert=True)
        
        # Store in context for copying (handled by bot)
        context.user_data['copy_link'] = link
    
    @staticmethod
    async def copy_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Copy UPI ID to clipboard"""
        query = update.callback_query
        payment_id = query.data.replace('copy_upi_', '')
        
        payment = db.get_payment(payment_id)
        if payment:
            upi_id = "kinvamaster@okhdfcbank"
            await query.answer(f"UPI ID copied: {upi_id}", show_alert=True)
            context.user_data['copy_upi'] = upi_id
    
    @staticmethod
    async def share(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Share bot with friends"""
        query = update.callback_query
        await query.answer()
        
        text = (
            "📱 <b>Share Kinva Master</b>\n\n"
            "Invite your friends to use Kinva Master!\n\n"
            f"<b>Bot Link:</b> https://t.me/{Config.BOT_USERNAME}\n"
            f"<b>Website:</b> {Config.WEBAPP_URL}\n\n"
            "<b>Referral Rewards:</b>\n"
            "• Invite 1 friend: 7 days premium\n"
            "• Invite 3 friends: 1 month premium\n"
            "• Invite 5 friends: 3 months premium\n"
            "• Invite 10 friends: Lifetime premium!\n\n"
            "Share your unique referral link:"
        )
        
        referral_link = f"https://t.me/{Config.BOT_USERNAME}?start=ref_{update.effective_user.id}"
        
        keyboard = [
            [InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_link_{referral_link}")],
            [InlineKeyboardButton("📱 Share on Telegram", switch_inline_query=f"Try Kinva Master! {referral_link}")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text + f"\n\n<code>{referral_link}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    
    @staticmethod
    async def rate_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Rate the bot"""
        query = update.callback_query
        await query.answer()
        
        text = (
            "⭐ <b>Rate Kinva Master</b>\n\n"
            "If you enjoy using Kinva Master, please consider rating us!\n\n"
            "Your feedback helps us improve and reach more users.\n\n"
            "<b>Rating Options:</b>\n"
            "⭐ 1 Star - Needs improvement\n"
            "⭐⭐ 2 Stars - Could be better\n"
            "⭐⭐⭐ 3 Stars - Good\n"
            "⭐⭐⭐⭐ 4 Stars - Very Good\n"
            "⭐⭐⭐⭐⭐ 5 Stars - Excellent!\n\n"
            "Click a rating below:"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("⭐ 1", callback_data="rate_1"),
                InlineKeyboardButton("⭐⭐ 2", callback_data="rate_2"),
                InlineKeyboardButton("⭐⭐⭐ 3", callback_data="rate_3"),
                InlineKeyboardButton("⭐⭐⭐⭐ 4", callback_data="rate_4"),
                InlineKeyboardButton("⭐⭐⭐⭐⭐ 5", callback_data="rate_5")
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send feedback"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
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

# Import for web app
from telegram import WebAppInfo
