"""
Razorpay Payment Handler - Indian payments with UPI, Cards, NetBanking
Author: @kinva_master
"""

import os
import logging
import razorpay
import hashlib
import hmac
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests

from ..config import Config
from ..database import db

logger = logging.getLogger(__name__)

class RazorpayHandler:
    """Razorpay payment processing for Indian users"""
    
    def __init__(self):
        # Initialize Razorpay client
        self.client = razorpay.Client(
            auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET)
        )
        self.key_id = Config.RAZORPAY_KEY_ID
        self.key_secret = Config.RAZORPAY_KEY_SECRET
        self.webhook_secret = Config.RAZORPAY_WEBHOOK_SECRET
        
        # Product configuration in Indian Rupees (paise)
        self.products = {
            'monthly': {
                'id': 'monthly',
                'name': 'Monthly Subscription',
                'price': 49900,      # ₹499.00
                'currency': 'INR',
                'interval': 'month',
                'description': 'Get premium access for 1 month'
            },
            'quarterly': {
                'id': 'quarterly',
                'name': 'Quarterly Subscription',
                'price': 129900,     # ₹1299.00
                'currency': 'INR',
                'interval': 'quarter',
                'description': 'Get premium access for 3 months (Save 13%)'
            },
            'half_yearly': {
                'id': 'half_yearly',
                'name': 'Half-Yearly Subscription',
                'price': 249900,     # ₹2499.00
                'currency': 'INR',
                'interval': 'half_year',
                'description': 'Get premium access for 6 months (Save 17%)'
            },
            'yearly': {
                'id': 'yearly',
                'name': 'Yearly Subscription',
                'price': 399900,     # ₹3999.00
                'currency': 'INR',
                'interval': 'year',
                'description': 'Get premium access for 1 year (Save 33%)'
            },
            'lifetime': {
                'id': 'lifetime',
                'name': 'Lifetime Access',
                'price': 999900,     # ₹9999.00
                'currency': 'INR',
                'interval': 'once',
                'description': 'One-time payment for lifetime access'
            }
        }
        
        # Supported payment methods for India
        self.payment_methods = {
            'card': {
                'name': 'Credit/Debit Card',
                'icon': '💳',
                'networks': ['Visa', 'Mastercard', 'RuPay', 'Amex'],
                'emi': True
            },
            'upi': {
                'name': 'UPI',
                'icon': '📱',
                'apps': ['Google Pay', 'PhonePe', 'Paytm', 'BHIM', 'Amazon Pay']
            },
            'netbanking': {
                'name': 'Net Banking',
                'icon': '🏦',
                'banks': ['SBI', 'HDFC', 'ICICI', 'Axis', 'Yes Bank', 'Kotak', 'PNB', 'Canara']
            },
            'wallet': {
                'name': 'Mobile Wallet',
                'icon': '👛',
                'wallets': ['Paytm Wallet', 'PhonePe Wallet', 'Mobikwik', 'Freecharge']
            }
        }
        
        # Offer codes (festival offers, coupons)
        self.offers = {
            'DIWALI50': {'discount': 50, 'type': 'percent', 'valid_until': '2026-11-15'},
            'NEWYEAR25': {'discount': 25, 'type': 'percent', 'valid_until': '2026-01-31'},
            'SUMMER20': {'discount': 20, 'type': 'percent', 'valid_until': '2026-06-30'},
            'FESTIVAL30': {'discount': 30, 'type': 'percent', 'valid_until': '2026-01-15'},
            'STUDENT40': {'discount': 40, 'type': 'percent', 'valid_until': '2026-12-31', 'requires_verification': True},
            'WELCOME50': {'discount': 50, 'type': 'percent', 'valid_until': '2026-03-31'},
            'FIRST100': {'discount': 100, 'type': 'fixed', 'valid_until': '2026-12-31'},
        }
    
    def create_order(self, user_id: int, plan: str, 
                     offer_code: str = None, 
                     payment_method: str = None) -> Dict:
        """Create Razorpay order"""
        try:
            product = self.products.get(plan)
            if not product:
                raise ValueError(f"Invalid plan: {plan}")
            
            amount = product['price']
            discount = 0
            
            # Apply offer if provided
            if offer_code:
                offer = self.offers.get(offer_code.upper())
                if offer and self._is_offer_valid(offer):
                    if offer['type'] == 'percent':
                        discount = int(amount * offer['discount'] / 100)
                    else:
                        discount = offer['discount'] * 100  # Convert to paise
                    amount -= discount
            
            # Create payment record
            payment_id = db.create_payment(
                user_id=user_id,
                amount=amount / 100,
                currency='INR',
                plan=plan,
                method='razorpay',
                status='pending',
                offer_code=offer_code,
                discount=discount / 100
            )
            
            # Create Razorpay order
            order = self.client.order.create({
                'amount': amount,
                'currency': 'INR',
                'receipt': f'receipt_{payment_id}',
                'payment_capture': 1,
                'notes': {
                    'user_id': user_id,
                    'payment_id': payment_id,
                    'plan': plan,
                    'offer_code': offer_code or ''
                }
            })
            
            # Update payment with order ID
            db.update_payment(payment_id, {'order_id': order['id']})
            
            return {
                'order_id': order['id'],
                'amount': order['amount'] / 100,
                'currency': order['currency'],
                'key': self.key_id,
                'payment_id': payment_id,
                'discount': discount / 100,
                'original_amount': product['price'] / 100,
                'payment_methods': self.payment_methods if not payment_method else {payment_method: self.payment_methods.get(payment_method)}
            }
            
        except Exception as e:
            logger.error(f"Create order error: {e}")
            raise
    
    def verify_payment(self, payment_data: Dict) -> Dict:
        """Verify Razorpay payment signature"""
        try:
            # Generate signature
            generated_signature = hmac.new(
                self.key_secret.encode(),
                f"{payment_data['razorpay_order_id']}|{payment_data['razorpay_payment_id']}".encode(),
                hashlib.sha256
            ).hexdigest()
            
            if generated_signature == payment_data['razorpay_signature']:
                # Payment verified
                order_id = payment_data['razorpay_order_id']
                payment_id = payment_data['razorpay_payment_id']
                
                # Get payment from database
                payment = db.get_payment_by_order_id(order_id)
                if not payment:
                    raise ValueError("Payment record not found")
                
                # Fetch payment details from Razorpay
                razorpay_payment = self.client.payment.fetch(payment_id)
                
                # Update payment status
                db.update_payment_status(payment['id'], 'completed')
                db.update_payment(payment['id'], {
                    'razorpay_payment_id': payment_id,
                    'payment_method': razorpay_payment.get('method'),
                    'bank': razorpay_payment.get('bank'),
                    'wallet': razorpay_payment.get('wallet'),
                    'vpa': razorpay_payment.get('vpa')
                })
                
                # Activate premium based on plan
                plan = payment['plan']
                if plan == 'monthly':
                    months = 1
                elif plan == 'quarterly':
                    months = 3
                elif plan == 'half_yearly':
                    months = 6
                elif plan == 'yearly':
                    months = 12
                elif plan == 'lifetime':
                    months = 0
                    db.activate_lifetime_premium(payment['user_id'])
                    self._send_success_notification(payment['user_id'], plan)
                    return {'status': 'success', 'message': 'Lifetime premium activated'}
                
                db.activate_premium(payment['user_id'], months=months)
                
                # Send success notification
                self._send_success_notification(payment['user_id'], plan)
                
                return {'status': 'success', 'message': f'{plan} plan activated'}
            else:
                return {'status': 'failed', 'message': 'Invalid signature'}
                
        except Exception as e:
            logger.error(f"Verify payment error: {e}")
            return {'status': 'failed', 'message': str(e)}
    
    def _is_offer_valid(self, offer: Dict) -> bool:
        """Check if offer is still valid"""
        if 'valid_until' in offer:
            valid_until = datetime.strptime(offer['valid_until'], '%Y-%m-%d')
            return valid_until >= datetime.now()
        return True
    
    def _send_success_notification(self, user_id: int, plan: str):
        """Send payment success notification"""
        try:
            # Create in-app notification
            db.create_notification(
                user_id=user_id,
                title='Payment Successful! 🎉',
                message=f'Your {plan} premium plan has been activated. Enjoy unlimited access to all premium features!',
                type='success'
            )
            
            # Send WhatsApp notification (if configured)
            user = db.get_user(user_id)
            if user and user.get('phone'):
                self._send_whatsapp_notification(user['phone'], plan)
                
        except Exception as e:
            logger.error(f"Send notification error: {e}")
    
    def _send_whatsapp_notification(self, phone: str, plan: str):
        """Send WhatsApp notification (placeholder)"""
        # In production, integrate with WhatsApp Business API
        logger.info(f"WhatsApp notification sent to {phone} for {plan} plan")
    
    def capture_payment(self, payment_id: str, amount: int = None) -> Dict:
        """Capture payment"""
        try:
            payment = self.client.payment.capture(payment_id, amount)
            return payment
        except Exception as e:
            logger.error(f"Capture payment error: {e}")
            raise
    
    def refund_payment(self, payment_id: str, amount: int = None) -> Dict:
        """Refund payment"""
        try:
            if amount:
                refund = self.client.payment.refund(payment_id, {'amount': amount})
            else:
                refund = self.client.payment.refund(payment_id)
            
            # Update payment status
            payment = db.get_payment_by_razorpay_id(payment_id)
            if payment:
                db.update_payment_status(payment['id'], 'refunded')
                db.create_notification(
                    user_id=payment['user_id'],
                    title='Refund Processed',
                    message=f'Your refund of ₹{payment["amount"]} has been processed.',
                    type='info'
                )
            
            return refund
            
        except Exception as e:
            logger.error(f"Refund payment error: {e}")
            raise
    
    def get_payment_status(self, payment_id: str) -> str:
        """Get payment status from Razorpay"""
        try:
            payment = self.client.payment.fetch(payment_id)
            return payment['status']
        except Exception as e:
            logger.error(f"Get payment status error: {e}")
            return 'failed'
    
    def get_order_details(self, order_id: str) -> Dict:
        """Get order details"""
        try:
            order = self.client.order.fetch(order_id)
            return order
        except Exception as e:
            logger.error(f"Get order details error: {e}")
            return {}
    
    def create_subscription(self, user_id: int, plan: str, 
                           customer_name: str, customer_email: str,
                           customer_phone: str) -> Dict:
        """Create subscription for recurring payments"""
        try:
            product = self.products.get(plan)
            if not product:
                raise ValueError(f"Invalid plan: {plan}")
            
            # Create customer
            customer = self.client.customer.create({
                'name': customer_name,
                'email': customer_email,
                'contact': customer_phone,
                'notes': {'user_id': user_id}
            })
            
            # Create subscription
            subscription = self.client.subscription.create({
                'plan_id': self._get_plan_id(plan),
                'customer_id': customer['id'],
                'total_count': self._get_total_count(plan),
                'notes': {'user_id': user_id}
            })
            
            return {
                'subscription_id': subscription['id'],
                'customer_id': customer['id'],
                'amount': product['price'] / 100,
                'currency': product['currency']
            }
            
        except Exception as e:
            logger.error(f"Create subscription error: {e}")
            raise
    
    def _get_plan_id(self, plan: str) -> str:
        """Get Razorpay plan ID for subscription"""
        # In production, create plans in Razorpay dashboard
        plan_ids = {
            'monthly': 'plan_monthly_001',
            'quarterly': 'plan_quarterly_001',
            'yearly': 'plan_yearly_001'
        }
        return plan_ids.get(plan, '')
    
    def _get_total_count(self, plan: str) -> int:
        """Get total number of billing cycles"""
        counts = {
            'monthly': 12,
            'quarterly': 4,
            'yearly': 1
        }
        return counts.get(plan, 12)
    
    def cancel_subscription(self, subscription_id: str) -> Dict:
        """Cancel subscription"""
        try:
            subscription = self.client.subscription.cancel(subscription_id)
            return subscription
        except Exception as e:
            logger.error(f"Cancel subscription error: {e}")
            raise
    
    def get_offers(self) -> List[Dict]:
        """Get active offers"""
        active_offers = []
        for code, offer in self.offers.items():
            if self._is_offer_valid(offer):
                active_offers.append({
                    'code': code,
                    'discount': offer['discount'],
                    'type': offer['type'],
                    'description': f"{offer['discount']}% off" if offer['type'] == 'percent' else f"₹{offer['discount']} off",
                    'requires_verification': offer.get('requires_verification', False)
                })
        return active_offers
    
    def handle_webhook(self, payload: str, signature: str) -> Dict:
        """Handle Razorpay webhook events"""
        try:
            # Verify webhook signature
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(expected_signature, signature):
                return {'status': 'failed', 'message': 'Invalid signature'}
            
            event = json.loads(payload)
            event_type = event.get('event')
            event_data = event.get('payload', {})
            
            logger.info(f"Received webhook: {event_type}")
            
            if event_type == 'payment.captured':
                payment = event_data.get('payment', {}).get('entity', {})
                order_id = payment.get('order_id')
                
                # Update payment status
                db_payment = db.get_payment_by_order_id(order_id)
                if db_payment:
                    db.update_payment_status(db_payment['id'], 'completed')
                    
                    # Activate premium
                    plan = db_payment['plan']
                    if plan == 'lifetime':
                        db.activate_lifetime_premium(db_payment['user_id'])
                    else:
                        months = self._get_months_from_plan(plan)
                        db.activate_premium(db_payment['user_id'], months=months)
                    
                    # Send notification
                    self._send_success_notification(db_payment['user_id'], plan)
            
            elif event_type == 'payment.failed':
                payment = event_data.get('payment', {}).get('entity', {})
                order_id = payment.get('order_id')
                
                db_payment = db.get_payment_by_order_id(order_id)
                if db_payment:
                    db.update_payment_status(db_payment['id'], 'failed')
                    db.create_notification(
                        user_id=db_payment['user_id'],
                        title='Payment Failed',
                        message=f'Your payment of ₹{db_payment["amount"]} failed. Please try again.',
                        type='error'
                    )
            
            elif event_type == 'subscription.charged':
                subscription = event_data.get('subscription', {}).get('entity', {})
                # Handle recurring payment success
                user_id = subscription.get('notes', {}).get('user_id')
                if user_id:
                    db.extend_premium(user_id, months=1)
                    db.create_notification(
                        user_id=user_id,
                        title='Subscription Renewed',
                        message='Your subscription has been automatically renewed.',
                        type='success'
                    )
            
            elif event_type == 'subscription.cancelled':
                subscription = event_data.get('subscription', {}).get('entity', {})
                user_id = subscription.get('notes', {}).get('user_id')
                if user_id:
                    db.create_notification(
                        user_id=user_id,
                        title='Subscription Cancelled',
                        message='Your subscription has been cancelled. You will have access until the end of the billing period.',
                        type='info'
                    )
            
            return {'status': 'success'}
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return {'status': 'failed', 'message': str(e)}
    
    def _get_months_from_plan(self, plan: str) -> int:
        """Convert plan to months"""
        months_map = {
            'monthly': 1,
            'quarterly': 3,
            'half_yearly': 6,
            'yearly': 12,
            'lifetime': 0
        }
        return months_map.get(plan, 1)
    
    def generate_upi_qr(self, amount: float, user_id: int, plan: str) -> Dict:
        """Generate UPI QR code for payment"""
        try:
            # Create payment record
            payment_id = db.create_payment(
                user_id=user_id,
                amount=amount,
                currency='INR',
                plan=plan,
                method='upi',
                status='pending'
            )
            
            # Create UPI intent URL
            upi_id = Config.UPI_ID
            merchant_name = Config.MERCHANT_NAME
            
            upi_url = f"upi://pay?pa={upi_id}&pn={merchant_name}&am={amount}&tn=Payment%20for%20Kinva%20Master&cu=INR"
            
            # Generate QR code
            import qrcode
            import base64
            from io import BytesIO
            
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(upi_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            return {
                'payment_id': payment_id,
                'qr_code': qr_base64,
                'upi_url': upi_url,
                'amount': amount,
                'upi_id': upi_id
            }
            
        except Exception as e:
            logger.error(f"Generate UPI QR error: {e}")
            raise

# Create global instance
razorpay_handler = RazorpayHandler()
