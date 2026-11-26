from app import db
from datetime import datetime
import json

class Advertisement(db.Model):
    __tablename__  = 'advertisements'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title          = db.Column(db.String(200), nullable=False)
    product_name   = db.Column(db.String(150), nullable=False)
    category       = db.Column(db.String(80), nullable=False)
    offer          = db.Column(db.String(200), nullable=True)
    description    = db.Column(db.Text, nullable=True)
    location       = db.Column(db.String(100), nullable=True)
    ad_format      = db.Column(db.String(20), default='poster')   # NEW: poster | video
    amount_paid    = db.Column(db.Float, default=0.0)              # NEW: actual cost paid
    generated_text = db.Column(db.Text, nullable=True)
    slogans        = db.Column(db.Text, nullable=True)
    template_style = db.Column(db.String(50), default='modern')
    theme_color    = db.Column(db.String(20), default='#6366f1')
    media_filename = db.Column(db.String(300), nullable=True)
    media_type     = db.Column(db.String(20), nullable=True)
    ad_type        = db.Column(db.String(20), default='ai_generated')
    status         = db.Column(db.String(20), default='draft')
    admin_notes    = db.Column(db.Text, nullable=True)
    payment_status = db.Column(db.String(20), default='unpaid')
    engagement_score = db.Column(db.Integer, default=0)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at    = db.Column(db.DateTime, nullable=True)
    schedules = db.relationship('AdSchedule', backref='advertisement', lazy='dynamic', cascade='all, delete-orphan')
    payments  = db.relationship('Payment', backref='advertisement', lazy='dynamic')
    videos    = db.relationship('AdVideo', backref='advertisement', lazy='dynamic')

    def get_slogans(self):
        try: return json.loads(self.slogans) if self.slogans else []
        except: return []

    def status_badge(self):
        return {'draft':'secondary','pending':'warning','approved':'success','rejected':'danger'}.get(self.status,'secondary')

    def format_icon(self):
        return '🖼️' if self.ad_format == 'poster' else '🎬'
