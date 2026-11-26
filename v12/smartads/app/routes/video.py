import threading
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response, stream_with_context
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.ad import Advertisement
from app.models.advideo import AdVideo

video_bp = Blueprint('video', __name__)

def _get_did():
    from app.utils.did_video import create_talk, poll_talk_status, get_avatar_for_category, \
        AVATAR_PRESETS, check_api_key_valid, _s3_to_https
    return create_talk, poll_talk_status, get_avatar_for_category, AVATAR_PRESETS, check_api_key_valid, _s3_to_https

def _poll_bg(advideo_id, app):
    with app.app_context():
        import time
        from app.utils.did_video import poll_talk_status
        av = AdVideo.query.get(advideo_id)
        if not av: return
        for attempt in range(75):
            time.sleep(8)
            result = poll_talk_status(av.did_talk_id)
            status = result.get('status','pending')
            print(f"[D-ID BG] Attempt {attempt+1}: {av.did_talk_id} → {status}")
            if status == 'done':
                av.status = 'done'; av.result_url = result.get('result_url'); av.completed_at = datetime.utcnow()
                db.session.commit(); return
            elif status == 'error':
                av.status = 'error'; av.error_msg = result.get('error','D-ID error')
                db.session.commit(); return
            else:
                av.status = 'processing'; db.session.commit()
        av.status = 'error'
        av.error_msg = 'Timed out. Use Check Status to fetch manually.'
        db.session.commit()

@video_bp.route('/<int:ad_id>')
@login_required
def studio(ad_id):
    ad = Advertisement.query.filter_by(id=ad_id, user_id=current_user.id).first_or_404()
    _, _, get_avatar_for_category, AVATAR_PRESETS, _, _ = _get_did()
    past_videos = AdVideo.query.filter_by(ad_id=ad.id, user_id=current_user.id)\
                  .order_by(AdVideo.created_at.desc()).limit(10).all()
    import os
    api_configured = bool(os.environ.get('DID_API_KEY',''))

    # Check if there is a demo/ready video for this ad
    demo_video = AdVideo.query.filter_by(
        ad_id=ad.id, user_id=current_user.id, status='done'
    ).order_by(AdVideo.created_at.desc()).first()

    return render_template('ads/video_studio.html',
        ad=ad, past_videos=past_videos,
        avatar=get_avatar_for_category(ad.category),
        all_avatars=AVATAR_PRESETS,
        api_configured=api_configured,
        demo_video=demo_video)

@video_bp.route('/<int:ad_id>/generate', methods=['POST'])
@login_required
def generate(ad_id):
    ad = Advertisement.query.filter_by(id=ad_id, user_id=current_user.id).first_or_404()
    create_talk, _, get_avatar_for_category, _, _, _ = _get_did()

    script_text  = request.form.get('script','').strip() or ad.generated_text or ad.title
    avatar_key   = request.form.get('avatar_category', ad.category)
    custom_image = request.form.get('custom_image_url','').strip()
    avatar       = get_avatar_for_category(avatar_key)

    result = create_talk(script_text, avatar, custom_image_url=custom_image or None)
    if result.get('error'):
        return jsonify({'ok': False, 'error': result['error']}), 400

    av = AdVideo(ad_id=ad.id, user_id=current_user.id,
                 did_talk_id=result['id'], status='processing',
                 avatar_label=avatar.get('label','AI Avatar'),
                 avatar_image=avatar.get('local_file',''),
                 voice_id=avatar.get('voice_id',''),
                 script_text=script_text[:500])
    db.session.add(av); db.session.commit()

    from flask import current_app
    app = current_app._get_current_object()
    threading.Thread(target=_poll_bg, args=(av.id, app), daemon=True).start()

    return jsonify({'ok': True, 'video_id': av.id, 'talk_id': result['id'], 'status': 'processing',
                    'poll_url': url_for('video.status', ad_id=ad.id, video_id=av.id)})

