"""
Stripe Payment Handler - International payments
Author: @kinva_master
"""

import os
import logging
import stripe
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..config import Config
from ..database import db

logger = logging.getLogger(__name__)

class StripeHandler:
    """Stripe payment processing for international users"""
    
    def __init__(self):
        # Initialize Stripe with API keys
        stripe.api_key = Config.STRIPE_SECRET_KEY
        self.publishable_key = Config.STRIPE_PUBLIC_KEY
        self.webhook_secret = Config.STRIPE_WEBHOOK_SECRET
        
        # Product configuration with multiple currencies
        self.products = {
            'monthly': {
                'id': 'price_monthly',
                'name': 'Monthly Subscription',
                'price_usd': 1499,  # $14.99 in cents
                'price_inr': 49900,  # ₹499.00 in paise
                'price_gbp': 1199,   # £11.99 in pence
                'price_eur': 1399,   # €13.99 in cents
                'price_aed': 5500,   # AED 55.00 in fils
                'price_sgd': 2000,   # SGD 20.00 in cents
                'price_myr': 6500,   # RM 65.00 in sen
                'interval': 'month',
                'currency': 'usd'
            },
            'quarterly': {
                'id': 'price_quarterly',
                'name': 'Quarterly Subscription',
                'price_usd': 3999,   # $39.99 in cents
                'price_inr': 129900, # ₹1299.00 in paise
                'price_gbp': 3199,   # £31.99 in pence
                'price_eur': 3699,   # €36.99 in cents
                'price_aed': 14700,  # AED 147.00 in fils
                'price_sgd': 5300,   # SGD 53.00 in cents
                'price_myr': 17000,  # RM 170.00 in sen
                'interval': 'month',
                'currency': 'usd'
            },
            'yearly': {
                'id': 'price_yearly',
                'name': 'Yearly Subscription',
                'price_usd': 11999,  # $119.99 in cents
                'price_inr': 399900, # ₹3999.00 in paise
                'price_gbp': 9599,   # £95.99 in pence
                'price_eur': 10999,  # €109.99 in cents
                'price_aed': 44000,  # AED 440.00 in fils
                'price_sgd': 16000,  # SGD 160.00 in cents
                'price_myr': 52000,  # RM 520.00 in sen
                'interval': 'year',
                'currency': 'usd'
            },
            'lifetime': {
                'id': 'price_lifetime',
                'name': 'Lifetime Access',
                'price_usd': 29999,  # $299.99 in cents
                'price_inr': 999900, # ₹9999.00 in paise
                'price_gbp': 23999,  # £239.99 in pence
                'price_eur': 27499,  # €274.99 in cents
                'price_aed': 110000, # AED 1100.00 in fils
                'price_sgd': 40000,  # SGD 400.00 in cents
                'price_myr': 130000, # RM 1300.00 in sen
                'interval': 'once',
                'currency': 'usd'
            }
        }
        
        # Supported currencies
        self.supported_currencies = ['usd', 'inr', 'gbp', 'eur', 'aed', 'sgd', 'myr']
    
    def get_price_for_currency(self, plan: str, currency: str = 'usd') -> int:
        """Get price in specified currency"""
        product = self.products.get(plan)
        if not product:
            raise ValueError(f"Invalid plan: {plan}")
        
        currency = currency.lower()
        if currency == 'usd':
            return product['price_usd']
        elif currency == 'inr':
            return product['price_inr']
        elif currency == 'gbp':
            return product['price_gbp']
        elif currency == 'eur':
            return product['price_eur']
        elif currency == 'aed':
            return product['price_aed']
        elif currency == 'sgd':
            return product['price_sgd']
        elif currency == 'myr':
            return product['price_myr']
        else:
            return product['price_usd']
    
    def create_checkout_session(self, user_id: int, plan: str, 
                                currency: str = 'usd',
                                success_url: str = None, 
                                cancel_url: str = None,
                                promo_code: str = None) -> str:
        """Create Stripe checkout session"""
        try:
            product = self.products.get(plan)
            if not product:
                raise ValueError(f"Invalid plan: {plan}")
            
            # Get price in selected currency
            amount = self.get_price_for_currency(plan, currency)
            
            # Apply promo code if provided
            discount = 0
            if promo_code:
                discount = self._validate_promo_code(promo_code)
                if discount:
                    amount = int(amount * (1 - discount / 100))
            
            # Create payment record
            payment_id = db.create_payment(
                user_id=user_id,
                amount=amount / 100,
                currency=currency.upper(),
                plan=plan,
                method='stripe',
                promo_code=promo_code,
                discount=discount
            )
            
            # Create line items
            line_items = [{
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': product['name'],
                        'description': f'Premium access for Kinva Master',
                        'images': [f"{Config.WEBAPP_URL}/static/images/logo.png"]
                    },
                    'unit_amount': amount,
                },
                'quantity': 1,
            }]
            
            # Add recurring interval if not lifetime
            if plan != 'lifetime':
                line_items[0]['price_data']['recurring'] = {
                    'interval': product['interval']
                }
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='subscription' if plan != 'lifetime' else 'payment',
                success_url=success_url or f"{Config.WEBAPP_URL}/payment/success?payment_id={payment_id}",
                cancel_url=cancel_url or f"{Config.WEBAPP_URL}/payment/cancel",
                metadata={
                    'user_id': user_id,
                    'payment_id': payment_id,
                    'plan': plan,
                    'currency': currency
                },
                customer_email=db.get_user_email(user_id),
                billing_address_collection='required',
                shipping_address_collection={
                    'allowed_countries': ['US', 'IN', 'GB', 'AE', 'SG', 'MY', 'DE', 'FR']
                },
                allow_promotion_codes=True
            )
            
            # Update payment with session ID
            db.update_payment(payment_id, {'stripe_session_id': session.id})
            
            return {
                'session_url': session.url,
                'payment_id': payment_id,
                'session_id': session.id
            }
            
        except Exception as e:
            logger.error(f"Stripe checkout error: {e}")
            raise
    
    def _validate_promo_code(self, code: str) -> int:
        """Validate promo code and return discount percentage"""
        # In production, check against database
        promo_codes = {
            'WELCOME50': 50,
            'KINVA20': 20,
            'FRIEND10': 10,
            'SUMMER30': 30,
            'FESTIVAL25': 25
        }
        return promo_codes.get(code.upper(), 0)
    
    def handle_webhook(self, payload: str, sig_header: str) -> Dict:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            
            event_type = event['type']
            event_data = event['data']['object']
            
            logger.info(f"Received webhook: {event_type}")
            
            # Handle checkout session completed
            if event_type == 'checkout.session.completed':
                session = event_data
                payment_id = session['metadata']['payment_id']
                user_id = int(session['metadata']['user_id'])
                plan = session['metadata']['plan']
                currency = session['metadata']['currency']
                
                # Update payment status
                db.update_payment_status(payment_id, 'completed')
                db.update_payment(payment_id, {
                    'stripe_payment_intent': session['payment_intent'],
                    'customer_id': session['customer']
                })
                
                # Activate premium based on plan
                if plan == 'monthly':
                    months = 1
                elif plan == 'quarterly':
                    months = 3
                elif plan == 'yearly':
                    months = 12
                elif plan == 'lifetime':
                    months = 0
                    db.activate_lifetime_premium(user_id)
                    # Send welcome email
                    self._send_welcome_email(user_id, plan)
                    return {'status': 'success'}
                
                db.activate_premium(user_id, months=months)
                
                # Send welcome email
                self._send_welcome_email(user_id, plan)
                
                # Create notification
                db.create_notification(
                    user_id=user_id,
                    title='Premium Activated!',
                    message=f'Your {plan} premium plan has been activated. Enjoy all premium features!',
                    type='success'
                )
                
            # Handle subscription created
            elif event_type == 'customer.subscription.created':
                subscription = event_data
                user_id = db.get_user_by_stripe_customer(subscription['customer'])
                if user_id:
                    db.update_user_stripe_subscription(
                        user_id=user_id,
                        subscription_id=subscription['id']
                    )
            
            # Handle subscription updated
            elif event_type == 'customer.subscription.updated':
                subscription = event_data
                user_id = db.get_user_by_stripe_customer(subscription['customer'])
                if user_id:
                    if subscription['cancel_at_period_end']:
                        db.create_notification(
                            user_id=user_id,
                            title='Subscription Ending',
                            message='Your subscription will end at the current period. Renew to continue premium benefits.',
                            type='warning'
                        )
            
            # Handle subscription deleted (cancelled)
            elif event_type == 'customer.subscription.deleted':
                subscription = event_data
                user_id = db.get_user_by_stripe_customer(subscription['customer'])
                if user_id:
                    db.deactivate_premium(user_id)
                    db.create_notification(
                        user_id=user_id,
                        title='Premium Expired',
                        message='Your premium subscription has ended. Upgrade again to continue enjoying premium features.',
                        type='info'
                    )
            
            # Handle invoice payment succeeded
            elif event_type == 'invoice.payment_succeeded':
                invoice = event_data
                if invoice['billing_reason'] == 'subscription_cycle':
                    user_id = db.get_user_by_stripe_customer(invoice['customer'])
                    if user_id:
                        db.extend_premium(user_id, months=1)
                        db.create_notification(
                            user_id=user_id,
                            title='Payment Successful',
                            message='Your monthly payment was successful. Your premium access has been extended.',
                            type='success'
                        )
            
            # Handle invoice payment failed
            elif event_type == 'invoice.payment_failed':
                invoice = event_data
                user_id = db.get_user_by_stripe_customer(invoice['customer'])
                if user_id:
                    db.create_notification(
                        user_id=user_id,
                        title='Payment Failed',
                        message='Your payment failed. Please update your payment method to continue premium access.',
                        type='error'
                    )
            
            return {'status': 'success'}
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Stripe webhook signature error: {e}")
            raise
        except Exception as e:
            logger.error(f"Stripe webhook error: {e}")
            raise
    
    def _send_welcome_email(self, user_id: int, plan: str):
        """Send welcome email to user"""
        try:
            user = db.get_user(user_id)
            if not user or not user.get('email'):
                return
            
            # In production, use email service like SendGrid
            email_content = f"""
            Welcome to Kinva Master Premium!
            
            Your {plan} plan is now active.
            
            Premium Features:
            - 4K Video Export
            - No Watermark
            - All Filters & Effects
            - Unlimited Exports
            - Priority Support
            
            Start creating amazing content!
            
            https://kinva-master.com/dashboard
            """
            
            # Send email (placeholder)
            logger.info(f"Welcome email sent to {user['email']}")
            
        except Exception as e:
            logger.error(f"Send welcome email error: {e}")
    
    def create_customer(self, user_id: int, email: str, name: str = None) -> str:
        """Create Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={'user_id': user_id}
            )
            
            db.update_user_stripe_customer(user_id, customer.id)
            return customer.id
            
        except Exception as e:
            logger.error(f"Create customer error: {e}")
            raise
    
    def create_setup_intent(self, user_id: int) -> Dict:
        """Create setup intent for saving payment methods"""
        try:
            customer_id = db.get_stripe_customer_id(user_id)
            if not customer_id:
                customer_id = self.create_customer(
                    user_id, 
                    db.get_user_email(user_id),
                    db.get_user_name(user_id)
                )
            
            intent = stripe.SetupIntent.create(
                customer=customer_id,
                payment_method_types=['card'],
                usage='off_session'
            )
            
            return {
                'client_secret': intent.client_secret,
                'publishable_key': self.publishable_key
            }
            
        except Exception as e:
            logger.error(f"Setup intent error: {e}")
            raise
    
    def create_payment_method(self, user_id: int, payment_method_id: str) -> Dict:
        """Attach payment method to customer"""
        try:
            customer_id = db.get_stripe_customer_id(user_id)
            if not customer_id:
                customer_id = self.create_customer(user_id, db.get_user_email(user_id))
            
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id
            )
            
            # Set as default
            stripe.Customer.modify(
                customer_id,
                invoice_settings={'default_payment_method': payment_method_id}
            )
            
            return {
                'id': payment_method.id,
                'brand': payment_method.card.brand,
                'last4': payment_method.card.last4,
                'exp_month': payment_method.card.exp_month,
                'exp_year': payment_method.card.exp_year
            }
            
        except Exception as e:
            logger.error(f"Create payment method error: {e}")
            raise
    
    def get_payment_methods(self, user_id: int) -> List[Dict]:
        """Get user's saved payment methods"""
        try:
            customer_id = db.get_stripe_customer_id(user_id)
            if not customer_id:
                return []
            
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type='card'
            )
            
            return [{
                'id': pm.id,
                'brand': pm.card.brand,
                'last4': pm.card.last4,
                'exp_month': pm.card.exp_month,
                'exp_year': pm.card.exp_year,
                'is_default': pm.id == db.get_default_payment_method(user_id)
            } for pm in payment_methods]
            
        except Exception as e:
            logger.error(f"Get payment methods error: {e}")
            return []
    
    def get_invoices(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user invoices"""
        try:
            customer_id = db.get_stripe_customer_id(user_id)
            if not customer_id:
                return []
            
            invoices = stripe.Invoice.list(
                customer=customer_id,
                limit=limit
            )
            
            return [{
                'id': inv.id,
                'amount': inv.amount_paid / 100,
                'currency': inv.currency.upper(),
                'status': inv.status,
                'date': datetime.fromtimestamp(inv.created).isoformat(),
                'pdf_url': inv.invoice_pdf,
                'number': inv.number
            } for inv in invoices if inv.status == 'paid']
            
        except Exception as e:
            logger.error(f"Get invoices error: {e}")
            return []
    
    def cancel_subscription(self, user_id: int, at_period_end: bool = True) -> bool:
        """Cancel user subscription"""
        try:
            subscription_id = db.get_stripe_subscription_id(user_id)
            if not subscription_id:
                return False
            
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=at_period_end
            )
            
            if not at_period_end:
                db.deactivate_premium(user_id)
            
            db.create_notification(
                user_id=user_id,
                title='Subscription Cancelled',
                message='Your subscription has been cancelled. You will have access until the end of the billing period.' if at_period_end else 'Your subscription has been cancelled immediately.',
                type='info'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Cancel subscription error: {e}")
            return False
    
    def update_subscription(self, user_id: int, new_plan: str) -> bool:
        """Update user subscription to new plan"""
        try:
            subscription_id = db.get_stripe_subscription_id(user_id)
            if not subscription_id:
                return False
            
            # Get price ID for new plan
            price_id = self.products.get(new_plan, {}).get('id')
            if not price_id:
                return False
            
            # Update subscription
            subscription = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription['items']['data'][0]['id'],
                    'price': price_id
                }],
                proration_behavior='create_prorations'
            )
            
            # Update user plan
            db.update_user_plan(user_id, new_plan)
            
            db.create_notification(
                user_id=user_id,
                title='Plan Updated',
                message=f'Your subscription has been updated to {new_plan} plan.',
                type='success'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Update subscription error: {e}")
            return False
    
    def create_refund(self, payment_id: str, amount: int = None) -> Dict:
        """Create refund for payment"""
        try:
            payment = db.get_payment(payment_id)
            if not payment:
                raise ValueError("Payment not found")
            
            stripe_payment_intent = payment.get('stripe_payment_intent')
            if not stripe_payment_intent:
                raise ValueError("No Stripe payment intent found")
            
            refund_params = {
                'payment_intent': stripe_payment_intent,
                'reason': 'requested_by_customer'
            }
            
            if amount:
                refund_params['amount'] = int(amount * 100)
            
            refund = stripe.Refund.create(**refund_params)
            
            db.update_payment_status(payment_id, 'refunded')
            db.create_notification(
                user_id=payment['user_id'],
                title='Refund Processed',
                message=f'A refund of {payment["amount"]} {payment["currency"]} has been processed.',
                type='info'
            )
            
            return {
                'id': refund.id,
                'amount': refund.amount / 100,
                'currency': refund.currency.upper(),
                'status': refund.status
            }
            
        except Exception as e:
            logger.error(f"Create refund error: {e}")
            raise

# Create global instance
stripe_handler = StripeHandler()
