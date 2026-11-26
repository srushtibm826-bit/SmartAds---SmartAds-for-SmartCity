from app import db
from datetime import datetime

class AdVideo(db.Model):
    __tablename__ = 'ad_videos'
    id            = db.Column(db.Integer, primary_key=True)
    ad_id         = db.Column(db.Integer, db.ForeignKey('advertisements.id'), nullable=False)
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
    demo_video_url = db.Column(db.String(500), nullable=True)   # pre-loaded demo video
    completed_at  = db.Column(db.DateTime, nullable=True)
    def status_badge(self):
        return {'pending':('warning','⏳ Queued'),'processing':('info','🔄 Generating'),
                'done':('success','✅ Ready'),'error':('danger','❌ Failed')}.get(self.status,('secondary',self.status))
