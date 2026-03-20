"""
Payments API - Payment processing endpoints
Author: @kinva_master
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..database import db
from ..config import Config
from ..payment.stripe_handler import stripe_handler
from ..payment.razorpay_handler import razorpay_handler
from ..payment.upi_handler import upi_handler
from ..payment.crypto_handler import crypto_handler
from ..payment.subscription import subscription_manager

logger = logging.getLogger(__name__)

payments_bp = Blueprint('payments', __name__, url_prefix='/api/v1/payments')


class PaymentsAPI:
    """Payments API endpoints"""
    
    @staticmethod
    @payments_bp.route('/plans', methods=['GET'])
    def get_plans():
        """Get available premium plans"""
        try:
            plans = subscription_manager.get_all_plans(include_free=False)
            yearly_plans = []
            
            for plan in plans:
                if plan['id'] != 'free' and plan['interval'] == 'month':
                    yearly = subscription_manager.get_yearly_plan(plan['id'])
                    if yearly:
                        yearly_plans.append(yearly)
            
            return jsonify({
                'monthly': [p for p in plans if p['interval'] == 'month'],
                'yearly': yearly_plans,
                'lifetime': [p for p in plans if p['id'] == 'lifetime']
            })
            
        except Exception as e:
            logger.error(f"Get plans error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @payments_bp.route('/create-order', methods=['POST'])
    @jwt_required()
    def create_order():
        """Create payment order"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            plan = data.get('plan')
            method = data.get('method', 'stripe')
            currency = data.get('currency', 'usd')
            promo_code = data.get('promo_code')
            
            if not plan:
                return jsonify({'error': 'Plan required'}), 400
            
            # Get plan details
            plan_data = subscription_manager.get_plan(plan)
            if not plan_data:
                return jsonify({'error': 'Invalid plan'}), 400
            
            amount = plan_data.get('price_inr') if currency == 'inr' else plan_data.get('price')
            
            if method == 'stripe':
                result = stripe_handler.create_checkout_session(
                    user_id=user_id,
                    plan=plan,
                    currency=currency,
                    promo_code=promo_code
                )
            elif method == 'razorpay':
                result = razorpay_handler.create_order(
                    user_id=user_id,
                    plan=plan,
                    offer_code=promo_code
                )
            elif method == 'upi':
                result = upi_handler.generate_qr(
                    amount=amount,
                    user_id=user_id,
                    plan=plan
                )
            elif method == 'crypto':
                result = crypto_handler.create_payment(
                    user_id=user_id,
                    amount_inr=amount,
                    plan=plan,
                    currency=data.get('crypto_currency', 'usdt')
                )
            else:
                return jsonify({'error': 'Invalid payment method'}), 400
            
            return jsonify({
                'success': True,
                'payment_id': result.get('payment_id'),
                'order_id': result.get('order_id'),
                'amount': amount,
                'currency': currency,
                'method': method,
                'data': result
            })
            
        except Exception as e:
            logger.error(f"Create order error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @payments_bp.route('/verify', methods=['POST'])
    @jwt_required()
    def verify_payment():
        """Verify payment"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            payment_id = data.get('payment_id')
            method = data.get('method')
            
            if not payment_id:
                return jsonify({'error': 'Payment ID required'}), 400
            
            payment = db.get_payment(payment_id)
            if not payment or payment['user_id'] != user_id:
                return jsonify({'error': 'Payment not found'}), 404
            
            if method == 'razorpay':
                result = razorpay_handler.verify_payment(data)
            elif method == 'upi':
                result = upi_handler.verify_payment(
                    payment_id,
                    transaction_id=data.get('transaction_id'),
                    upi_ref=data.get('upi_ref')
                )
            elif method == 'crypto':
                result = crypto_handler.verify_payment(
                    payment_id,
                    tx_hash=data.get('tx_hash')
                )
            else:
                # Stripe verification via webhook
                return jsonify({'error': 'Use webhook for Stripe verification'}), 400
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Verify payment error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @payments_bp.route('/status/<payment_id>', methods=['GET'])
    @jwt_required()
    def get_payment_status(payment_id):
        """Get payment status"""
        try:
            user_id = get_jwt_identity()
            payment = db.get_payment(payment_id)
            
            if not payment or payment['user_id'] != user_id:
                return jsonify({'error': 'Payment not found'}), 404
            
            return jsonify({
                'id': payment['id'],
                'status': payment['status'],
                'amount': payment['amount'],
                'currency': payment['currency'],
                'plan': payment['plan'],
                'method': payment['method'],
                'created_at': payment['created_at'],
                'completed_at': payment.get('completed_at')
            })
            
        except Exception as e:
            logger.error(f"Get payment status error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @payments_bp.route('/history', methods=['GET'])
    @jwt_required()
    def get_payment_history():
        """Get user payment history"""
        try:
            user_id = get_jwt_identity()
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 20, type=int)
            
            payments = db.get_user_payments(user_id, page=page, limit=limit)
            
            return jsonify(payments)
            
        except Exception as e:
            logger.error(f"Get payment history error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @payments_bp.route('/subscription', methods=['GET'])
    @jwt_required()
    def get_subscription():
        """Get user subscription details"""
        try:
            user_id = get_jwt_identity()
            subscription = subscription_manager.get_subscription_status(user_id)
            
            return jsonify(subscription)
            
        except Exception as e:
            logger.error(f"Get subscription error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @payments_bp.route('/subscription/cancel', methods=['POST'])
    @jwt_required()
    def cancel_subscription():
        """Cancel subscription"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            immediate = data.get('immediate', False)
            
            result = subscription_manager.cancel_subscription(user_id, immediate=immediate)
            
            if result:
                return jsonify({'success': True, 'message': 'Subscription cancelled'})
            else:
                return jsonify({'error': 'Failed to cancel subscription'}), 400
            
        except Exception as e:
            logger.error(f"Cancel subscription error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @payments_bp.route('/subscription/reactivate', methods=['POST'])
    @jwt_required()
    def reactivate_subscription():
        """Reactivate cancelled subscription"""
        try:
            user_id = get_jwt_identity()
            # In production, call Stripe/Razorpay API
            db.reactivate_subscription(user_id)
            
            return jsonify({'success': True, 'message': 'Subscription reactivated'})
            
        except Exception as e:
            logger.error(f"Reactivate subscription error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @payments_bp.route('/invoices', methods=['GET'])
    @jwt_required()
    def get_invoices():
        """Get user invoices"""
        try:
            user_id = get_jwt_identity()
            
            # Get from Stripe if available
            invoices = stripe_handler.get_invoices(user_id)
            
            return jsonify(invoices)
            
        except Exception as e:
            logger.error(f"Get invoices error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @payments_bp.route('/promo/validate', methods=['POST'])
    @jwt_required()
    def validate_promo():
        """Validate promo code"""
        try:
            data = request.get_json()
            promo_code = data.get('code')
            plan = data.get('plan')
            
            if not promo_code:
                return jsonify({'error': 'Promo code required'}), 400
            
            # Check promo code (in production, check database)
            promo = razorpay_handler.offers.get(promo_code.upper())
            
            if not promo:
                return jsonify({'error': 'Invalid promo code'}), 400
            
            if not razorpay_handler._is_offer_valid(promo):
                return jsonify({'error': 'Promo code expired'}), 400
            
            # Get plan price
            plan_data = subscription_manager.get_plan(plan)
            if not plan_data:
                return jsonify({'error': 'Invalid plan'}), 400
            
            amount = plan_data.get('price_inr', plan_data.get('price', 0))
            discount = promo['discount']
            
            if promo['type'] == 'percent':
                discounted_amount = amount * (1 - discount / 100)
                discount_amount = amount - discounted_amount
            else:
                discounted_amount = max(0, amount - discount)
                discount_amount = discount
            
            return jsonify({
                'success': True,
                'code': promo_code.upper(),
                'discount': discount,
                'type': promo['type'],
                'original_amount': amount,
                'discounted_amount': discounted_amount,
                'discount_amount': discount_amount
            })
            
        except Exception as e:
            logger.error(f"Validate promo error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @payments_bp.route('/refund', methods=['POST'])
    @jwt_required()
    def request_refund():
        """Request refund"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            
            payment_id = data.get('payment_id')
            reason = data.get('reason', 'Customer requested')
            
            if not payment_id:
                return jsonify({'error': 'Payment ID required'}), 400
            
            payment = db.get_payment(payment_id)
            if not payment or payment['user_id'] != user_id:
                return jsonify({'error': 'Payment not found'}), 404
            
            if payment['status'] != 'completed':
                return jsonify({'error': 'Payment not completed'}), 400
            
            # Process refund based on payment method
            if payment['method'] == 'stripe':
                result = stripe_handler.create_refund(payment_id)
            elif payment['method'] == 'razorpay':
                result = razorpay_handler.refund_payment(payment['payment_id'])
            elif payment['method'] == 'upi':
                result = upi_handler.initiate_refund(payment_id)
            else:
                return jsonify({'error': 'Refund not supported for this payment method'}), 400
            
            # Create refund record
            db.create_refund_record(
                payment_id=payment_id,
                user_id=user_id,
                amount=payment['amount'],
                reason=reason,
                status='pending'
            )
            
            return jsonify({
                'success': True,
                'message': 'Refund request submitted',
                'refund_id': result.get('id')
            })
            
        except Exception as e:
            logger.error(f"Request refund error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @payments_bp.route('/methods', methods=['GET'])
    def get_payment_methods():
        """Get available payment methods"""
        try:
            methods = [
                {
                    'id': 'stripe',
                    'name': 'Credit/Debit Card',
                    'icon': '💳',
                    'currencies': ['usd', 'eur', 'gbp', 'aed', 'sgd', 'myr'],
                    'countries': ['US', 'GB', 'AE', 'SG', 'MY', 'EU']
                },
                {
                    'id': 'razorpay',
                    'name': 'UPI / Card / NetBanking',
                    'icon': '🇮🇳',
                    'currencies': ['inr'],
                    'countries': ['IN']
                },
                {
                    'id': 'upi',
                    'name': 'UPI QR Code',
                    'icon': '📱',
                    'currencies': ['inr'],
                    'countries': ['IN']
                },
                {
                    'id': 'crypto',
                    'name': 'Cryptocurrency',
                    'icon': '₿',
                    'currencies': ['btc', 'eth', 'usdt', 'usdc', 'ltc', 'doge'],
                    'countries': ['ALL']
                }
            ]
            
            return jsonify(methods)
            
        except Exception as e:
            logger.error(f"Get payment methods error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @payments_bp.route('/webhook/<provider>', methods=['POST'])
    def webhook(provider):
        """Handle payment webhooks"""
        try:
            payload = request.get_data(as_text=True)
            signature = request.headers.get('X-Signature')
            
            if provider == 'stripe':
                result = stripe_handler.handle_webhook(payload, signature)
            elif provider == 'razorpay':
                result = razorpay_handler.handle_webhook(payload, signature)
            else:
                return jsonify({'error': 'Invalid provider'}), 400
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return jsonify({'error': str(e)}), 500
