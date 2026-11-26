from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.user import User
from app.models.ad import Advertisement
from app.models.payment import Payment
from app.models.schedule import AdSchedule
from app.models.notification import Notification
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('dashboard.home'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/')
@admin_required
def index():
    total_users = User.query.count()
    total_ads   = Advertisement.query.count()
    pending_ads = Advertisement.query.filter_by(status='pending').count()
    total_rev   = db.session.query(db.func.sum(Payment.amount))\
                  .filter_by(status='success').scalar() or 0
    recent_ads  = Advertisement.query.order_by(Advertisement.created_at.desc()).limit(5).all()
    return render_template('admin/index.html',
        total_users=total_users, total_ads=total_ads,
        pending_ads=pending_ads, total_rev=total_rev,
        recent_ads=recent_ads)

@admin_bp.route('/ads')
@admin_required
def ads():
    # ── Filters ──────────────────────────────────────────────────────────
    status     = request.args.get('status','all')
    ad_format  = request.args.get('ad_format','all')
    category   = request.args.get('category','all')
    from_date  = request.args.get('from_date','')
    to_date    = request.args.get('to_date','')
    search     = request.args.get('search','').strip()

    q = Advertisement.query

    if status != 'all':
        q = q.filter(Advertisement.status == status)
    if ad_format != 'all':
        q = q.filter(Advertisement.ad_format == ad_format)
    if category != 'all':
        q = q.filter(Advertisement.category == category)
    if from_date:
        try:
            q = q.filter(Advertisement.created_at >= datetime.strptime(from_date,'%Y-%m-%d'))
        except: pass
    if to_date:
        try:
            from datetime import timedelta
            q = q.filter(Advertisement.created_at < datetime.strptime(to_date,'%Y-%m-%d') + timedelta(days=1))
        except: pass
    if search:
        q = q.filter(db.or_(
            Advertisement.title.ilike(f'%{search}%'),
            Advertisement.product_name.ilike(f'%{search}%')))

    ads  = q.order_by(Advertisement.created_at.desc()).all()
    total = q.count()

    # All categories for filter dropdown
    categories = [r[0] for r in db.session.query(Advertisement.category).distinct().all()]

    return render_template('admin/ads.html',
        ads=ads, total=total,
        status=status, ad_format=ad_format,
        category=category, from_date=from_date, to_date=to_date,
        search=search, categories=categories)

@admin_bp.route('/ads/<int:ad_id>/approve', methods=['POST'])
@admin_required
def approve_ad(ad_id):
    ad = Advertisement.query.get_or_404(ad_id)
    ad.status      = 'approved'
    ad.approved_at = datetime.utcnow()
    db.session.add(Notification(
        user_id=ad.user_id, title='Ad Approved! ✅',
        message=f'Your ad "{ad.title}" has been approved and is now live.',
        type='success', link=url_for('ads.preview', ad_id=ad.id)))
    db.session.commit()
    flash(f'Ad "{ad.title}" approved.', 'success')
    return redirect(url_for('admin.ads'))

@admin_bp.route('/ads/<int:ad_id>/reject', methods=['POST'])
@admin_required
def reject_ad(ad_id):
    ad     = Advertisement.query.get_or_404(ad_id)
    reason = request.form.get('reason','Does not meet guidelines.')
    ad.status      = 'rejected'
    ad.admin_notes = reason
    db.session.add(Notification(
        user_id=ad.user_id, title='Ad Rejected',
        message=f'Your ad "{ad.title}" was rejected. Reason: {reason}',
        type='danger', link=url_for('ads.preview', ad_id=ad.id)))
    db.session.commit()
    flash(f'Ad "{ad.title}" rejected.', 'info')
    return redirect(url_for('admin.ads'))

@admin_bp.route('/users')
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)

@admin_bp.route('/users/<int:uid>/toggle', methods=['POST'])
@admin_required
def toggle_user(uid):
    u = User.query.get_or_404(uid)
    if u.id == current_user.id:
        flash('Cannot deactivate yourself.', 'danger')
    else:
        u.is_active = not u.is_active
        db.session.commit()
        flash(f'User {"activated" if u.is_active else "deactivated"}.', 'info')
    return redirect(url_for('admin.users'))

@admin_bp.route('/payments')
@admin_required
def payments():
    pays = Payment.query.order_by(Payment.created_at.desc()).all()
    total = sum(p.amount for p in pays if p.status == 'success')
    return render_template('admin/payments.html', payments=pays, total=total)

@admin_bp.route('/schedules')
@admin_required
def schedules():
    scheds = AdSchedule.query.order_by(AdSchedule.created_at.desc()).all()
    return render_template('admin/schedules.html', schedules=scheds)
