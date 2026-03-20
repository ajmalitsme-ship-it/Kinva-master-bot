"""
Webhooks API - External webhook endpoints
Author: @kinva_master
"""

import logging
import json
import hashlib
import hmac
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app

from ..database import db
from ..config import Config
from ..payment.stripe_handler import stripe_handler
from ..payment.razorpay_handler import razorpay_handler
from ..utils import verify_telegram_hash

logger = logging.getLogger(__name__)

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/api/v1/webhooks')


class WebhooksAPI:
    """External webhook endpoints"""
    
    @staticmethod
    @webhooks_bp.route('/stripe', methods=['POST'])
    def stripe_webhook():
        """Handle Stripe webhook events"""
        try:
            payload = request.get_data(as_text=True)
            sig_header = request.headers.get('Stripe-Signature')
            
            if not sig_header:
                return jsonify({'error': 'Missing signature'}), 400
            
            result = stripe_handler.handle_webhook(payload, sig_header)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Stripe webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/razorpay', methods=['POST'])
    def razorpay_webhook():
        """Handle Razorpay webhook events"""
        try:
            payload = request.get_data(as_text=True)
            signature = request.headers.get('X-Razorpay-Signature')
            
            if not signature:
                return jsonify({'error': 'Missing signature'}), 400
            
            result = razorpay_handler.handle_webhook(payload, signature)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Razorpay webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/telegram', methods=['POST'])
    def telegram_webhook():
        """Handle Telegram webhook (for bot updates)"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'No data'}), 400
            
            # Process update
            from ..bot import process_update
            process_update(data)
            
            return jsonify({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Telegram webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/whatsapp', methods=['POST'])
    def whatsapp_webhook():
        """Handle WhatsApp webhook events"""
        try:
            data = request.get_json()
            
            # Verify signature
            signature = request.headers.get('X-WhatsApp-Signature')
            if not verify_whatsapp_signature(payload, signature):
                return jsonify({'error': 'Invalid signature'}), 401
            
            # Process WhatsApp message
            if data.get('event') == 'message':
                from_number = data.get('from')
                message = data.get('message')
                
                # Store message
                db.save_whatsapp_message(from_number, message)
                
                # Auto-reply
                send_whatsapp_reply(from_number, message)
            
            return jsonify({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"WhatsApp webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/facebook', methods=['POST'])
    def facebook_webhook():
        """Handle Facebook webhook events"""
        try:
            data = request.get_json()
            
            # Verify hub challenge
            if request.args.get('hub.mode') == 'subscribe':
                challenge = request.args.get('hub.challenge')
                return challenge, 200
            
            # Process events
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    event_type = change.get('field')
                    event_data = change.get('value')
                    
                    # Store event
                    db.save_facebook_event(event_type, event_data)
            
            return jsonify({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Facebook webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/instagram', methods=['POST'])
    def instagram_webhook():
        """Handle Instagram webhook events"""
        try:
            data = request.get_json()
            
            # Verify hub challenge
            if request.args.get('hub.mode') == 'subscribe':
                challenge = request.args.get('hub.challenge')
                return challenge, 200
            
            # Process events
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    event_type = change.get('field')
                    event_data = change.get('value')
                    
                    # Store event
                    db.save_instagram_event(event_type, event_data)
            
            return jsonify({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Instagram webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/github', methods=['POST'])
    def github_webhook():
        """Handle GitHub webhook events"""
        try:
            event_type = request.headers.get('X-GitHub-Event')
            payload = request.get_json()
            
            # Verify signature
            signature = request.headers.get('X-Hub-Signature-256')
            if not verify_github_signature(payload, signature):
                return jsonify({'error': 'Invalid signature'}), 401
            
            # Process deployment events
            if event_type == 'deployment':
                deployment = payload.get('deployment')
                db.create_deployment_record(deployment)
                
                # Trigger deployment
                deploy_application(deployment)
            
            elif event_type == 'push':
                # Update deployment status
                branch = payload.get('ref', '').split('/')[-1]
                if branch == 'main':
                    db.update_deployment_status('pending')
            
            return jsonify({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"GitHub webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/cloudinary', methods=['POST'])
    def cloudinary_webhook():
        """Handle Cloudinary webhook events"""
        try:
            data = request.get_json()
            
            # Verify signature
            signature = request.headers.get('X-Cld-Signature')
            if not verify_cloudinary_signature(payload, signature):
                return jsonify({'error': 'Invalid signature'}), 401
            
            event_type = data.get('notification_type')
            
            if event_type == 'upload':
                # Update file status
                public_id = data.get('public_id')
                db.update_file_status(public_id, 'uploaded')
            
            elif event_type == 'delete':
                public_id = data.get('public_id')
                db.update_file_status(public_id, 'deleted')
            
            return jsonify({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Cloudinary webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/aws-s3', methods=['POST'])
    def aws_s3_webhook():
        """Handle AWS S3 event notifications"""
        try:
            data = request.get_json()
            
            for record in data.get('Records', []):
                event_name = record.get('eventName')
                bucket = record.get('s3', {}).get('bucket', {}).get('name')
                key = record.get('s3', {}).get('object', {}).get('key')
                
                if 'ObjectCreated' in event_name:
                    db.create_file_record(bucket, key, 'created')
                elif 'ObjectRemoved' in event_name:
                    db.update_file_record(bucket, key, 'deleted')
            
            return jsonify({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"AWS S3 webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/sendgrid', methods=['POST'])
    def sendgrid_webhook():
        """Handle SendGrid email events"""
        try:
            data = request.get_json()
            
            for event in data:
                event_type = event.get('event')
                email = event.get('email')
                timestamp = event.get('timestamp')
                
                # Store email event
                db.save_email_event(email, event_type, timestamp)
                
                # Update user status based on email events
                if event_type == 'bounce' or event_type == 'dropped':
                    db.mark_email_invalid(email)
                elif event_type == 'spamreport':
                    db.mark_email_spam(email)
            
            return jsonify({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"SendGrid webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/twilio', methods=['POST'])
    def twilio_webhook():
        """Handle Twilio SMS webhook"""
        try:
            from_number = request.form.get('From')
            to_number = request.form.get('To')
            body = request.form.get('Body')
            
            # Store SMS
            db.save_sms(from_number, to_number, body)
            
            # Auto-reply for support
            if 'help' in body.lower():
                reply = "Thank you for contacting Kinva Master Support. We'll get back to you soon.\n\nVisit: https://kinva-master.com/support"
                # Send SMS reply via Twilio
                send_sms_reply(to_number, from_number, reply)
            
            return jsonify({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Twilio webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/paytm', methods=['POST'])
    def paytm_webhook():
        """Handle Paytm payment webhook"""
        try:
            data = request.get_json()
            
            # Verify checksum
            checksum = data.get('CHECKSUMHASH')
            if not verify_paytm_checksum(data, checksum):
                return jsonify({'error': 'Invalid checksum'}), 401
            
            order_id = data.get('ORDERID')
            status = data.get('STATUS')
            
            if status == 'TXN_SUCCESS':
                # Update payment status
                db.update_payment_status(order_id, 'completed')
                
                # Activate premium
                payment = db.get_payment_by_order_id(order_id)
                if payment:
                    subscription_manager.activate_premium(
                        payment['user_id'],
                        months=payment.get('months', 1)
                    )
            
            return jsonify({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Paytm webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/phonepe', methods=['POST'])
    def phonepe_webhook():
        """Handle PhonePe payment webhook"""
        try:
            data = request.get_json()
            
            # Verify signature
            signature = request.headers.get('X-Verify')
            if not verify_phonepe_signature(payload, signature):
                return jsonify({'error': 'Invalid signature'}), 401
            
            transaction_id = data.get('transactionId')
            status = data.get('state')
            
            if status == 'COMPLETED':
                # Update payment status
                db.update_payment_status(transaction_id, 'completed')
                
                # Activate premium
                payment = db.get_payment_by_transaction_id(transaction_id)
                if payment:
                    subscription_manager.activate_premium(
                        payment['user_id'],
                        months=payment.get('months', 1)
                    )
            
            return jsonify({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"PhonePe webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/google-pay', methods=['POST'])
    def google_pay_webhook():
        """Handle Google Pay webhook"""
        try:
            data = request.get_json()
            
            # Verify JWT token
            token = request.headers.get('Authorization')
            if not verify_google_pay_token(token):
                return jsonify({'error': 'Invalid token'}), 401
            
            payment_id = data.get('paymentId')
            status = data.get('status')
            
            if status == 'SUCCESS':
                db.update_payment_status(payment_id, 'completed')
                
                # Activate premium
                payment = db.get_payment(payment_id)
                if payment:
                    subscription_manager.activate_premium(
                        payment['user_id'],
                        months=payment.get('months', 1)
                    )
            
            return jsonify({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Google Pay webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/apple-pay', methods=['POST'])
    def apple_pay_webhook():
        """Handle Apple Pay webhook"""
        try:
            data = request.get_json()
            
            # Verify payment token
            payment_token = data.get('paymentToken')
            if not verify_apple_pay_token(payment_token):
                return jsonify({'error': 'Invalid token'}), 401
            
            payment_id = data.get('paymentId')
            status = data.get('status')
            
            if status == 'SUCCESS':
                db.update_payment_status(payment_id, 'completed')
                
                # Activate premium
                payment = db.get_payment(payment_id)
                if payment:
                    subscription_manager.activate_premium(
                        payment['user_id'],
                        months=payment.get('months', 1)
                    )
            
            return jsonify({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Apple Pay webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/bitcoin', methods=['POST'])
    def bitcoin_webhook():
        """Handle Bitcoin payment webhook"""
        try:
            data = request.get_json()
            
            # Verify webhook secret
            secret = request.headers.get('X-Webhook-Secret')
            if secret != Config.BITCOIN_WEBHOOK_SECRET:
                return jsonify({'error': 'Invalid secret'}), 401
            
            tx_hash = data.get('tx_hash')
            address = data.get('address')
            amount = data.get('amount')
            confirmations = data.get('confirmations')
            
            # Find payment by address
            payment = db.get_payment_by_crypto_address(address)
            if payment and amount >= payment['crypto_amount']:
                if confirmations >= 2:
                    db.update_payment_status(payment['id'], 'completed')
                    subscription_manager.activate_premium(
                        payment['user_id'],
                        months=payment.get('months', 1)
                    )
            
            return jsonify({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Bitcoin webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/ethereum', methods=['POST'])
    def ethereum_webhook():
        """Handle Ethereum payment webhook"""
        try:
            data = request.get_json()
            
            # Verify webhook secret
            secret = request.headers.get('X-Webhook-Secret')
            if secret != Config.ETHEREUM_WEBHOOK_SECRET:
                return jsonify({'error': 'Invalid secret'}), 401
            
            tx_hash = data.get('transactionHash')
            address = data.get('to')
            amount = data.get('value')
            confirmations = data.get('confirmations')
            
            # Find payment by address
            payment = db.get_payment_by_crypto_address(address)
            if payment and amount >= payment['crypto_amount']:
                if confirmations >= 12:
                    db.update_payment_status(payment['id'], 'completed')
                    subscription_manager.activate_premium(
                        payment['user_id'],
                        months=payment.get('months', 1)
                    )
            
            return jsonify({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"Ethereum webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @staticmethod
    @webhooks_bp.route('/usdt', methods=['POST'])
    def usdt_webhook():
        """Handle USDT (TRC-20) payment webhook"""
        try:
            data = request.get_json()
            
            # Verify webhook secret
            secret = request.headers.get('X-Webhook-Secret')
            if secret != Config.USDT_WEBHOOK_SECRET:
                return jsonify({'error': 'Invalid secret'}), 401
            
            tx_hash = data.get('transaction_id')
            address = data.get('to')
            amount = data.get('amount')
            confirmations = data.get('confirmations')
            
            # Find payment by address
            payment = db.get_payment_by_crypto_address(address)
            if payment and amount >= payment['crypto_amount']:
                if confirmations >= 1:
                    db.update_payment_status(payment['id'], 'completed')
                    subscription_manager.activate_premium(
                        payment['user_id'],
                        months=payment.get('months', 1)
                    )
            
            return jsonify({'status': 'ok'})
            
        except Exception as e:
            logger.error(f"USDT webhook error: {e}")
            return jsonify({'error': str(e)}), 500

# Helper functions (to be implemented)
def verify_whatsapp_signature(payload, signature):
    """Verify WhatsApp webhook signature"""
    # Implementation
    return True

def send_whatsapp_reply(to_number, message):
    """Send WhatsApp reply"""
    # Implementation
    pass

def verify_github_signature(payload, signature):
    """Verify GitHub webhook signature"""
    # Implementation
    return True

def deploy_application(deployment):
    """Trigger application deployment"""
    # Implementation
    pass

def verify_cloudinary_signature(payload, signature):
    """Verify Cloudinary webhook signature"""
    # Implementation
    return True

def verify_paytm_checksum(data, checksum):
    """Verify Paytm checksum"""
    # Implementation
    return True

def verify_phonepe_signature(payload, signature):
    """Verify PhonePe signature"""
    # Implementation
    return True

def verify_google_pay_token(token):
    """Verify Google Pay token"""
    # Implementation
    return True

def verify_apple_pay_token(token):
    """Verify Apple Pay token"""
    # Implementation
    return True

def send_sms_reply(from_number, to_number, message):
    """Send SMS reply via Twilio"""
    # Implementation
    pass
