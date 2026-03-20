"""
Subscription Manager - Handles subscription plans, renewals, and management
Author: @kinva_master
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import asyncio

from ..database import db
from ..config import Config

logger = logging.getLogger(__name__)

class SubscriptionManager:
    """Subscription plan management with auto-renewal and notifications"""
    
    def __init__(self):
        # Premium plans with Indian pricing
        self.plans = {
            'free': {
                'id': 'free',
                'name': 'Free',
                'price': 0,
                'price_inr': 0,
                'currency': 'INR',
                'interval': 'forever',
                'features': [
                    'Basic video editing (up to 60s)',
                    '10 image filters',
                    '100+ templates',
                    '720p export',
                    'Watermark: @kinva_master.com',
                    '3 exports per day',
                    '100MB cloud storage'
                ],
                'limits': {
                    'video_length': 60,
                    'exports_per_day': 3,
                    'storage': 100 * 1024 * 1024,
                    'max_file_size': 50 * 1024 * 1024,
                    'max_video_size': 500 * 1024 * 1024,
                    'filters': 10,
                    'templates': 100
                },
                'popular': False,
                'recommended': False
            },
            'basic': {
                'id': 'basic',
                'name': 'Basic',
                'price': 9.99,
                'price_inr': 499,
                'currency': 'USD',
                'interval': 'month',
                'features': [
                    '1080p video export',
                    '20 image filters',
                    '500+ templates',
                    'No watermark',
                    '50 exports per day',
                    '5GB cloud storage',
                    'Priority email support',
                    'Remove ads'
                ],
                'limits': {
                    'video_length': 1800,
                    'exports_per_day': 50,
                    'storage': 5 * 1024 * 1024 * 1024,
                    'max_file_size': 200 * 1024 * 1024,
                    'max_video_size': 1024 * 1024 * 1024,
                    'filters': 20,
                    'templates': 500
                },
                'popular': False,
                'recommended': False,
                'discount': 0
            },
            'pro': {
                'id': 'pro',
                'name': 'Pro',
                'price': 14.99,
                'price_inr': 799,
                'currency': 'USD',
                'interval': 'month',
                'features': [
                    '4K video export',
                    'All 30+ image filters',
                    '1000+ templates',
                    'No watermark',
                    'Unlimited exports',
                    '10GB cloud storage',
                    'Priority support',
                    'API access',
                    'Custom watermark removal',
                    'Advanced effects'
                ],
                'limits': {
                    'video_length': 7200,
                    'exports_per_day': 999999,
                    'storage': 10 * 1024 * 1024 * 1024,
                    'max_file_size': 500 * 1024 * 1024,
                    'max_video_size': 2 * 1024 * 1024 * 1024,
                    'filters': 999,
                    'templates': 1000
                },
                'popular': True,
                'recommended': True,
                'discount': 0
            },
            'pro_yearly': {
                'id': 'pro_yearly',
                'name': 'Pro Yearly',
                'price': 119.99,
                'price_inr': 5999,
                'currency': 'USD',
                'interval': 'year',
                'features': [
                    '4K video export',
                    'All 30+ image filters',
                    '1000+ templates',
                    'No watermark',
                    'Unlimited exports',
                    '10GB cloud storage',
                    'Priority support',
                    'API access',
                    'Custom watermark removal',
                    'Advanced effects',
                    '2 months free',
                    'Save 33%'
                ],
                'limits': {
                    'video_length': 7200,
                    'exports_per_day': 999999,
                    'storage': 10 * 1024 * 1024 * 1024,
                    'max_file_size': 500 * 1024 * 1024,
                    'max_video_size': 2 * 1024 * 1024 * 1024,
                    'filters': 999,
                    'templates': 1000
                },
                'popular': True,
                'recommended': True,
                'discount': 20
            },
            'business': {
                'id': 'business',
                'name': 'Business',
                'price': 29.99,
                'price_inr': 1499,
                'currency': 'USD',
                'interval': 'month',
                'features': [
                    'Everything in Pro',
                    'Team collaboration (5 users)',
                    'Custom branding',
                    'White-label export',
                    'Dedicated support',
                    '100GB cloud storage',
                    'Analytics dashboard',
                    'API rate limits: 1000/min'
                ],
                'limits': {
                    'video_length': 14400,
                    'exports_per_day': 999999,
                    'storage': 100 * 1024 * 1024 * 1024,
                    'max_file_size': 1024 * 1024 * 1024,
                    'max_video_size': 5 * 1024 * 1024 * 1024,
                    'team_members': 5,
                    'filters': 999,
                    'templates': 999
                },
                'popular': False,
                'recommended': False,
                'discount': 0
            },
            'business_yearly': {
                'id': 'business_yearly',
                'name': 'Business Yearly',
                'price': 299.99,
                'price_inr': 14999,
                'currency': 'USD',
                'interval': 'year',
                'features': [
                    'Everything in Pro',
                    'Team collaboration (5 users)',
                    'Custom branding',
                    'White-label export',
                    'Dedicated support',
                    '100GB cloud storage',
                    'Analytics dashboard',
                    'API rate limits: 1000/min',
                    '3 months free',
                    'Save 20%'
                ],
                'limits': {
                    'video_length': 14400,
                    'exports_per_day': 999999,
                    'storage': 100 * 1024 * 1024 * 1024,
                    'max_file_size': 1024 * 1024 * 1024,
                    'max_video_size': 5 * 1024 * 1024 * 1024,
                    'team_members': 5,
                    'filters': 999,
                    'templates': 999
                },
                'popular': False,
                'recommended': False,
                'discount': 20
            },
            'enterprise': {
                'id': 'enterprise',
                'name': 'Enterprise',
                'price': 99.99,
                'price_inr': 4999,
                'currency': 'USD',
                'interval': 'month',
                'features': [
                    'Everything in Business',
                    'Unlimited team members',
                    'Custom development',
                    '24/7 dedicated support',
                    'On-premise deployment',
                    'SLA guarantee 99.99%',
                    'Priority feature requests',
                    'Account manager'
                ],
                'limits': {
                    'video_length': 86400,
                    'exports_per_day': 999999,
                    'storage': 10 * 1024 * 1024 * 1024 * 1024,
                    'max_file_size': 10 * 1024 * 1024 * 1024,
                    'team_members': 999,
                    'filters': 999,
                    'templates': 999
                },
                'popular': False,
                'recommended': False,
                'discount': 0,
                'custom': True
            }
        }
        
        # Annual discount percentage
        self.yearly_discount = 20
        
        # Trial period in days
        self.trial_days = 7
        
        # Grace period in days after expiry
        self.grace_period_days = 3
    
    def get_plan(self, plan_id: str) -> Optional[Dict]:
        """Get plan details by ID"""
        return self.plans.get(plan_id)
    
    def get_all_plans(self, include_free: bool = True) -> List[Dict]:
        """Get all available plans"""
        plans = []
        for plan_id, plan in self.plans.items():
            if not include_free and plan_id == 'free':
                continue
            plans.append(plan)
        return plans
    
    def get_plans_by_interval(self, interval: str) -> List[Dict]:
        """Get plans by billing interval"""
        return [p for p in self.plans.values() if p.get('interval') == interval]
    
    def get_yearly_plan(self, plan_id: str) -> Optional[Dict]:
        """Get yearly version of a monthly plan"""
        yearly_plan_id = f"{plan_id}_yearly"
        return self.plans.get(yearly_plan_id)
    
    def calculate_yearly_price(self, monthly_price: float) -> float:
        """Calculate yearly price with discount"""
        yearly = monthly_price * 12
        discount = yearly * (self.yearly_discount / 100)
        return yearly - discount
    
    def get_recommended_plan(self) -> Optional[Dict]:
        """Get recommended plan"""
        for plan in self.plans.values():
            if plan.get('recommended'):
                return plan
        return self.plans.get('pro')
    
    def get_popular_plan(self) -> Optional[Dict]:
        """Get most popular plan"""
        for plan in self.plans.values():
            if plan.get('popular'):
                return plan
        return self.plans.get('pro')
    
    def activate_subscription(self, user_id: int, plan_id: str, 
                             months: int = 1, payment_id: str = None) -> bool:
        """Activate subscription for user"""
        try:
            plan = self.get_plan(plan_id)
            if not plan:
                logger.error(f"Plan not found: {plan_id}")
                return False
            
            # Calculate expiry date
            if plan_id == 'free':
                expiry = None
            elif plan_id == 'lifetime':
                expiry = datetime.now() + timedelta(days=365*100)
                months = 0
            else:
                expiry = datetime.now() + timedelta(days=30 * months)
            
            # Update user subscription
            db.update_user_subscription(
                user_id=user_id,
                plan=plan_id,
                expiry=expiry.isoformat() if expiry else None,
                payment_id=payment_id
            )
            
            # Create subscription record
            db.create_subscription_record(
                user_id=user_id,
                plan=plan_id,
                start_date=datetime.now().isoformat(),
                end_date=expiry.isoformat() if expiry else None,
                payment_id=payment_id
            )
            
            # Create notification
            db.create_notification(
                user_id=user_id,
                title='Premium Activated! 🎉',
                message=f'Your {plan["name"]} plan is now active. Enjoy all premium features!',
                type='success'
            )
            
            logger.info(f"Subscription activated for user {user_id}: {plan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Activate subscription error: {e}")
            return False
    
    def extend_subscription(self, user_id: int, months: int = 1) -> bool:
        """Extend existing subscription"""
        try:
            user = db.get_user(user_id)
            if not user:
                return False
            
            current_expiry = user.get('premium_until')
            if current_expiry:
                current_date = datetime.fromisoformat(current_expiry)
                if current_date > datetime.now():
                    new_expiry = current_date + timedelta(days=30 * months)
                else:
                    new_expiry = datetime.now() + timedelta(days=30 * months)
            else:
                new_expiry = datetime.now() + timedelta(days=30 * months)
            
            db.update_user_subscription(
                user_id=user_id,
                plan=user.get('plan', 'pro'),
                expiry=new_expiry.isoformat()
            )
            
            # Create extension record
            db.create_subscription_extension(
                user_id=user_id,
                months=months,
                previous_expiry=current_expiry,
                new_expiry=new_expiry.isoformat()
            )
            
            # Create notification
            db.create_notification(
                user_id=user_id,
                title='Subscription Extended! 📅',
                message=f'Your subscription has been extended by {months} month(s).',
                type='success'
            )
            
            logger.info(f"Subscription extended for user {user_id}: +{months} months")
            return True
            
        except Exception as e:
            logger.error(f"Extend subscription error: {e}")
            return False
    
    def cancel_subscription(self, user_id: int, immediate: bool = False) -> bool:
        """Cancel user subscription"""
        try:
            if immediate:
                # Immediate cancellation
                db.deactivate_premium(user_id)
                db.update_user_subscription(user_id, plan='free', expiry=None)
                
                db.create_notification(
                    user_id=user_id,
                    title='Subscription Cancelled',
                    message='Your subscription has been cancelled immediately.',
                    type='info'
                )
            else:
                # Cancel at end of period
                user = db.get_user(user_id)
                if user and user.get('premium_until'):
                    db.set_cancel_at_period_end(user_id, True)
                    
                    db.create_notification(
                        user_id=user_id,
                        title='Subscription Cancelled',
                        message='Your subscription will end at the current billing period.',
                        type='info'
                    )
            
            logger.info(f"Subscription cancelled for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Cancel subscription error: {e}")
            return False
    
    def check_expiring_subscriptions(self) -> List[Dict]:
        """Check for subscriptions expiring soon"""
        try:
            expiring_soon = []
            expiring_in_days = [3, 7, 14, 30]
            
            for days in expiring_in_days:
                expiry_date = datetime.now() + timedelta(days=days)
                users = db.get_users_expiring_on(expiry_date)
                for user in users:
                    expiring_soon.append({
                        'user': user,
                        'days_left': days,
                        'expiry_date': expiry_date
                    })
            
            return expiring_soon
            
        except Exception as e:
            logger.error(f"Check expiring subscriptions error: {e}")
            return []
    
    async def send_expiry_notifications(self):
        """Send notifications for expiring subscriptions"""
        try:
            expiring = self.check_expiring_subscriptions()
            
            for item in expiring:
                user = item['user']
                days_left = item['days_left']
                
                message = (
                    f"⚠️ Your premium subscription will expire in {days_left} days!\n\n"
                    f"Don't lose access to premium features:\n"
                    f"✓ 4K Video Export\n"
                    f"✓ No Watermark\n"
                    f"✓ All Filters & Effects\n"
                    f"✓ Unlimited Exports\n\n"
                    f"Renew now to continue enjoying premium benefits!"
                )
                
                # Create notification in database
                db.create_notification(
                    user_id=user['id'],
                    title=f'Subscription Expiring in {days_left} Days!',
                    message=message,
                    type='warning'
                )
                
                # Send Telegram notification
                try:
                    from telegram import Bot
                    bot = Bot(token=Config.BOT_TOKEN)
                    await bot.send_message(
                        chat_id=user['telegram_id'],
                        text=message,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Send expiry notification error: {e}")
                    
        except Exception as e:
            logger.error(f"Send expiry notifications error: {e}")
    
    def check_expired_subscriptions(self) -> List[Dict]:
        """Check for expired subscriptions"""
        try:
            expired_users = db.get_expired_premium_users()
            
            for user in expired_users:
                # Deactivate premium
                db.deactivate_premium(user['id'])
                db.update_user_subscription(user['id'], plan='free', expiry=None)
                
                # Create notification
                db.create_notification(
                    user_id=user['id'],
                    title='Premium Expired',
                    message='Your premium subscription has expired. Upgrade again to continue enjoying premium features!',
                    type='warning'
                )
            
            return expired_users
            
        except Exception as e:
            logger.error(f"Check expired subscriptions error: {e}")
            return []
    
    def get_subscription_status(self, user_id: int) -> Dict:
        """Get user's subscription status"""
        try:
            user = db.get_user(user_id)
            if not user:
                return {'status': 'not_found'}
            
            is_premium = user.get('is_premium', False)
            plan_id = user.get('plan', 'free')
            premium_until = user.get('premium_until')
            
            plan = self.get_plan(plan_id)
            
            status = {
                'is_premium': is_premium,
                'plan': plan,
                'plan_id': plan_id,
                'expiry_date': premium_until
            }
            
            if is_premium and premium_until:
                expiry = datetime.fromisoformat(premium_until)
                days_left = (expiry - datetime.now()).days
                status['days_left'] = days_left
                status['expiring_soon'] = days_left <= 7
            
            return status
            
        except Exception as e:
            logger.error(f"Get subscription status error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_subscription_history(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get user's subscription history"""
        try:
            return db.get_subscription_history(user_id, limit)
        except Exception as e:
            logger.error(f"Get subscription history error: {e}")
            return []
    
    def get_usage_stats(self, user_id: int) -> Dict:
        """Get user's usage statistics"""
        try:
            user = db.get_user(user_id)
            plan = self.get_plan(user.get('plan', 'free'))
            limits = plan.get('limits', {})
            
            stats = db.get_user_stats(user_id)
            
            return {
                'current': {
                    'exports_today': stats.get('exports_today', 0),
                    'exports_limit': limits.get('exports_per_day', 3),
                    'storage_used': stats.get('storage_used', 0),
                    'storage_limit': limits.get('storage', 100 * 1024 * 1024),
                    'videos_edited': stats.get('videos_edited', 0),
                    'images_edited': stats.get('images_edited', 0)
                },
                'limits': limits,
                'remaining': {
                    'exports': max(0, limits.get('exports_per_day', 3) - stats.get('exports_today', 0)),
                    'storage': max(0, limits.get('storage', 0) - stats.get('storage_used', 0))
                }
            }
            
        except Exception as e:
            logger.error(f"Get usage stats error: {e}")
            return {}
    
    def upgrade_plan(self, user_id: int, new_plan_id: str) -> bool:
        """Upgrade user's plan"""
        try:
            user = db.get_user(user_id)
            current_plan = user.get('plan', 'free')
            new_plan = self.get_plan(new_plan_id)
            
            if not new_plan:
                return False
            
            # Calculate prorated amount if applicable
            prorated_amount = 0
            if current_plan != 'free':
                # Calculate prorated upgrade cost
                current_plan_data = self.get_plan(current_plan)
                remaining_days = self._get_remaining_days(user)
                current_monthly = current_plan_data.get('price', 0)
                new_monthly = new_plan.get('price', 0)
                prorated_amount = (new_monthly - current_monthly) * (remaining_days / 30)
            
            # Update subscription
            db.update_user_subscription(user_id, plan=new_plan_id)
            
            # Create upgrade record
            db.create_upgrade_record(
                user_id=user_id,
                from_plan=current_plan,
                to_plan=new_plan_id,
                prorated_amount=prorated_amount
            )
            
            # Create notification
            db.create_notification(
                user_id=user_id,
                title='Plan Upgraded! 🚀',
                message=f'Your plan has been upgraded to {new_plan["name"]}. Enjoy new features!',
                type='success'
            )
            
            logger.info(f"Plan upgraded for user {user_id}: {current_plan} -> {new_plan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Upgrade plan error: {e}")
            return False
    
    def _get_remaining_days(self, user: Dict) -> int:
        """Get remaining days in current billing cycle"""
        if not user.get('premium_until'):
            return 0
        
        expiry = datetime.fromisoformat(user['premium_until'])
        remaining = (expiry - datetime.now()).days
        return max(0, remaining)
    
    def start_free_trial(self, user_id: int) -> bool:
        """Start free trial for user"""
        try:
            user = db.get_user(user_id)
            if user.get('trial_used'):
                return False
            
            # Activate trial
            expiry = datetime.now() + timedelta(days=self.trial_days)
            db.activate_premium(user_id, months=0, trial=True)
            db.update_user_subscription(
                user_id=user_id,
                plan='pro',
                expiry=expiry.isoformat(),
                trial=True
            )
            
            # Mark trial as used
            db.set_trial_used(user_id, True)
            
            # Create notification
            db.create_notification(
                user_id=user_id,
                title='Free Trial Started! 🎁',
                message=f'You have {self.trial_days} days of premium access. Enjoy all features!',
                type='success'
            )
            
            logger.info(f"Free trial started for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Start free trial error: {e}")
            return False
    
    def apply_referral_reward(self, referrer_id: int, referred_id: int) -> bool:
        """Apply referral reward"""
        try:
            # Check if referral already rewarded
            if db.is_referral_rewarded(referrer_id, referred_id):
                return False
            
            # Give 7 days premium to referrer
            self.extend_subscription(referrer_id, months=0, days=7)
            
            # Give 3 days premium to referred user
            self.extend_subscription(referred_id, months=0, days=3)
            
            # Record referral
            db.record_referral(referrer_id, referred_id)
            
            # Create notifications
            db.create_notification(
                user_id=referrer_id,
                title='Referral Reward! 🎉',
                message='You received 7 days of premium for referring a friend!',
                type='success'
            )
            
            db.create_notification(
                user_id=referred_id,
                title='Welcome Gift! 🎁',
                message='You received 3 days of premium for joining through a referral!',
                type='success'
            )
            
            logger.info(f"Referral reward applied: {referrer_id} -> {referred_id}")
            return True
            
        except Exception as e:
            logger.error(f"Apply referral reward error: {e}")
            return False
    
    def get_referral_stats(self, user_id: int) -> Dict:
        """Get user's referral statistics"""
        try:
            referrals = db.get_user_referrals(user_id)
            active = [r for r in referrals if r.get('active', False)]
            
            return {
                'total_referrals': len(referrals),
                'active_referrals': len(active),
                'rewards_earned': len(referrals) * 7,  # 7 days per referral
                'referral_link': f"https://t.me/{Config.BOT_USERNAME}?start=ref_{user_id}"
            }
            
        except Exception as e:
            logger.error(f"Get referral stats error: {e}")
            return {}

# Create global instance
subscription_manager = SubscriptionManager()
