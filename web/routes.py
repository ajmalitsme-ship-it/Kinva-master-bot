"""
Web Routes - Frontend Pages
Author: @kinva_master
"""

import logging
from datetime import datetime
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, g, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..database import db
from ..config import Config
from ..utils.decorators import require_auth, require_admin
from ..utils.helpers import format_file_size

logger = logging.getLogger(__name__)

web_bp = Blueprint('web', __name__)

# ============================================
# Public Routes
# ============================================

@web_bp.route('/')
def index():
    """Home page"""
    user = None
    if 'user_id' in session:
        user = db.get_user(session['user_id'])
    return render_template('index.html', user=user)

@web_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@web_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

@web_bp.route('/terms')
def terms():
    """Terms of service"""
    return render_template('terms.html')

@web_bp.route('/privacy')
def privacy():
    """Privacy policy"""
    return render_template('privacy.html')

@web_bp.route('/help')
def help_page():
    """Help & support page"""
    user = None
    if 'user_id' in session:
        user = db.get_user(session['user_id'])
    return render_template('help.html', user=user)

@web_bp.route('/templates')
def templates():
    """Templates gallery"""
    category = request.args.get('category', 'all')
    user = None
    if 'user_id' in session:
        user = db.get_user(session['user_id'])
    
    templates = db.get_templates(category=category)
    categories = db.get_template_categories()
    
    return render_template('templates.html', 
                         user=user,
                         templates=templates, 
                         categories=categories,
                         current_category=category)

@web_bp.route('/premium')
def premium():
    """Premium plans page"""
    user = None
    if 'user_id' in session:
        user = db.get_user(session['user_id'])
    
    plans = Config.PREMIUM_PLANS
    
    return render_template('premium.html', user=user, plans=plans)

@web_bp.route('/login')
def login():
    """Login page"""
    if 'user_id' in session:
        return redirect(url_for('web.dashboard'))
    return render_template('login.html')

@web_bp.route('/register')
def register():
    """Register page"""
    if 'user_id' in session:
        return redirect(url_for('web.dashboard'))
    return render_template('register.html')

@web_bp.route('/forgot-password')
def forgot_password():
    """Forgot password page"""
    return render_template('forgot-password.html')

@web_bp.route('/reset-password/<token>')
def reset_password(token):
    """Reset password page"""
    # Verify token
    reset = db.get_password_reset_token(token)
    if not reset or reset.get('expires_at') < datetime.now().isoformat():
        return render_template('error.html', message='Invalid or expired reset token'), 400
    return render_template('reset-password.html', token=token)

@web_bp.route('/verify-email/<token>')
def verify_email(token):
    """Email verification page"""
    result = db.verify_email_token(token)
    return render_template('verify-email.html', result=result)

@web_bp.route('/share/<token>')
def shared_design(token):
    """View shared design"""
    design = db.get_design_by_token(token)
    if not design:
        return render_template('404.html'), 404
    
    # Increment view count
    db.increment_design_views(design['id'])
    
    return render_template('shared-design.html', design=design)

@web_bp.route('/payment/success')
def payment_success():
    """Payment success page"""
    payment_id = request.args.get('payment_id')
    return render_template('payment-success.html', payment_id=payment_id)

@web_bp.route('/payment/cancel')
def payment_cancel():
    """Payment cancel page"""
    return render_template('payment-cancel.html')

# ============================================
# Protected Routes (Requires Auth)
# ============================================

@web_bp.route('/dashboard')
@require_auth
def dashboard():
    """User dashboard"""
    user = db.get_user(g.user_id)
    stats = db.get_user_stats(g.user_id)
    recent_projects = db.get_user_projects(g.user_id, limit=6)
    weekly_data = db.get_weekly_stats(g.user_id)
    
    return render_template('dashboard.html', 
                         user=user, 
                         stats=stats, 
                         recent_projects=recent_projects,
                         weekly_data=weekly_data)

@web_bp.route('/editor')
@require_auth
def editor():
    """Canva-style design editor"""
    user = db.get_user(g.user_id)
    templates = db.get_templates(limit=12)
    fonts = db.get_available_fonts()
    
    return render_template('editor.html', 
                         user=user, 
                         templates=templates,
                         fonts=fonts)

@web_bp.route('/video-editor')
@require_auth
def video_editor():
    """Video editor page"""
    user = db.get_user(g.user_id)
    videos = db.get_user_videos(g.user_id, limit=10)
    effects = db.get_available_effects()
    
    return render_template('video-editor.html', 
                         user=user, 
                         videos=videos,
                         effects=effects)

@web_bp.route('/image-editor')
@require_auth
def image_editor():
    """Image editor page"""
    user = db.get_user(g.user_id)
    images = db.get_user_images(g.user_id, limit=10)
    filters = db.get_available_filters()
    
    return render_template('image-editor.html', 
                         user=user, 
                         images=images,
                         filters=filters)

@web_bp.route('/profile')
@require_auth
def profile():
    """User profile page"""
    user = db.get_user(g.user_id)
    stats = db.get_user_stats(g.user_id)
    
    return render_template('profile.html', user=user, stats=stats)

@web_bp.route('/settings')
@require_auth
def settings():
    """User settings page"""
    user = db.get_user(g.user_id)
    settings = db.get_user_settings(g.user_id)
    
    return render_template('settings.html', user=user, settings=settings)

@web_bp.route('/my-works')
@require_auth
def my_works():
    """My works page"""
    user = db.get_user(g.user_id)
    designs = db.get_user_designs(g.user_id)
    videos = db.get_user_videos(g.user_id)
    images = db.get_user_images(g.user_id)
    
    return render_template('my-works.html', 
                         user=user, 
                         designs=designs, 
                         videos=videos, 
                         images=images)

@web_bp.route('/history')
@require_auth
def history():
    """Export history page"""
    user = db.get_user(g.user_id)
    exports = db.get_user_exports(g.user_id)
    
    return render_template('history.html', user=user, exports=exports)

# ============================================
# Admin Routes
# ============================================

@web_bp.route('/admin')
@require_admin
def admin():
    """Admin dashboard"""
    user = db.get_user(g.user_id)
    stats = db.get_admin_stats()
    users = db.get_all_users(limit=50)
    payments = db.get_all_payments(limit=50)
    
    return render_template('admin.html', 
                         user=user,
                         stats=stats, 
                         users=users, 
                         payments=payments)

@web_bp.route('/admin/users')
@require_admin
def admin_users():
    """Admin user management"""
    user = db.get_user(g.user_id)
    users = db.get_all_users()
    
    return render_template('admin-users.html', user=user, users=users)

@web_bp.route('/admin/templates')
@require_admin
def admin_templates():
    """Admin template management"""
    user = db.get_user(g.user_id)
    templates = db.get_all_templates()
    
    return render_template('admin-templates.html', user=user, templates=templates)

@web_bp.route('/admin/payments')
@require_admin
def admin_payments():
    """Admin payment management"""
    user = db.get_user(g.user_id)
    payments = db.get_all_payments()
    
    return render_template('admin-payments.html', user=user, payments=payments)

@web_bp.route('/admin/analytics')
@require_admin
def admin_analytics():
    """Admin analytics dashboard"""
    user = db.get_user(g.user_id)
    stats = db.get_admin_stats()
    
    return render_template('admin-analytics.html', user=user, stats=stats)

@web_bp.route('/admin/settings')
@require_admin
def admin_settings():
    """Admin settings"""
    user = db.get_user(g.user_id)
    
    return render_template('admin-settings.html', user=user)
