from app import db
from datetime import datetime

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
