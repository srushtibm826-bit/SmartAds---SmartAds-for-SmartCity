from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.schedule import AdSchedule
from app.models.ad import Advertisement
from datetime import datetime

schedule_bp = Blueprint('schedule', __name__)

@schedule_bp.route('/')
@login_required
def index():
    schedules = AdSchedule.query.filter_by(user_id=current_user.id)\
                .order_by(AdSchedule.created_at.desc()).all()
    return render_template('schedule/index.html', schedules=schedules)

@schedule_bp.route('/new/<int:ad_id>', methods=['GET','POST'])
@login_required
def new_schedule(ad_id):
    ad = Advertisement.query.filter_by(id=ad_id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        location   = request.form.get('location')
        start_str  = request.form.get('start_time')
        end_str    = request.form.get('end_time')
        try:
            start = datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
            end   = datetime.strptime(end_str,   '%Y-%m-%dT%H:%M')
        except Exception:
            flash('Invalid date/time format.', 'danger')
            return redirect(request.url)
        if end <= start:
            flash('End time must be after start time.', 'danger')
            return redirect(request.url)
        sched = AdSchedule(ad_id=ad.id, user_id=current_user.id,
                           location=location, start_time=start, end_time=end,
                           duration_seconds=int(request.form.get('duration',30)),
                           is_active=True)
        db.session.add(sched)
        db.session.commit()
        flash('Schedule created!', 'success')
        return redirect(url_for('schedule.index'))
    return render_template('schedule/new.html', ad=ad)

@schedule_bp.route('/<int:sched_id>/cancel', methods=['POST'])
@login_required
def cancel(sched_id):
    s = AdSchedule.query.filter_by(id=sched_id, user_id=current_user.id).first_or_404()
    s.is_active = False
    db.session.commit()
    flash('Schedule cancelled.', 'info')
    return redirect(url_for('schedule.index'))

@schedule_bp.route('/api/active')
def api_active():
    now = datetime.utcnow()
    rows = AdSchedule.query.filter(
        AdSchedule.is_active==True,
        AdSchedule.start_time<=now,
        AdSchedule.end_time>=now).all()
    return jsonify([{
        'location': r.location,
        'ad_title': r.advertisement.title if r.advertisement else '',
        'start': r.start_time.isoformat(),
        'end':   r.end_time.isoformat(),
    } for r in rows])
