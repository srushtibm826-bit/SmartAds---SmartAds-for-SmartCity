from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from dotenv import load_dotenv
import os, json

load_dotenv()
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///smartads.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from app.routes.auth          import auth_bp
    from app.routes.dashboard     import dashboard_bp
    from app.routes.ads           import ads_bp
    from app.routes.payment       import payment_bp
    from app.routes.schedule      import schedule_bp
    from app.routes.admin         import admin_bp
    from app.routes.display       import display_bp
    from app.routes.notifications import notifications_bp
    from app.routes.video         import video_bp

    app.register_blueprint(auth_bp,          url_prefix='/auth')
    app.register_blueprint(dashboard_bp,     url_prefix='/dashboard')
    app.register_blueprint(ads_bp,           url_prefix='/ads')
    app.register_blueprint(payment_bp,       url_prefix='/payment')
    app.register_blueprint(schedule_bp,      url_prefix='/schedule')
    app.register_blueprint(admin_bp,         url_prefix='/admin')
    app.register_blueprint(display_bp,       url_prefix='/display')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(video_bp,         url_prefix='/video')

    @app.route('/')
    def index():
        return redirect(url_for('dashboard.home') if current_user.is_authenticated else url_for('auth.login'))

    with app.app_context():
        db.create_all()
        _seed()

    return app


def _seed():
    from app.models.user import User
    from app.models.ad import Advertisement
    from app.models.schedule import AdSchedule
    from werkzeug.security import generate_password_hash
    from datetime import datetime, timedelta

    if not User.query.filter_by(email='admin@smartads.com').first():
        db.session.add(User(name='Admin User', email='admin@smartads.com',
                            password_hash=generate_password_hash('admin123'),
                            role='admin', is_active=True))

    if not User.query.filter_by(email='demo@smartads.com').first():
        demo = User(name='Demo User', email='demo@smartads.com',
                    password_hash=generate_password_hash('demo123'),
                    role='user', is_active=True)
        db.session.add(demo)
        db.session.flush()

        ads = [
            Advertisement(user_id=demo.id, title='Summer Sale Bonanza',
                product_name='Fashion Collection', category='Fashion',
                offer='50% Off Everything', ad_format='poster',
                description='Huge summer clearance on all fashion items.',
                generated_text='Summer Sale Bonanza! Get 50% off our entire Fashion Collection. Style meets savings!',
                slogans=json.dumps(['Style Without Limits','Fashion Forward']),
                status='approved', engagement_score=87, ad_type='ai_generated',
                payment_status='paid', location='Mall Billboard', theme_color='#ec4899',
                amount_paid=500.0, created_at=datetime.utcnow() - timedelta(days=5)),
            Advertisement(user_id=demo.id, title='Tech Gadgets Launch',
                product_name='SmartHome Hub', category='Technology',
                offer='Free Installation', ad_format='video',
                description='Next-gen smart home controller.',
                generated_text='Transform Your Home! SmartHome Hub — AI-powered. Free installation this month!',
                slogans=json.dumps(['Live Smarter','Home Reinvented']),
                status='approved', engagement_score=92, ad_type='ai_generated',
                payment_status='paid', location='City Center Screen', theme_color='#6366f1',
                amount_paid=1200.0, created_at=datetime.utcnow() - timedelta(days=3)),
            Advertisement(user_id=demo.id, title='Gourmet Burger Special',
                product_name='Gourmet Burger', category='Food & Beverage',
                offer='Buy 1 Get 1 Free', ad_format='poster',
                description='Premium handcrafted burgers.',
                generated_text='Taste the Difference! Gourmet Burgers handcrafted with love. BOGO this weekend!',
                slogans=json.dumps(['Every Bite Tells a Story']),
                status='pending', engagement_score=78, ad_type='ai_generated',
                payment_status='paid', location='Food Court Display', theme_color='#f59e0b',
                amount_paid=500.0, created_at=datetime.utcnow() - timedelta(days=1)),
        ]
        db.session.add_all(ads)
        db.session.flush()

        now = datetime.utcnow()
        for i, ad in enumerate(ads[:2]):
            db.session.add(AdSchedule(
                ad_id=ad.id, user_id=demo.id, location=ad.location,
                start_time=now - timedelta(hours=1),
                end_time=now + timedelta(hours=23),
                duration_seconds=15, is_active=True))

        db.session.commit()

    # ── Seed demo AI videos for saree and burger ads ────────────────────
    _seed_demo_videos()


def _seed_demo_videos():
    """Pre-load demo AI videos so they appear instantly on video studio."""
    from app.models.advideo import AdVideo
    from app.models.ad import Advertisement
    from app.models.user import User
    from datetime import datetime

    demo = User.query.filter_by(email='demo@smartads.com').first()
    if not demo:
        return

    # Map: ad title keyword → demo video static path
    DEMO_VIDEO_MAP = {
        'Fashion':         '/static/demo_videos/saree_ad.mp4',
        'Food & Beverage': '/static/demo_videos/burger_ad.mp4',
    }

    for category, video_url in DEMO_VIDEO_MAP.items():
        # Find a matching ad for this category
        ad = Advertisement.query.filter_by(
            user_id=demo.id, category=category
        ).first()
        if not ad:
            continue

        # Check if demo video already exists
        existing = AdVideo.query.filter_by(
            ad_id=ad.id, demo_video_url=video_url
        ).first()
        if existing:
            continue

        av = AdVideo(
            ad_id        = ad.id,
            user_id      = demo.id,
            did_talk_id  = f'demo_{category.lower().replace(" ","_")}',
            status       = 'done',
            result_url   = video_url,         # served from Flask static
            demo_video_url = video_url,
            avatar_label = 'Demo AI Avatar',
            voice_id     = 'en-IN-NeerjaNeural',
            script_text  = ad.generated_text or ad.title,
            completed_at = datetime.utcnow(),
        )
        db.session.add(av)

    db.session.commit()
