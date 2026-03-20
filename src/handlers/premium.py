"""
Premium Handler - Handles premium subscriptions and payments
Author: @kinva_master
Updated: 2026
"""

import logging
import json
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from ..database import db
from ..config import Config

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_PAYMENT = 1
WAITING_FOR_PROMO = 2
WAITING_FOR_UPI = 3
WAITING_FOR_REDEEM = 4
WAITING_FOR_UPI_PAYMENT = 5
WAITING_FOR_QR_SCAN = 6

class PremiumHandler:
    """Handler for premium subscriptions"""
    
    # Premium plans with multiple currency support
    PLANS = {
        'monthly': {
            'id': 'monthly',
            'name': '📅 Monthly Plan',
            'price_usd': 14.99,
            'price_inr': 499,
            'price_gbp': 11.99,
            'price_eur': 13.99,
            'price_aed': 55,
            'price_sgd': 20,
            'price_myr': 65,
            'interval': 'month',
            'features': [
                '✓ 4K Video Export',
                '✓ No Watermark',
                '✓ All Filters & Effects',
                '✓ Unlimited Exports',
                '✓ Priority Support',
                '✓ 10GB Cloud Storage',
                '✓ 24/7 Support'
            ],
            'popular': False,
            'discount': 0
        },
        'quarterly': {
            'id': 'quarterly',
            'name': '📆 Quarterly Plan',
            'price_usd': 39.99,
            'price_inr': 1299,
            'price_gbp': 31.99,
            'price_eur': 36.99,
            'price_aed': 147,
            'price_sgd': 53,
            'price_myr': 170,
            'interval': 'quarter',
            'features': [
                '✓ 4K Video Export',
                '✓ No Watermark',
                '✓ All Filters & Effects',
                '✓ Unlimited Exports',
                '✓ Priority Support',
                '✓ 10GB Cloud Storage',
                '✓ 24/7 Support',
                '✓ Save 10% vs Monthly'
            ],
            'popular': False,
            'discount': 10
        },
        'yearly': {
            'id': 'yearly',
            'name': '🎉 Yearly Plan',
            'price_usd': 119.99,
            'price_inr': 3999,
            'price_gbp': 95.99,
            'price_eur': 109.99,
            'price_aed': 440,
            'price_sgd': 160,
            'price_myr': 520,
            'interval': 'year',
            'features': [
                '✓ 4K Video Export',
                '✓ No Watermark',
                '✓ All Filters & Effects',
                '✓ Unlimited Exports',
                '✓ Priority Support',
                '✓ 10GB Cloud Storage',
                '✓ 24/7 Support',
                '✓ 2 Months Free',
                '✓ Save 20% vs Monthly'
            ],
            'popular': True,
            'discount': 20
        },
        'lifetime': {
            'id': 'lifetime',
            'name': '💎 Lifetime Plan',
            'price_usd': 299.99,
            'price_inr': 9999,
            'price_gbp': 239.99,
            'price_eur': 274.99,
            'price_aed': 1100,
            'price_sgd': 400,
            'price_myr': 1300,
            'interval': 'once',
            'features': [
                '✓ 4K Video Export',
                '✓ No Watermark',
                '✓ All Filters & Effects',
                '✓ Unlimited Exports',
                '✓ Priority Support Forever',
                '✓ 50GB Cloud Storage',
                '✓ Lifetime Updates',
                '✓ API Access',
                '✓ White-label Export'
            ],
            'popular': False,
            'discount': 0
        }
    }
    
    # Indian Payment Methods (UPI)
    UPI_APPS = {
        'googlepay': {
            'name': 'Google Pay',
            'upi_id': 'kinvamaster@okhdfcbank',
            'icon': '📱',
            'qr_code': 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa=kinvamaster@okhdfcbank&pn=Kinva%20Master&am=0&cu=INR'
        },
        'phonepe': {
            'name': 'PhonePe',
            'upi_id': 'kinvamaster@ybl',
            'icon': '📱',
            'qr_code': 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa=kinvamaster@ybl&pn=Kinva%20Master&am=0&cu=INR'
        },
        'paytm': {
            'name': 'Paytm',
            'upi_id': 'kinvamaster@paytm',
            'icon': '📱',
            'qr_code': 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa=kinvamaster@paytm&pn=Kinva%20Master&am=0&cu=INR'
        },
        'bhim': {
            'name': 'BHIM UPI',
            'upi_id': 'kinvamaster@upi',
            'icon': '📱',
            'qr_code': 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa=kinvamaster@upi&pn=Kinva%20Master&am=0&cu=INR'
        }
    }
    
    # International Payment Methods
    INTERNATIONAL_PAYMENTS = {
        'stripe': {
            'name': 'Credit/Debit Card (Visa, Mastercard, Amex)',
            'icon': '💳',
            'currencies': ['USD', 'EUR', 'GBP', 'AED', 'SGD', 'MYR']
        },
        'paypal': {
            'name': 'PayPal',
            'icon': '🅿️',
            'currencies': ['USD', 'EUR', 'GBP', 'AUD', 'CAD', 'JPY']
        },
        'crypto': {
            'name': 'Cryptocurrency (BTC, ETH, USDT)',
            'icon': '₿',
            'currencies': ['BTC', 'ETH', 'USDT']
        }
    }
    
    # Redeem codes database
    REDEEM_CODES = {
        # Discount Codes
        'KINVA50': {'discount': 50, 'type': 'percent', 'uses_left': 100, 'expiry': '2026-12-31', 'min_amount': 0},
        'KINVA100': {'discount': 100, 'type': 'fixed', 'uses_left': 50, 'expiry': '2026-12-31', 'min_amount': 0},
        'FESTIVAL30': {'discount': 30, 'type': 'percent', 'uses_left': 200, 'expiry': '2026-01-15', 'min_amount': 500},
        'DIWALI50': {'discount': 50, 'type': 'percent', 'uses_left': 150, 'expiry': '2026-11-15', 'min_amount': 1000},
        'NEWYEAR25': {'discount': 25, 'type': 'percent', 'uses_left': 300, 'expiry': '2026-01-31', 'min_amount': 0},
        'SUMMER20': {'discount': 20, 'type': 'percent', 'uses_left': 500, 'expiry': '2026-06-30', 'min_amount': 0},
        
        # Special Codes
        'STUDENT40': {'discount': 40, 'type': 'percent', 'uses_left': 500, 'expiry': '2026-12-31', 'min_amount': 0, 'requires_verification': True},
        'TEACHER30': {'discount': 30, 'type': 'percent', 'uses_left': 500, 'expiry': '2026-12-31', 'min_amount': 0, 'requires_verification': True},
        'CREATOR20': {'discount': 20, 'type': 'percent', 'uses_left': 1000, 'expiry': '2026-12-31', 'min_amount': 0},
        'WELCOME50': {'discount': 50, 'type': 'percent', 'uses_left': 500, 'expiry': '2026-06-30', 'min_amount': 0},
        'FRIEND10': {'discount': 10, 'type': 'percent', 'uses_left': 1000, 'expiry': '2026-12-31', 'min_amount': 0},
        
        # Gift Cards
        'GIFT100': {'discount': 100, 'type': 'fixed', 'uses_left': 200, 'expiry': '2026-12-31', 'min_amount': 0, 'is_gift': True},
        'GIFT500': {'discount': 500, 'type': 'fixed', 'uses_left': 100, 'expiry': '2026-12-31', 'min_amount': 0, 'is_gift': True},
        'GIFT1000': {'discount': 1000, 'type': 'fixed', 'uses_left': 50, 'expiry': '2026-12-31', 'min_amount': 0, 'is_gift': True},
        
        # Premium Codes
        'PREMIUM7': {'days': 7, 'type': 'trial', 'uses_left': 1000, 'expiry': '2026-12-31'},
        'PREMIUM30': {'days': 30, 'type': 'subscription', 'uses_left': 500, 'expiry': '2026-12-31'},
        'PREMIUM365': {'days': 365, 'type': 'subscription', 'uses_left': 100, 'expiry': '2026-12-31'},
        'LIFETIME': {'days': 9999, 'type': 'lifetime', 'uses_left': 50, 'expiry': '2026-12-31'},
    }
    
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start premium menu"""
        user = update.effective_user
        user_data = db.get_user(user.id)
        is_premium = user_data.get('is_premium', False) if user_data else False
        
        if is_premium:
            await PremiumHandler.show_premium_dashboard(update, context)
        else:
            await PremiumHandler.show_pricing(update, context)
    
    @staticmethod
    async def show_pricing(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show pricing plans with multiple currencies"""
        query = update.callback_query if update.callback_query else update
        is_callback = update.callback_query is not None
        
        # Detect user's country (simplified)
        user = update.effective_user
        user_data = db.get_user(user.id)
        country = user_data.get('country', 'IN') if user_data else 'IN'
        
        # Set currency based on country
        if country == 'IN':
            currency = 'INR'
            currency_symbol = '₹'
            get_price = lambda p: p['price_inr']
        elif country in ['AE', 'SA', 'QA', 'KW', 'OM', 'BH']:
            currency = 'AED'
            currency_symbol = 'د.إ'
            get_price = lambda p: p['price_aed']
        elif country in ['SG', 'MY']:
            currency = country == 'SG' and 'SGD' or 'MYR'
            currency_symbol = country == 'SG' and 'S$' or 'RM'
            get_price = lambda p: p['price_sgd'] if country == 'SG' else p['price_myr']
        elif country in ['GB', 'UK']:
            currency = 'GBP'
            currency_symbol = '£'
            get_price = lambda p: p['price_gbp']
        elif country in ['DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'AT', 'CH']:
            currency = 'EUR'
            currency_symbol = '€'
            get_price = lambda p: p['price_eur']
        else:
            currency = 'USD'
            currency_symbol = '$'
            get_price = lambda p: p['price_usd']
        
        text = (
            f"⭐ <b>Upgrade to Premium - {currency} Pricing</b>\n\n"
            f"Get unlimited access to all professional features!\n\n"
            f"<b>🇮🇳 Indian Users:</b> Special INR pricing with UPI, Cards, Net Banking\n"
            f"<b>🌍 International Users:</b> Pay in your local currency\n\n"
        )
        
        # Add plans with local pricing
        for plan_id, plan in PremiumHandler.PLANS.items():
            popular_badge = " 🔥" if plan.get('popular', False) else ""
            price = get_price(plan)
            text += f"<b>{plan['name']}{popular_badge}</b>\n"
            text += f"💰 <b>{currency_symbol}{price}</b> per {plan['interval']}\n"
            text += f"✨ Features:\n"
            for feature in plan['features'][:6]:
                text += f"   {feature}\n"
            if len(plan['features']) > 6:
                text += f"   ... and {len(plan['features']) - 6} more\n"
            if plan.get('discount', 0) > 0:
                text += f"   💰 Save {plan['discount']}% vs monthly\n"
            text += "\n"
        
        text += (
            f"<b>🎁 Special Offers:</b>\n"
            f"• First month 50% off for new users!\n"
            f"• Student/Teacher discount: 40% off with valid ID\n"
            f"• Referral program: Get 1 month free per referral\n"
            f"• Festival offers: Up to 50% off\n\n"
            f"<b>💳 Accepted Payment Methods:</b>\n"
            f"• 🇮🇳 India: UPI (GPay, PhonePe, Paytm), Cards, NetBanking\n"
            f"• 🌍 International: Credit/Debit Cards, PayPal, Crypto\n\n"
            f"<b>🔒 Secure Payments:</b> RBI-compliant & PCI-DSS certified\n\n"
            f"<b>❓ Questions?</b> Contact @{Config.ADMIN_CONTACT}"
        )
        
        # Create keyboard with plan buttons
        keyboard = []
        for plan_id, plan in PremiumHandler.PLANS.items():
            popular_badge = " 🔥" if plan.get('popular', False) else ""
            price = get_price(plan)
            keyboard.append([InlineKeyboardButton(
                f"{plan['name']}{popular_badge} - {currency_symbol}{price}", 
                callback_data=f"select_plan_{plan_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🎁 Try 7-Day Free Trial", callback_data="free_trial")])
        keyboard.append([InlineKeyboardButton("🎟️ Redeem Code / Gift Card", callback_data="redeem_code")])
        keyboard.append([InlineKeyboardButton("📞 Contact Support", callback_data="contact")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if is_callback:
            await query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
    
    @staticmethod
    async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle plan selection with multiple payment options"""
        query = update.callback_query
        plan_id = query.data.replace('select_plan_', '')
        
        plan = PremiumHandler.PLANS.get(plan_id)
        if not plan:
            await query.answer("Plan not found")
            return
        
        context.user_data['selected_plan'] = plan_id
        context.user_data['plan_amount'] = plan['price_inr']
        
        # Detect user's country
        user = update.effective_user
        user_data = db.get_user(user.id)
        country = user_data.get('country', 'IN') if user_data else 'IN'
        
        text = (
            f"💳 <b>Choose Payment Method</b>\n\n"
            f"<b>Plan:</b> {plan['name']}\n"
            f"<b>Amount:</b> ₹{plan['price_inr']} / {plan['interval']}\n\n"
            f"<b>Select your preferred payment method:</b>\n\n"
        )
        
        keyboard = []
        
        # Indian payment methods
        if country == 'IN':
            text += "<b>🇮🇳 Indian Payment Methods:</b>\n"
            keyboard.append([InlineKeyboardButton("📱 UPI (Google Pay, PhonePe, Paytm)", callback_data=f"pay_upi_{plan_id}")])
            keyboard.append([InlineKeyboardButton("💳 Credit/Debit Card (Razorpay)", callback_data=f"pay_card_{plan_id}")])
            keyboard.append([InlineKeyboardButton("🏦 Net Banking (All Banks)", callback_data=f"pay_netbanking_{plan_id}")])
            keyboard.append([InlineKeyboardButton("👛 Mobile Wallet (Paytm, PhonePe)", callback_data=f"pay_wallet_{plan_id}")])
        
        # International payment methods
        text += "\n<b>🌍 International Payment Methods:</b>\n"
        keyboard.append([InlineKeyboardButton("💳 Credit/Debit Card (Stripe)", callback_data=f"pay_stripe_{plan_id}")])
        keyboard.append([InlineKeyboardButton("🅿️ PayPal", callback_data=f"pay_paypal_{plan_id}")])
        keyboard.append([InlineKeyboardButton("₿ Cryptocurrency (BTC, ETH, USDT)", callback_data=f"pay_crypto_{plan_id}")])
        
        keyboard.append([InlineKeyboardButton("🎁 Apply Promo Code", callback_data="enter_promo")])
        keyboard.append([InlineKeyboardButton("🎟️ Redeem Gift Card", callback_data="redeem_code")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="premium")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def process_upi_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process UPI payment (Indian users)"""
        query = update.callback_query
        plan_id = query.data.split('_')[2]
        
        user = update.effective_user
        plan = PremiumHandler.PLANS.get(plan_id)
        
        if not plan:
            await query.answer("Plan not found")
            return
        
        context.user_data['payment_method'] = 'upi'
        context.user_data['payment_amount'] = plan['price_inr']
        
        # Create payment record
        payment_id = f"UPI_{user.id}_{int(datetime.now().timestamp())}"
        db.create_payment_record(
            user_id=user.id,
            amount=plan['price_inr'],
            currency='INR',
            payment_id=payment_id,
            plan_id=plan_id,
            method='upi',
            status='pending'
        )
        
        text = (
            f"📱 <b>UPI Payment - ₹{plan['price_inr']}</b>\n\n"
            f"<b>Plan:</b> {plan['name']}\n"
            f"<b>Amount:</b> ₹{plan['price_inr']}\n"
            f"<b>Payment ID:</b> <code>{payment_id}</code>\n\n"
            f"<b>Choose your UPI app and scan the QR code:</b>\n\n"
        )
        
        # Show UPI options
        keyboard = []
        for app_id, app in PremiumHandler.UPI_APPS.items():
            keyboard.append([InlineKeyboardButton(
                f"{app['icon']} {app['name']}", 
                callback_data=f"show_qr_{app_id}_{payment_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("📋 Copy UPI ID", callback_data=f"copy_upi_{payment_id}")])
        keyboard.append([InlineKeyboardButton("✅ I've Made Payment", callback_data=f"confirm_upi_{payment_id}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=f"select_plan_{plan_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def show_upi_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show UPI QR code for payment"""
        query = update.callback_query
        app_id = query.data.split('_')[2]
        payment_id = query.data.split('_')[3]
        
        app = PremiumHandler.UPI_APPS.get(app_id)
        if not app:
            await query.answer("App not found")
            return
        
        payment = db.get_payment(payment_id)
        if not payment:
            await query.answer("Payment not found")
            return
        
        amount = payment['amount']
        
        # Generate QR code URL with amount
        qr_data = f"upi://pay?pa={app['upi_id']}&pn=Kinva%20Master&am={amount}&cu=INR"
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={qr_data}"
        
        text = (
            f"📱 <b>Scan QR Code to Pay</b>\n\n"
            f"<b>App:</b> {app['name']}\n"
            f"<b>Amount:</b> ₹{amount}\n"
            f"<b>Payment ID:</b> <code>{payment_id}</code>\n\n"
            f"<b>UPI ID:</b> <code>{app['upi_id']}</code>\n\n"
            f"<b>Instructions:</b>\n"
            f"1. Open {app['name']} app\n"
            f"2. Scan the QR code below\n"
            f"3. Enter amount: ₹{amount}\n"
            f"4. Add note: {payment_id}\n"
            f"5. Complete payment\n\n"
            f"After payment, click 'I've Made Payment' to confirm."
        )
        
        keyboard = [
            [InlineKeyboardButton("📱 Open UPI App", url=f"upi://pay?pa={app['upi_id']}&pn=Kinva%20Master&am={amount}&cu=INR")],
            [InlineKeyboardButton("📋 Copy UPI ID", callback_data=f"copy_upi_{payment_id}")],
            [InlineKeyboardButton("✅ I've Made Payment", callback_data=f"confirm_upi_{payment_id}")],
            [InlineKeyboardButton("🔙 Back", callback_data=f"pay_upi_{payment['plan_id']}")]
        ]
        
        # Send QR code image
        await context.bot.send_photo(
            chat_id=user.id,
            photo=qr_url,
            caption=text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        await query.delete_message()
    
    @staticmethod
    async def confirm_upi_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm UPI payment"""
        query = update.callback_query
        payment_id = query.data.replace('confirm_upi_', '')
        
        user = update.effective_user
        payment = db.get_payment(payment_id)
        
        if not payment:
            await query.answer("Payment not found")
            return
        
        await query.edit_message_text(
            "⏳ <b>Verifying payment...</b>\n\n"
            "Please wait while we verify your payment.\n"
            "This may take 2-3 minutes...",
            parse_mode=ParseMode.HTML
        )
        
        # Simulate verification (in production, check with bank)
        import asyncio
        await asyncio.sleep(3)
        
        # Update payment status
        db.update_payment_status(payment_id, 'completed')
        
        # Activate premium
        plan = PremiumHandler.PLANS.get(payment['plan_id'])
        if plan:
            if plan['interval'] == 'month':
                months = 1
            elif plan['interval'] == 'quarter':
                months = 3
            elif plan['interval'] == 'year':
                months = 12
            else:
                months = 0
                premium_until = datetime.now() + timedelta(days=365*10)  # Lifetime
                db.activate_premium(user.id, months=months, lifetime=True)
            else:
                db.activate_premium(user.id, months=months)
        
        text = (
            f"✅ <b>Payment Confirmed!</b>\n\n"
            f"Congratulations! Your premium subscription is now active.\n\n"
            f"<b>Plan:</b> {plan['name']}\n"
            f"<b>Valid until:</b> {db.get_user(user.id).get('premium_until', 'Active')}\n\n"
            f"<b>🎉 What's Next?</b>\n"
            f"• Start creating with 4K video export\n"
            f"• No more watermarks\n"
            f"• Access all premium filters\n"
            f"• Enjoy unlimited exports\n\n"
            f"<b>Need help?</b> Contact @{Config.ADMIN_CONTACT}"
        )
        
        keyboard = [
            [InlineKeyboardButton("🎬 Edit Video", callback_data="video")],
            [InlineKeyboardButton("🖼️ Edit Image", callback_data="image")],
            [InlineKeyboardButton("🎨 Design", callback_data="design")],
            [InlineKeyboardButton("📋 Templates", callback_data="templates")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def redeem_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle redeem code / gift card"""
        query = update.callback_query
        
        text = (
            "🎟️ <b>Redeem Code / Gift Card</b>\n\n"
            "Enter your redeem code or gift card code below.\n\n"
            "<b>Types of codes you can redeem:</b>\n"
            "• Discount Codes (KINVA50, FESTIVAL30, etc.)\n"
            "• Gift Cards (GIFT100, GIFT500, GIFT1000)\n"
            "• Premium Codes (PREMIUM7, PREMIUM30, PREMIUM365, LIFETIME)\n"
            "• Student/Teacher Codes (STUDENT40, TEACHER30)\n\n"
            "<b>Where to get codes?</b>\n"
            "• Social media giveaways\n"
            "• Referral program rewards\n"
            "• Festival offers\n"
            "• Purchase gift cards from our website\n\n"
            "Enter your code below:"
        )
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML
        )
        
        return WAITING_FOR_REDEEM
    
    @staticmethod
    async def handle_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle redeem code input"""
        user = update.effective_user
        code = update.message.text.strip().upper()
        
        # Check if code exists
        redeem = PremiumHandler.REDEEM_CODES.get(code)
        
        if not redeem:
            await update.message.reply_text(
                "❌ <b>Invalid Code</b>\n\n"
                "The code you entered is invalid or expired.\n\n"
                "Please check and try again, or contact support for assistance.",
                parse_mode=ParseMode.HTML
            )
            return WAITING_FOR_REDEEM
        
        # Check expiry
        if redeem.get('expiry'):
            expiry_date = datetime.strptime(redeem['expiry'], '%Y-%m-%d')
            if expiry_date < datetime.now():
                await update.message.reply_text(
                    "❌ <b>Code Expired</b>\n\n"
                    "This code has expired.\n\n"
                    "Please check for active codes or contact support.",
                    parse_mode=ParseMode.HTML
                )
                return WAITING_FOR_REDEEM
        
        # Check uses left
        if redeem.get('uses_left', 0) <= 0:
            await update.message.reply_text(
                "❌ <b>Code Used Up</b>\n\n"
                "This code has reached its maximum usage limit.\n\n"
                "Please try another code.",
                parse_mode=ParseMode.HTML
            )
            return WAITING_FOR_REDEEM
        
        # Check if user already used this code
        if db.has_user_used_code(user.id, code):
            await update.message.reply_text(
                "❌ <b>Code Already Used</b>\n\n"
                "You have already used this code.\n\n"
                "Each code can only be used once per user.",
                parse_mode=ParseMode.HTML
            )
            return WAITING_FOR_REDEEM
        
        # Process based on code type
        if redeem.get('type') == 'trial':
            # Free trial
            days = redeem.get('days', 7)
            db.activate_premium(user.id, months=0, trial_days=days)
            
            await update.message.reply_text(
                f"🎉 <b>Code Redeemed Successfully!</b>\n\n"
                f"You've received a {days}-day premium trial!\n\n"
                f"<b>Your Benefits:</b>\n"
                f"✓ 4K Video Export\n"
                f"✓ No Watermark\n"
                f"✓ All Filters & Effects\n"
                f"✓ Unlimited Exports\n\n"
                f"Enjoy your premium access!",
                parse_mode=ParseMode.HTML
            )
            
        elif redeem.get('type') == 'subscription':
            # Premium subscription
            days = redeem.get('days', 30)
            db.extend_premium(user.id, days=days)
            
            await update.message.reply_text(
                f"🎉 <b>Code Redeemed Successfully!</b>\n\n"
                f"You've received {days} days of premium access!\n\n"
                f"<b>Your Benefits:</b>\n"
                f"✓ 4K Video Export\n"
                f"✓ No Watermark\n"
                f"✓ All Filters & Effects\n"
                f"✓ Unlimited Exports\n\n"
                f"Enjoy your premium access!",
                parse_mode=ParseMode.HTML
            )
            
        elif redeem.get('type') == 'lifetime':
            # Lifetime premium
            db.activate_lifetime_premium(user.id)
            
            await update.message.reply_text(
                f"🎉 <b>Congratulations! Lifetime Premium Activated!</b>\n\n"
                f"You've received LIFETIME premium access!\n\n"
                f"<b>Your Lifetime Benefits:</b>\n"
                f"✓ 4K Video Export Forever\n"
                f"✓ No Watermark Ever\n"
                f"✓ All Filters & Effects\n"
                f"✓ Unlimited Exports\n"
                f"✓ Priority Support Forever\n"
                f"✓ Lifetime Updates\n\n"
                f"Thank you for being a valued member!",
                parse_mode=ParseMode.HTML
            )
            
        elif redeem.get('is_gift'):
            # Gift card
            amount = redeem.get('discount', 0)
            db.add_wallet_balance(user.id, amount)
            
            await update.message.reply_text(
                f"🎁 <b>Gift Card Redeemed!</b>\n\n"
                f"₹{amount} has been added to your wallet!\n\n"
                f"<b>Wallet Balance:</b> ₹{db.get_wallet_balance(user.id)}\n\n"
                f"You can use this balance to purchase premium subscriptions.",
                parse_mode=ParseMode.HTML
            )
            
        else:
            # Discount code
            discount = redeem.get('discount', 0)
            discount_type = redeem.get('type', 'percent')
            
            # Store discount in session
            context.user_data['discount_code'] = code
            context.user_data['discount_amount'] = discount
            context.user_data['discount_type'] = discount_type
            
            await update.message.reply_text(
                f"🎉 <b>Code Applied!</b>\n\n"
                f"<b>Code:</b> {code}\n"
                f"<b>Discount:</b> {discount}% off\n\n"
                f"Now select a plan to apply your discount:",
                parse_mode=ParseMode.HTML
            )
            
            # Show plans with discount
            await PremiumHandler.show_plans_with_discount(update, context)
        
        # Update code usage
        db.increment_code_usage(code)
        db.record_user_code(user.id, code)
        
        return ConversationHandler.END
    
    @staticmethod
    async def show_plans_with_discount(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show plans with discount applied"""
        discount = context.user_data.get('discount_amount', 0)
        discount_type = context.user_data.get('discount_type', 'percent')
        
        text = f"⭐ <b>Premium Plans with {discount}% Discount</b>\n\n"
        
        keyboard = []
        for plan_id, plan in PremiumHandler.PLANS.items():
            if discount_type == 'percent':
                discounted_price = plan['price_inr'] * (1 - discount / 100)
            else:
                discounted_price = max(0, plan['price_inr'] - discount)
            
            popular_badge = " 🔥" if plan.get('popular', False) else ""
            text += f"<b>{plan['name']}{popular_badge}</b>\n"
            text += f"💰 <s>₹{plan['price_inr']}</s> → <b>₹{int(discounted_price)}</b>\n"
            text += f"✨ {plan['interval']} access\n\n"
            
            keyboard.append([InlineKeyboardButton(
                f"{plan['name']} - ₹{int(discounted_price)}", 
                callback_data=f"buy_with_discount_{plan_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Cancel", callback_data="premium")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def free_trial(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start free trial"""
        query = update.callback_query
        user = update.effective_user
        
        user_data = db.get_user(user.id)
        
        if user_data and user_data.get('trial_used', False):
            await query.answer("You've already used your free trial!", show_alert=True)
            return
        
        # Activate 7-day trial
        db.activate_premium(user.id, months=0, trial=True)
        
        text = (
            "🎉 <b>Free Trial Activated!</b>\n\n"
            "You now have 7 days of premium access!\n\n"
            "<b>🎁 Trial Benefits:</b>\n"
            "✓ 4K Video Export\n"
            "✓ No Watermark\n"
            "✓ All Filters & Effects\n"
            "✓ Unlimited Exports\n"
            "✓ Priority Support\n\n"
            "<b>⏰ Trial ends in 7 days.</b>\n"
            "Upgrade to keep premium benefits!\n\n"
            "Start creating now and experience the full power of Kinva Master!"
        )
        
        keyboard = [
            [InlineKeyboardButton("🎬 Edit Video", callback_data="video")],
            [InlineKeyboardButton("🖼️ Edit Image", callback_data="image")],
            [InlineKeyboardButton("🎨 Design", callback_data="design")],
            [InlineKeyboardButton("⭐ Upgrade Now", callback_data="premium")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    @staticmethod
    async def show_premium_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show premium user dashboard"""
        user = update.effective_user
        user_data = db.get_user(user.id)
        
        is_premium = user_data.get('is_premium', False)
        premium_until = user_data.get('premium_until', 'Active')
        plan = user_data.get('premium_plan', 'Premium')
        
        # Check if lifetime
        if premium_until == 'Lifetime':
            premium_display = 'Lifetime (Forever)'
        else:
            premium_display = premium_until[:10] if premium_until else 'Active'
        
        # Get stats
        stats = db.get_user_stats(user.id)
        
        text = (
            f"⭐ <b>Premium Dashboard</b>\n\n"
            f"<b>Status:</b> ✅ Active\n"
            f"<b>Plan:</b> {plan}\n"
            f"<b>Valid until:</b> {premium_display}\n\n"
            f"<b>📊 Your Usage:</b>\n"
            f"• Exports this month: {stats.get('exports_this_month', 0)}\n"
            f"• Storage used: {stats.get('storage_used', 0)} MB / {stats.get('storage_limit', 10240)} MB\n"
            f"• Videos edited: {stats.get('total_videos', 0)}\n"
            f"• Images edited: {stats.get('total_images', 0)}\n"
            f"• Designs created: {stats.get('total_designs', 0)}\n\n"
            f"<b>✨ Premium Benefits:</b>\n"
            f"✓ 4K Video Export\n"
            f"✓ No Watermark\n"
            f"✓ All Filters & Effects\n"
            f"✓ Unlimited Exports\n"
            f"✓ Priority Support\n"
            f"✓ Cloud Storage\n\n"
            f"<b>🔄 Need to renew?</b> Contact support for special offers!"
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 View Detailed Stats", callback_data="stats")],
            [InlineKeyboardButton("🔄 Extend Subscription", callback_data="extend_premium")],
            [InlineKeyboardButton("🎁 Refer a Friend", callback_data="referral")],
            [InlineKeyboardButton("📞 Premium Support", callback_data="contact")],
            [InlineKeyboardButton("🔙 Back", callback_data="back")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
)
