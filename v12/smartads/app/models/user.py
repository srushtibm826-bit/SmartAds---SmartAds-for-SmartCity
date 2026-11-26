from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

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
    advertisements = db.relationship('Advertisement', backref='owner', lazy='dynamic', foreign_keys='Advertisement.user_id')
    payments       = db.relationship('Payment', backref='user', lazy='dynamic')
    schedules      = db.relationship('AdSchedule', backref='user', lazy='dynamic', foreign_keys='AdSchedule.user_id')
    notifications  = db.relationship('Notification', backref='user', lazy='dynamic')
    videos         = db.relationship('AdVideo', backref='user', lazy='dynamic')
    def is_admin(self): return self.role == 'admin'
    def unread_count(self): return self.notifications.filter_by(is_read=False).count()

@login_manager.user_loader
def load_user(uid): return User.query.get(int(uid))
