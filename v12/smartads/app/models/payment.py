from app import db
from datetime import datetime
import uuid

class Payment(db.Model):
    __tablename__  = 'payments'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ad_id          = db.Column(db.Integer, db.ForeignKey('advertisements.id'), nullable=False)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False,
                               default=lambda: f'TXN-{uuid.uuid4().hex[:12].upper()}')
    amount         = db.Column(db.Float, nullable=False)
    currency       = db.Column(db.String(10), default='INR')
    method         = db.Column(db.String(30), default='card')
    status         = db.Column(db.String(20), default='success')
    description    = db.Column(db.String(300), nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
