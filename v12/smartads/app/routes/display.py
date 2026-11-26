from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from app.models.schedule import AdSchedule
from app.models.ad import Advertisement
from datetime import datetime

display_bp = Blueprint('display', __name__)

VIRTUAL_LOCATIONS = [
    'Mall Billboard', 'City Center Screen', 'Food Court Display',
    'Highway Billboard', 'Airport Terminal', 'Metro Station'
]

DEMO_ADS = [
    {'location':'Mall Billboard',      'title':'Summer Fashion Sale','product_name':'Silk Saree Collection','category':'Fashion',         'offer':'50% Off Today','theme_color':'#ec4899','generated_text':'Step into elegance! Our Silk Saree Collection brings you timeless beauty at unbeatable prices.','slogans':['Style Without Limits'],'ad_format':'poster'},
    {'location':'City Center Screen',  'title':'SmartHome Hub Launch','product_name':'SmartHome Hub',      'category':'Technology',      'offer':'Free Install','theme_color':'#6366f1','generated_text':'Transform your home with AI-powered SmartHome Hub. Control everything with your voice.','slogans':['Live Smarter'],'ad_format':'video'},
    {'location':'Food Court Display',  'title':'Gourmet Burger Fest','product_name':'Gourmet Burger',      'category':'Food & Beverage', 'offer':'Buy 1 Get 1','theme_color':'#f59e0b','generated_text':'Taste the difference! Handcrafted burgers made fresh daily. BOGO this weekend only!','slogans':['Every Bite Tells a Story'],'ad_format':'poster'},
    {'location':'Highway Billboard',   'title':'Dream Homes Await',  'product_name':'Premium Villas',      'category':'Real Estate',     'offer':'Zero GST','theme_color':'#3b82f6','generated_text':'Your dream home is closer than you think. Premium villas with world-class amenities.','slogans':['Home is Where the Heart Is'],'ad_format':'poster'},
    {'location':'Airport Terminal',    'title':'FlyEasy Holidays',   'product_name':'Travel Package',      'category':'Travel',          'offer':'30% Off','theme_color':'#8b5cf6','generated_text':'Fly to your dream destination! Exclusive holiday packages with all-inclusive deals.','slogans':['Explore the World'],'ad_format':'video'},
    {'location':'Metro Station',       'title':'FitLife Membership',  'product_name':'Gym Membership',     'category':'Fitness',         'offer':'First Month Free','theme_color':'#10b981','generated_text':'Start your fitness journey today! State-of-the-art gym with expert trainers.','slogans':['Stronger Every Day'],'ad_format':'poster'},
]

@display_bp.route('/')
@login_required
def index():
    return render_template('display/index.html', locations=VIRTUAL_LOCATIONS)

@display_bp.route('/api/active')
def active_ads():
    now = datetime.utcnow()

    # Get real active scheduled ads
    schedules = AdSchedule.query.filter(
        AdSchedule.is_active == True,
        AdSchedule.start_time <= now,
        AdSchedule.end_time   >= now
    ).all()

    live = {}
    for s in schedules:
        ad = s.advertisement
        # Show approved OR paid ads (so newly paid ads show up)
        if ad and ad.status in ('approved', 'pending') and ad.payment_status == 'paid':
            live[s.location] = {
                'location':      s.location,
                'title':         ad.title,
                'product_name':  ad.product_name,
                'offer':         ad.offer or '',
                'category':      ad.category,
                'theme_color':   ad.theme_color or '#6366f1',
                'generated_text': ad.generated_text or ad.description or '',
                'slogans':       ad.get_slogans(),
                'ad_format':     ad.ad_format,
                'is_live':       True,
            }

    # Fill missing locations with demo ads
    result = []
    for demo in DEMO_ADS:
        loc = demo['location']
        if loc in live:
            result.append(live[loc])
        else:
            # Use demo ad but mark it
            d = dict(demo)
            d['is_live'] = False
            result.append(d)

    return jsonify(result)
