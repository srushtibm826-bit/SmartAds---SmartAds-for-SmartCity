from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import json, uuid


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20), default='user')
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login    = db.Column(db.DateTime, nullable=True)

    advertisements = db.relationship('Advertisement', backref='owner',   lazy='dynamic', foreign_keys='Advertisement.user_id')
    payments       = db.relationship('Payment',       backref='user',    lazy='dynamic')
    schedules      = db.relationship('AdSchedule',    backref='user',    lazy='dynamic', foreign_keys='AdSchedule.user_id')
    notifications  = db.relationship('Notification',  backref='user',    lazy='dynamic')
    videos         = db.relationship('AdVideo',       backref='user',    lazy='dynamic')

    def is_admin(self): return self.role == 'admin'
    def unread_count(self): return self.notifications.filter_by(is_read=False).count()


@login_manager.user_loader
def load_user(uid): return User.query.get(int(uid))


class Advertisement(db.Model):
    __tablename__ = 'advertisements'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title          = db.Column(db.String(200), nullable=False)
    product_name   = db.Column(db.String(150), nullable=False)
    category       = db.Column(db.String(80),  nullable=False)
    offer          = db.Column(db.String(200),  nullable=True)
    description    = db.Column(db.Text,         nullable=True)
    location       = db.Column(db.String(100),  nullable=True)
    # ── NEW: format (poster / video) ──
    ad_format      = db.Column(db.String(20),   default='poster')   # 'poster' | 'video'
    amount_paid    = db.Column(db.Float,         default=0.0)        # actual amount paid
    generated_text = db.Column(db.Text,         nullable=True)
    slogans        = db.Column(db.Text,         nullable=True)
    template_style = db.Column(db.String(50),   default='modern')
    theme_color    = db.Column(db.String(20),   default='#6366f1')
    media_filename = db.Column(db.String(300),  nullable=True)
    media_type     = db.Column(db.String(20),   nullable=True)
    ad_type        = db.Column(db.String(20),   default='ai_generated')
    status         = db.Column(db.String(20),   default='draft')
    admin_notes    = db.Column(db.Text,         nullable=True)
    payment_status = db.Column(db.String(20),   default='unpaid')
    engagement_score = db.Column(db.Integer,    default=0)
    created_at     = db.Column(db.DateTime,     default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime,     default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at    = db.Column(db.DateTime,     nullable=True)

    schedules = db.relationship('AdSchedule', backref='advertisement', lazy='dynamic', cascade='all, delete-orphan')
    payments  = db.relationship('Payment',    backref='advertisement', lazy='dynamic')
    videos    = db.relationship('AdVideo',    backref='advertisement', lazy='dynamic')

    def get_slogans(self):
        try: return json.loads(self.slogans) if self.slogans else []
        except: return []

    def status_badge(self):
        return {'draft':'secondary','pending':'warning','approved':'success','rejected':'danger'}.get(self.status,'secondary')

    def format_badge(self):
        return {'poster': ('info','🖼️ Poster'), 'video': ('purple','🎬 Video')}.get(self.ad_format, ('secondary','?'))


class Payment(db.Model):
    __tablename__  = 'payments'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ad_id          = db.Column(db.Integer, db.ForeignKey('advertisements.id'), nullable=False)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False,
                               default=lambda: f'TXN-{uuid.uuid4().hex[:12].upper()}')
    amount         = db.Column(db.Float,   nullable=False)
    currency       = db.Column(db.String(10), default='INR')
    method         = db.Column(db.String(30), default='card')
    status         = db.Column(db.String(20), default='success')
    description    = db.Column(db.String(300), nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)


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


class Notification(db.Model):
    __tablename__ = 'notifications'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title      = db.Column(db.String(200), nullable=False)
    message    = db.Column(db.Text, nullable=False)
    type       = db.Column(db.String(30), default='info')
    is_read    = db.Column(db.Boolean, default=False)
    link       = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def icon(self):
        return {'info':'bi-info-circle-fill','success':'bi-check-circle-fill',
                'warning':'bi-exclamation-triangle-fill','danger':'bi-x-circle-fill'}.get(self.type,'bi-bell-fill')


class AdVideo(db.Model):
    __tablename__ = 'ad_videos'
    id            = db.Column(db.Integer, primary_key=True)
    ad_id         = db.Column(db.Integer, db.ForeignKey('advertisements.id'), nullable=False, index=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    did_talk_id   = db.Column(db.String(100), nullable=True)
    status        = db.Column(db.String(30), default='pending')
    result_url    = db.Column(db.String(500), nullable=True)
    error_msg     = db.Column(db.Text, nullable=True)
    avatar_label  = db.Column(db.String(100), nullable=True)
    avatar_image  = db.Column(db.String(500), nullable=True)
    voice_id      = db.Column(db.String(100), nullable=True)
    script_text   = db.Column(db.Text, nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at  = db.Column(db.DateTime, nullable=True)

    def status_badge(self):
        return {'pending':('warning','⏳ Queued'),'processing':('info','🔄 Generating'),
                'done':('success','✅ Ready'),'error':('danger','❌ Failed')}.get(self.status,('secondary',self.status))
