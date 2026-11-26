import json, uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.ad import Advertisement
from app.models.payment import Payment
from app.models.notification import Notification
from app.models.schedule import AdSchedule
from app.utils.pricing import calculate_price
from datetime import datetime, timedelta

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/checkout/<int:ad_id>', methods=['GET','POST'])
@login_required
def checkout(ad_id):
    ad = Advertisement.query.filter_by(id=ad_id, user_id=current_user.id).first_or_404()

    # Load slot meta saved by confirm_slot
    slot_meta = {}
    pricing   = None
    if ad.admin_notes:
        try:
            slot_meta = json.loads(ad.admin_notes)
            pricing   = slot_meta.get('pricing')
        except Exception:
            pass

    # Fallback pricing if missing
    if not pricing:
        from app.utils.pricing import calculate_price, VIRTUAL_LOCATIONS
        pricing = calculate_price(
            location=ad.location or VIRTUAL_LOCATIONS[0],
            ad_format=ad.ad_format or 'poster',
            slot_type='normal', days=1)

    if request.method == 'POST':
        method  = request.form.get('method', 'card')
        amount  = pricing['total']

        # Simulate payment
        pay = Payment(
            user_id=current_user.id, ad_id=ad.id,
            amount=amount, method=method, status='success',
            description=f'{ad.ad_format.title()} ad — {ad.location} — {slot_meta.get("days",1)} day(s)')
        db.session.add(pay)

        ad.payment_status = 'paid'
        ad.amount_paid    = amount
        ad.status         = 'pending'  # awaiting admin approval

        # Auto-create schedule from slot info
        days       = int(slot_meta.get('days', 1))
        slot_type  = slot_meta.get('slot_type', 'normal')
        start_time_str = slot_meta.get('start_time', '')
        end_time_str   = slot_meta.get('end_time', '')

        now = datetime.utcnow()
        if slot_type == 'prime':
            sched_start = now.replace(hour=17, minute=0, second=0)
            sched_end   = sched_start + timedelta(hours=4*days)
        elif slot_type == 'normal':
            sched_start = now.replace(hour=10, minute=0, second=0)
            sched_end   = sched_start + timedelta(hours=7*days)
        else:
            try:
                sh, sm = map(int, start_time_str.split(':'))
                eh, em = map(int, end_time_str.split(':'))
                sched_start = now.replace(hour=sh, minute=sm, second=0)
                sched_end   = sched_start + timedelta(
                    hours=(eh*60+em-sh*60-sm)/60 * days)
            except Exception:
                sched_start = now
                sched_end   = now + timedelta(days=days)

        db.session.add(AdSchedule(
            ad_id=ad.id, user_id=current_user.id,
            location=ad.location or 'Mall Billboard',
            start_time=sched_start, end_time=sched_end,
            duration_seconds=15, is_active=True))

        # Notify
        db.session.add(Notification(
            user_id=current_user.id,
            title='Payment Successful',
            message=f'₹{amount:.0f} paid for "{ad.title}". Ad submitted for review.',
            type='success',
            link=url_for('ads.preview', ad_id=ad.id)))

        # Clear slot meta from admin_notes
        ad.admin_notes = None
        db.session.commit()

        db.session.refresh(pay)
        flash(f'Payment of ₹{amount:.0f} successful! Ad submitted for admin review.', 'success')
        return redirect(url_for('payment.receipt_page', payment_id=pay.id))

    return render_template('payment/checkout.html',
        ad=ad, pricing=pricing, slot_meta=slot_meta)

@payment_bp.route('/history')
@login_required
def history():
    pays = Payment.query.filter_by(user_id=current_user.id)\
           .order_by(Payment.created_at.desc()).all()
    return render_template('payment/history.html', payments=pays)

@payment_bp.route('/api/calculate', methods=['POST'])
@login_required
def api_calculate():
    data = request.json or {}
    result = calculate_price(
        location=data.get('location','Mall Billboard'),
        ad_format=data.get('ad_format','poster'),
        slot_type=data.get('slot_type','normal'),
        days=int(data.get('days',1)),
        start_time=data.get('start_time',''),
        end_time=data.get('end_time',''),
    )
    return jsonify(result)


@payment_bp.route('/receipt/<int:payment_id>/pdf')
@login_required
def download_receipt(payment_id):
    """Download payment receipt as PDF."""
    pay = Payment.query.filter_by(id=payment_id, user_id=current_user.id).first_or_404()
    ad  = Advertisement.query.get(pay.ad_id)

    from app.utils.receipt_pdf import generate_receipt_pdf
    from flask import Response

    pdf_bytes = generate_receipt_pdf(pay, ad, current_user)
    filename  = f"SmartAds_Receipt_{pay.transaction_id}.pdf"

    return Response(
        pdf_bytes,
        status=200,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type':        'application/pdf',
        }
    )


@payment_bp.route('/receipt/<int:payment_id>')
@login_required
def receipt_page(payment_id):
    """Show payment success page with receipt download."""
    pay = Payment.query.filter_by(id=payment_id, user_id=current_user.id).first_or_404()
    ad  = Advertisement.query.get(pay.ad_id)
    slot_meta = {}
    if ad and ad.admin_notes:
        try:
            import json as _j
            slot_meta = _j.loads(ad.admin_notes)
        except Exception:
            pass
    return render_template('payment/receipt.html', payment=pay, ad=ad, slot_meta=slot_meta)
