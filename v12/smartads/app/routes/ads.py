import json, random, os
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models.ad import Advertisement
from app.models.notification import Notification
from app.utils.pricing import VIRTUAL_LOCATIONS, LOCATION_BASE, FORMAT_MULT, calculate_price, get_slot_examples
from datetime import datetime

ads_bp = Blueprint('ads', __name__)

CATEGORIES = ['Fashion','Technology','Food & Beverage','Healthcare','Real Estate',
              'Education','Automotive','Travel','Entertainment','Finance','Fitness','Beauty','General']
THEME_COLORS = ['#6366f1','#ec4899','#f59e0b','#10b981','#3b82f6','#ef4444','#8b5cf6','#06b6d4']
TEMPLATES = ['modern','bold','elegant','minimal','vibrant']

def _engagement_score():
    return random.randint(72, 96)

def _generate_text_fallback(product, category, offer):
    templates = {
        'Fashion':    f"Step into Style! {product} — where fashion meets passion. {offer}. Elevate your wardrobe today!",
        'Technology': f"Innovate with {product}! Cutting-edge technology for modern life. {offer}. The future is now!",
        'Food & Beverage': f"Taste the Difference! {product} crafted with love. {offer}. Come hungry, leave happy!",
        'Healthcare': f"Your Health, Our Priority. {product} — trusted wellness solutions. {offer}. Feel better today!",
        'Real Estate': f"Find Your Dream Home! {product} — premium living awaits. {offer}. Your future starts here!",
        'General':    f"Discover {product}! Premium quality you can trust. {offer}. Experience the difference today!",
    }
    return templates.get(category, templates['General'])

def _generate_slogans(product, category):
    slogans = {
        'Fashion':    ['Style Without Limits','Fashion Forward','Wear Your Story'],
        'Technology': ['Innovate Today','Live Smarter','Future Ready'],
        'Food & Beverage': ['Every Bite Tells a Story','Taste Perfection','Fresh Every Day'],
        'Healthcare': ['Health is Wealth','Care You Deserve','Wellness First'],
        'General':    ['Quality Guaranteed','Excellence Always','Your Best Choice'],
    }
    base = slogans.get(category, slogans['General'])
    return base[:2]

@ads_bp.route('/')
@login_required
def list_ads():
    ads = Advertisement.query.filter_by(user_id=current_user.id)\
          .order_by(Advertisement.created_at.desc()).all()
    return render_template('ads/list.html', ads=ads)

@ads_bp.route('/create')
@login_required
def create():
    return render_template('ads/create.html',
        categories=CATEGORIES, locations=VIRTUAL_LOCATIONS,
        theme_colors=THEME_COLORS, templates=TEMPLATES)

@ads_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    data        = request.json or {}
    product     = data.get('product_name','').strip()
    category    = data.get('category','General')
    offer       = data.get('offer','').strip()
    description = data.get('description','').strip()

    if not product:
        return jsonify({'error': 'Product name required'}), 400

    # Try Groq AI
    text = None
    try:
        import groq as groq_lib
        groq_key = os.environ.get('GROQ_API_KEY','')
        if groq_key:
            client = groq_lib.Groq(api_key=groq_key)
            resp   = client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=[{'role':'user','content':
                    f"Write a compelling 2-sentence advertisement for: Product={product}, "
                    f"Category={category}, Offer={offer}. Be enthusiastic and persuasive. Max 150 chars."}],
                max_tokens=200, temperature=0.8)
            text = resp.choices[0].message.content.strip()
    except Exception:
        pass

    if not text:
        text = _generate_text_fallback(product, category, offer or 'Special offer available')

    slogans = _generate_slogans(product, category)
    return jsonify({
        'generated_text': text,
        'slogans': slogans,
        'engagement_score': _engagement_score(),
        'theme_color': random.choice(THEME_COLORS),
    })

@ads_bp.route('/select-format', methods=['POST'])
@login_required
def select_format():
    """Save ad draft and redirect to format+slot selection."""
    product     = request.form.get('product_name','').strip()
    category    = request.form.get('category','General')
    offer       = request.form.get('offer','').strip()
    description = request.form.get('description','').strip()
    gen_text    = request.form.get('generated_text','').strip()
    slogans_raw = request.form.get('slogans','[]')
    theme_color = request.form.get('theme_color','#6366f1')
    tmpl        = request.form.get('template_style','modern')
    location    = request.form.get('location', VIRTUAL_LOCATIONS[0])

    if not product:
        flash('Product name is required.', 'danger')
        return redirect(url_for('ads.create'))

    ad = Advertisement(
        user_id=current_user.id,
        title=f"{product} — {offer}" if offer else product,
        product_name=product, category=category, offer=offer,
        description=description, generated_text=gen_text,
        slogans=slogans_raw, theme_color=theme_color,
        template_style=tmpl, location=location,
        status='draft', payment_status='unpaid',
        engagement_score=_engagement_score(),
        ad_type='ai_generated',
    )
    db.session.add(ad)
    db.session.commit()
    return redirect(url_for('ads.choose_format', ad_id=ad.id))