@video_bp.route('/<int:ad_id>/status/<int:video_id>')
@login_required
def status(ad_id, video_id):
    av = AdVideo.query.filter_by(id=video_id, ad_id=ad_id, user_id=current_user.id).first_or_404()
    _, poll_talk_status, _, _, _, _ = _get_did()
    # Skip D-ID polling for demo videos
    is_demo = av.did_talk_id and av.did_talk_id.startswith('demo_')
    if not is_demo and av.status == 'processing' and av.did_talk_id:
        fresh = poll_talk_status(av.did_talk_id)
        if fresh.get('status') == 'done' and fresh.get('result_url'):
            av.status = 'done'; av.result_url = fresh['result_url']; av.completed_at = datetime.utcnow()
            db.session.commit()
        elif fresh.get('status') == 'error':
            av.status = 'error'; av.error_msg = fresh.get('error'); db.session.commit()
    bc, bl = av.status_badge()
    return jsonify({'status': av.status, 'result_url': av.result_url, 'error': av.error_msg,
                    'badge_class': bc, 'badge_label': bl, 'video_id': av.id,
                    'created_at': av.created_at.strftime('%d %b %Y, %H:%M'),
                    'completed_at': av.completed_at.strftime('%H:%M:%S') if av.completed_at else None})

@video_bp.route('/<int:ad_id>/recover/<int:video_id>', methods=['POST'])
@login_required
def recover_video(ad_id, video_id):
    av = AdVideo.query.filter_by(id=video_id, ad_id=ad_id, user_id=current_user.id).first_or_404()
    _, poll_talk_status, _, _, _, _ = _get_did()
    if not av.did_talk_id:
        return jsonify({'ok': False, 'error': 'No talk ID'})
    result = poll_talk_status(av.did_talk_id)
    if result.get('status') == 'done' and result.get('result_url'):
        av.status = 'done'; av.result_url = result['result_url']
        av.completed_at = datetime.utcnow(); av.error_msg = None; db.session.commit()
        return jsonify({'ok': True, 'status': 'done', 'result_url': av.result_url})
    elif result.get('status') == 'error':
        av.status = 'error'; av.error_msg = result.get('error'); db.session.commit()
        return jsonify({'ok': False, 'status': 'error', 'error': av.error_msg})
    else:
        av.status = 'processing'; av.error_msg = None; db.session.commit()
        from flask import current_app
        threading.Thread(target=_poll_bg, args=(av.id, current_app._get_current_object()), daemon=True).start()
        return jsonify({'ok': True, 'status': result.get('status','processing'),
                        'message': 'Still processing. Polling restarted.'})

@video_bp.route('/<int:ad_id>/fresh-url/<int:video_id>')
@login_required
def fresh_url(ad_id, video_id):
    av = AdVideo.query.filter_by(id=video_id, ad_id=ad_id, user_id=current_user.id).first_or_404()
    _, poll_talk_status, _, _, _, _ = _get_did()
    result = poll_talk_status(av.did_talk_id)
    if result.get('status') == 'done' and result.get('result_url'):
        av.result_url = result['result_url']; db.session.commit()
        return jsonify({'ok': True, 'result_url': av.result_url})
    return jsonify({'ok': False, 'status': result.get('status'), 'error': result.get('error')})

@video_bp.route('/check/<talk_id>')
@login_required
def check_talk(talk_id):
    _, poll_talk_status, _, _, _, _ = _get_did()
    return jsonify(poll_talk_status(talk_id))

@video_bp.route('/credits')
@login_required
def credits():
    _, _, _, _, check_api_key_valid, _ = _get_did()
    return jsonify(check_api_key_valid())

@video_bp.route('/proxy/<talk_id>.mp4')
@login_required
def proxy_video(talk_id):
    import requests as req
    _, poll_talk_status, _, _, _, _ = _get_did()
    result = poll_talk_status(talk_id)
    if result.get('status') != 'done' or not result.get('result_url'):
        return jsonify({'error': 'Video not ready'}), 404
    try:
        r = req.get(result['result_url'], stream=True, timeout=30)
        return Response(stream_with_context(r.iter_content(8192)), status=200,
            headers={'Content-Type': 'video/mp4',
                     'Content-Disposition': f'attachment; filename="smartad_{talk_id}.mp4"'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
