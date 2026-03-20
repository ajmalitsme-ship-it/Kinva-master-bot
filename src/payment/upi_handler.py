"""
UPI Payment Handler - Indian UPI payments with QR codes
Author: @kinva_master
"""

import os
import logging
import qrcode
import base64
import hashlib
import hmac
import json
from io import BytesIO
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests

from ..config import Config
from ..database import db

logger = logging.getLogger(__name__)

class UPIHandler:
    """UPI payment processing for Indian users"""
    
    def __init__(self):
        self.upi_id = Config.UPI_ID
        self.merchant_name = Config.MERCHANT_NAME
        self.merchant_code = Config.MERCHANT_CODE
        self.merchant_vpa = Config.MERCHANT_VPA or Config.UPI_ID
        
        # UPI apps with their intent schemes
        self.upi_apps = {
            'googlepay': {
                'name': 'Google Pay',
                'scheme': 'gpay://upi/pay',
                'package': 'com.google.android.apps.nbu.paisa.user',
                'icon': '📱',
                'color': '#4285F4'
            },
            'phonepe': {
                'name': 'PhonePe',
                'scheme': 'phonepe://upi/pay',
                'package': 'com.phonepe.app',
                'icon': '📱',
                'color': '#5F259F'
            },
            'paytm': {
                'name': 'Paytm',
                'scheme': 'paytmmp://upi/pay',
                'package': 'net.one97.paytm',
                'icon': '📱',
                'color': '#003B71'
            },
            'bhim': {
                'name': 'BHIM UPI',
                'scheme': 'bhim://upi/pay',
                'package': 'in.org.npci.upiapp',
                'icon': '📱',
                'color': '#FF9933'
            },
            'amazonpay': {
                'name': 'Amazon Pay',
                'scheme': 'amazonpay://upi/pay',
                'package': 'in.amazon.mShop.android.shopping',
                'icon': '📱',
                'color': '#FF9900'
            },
            'whatsapp': {
                'name': 'WhatsApp Pay',
                'scheme': 'whatsapp://pay',
                'package': 'com.whatsapp',
                'icon': '📱',
                'color': '#25D366'
            }
        }
        
        # UPI transaction status
        self.transaction_status = {
            'pending': 'Pending',
            'success': 'Success',
            'failed': 'Failed',
            'refunded': 'Refunded'
        }
    
    def generate_qr(self, amount: float, user_id: int, plan: str, 
                    description: str = None) -> Dict:
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
            upi_params = {
                'pa': self.upi_id,
                'pn': self.merchant_name,
                'am': amount,
                'tn': description or f'Payment for Kinva Master - {plan} plan',
                'cu': 'INR'
            }
            
            upi_url = self._create_upi_url(upi_params)
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                box_size=10,
                border=4,
                error_correction=qrcode.constants.ERROR_CORRECT_H
            )
            qr.add_data(upi_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            # Generate deep links for each UPI app
            app_links = {}
            for app_id, app in self.upi_apps.items():
                app_links[app_id] = self._create_app_link(app['scheme'], upi_params)
            
            return {
                'payment_id': payment_id,
                'qr_code': qr_base64,
                'upi_url': upi_url,
                'amount': amount,
                'upi_id': self.upi_id,
                'merchant_name': self.merchant_name,
                'apps': app_links,
                'expires_in': 3600  # 1 hour
            }
            
        except Exception as e:
            logger.error(f"Generate QR error: {e}")
            raise
    
    def _create_upi_url(self, params: Dict) -> str:
        """Create UPI intent URL"""
        url_params = []
        for key, value in params.items():
            url_params.append(f"{key}={value}")
        return f"upi://pay?{'&'.join(url_params)}"
    
    def _create_app_link(self, scheme: str, params: Dict) -> str:
        """Create deep link for specific UPI app"""
        url_params = []
        for key, value in params.items():
            url_params.append(f"{key}={value}")
        return f"{scheme}?{'&'.join(url_params)}"
    
    def verify_payment(self, payment_id: str, transaction_id: str = None, 
                       upi_ref: str = None) -> Dict:
        """Verify UPI payment (manual verification)"""
        try:
            payment = db.get_payment(payment_id)
            if not payment:
                return {'status': 'failed', 'message': 'Payment not found'}
            
            # In production, integrate with NPCI/UPI API for automatic verification
            # For demo, we'll simulate verification
            
            # Check if payment is already processed
            if payment['status'] == 'completed':
                return {'status': 'success', 'message': 'Payment already verified'}
            
            # Update payment status
            update_data = {
                'status': 'completed',
                'transaction_id': transaction_id,
                'upi_ref': upi_ref,
                'verified_at': datetime.now().isoformat()
            }
            db.update_payment(payment_id, update_data)
            
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
                return {'status': 'success', 'message': 'Lifetime premium activated'}
            
            db.activate_premium(payment['user_id'], months=months)
            
            # Create notification
            db.create_notification(
                user_id=payment['user_id'],
                title='Payment Successful! 🎉',
                message=f'Your UPI payment of ₹{payment["amount"]} has been verified. {plan.capitalize()} plan activated!',
                type='success'
            )
            
            return {
                'status': 'success',
                'message': f'{plan.capitalize()} plan activated',
                'transaction_id': transaction_id,
                'upi_ref': upi_ref
            }
            
        except Exception as e:
            logger.error(f"Verify payment error: {e}")
            return {'status': 'failed', 'message': str(e)}
    
    def get_payment_status(self, payment_id: str) -> Dict:
        """Get payment status"""
        try:
            payment = db.get_payment(payment_id)
            if not payment:
                return {'status': 'not_found', 'message': 'Payment not found'}
            
            return {
                'status': payment['status'],
                'amount': payment['amount'],
                'currency': payment['currency'],
                'plan': payment['plan'],
                'created_at': payment['created_at'],
                'verified_at': payment.get('verified_at'),
                'transaction_id': payment.get('transaction_id')
            }
            
        except Exception as e:
            logger.error(f"Get payment status error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def create_payment_link(self, amount: float, user_id: int, 
                           plan: str, description: str = None) -> Dict:
        """Create payment link for UPI"""
        try:
            payment_id = db.create_payment(
                user_id=user_id,
                amount=amount,
                currency='INR',
                plan=plan,
                method='upi',
                status='pending'
            )
            
            payment_link = f"{Config.WEBAPP_URL}/payment/upi?payment_id={payment_id}&amount={amount}"
            
            return {
                'payment_id': payment_id,
                'payment_link': payment_link,
                'qr_code': self.generate_qr(amount, user_id, plan, description)['qr_code'],
                'amount': amount
            }
            
        except Exception as e:
            logger.error(f"Create payment link error: {e}")
            raise
    
    def get_upi_apps(self) -> Dict:
        """Get list of supported UPI apps"""
        return self.upi_apps
    
    def get_transaction_status(self, transaction_id: str) -> str:
        """Get transaction status from NPCI (simplified)"""
        # In production, integrate with NPCI API
        return self.transaction_status.get('pending', 'Pending')
    
    def initiate_refund(self, payment_id: str, amount: float = None) -> Dict:
        """Initiate refund for UPI payment"""
        try:
            payment = db.get_payment(payment_id)
            if not payment:
                return {'status': 'failed', 'message': 'Payment not found'}
            
            if payment['status'] != 'completed':
                return {'status': 'failed', 'message': 'Payment not completed'}
            
            refund_amount = amount or payment['amount']
            
            # In production, initiate refund through payment gateway
            # For demo, we'll simulate
            
            db.update_payment(payment_id, {
                'status': 'refunded',
                'refund_amount': refund_amount,
                'refunded_at': datetime.now().isoformat()
            })
            
            db.create_notification(
                user_id=payment['user_id'],
                title='Refund Processed',
                message=f'Refund of ₹{refund_amount} has been processed. Amount will reflect in 3-5 business days.',
                type='info'
            )
            
            return {
                'status': 'success',
                'message': 'Refund initiated',
                'refund_amount': refund_amount
            }
            
        except Exception as e:
            logger.error(f"Initiate refund error: {e}")
            return {'status': 'failed', 'message': str(e)}
    
    def generate_collect_request(self, amount: float, user_id: int,
                                 purpose: str, expires_in: int = 24) -> Dict:
        """Generate UPI collect request (for requesting payments)"""
        try:
            collect_id = db.create_collect_request(
                user_id=user_id,
                amount=amount,
                purpose=purpose,
                expires_in=expires_in
            )
            
            collect_url = f"https://kinva-master.com/pay/{collect_id}"
            
            return {
                'collect_id': collect_id,
                'collect_url': collect_url,
                'amount': amount,
                'purpose': purpose,
                'expires_in': expires_in
            }
            
        except Exception as e:
            logger.error(f"Generate collect request error: {e}")
            raise
    
    def verify_collect_payment(self, collect_id: str, transaction_id: str) -> Dict:
        """Verify collect request payment"""
        try:
            collect = db.get_collect_request(collect_id)
            if not collect:
                return {'status': 'failed', 'message': 'Collect request not found'}
            
            if collect['status'] == 'completed':
                return {'status': 'success', 'message': 'Already paid'}
            
            if collect['expires_at'] and datetime.fromisoformat(collect['expires_at']) < datetime.now():
                return {'status': 'failed', 'message': 'Request expired'}
            
            # Update collect request
            db.update_collect_request(collect_id, {
                'status': 'completed',
                'transaction_id': transaction_id,
                'paid_at': datetime.now().isoformat()
            })
            
            # Activate premium
            db.activate_premium(collect['user_id'], months=1)
            
            return {
                'status': 'success',
                'message': 'Payment received',
                'amount': collect['amount']
            }
            
        except Exception as e:
            logger.error(f"Verify collect payment error: {e}")
            return {'status': 'failed', 'message': str(e)}
    
    def generate_bharat_qr(self, amount: float, user_id: int, plan: str) -> Dict:
        """Generate BharatQR (interoperable QR code)"""
        try:
            # BharatQR format (ISO 18004)
            bharat_qr_data = {
                'payee': {
                    'name': self.merchant_name,
                    'vpa': self.upi_id,
                    'merchant_code': self.merchant_code
                },
                'amount': amount,
                'currency': 'INR',
                'purpose': f'Kinva Master {plan} Plan'
            }
            
            qr_data = json.dumps(bharat_qr_data)
            
            # Generate QR
            qr = qrcode.QRCode(version=2, box_size=10, border=4)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            return {
                'qr_code': qr_base64,
                'qr_data': qr_data,
                'amount': amount
            }
            
        except Exception as e:
            logger.error(f"Generate BharatQR error: {e}")
            raise
    
    def simulate_payment(self, payment_id: str) -> Dict:
        """Simulate payment for testing (development only)"""
        if Config.DEBUG:
            return self.verify_payment(payment_id, f"TEST_{int(datetime.now().timestamp())}")
        return {'status': 'failed', 'message': 'Simulation only available in debug mode'}

# Create global instance
upi_handler = UPIHandler()
