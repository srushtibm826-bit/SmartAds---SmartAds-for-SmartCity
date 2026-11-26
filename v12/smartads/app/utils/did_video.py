import os, re, requests, base64, time, unicodedata
from pathlib import Path

DID_API_BASE = "https://api.d-id.com"
DID_API_KEY  = os.environ.get("DID_API_KEY", "")
_image_url_cache = {}
STATIC_IMG_DIR = Path(__file__).parent.parent / "static" / "images"

AVATAR_PRESETS = {
    "Fashion":         {"label":"Priya — Fashion","local_file":"avatar_woman1.jpg","voice_id":"en-IN-NeerjaNeural","provider":"microsoft","emoji":"👗","desc":"Indian female"},
    "Technology":      {"label":"Aria — Tech","local_file":"avatar_woman2.jpg","voice_id":"en-US-JennyNeural","provider":"microsoft","emoji":"💻","desc":"American English"},
    "Food & Beverage": {"label":"Noelle — Food","local_file":"avatar_woman3.jpg","voice_id":"en-US-AriaNeural","provider":"microsoft","emoji":"🍔","desc":"Warm female"},
    "Healthcare":      {"label":"Amy — Health","local_file":"avatar_woman4.jpg","voice_id":"en-GB-SoniaNeural","provider":"microsoft","emoji":"💊","desc":"British English"},
    "General":         {"label":"Priya — Brand","local_file":"avatar_woman1.jpg","voice_id":"en-IN-NeerjaNeural","provider":"microsoft","emoji":"⭐","desc":"Indian female"},
}
for cat in ["Real Estate","Finance","Travel","Automotive","Education","Fitness","Beauty","Entertainment"]:
    AVATAR_PRESETS[cat] = AVATAR_PRESETS["General"].copy()

DEFAULT_AVATAR = AVATAR_PRESETS["General"]

def get_avatar_for_category(cat): return AVATAR_PRESETS.get(cat, DEFAULT_AVATAR)

def _s3_to_https(url):
    if not url: return url
    if url.startswith(('https://','http://')): return url
    if url.startswith('s3://'):
        path = url[5:]; parts = path.split('/',1)
        return f"https://{parts[0]}.s3.amazonaws.com/{parts[1] if len(parts)>1 else ''}"
    return url

s3_to_https = _s3_to_https

def _auth_header():
    if not DID_API_KEY: raise ValueError("DID_API_KEY not set")
    token = base64.b64encode(f"{DID_API_KEY}:".encode()).decode()
    return {"Authorization":f"Basic {token}","Accept":"application/json"}

def _auth_header_json():
    h = _auth_header(); h["Content-Type"]="application/json"; return h

def _clean_script(text):
    c = ""
    for ch in text:
        cat = unicodedata.category(ch)
        c += ch if cat.startswith(('L','N','P','Z')) else " "
    for o,r in {"\u2014":",","\u2013":"-","\u2019":"'","\u201c":'"',"\u201d":'"'}.items():
        c = c.replace(o,r)
    return re.sub(r'\s+',' ',c).strip()

def _validate_image_url(url):
    if not url: return False,"Empty URL"
    blocked = ["share.google","photos.google","instagram.com","facebook.com","twitter.com","x.com"]
    lower = url.lower()
    for b in blocked:
        if b in lower: return False,f"'{b}' is not a direct image URL. Use imgbb.com."
    ok_ext = ('.jpg','.jpeg','.png','.webp')
    is_did = 'd-id.com' in lower or 'd-id-' in lower
    has_ext = any(lower.split('?')[0].endswith(e) for e in ok_ext)
    if not is_did and not has_ext: return False,"URL must end in .jpg or .png"
    return True,""