@ads_bp.route('/<int:ad_id>/choose-format')
@login_required
def choose_format(ad_id):
    """Step 1: Choose POSTER or VIDEO with pricing preview."""
    ad = Advertisement.query.filter_by(id=ad_id, user_id=current_user.id).first_or_404()
    location = ad.location or VIRTUAL_LOCATIONS[0]
    base     = LOCATION_BASE.get(location, 400)
    return render_template('ads/choose_format.html',
        ad=ad, location=location, base=base,
        poster_mult=FORMAT_MULT['poster'],
        video_mult=FORMAT_MULT['video'],
        locations=VIRTUAL_LOCATIONS)

@ads_bp.route('/<int:ad_id>/set-format', methods=['POST'])
@login_required
def set_format(ad_id):
    """Save chosen format and redirect to slot selection."""
    ad = Advertisement.query.filter_by(id=ad_id, user_id=current_user.id).first_or_404()
    ad.ad_format = request.form.get('ad_format', 'poster')
    ad.location  = request.form.get('location', ad.location or VIRTUAL_LOCATIONS[0])
    db.session.commit()
    return redirect(url_for('ads.select_slot', ad_id=ad.id))

@ads_bp.route('/<int:ad_id>/select-slot')
@login_required
def select_slot(ad_id):
    """Step 2: Choose time slot + days with live price calculator."""
    ad       = Advertisement.query.filter_by(id=ad_id, user_id=current_user.id).first_or_404()
    location = ad.location or VIRTUAL_LOCATIONS[0]
    examples = get_slot_examples(location)
    base     = LOCATION_BASE.get(location, 400)
    fm       = FORMAT_MULT.get(ad.ad_format, 1.0)
    return render_template('ads/select_slot.html',
        ad=ad, location=location, examples=examples,
        base=base, format_mult=fm,
        ad_format=ad.ad_format)

@ads_bp.route('/<int:ad_id>/confirm-slot', methods=['POST'])
@login_required
def confirm_slot(ad_id):
    """Save slot choice + calculated price, go to payment."""
    ad = Advertisement.query.filter_by(id=ad_id, user_id=current_user.id).first_or_404()
    slot_type  = request.form.get('slot_type','normal')
    days       = max(1, min(30, int(request.form.get('days', 1))))
    start_time = request.form.get('start_time','')
    end_time   = request.form.get('end_time','')

    pricing = calculate_price(
        location=ad.location or VIRTUAL_LOCATIONS[0],
        ad_format=ad.ad_format,
        slot_type=slot_type,
        days=days,
        start_time=start_time,
        end_time=end_time,
    )
    # Store slot info in description temporarily
    import json as _j
    slot_meta = _j.dumps({
        'slot_type': slot_type, 'days': days,
        'start_time': start_time, 'end_time': end_time,
        'pricing': pricing,
    })
    ad.admin_notes = slot_meta          # reuse field to carry slot info
    ad.amount_paid = pricing['total']   # pre-set expected amount
    db.session.commit()
    return redirect(url_for('payment.checkout', ad_id=ad.id))

@ads_bp.route('/<int:ad_id>/preview')
@login_required
def preview(ad_id):
    ad = Advertisement.query.filter_by(id=ad_id, user_id=current_user.id).first_or_404()
    return render_template('ads/preview.html', ad=ad)

@ads_bp.route('/<int:ad_id>/video')
@login_required
def video(ad_id):
    ad = Advertisement.query.filter_by(id=ad_id, user_id=current_user.id).first_or_404()
    return render_template('ads/video.html', ad=ad)

@ads_bp.route('/<int:ad_id>/download')
@login_required
def download(ad_id):
    ad = Advertisement.query.filter_by(id=ad_id, user_id=current_user.id).first_or_404()
    html = render_template('ads/banner_export.html', ad=ad)
    from flask import Response
    return Response(html, mimetype='text/html',
        headers={'Content-Disposition': f'attachment; filename=ad_{ad.id}.html'})
