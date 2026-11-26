from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.ad import Advertisement
from app.models.payment import Payment
from app.models.schedule import AdSchedule
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def home():
    ads      = Advertisement.query.filter_by(user_id=current_user.id).order_by(Advertisement.created_at.desc()).limit(5).all()
    total    = Advertisement.query.filter_by(user_id=current_user.id).count()
    approved = Advertisement.query.filter_by(user_id=current_user.id, status='approved').count()
    spend    = sum(p.amount for p in Payment.query.filter_by(user_id=current_user.id, status='success').all())
    active   = AdSchedule.query.filter_by(user_id=current_user.id, is_active=True)\
                .filter(AdSchedule.end_time > datetime.utcnow()).count()
    return render_template('dashboard/home.html',
        ads=ads, total_ads=total, approved_ads=approved,
        total_spend=spend, active_schedules=active)
