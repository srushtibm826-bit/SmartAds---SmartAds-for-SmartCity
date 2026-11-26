from app import db
from datetime import datetime

class AdSchedule(db.Model):
    __tablename__    = 'ad_schedules'
    id               = db.Column(db.Integer, primary_key=True)
    ad_id            = db.Column(db.Integer, db.ForeignKey('advertisements.id'), nullable=False, index=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    location         = db.Column(db.String(100), nullable=False)
    start_time       = db.Column(db.DateTime, nullable=False)
    end_time         = db.Column(db.DateTime, nullable=False)
    duration_seconds = db.Column(db.Integer, default=30)
    is_active        = db.Column(db.Boolean, default=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
