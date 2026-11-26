"""
SmartAds Pricing Engine
=======================
Pricing tiers for ad slots:

FORMAT:   Poster = base rate × 1.0  |  Video = base rate × 2.4
SLOT:     Prime  = base × 2.0       |  Normal = base × 1.0  |  Manual = calculated
LOCATION: each location has its own base rate per day

Final = base_location_rate × format_mult × slot_mult × days
"""

# ── Base rate per day (INR) per location ──────────────────────────────────
LOCATION_BASE = {
    'Mall Billboard':      400,
    'City Center Screen':  650,
    'Food Court Display':  250,
    'Highway Billboard':   500,
    'Airport Terminal':    900,
    'Metro Station':       350,
}

# ── Format multiplier ─────────────────────────────────────────────────────
FORMAT_MULT = {
    'poster': 1.0,
    'video':  2.4,
}

# ── Slot tier multiplier ──────────────────────────────────────────────────
SLOT_MULT = {
    'prime':  2.0,
    'normal': 1.0,
}

# ── Prime time slots (high engagement hours) ─────────────────────────────
PRIME_SLOTS = {
    'Mall Billboard':      [('10:00','13:00'), ('17:00','21:00')],
    'City Center Screen':  [('08:00','10:00'), ('17:00','21:00')],
    'Food Court Display':  [('12:00','15:00'), ('19:00','22:00')],
    'Highway Billboard':   [('07:00','10:00'), ('17:00','20:00')],
    'Airport Terminal':    [('06:00','09:00'), ('14:00','18:00')],
    'Metro Station':       [('08:00','10:00'), ('17:00','20:00')],
}

# ── Normal time slots ──────────────────────────────────────────────────────
NORMAL_SLOTS = {
    'Mall Billboard':      [('10:00','17:00')],
    'City Center Screen':  [('10:00','17:00')],
    'Food Court Display':  [('09:00','12:00'), ('15:00','19:00')],
    'Highway Billboard':   [('10:00','17:00')],
    'Airport Terminal':    [('09:00','14:00'), ('18:00','22:00')],
    'Metro Station':       [('10:00','17:00')],
}

VIRTUAL_LOCATIONS = list(LOCATION_BASE.keys())


def calculate_price(location: str, ad_format: str, slot_type: str,
                    days: int, start_time: str = None, end_time: str = None) -> dict:
    """
    Calculate ad price.

    Args:
        location:   virtual screen location
        ad_format:  'poster' | 'video'
        slot_type:  'prime' | 'normal' | 'manual'
        days:       number of days
        start_time: HH:MM (required for manual)
        end_time:   HH:MM (required for manual)

    Returns dict with:
        base_per_day, format_mult, slot_mult, days,
        subtotal, gst, total, breakdown (list of strings)
    """
    base = LOCATION_BASE.get(location, 400)
    fm   = FORMAT_MULT.get(ad_format, 1.0)

    if slot_type == 'manual' and start_time and end_time:
        # Calculate hours, rate per hour = base/8
        try:
            sh, sm = map(int, start_time.split(':'))
            eh, em = map(int, end_time.split(':'))
            hours  = max(0.5, (eh * 60 + em - sh * 60 - sm) / 60)
        except Exception:
            hours = 4
        sm_val = max(0.5, hours / 8)   # normalize against 8-hr day
    else:
        sm_val = SLOT_MULT.get(slot_type, 1.0)
        hours  = None

    subtotal = round(base * fm * sm_val * days, 2)
    gst      = round(subtotal * 0.18, 2)
    total    = round(subtotal + gst, 2)

    breakdown = [
        f"Base rate ({location}): ₹{base}/day",
        f"Format ({ad_format}): ×{fm}",
        f"Slot ({slot_type}{'  '+start_time+'-'+end_time if slot_type=='manual' else ''}): ×{round(sm_val,2)}",
        f"Duration: {days} day{'s' if days>1 else ''}",
        f"Subtotal: ₹{subtotal}",
        f"GST (18%): ₹{gst}",
    ]

    return {
        'base_per_day': base,
        'format_mult':  fm,
        'slot_mult':    round(sm_val, 2),
        'hours':        hours,
        'days':         days,
        'subtotal':     subtotal,
        'gst':          gst,
        'total':        total,
        'breakdown':    breakdown,
    }


def get_slot_examples(location: str) -> dict:
    """Return example slots for a location."""
    return {
        'prime':  PRIME_SLOTS.get(location, [('17:00','21:00')]),
        'normal': NORMAL_SLOTS.get(location, [('10:00','17:00')]),
    }


def poster_base_price(location: str) -> float:
    return LOCATION_BASE.get(location, 400) * FORMAT_MULT['poster']

def video_base_price(location: str) -> float:
    return LOCATION_BASE.get(location, 400) * FORMAT_MULT['video']