def _upload_image_to_did(local_filename):
    if local_filename in _image_url_cache:
        return _image_url_cache[local_filename]
    img_path = STATIC_IMG_DIR / local_filename
    if not img_path.exists():
        raise FileNotFoundError(f"Avatar image not found: {img_path}")
    with open(img_path,'rb') as f: img_bytes = f.read()
    headers = {"Authorization":_auth_header()["Authorization"],"Accept":"application/json"}
    resp = requests.post(f"{DID_API_BASE}/images",headers=headers,
                         files={'image':(local_filename,img_bytes,'image/jpeg')},
                         data={'name':local_filename.replace('.jpg','')},timeout=30)
    print(f"[D-ID] Upload {local_filename} → {resp.status_code}: {resp.text[:200]}")
    if resp.status_code not in (200,201):
        raise RuntimeError(f"Upload failed: {resp.text[:200]}")
    data = resp.json()
    s3_url = data.get('url','')
    https_url = _s3_to_https(s3_url) if s3_url else ''
    if not any(https_url.lower().endswith(e) for e in ('.jpg','.jpeg','.png')):
        https_url += '/' + local_filename
    _image_url_cache[local_filename] = https_url
    return https_url

def _resolve_image_url(avatar, custom_url=None):
    if custom_url and custom_url.strip():
        valid,err = _validate_image_url(custom_url.strip())
        if valid: return custom_url.strip()
        raise ValueError(f"Image URL error: {err}")
    return _upload_image_to_did(avatar.get('local_file','avatar_woman1.jpg'))

def create_talk(script_text, avatar, custom_image_url=None):
    if not DID_API_KEY:
        return {"error":"DID_API_KEY not set. Get free key at https://studio.d-id.com"}
    script = _clean_script(script_text)
    if not script: return {"error":"Script is empty."}
    if len(script)>400: script = script[:397]+"..."
    try:
        image_url = _resolve_image_url(avatar, custom_image_url)
    except Exception as e:
        return {"error":str(e)}
    if not any(image_url.lower().split('?')[0].endswith(e) for e in ('.jpg','.jpeg','.png','.webp')):
        return {"error":f"Image URL must end in .jpg/.png: {image_url[:80]}"}
    payload = {"source_url":image_url,"script":{"type":"text","input":script,
        "provider":{"type":avatar.get("provider","microsoft"),"voice_id":avatar.get("voice_id","en-IN-NeerjaNeural")},"ssml":False},
        "config":{"fluent":True,"pad_audio":0.5,"stitch":True},"persist":True}
    try:
        resp = requests.post(f"{DID_API_BASE}/talks",headers=_auth_header_json(),json=payload,timeout=30)
        print(f"[D-ID] POST /talks → {resp.status_code}: {resp.text[:300]}")
        if resp.status_code in (200,201):
            data = resp.json()
            return {"id":data.get("id"),"status":data.get("status","created"),"error":None}
        try: err = resp.json()
        except: err = {}
        kind = err.get("kind",""); desc = err.get("description",resp.text[:200])
        return {"error":f"D-ID [{kind or resp.status_code}]: {desc}"}
    except Exception as e:
        return {"error":str(e)}

def poll_talk_status(talk_id):
    if not DID_API_KEY or not talk_id: return {"status":"error","error":"Missing key or ID"}
    try:
        resp = requests.get(f"{DID_API_BASE}/talks/{talk_id}",headers=_auth_header_json(),timeout=15)
        if resp.status_code == 200:
            data = resp.json(); status = data.get("status","unknown")
            raw_url = data.get("result_url"); public_url = _s3_to_https(raw_url) if raw_url else None
            print(f"[D-ID] Poll {talk_id} → {status}")
            return {"status":status,"result_url":public_url,
                    "error":data.get("error",{}).get("description") if status=="error" else None}
        return {"status":"error","error":f"HTTP {resp.status_code}"}
    except requests.exceptions.Timeout:
        return {"status":"processing","error":None}
    except Exception as e:
        return {"status":"error","error":str(e)}

def check_api_key_valid():
    if not DID_API_KEY: return {"valid":False,"reason":"DID_API_KEY not set"}
    try:
        resp = requests.get(f"{DID_API_BASE}/credits",headers=_auth_header_json(),timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            return {"valid":True,"credits":data.get("remaining","?"),"total":data.get("total","?")}
        return {"valid":False,"reason":f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"valid":False,"reason":str(e)}

def wait_for_completion(talk_id, max_wait=120):
    start = time.time()
    while time.time()-start < max_wait:
        r = poll_talk_status(talk_id)
        if r["status"] in ("done","error"): return r
        time.sleep(4)
    return {"status":"error","error":"Timed out."}
