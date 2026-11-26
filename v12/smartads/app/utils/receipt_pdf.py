"""
SmartAds — PDF Receipt Generator
Uses ReportLab to create a professional payment receipt.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import io, json
from datetime import datetime


# Brand colors
PURPLE = colors.HexColor('#6366f1')
PINK   = colors.HexColor('#ec4899')
DARK   = colors.HexColor('#0d0d18')
CARD   = colors.HexColor('#13131f')
TEXT   = colors.HexColor('#e5e7eb')
MUTED  = colors.HexColor('#6b7280')
GREEN  = colors.HexColor('#10b981')
WHITE  = colors.white


def generate_receipt_pdf(payment, ad, user) -> bytes:
    """
    Generate a PDF receipt for a payment.
    Returns bytes (the PDF file content).
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()
    W = A4[0] - 40*mm   # usable width

    # Custom styles
    h1 = ParagraphStyle('H1', fontSize=24, fontName='Helvetica-Bold',
                        textColor=WHITE, spaceAfter=4)
    h2 = ParagraphStyle('H2', fontSize=14, fontName='Helvetica-Bold',
                        textColor=WHITE, spaceAfter=6)
    body = ParagraphStyle('Body', fontSize=10, fontName='Helvetica',
                          textColor=TEXT, spaceAfter=4, leading=14)
    muted = ParagraphStyle('Muted', fontSize=9, fontName='Helvetica',
                           textColor=MUTED, spaceAfter=4)
    right = ParagraphStyle('Right', fontSize=10, fontName='Helvetica',
                           textColor=TEXT, alignment=TA_RIGHT)
    total_style = ParagraphStyle('Total', fontSize=18, fontName='Helvetica-Bold',
                                 textColor=PURPLE, alignment=TA_RIGHT)
    center = ParagraphStyle('Center', fontSize=9, fontName='Helvetica',
                            textColor=MUTED, alignment=TA_CENTER)
    success_style = ParagraphStyle('Success', fontSize=11, fontName='Helvetica-Bold',
                                   textColor=GREEN, alignment=TA_CENTER)

    story = []

    # ── Header banner ─────────────────────────────────────────────────────
    header_data = [[
        Paragraph('<font color="#6366f1">⚡</font> SmartAds AI', h1),
        Paragraph('PAYMENT RECEIPT', ParagraphStyle('PR', fontSize=11, fontName='Helvetica-Bold',
                  textColor=MUTED, alignment=TA_RIGHT)),
    ]]
    header_tbl = Table(header_data, colWidths=[W*0.6, W*0.4])
    header_tbl.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,-1), CARD),
        ('TOPPADDING',  (0,0), (-1,-1), 16),
        ('BOTTOMPADDING',(0,0),(-1,-1), 16),
        ('LEFTPADDING', (0,0), (-1,-1), 16),
        ('RIGHTPADDING',(0,0), (-1,-1), 16),
        ('ROUNDEDCORNERS', (0,0), (-1,-1), [8,8,8,8]),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 6*mm))

    # ── Success status ────────────────────────────────────────────────────
    status_data = [[
        Paragraph('✅  Payment Successful', success_style),
    ]]
    status_tbl = Table(status_data, colWidths=[W])
    status_tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), colors.HexColor('#052e16')),
        ('TOPPADDING',   (0,0), (-1,-1), 12),
        ('BOTTOMPADDING',(0,0), (-1,-1), 12),
        ('LEFTPADDING',  (0,0), (-1,-1), 16),
        ('RIGHTPADDING', (0,0), (-1,-1), 16),
        ('BOX',          (0,0), (-1,-1), 1, colors.HexColor('#166534')),
        ('ROUNDEDCORNERS',(0,0),(-1,-1),[6,6,6,6]),
    ]))
    story.append(status_tbl)
    story.append(Spacer(1, 6*mm))

    # ── Transaction Details ───────────────────────────────────────────────
    txn_date = payment.created_at.strftime('%d %B %Y, %I:%M %p') if payment.created_at else datetime.utcnow().strftime('%d %B %Y')

    txn_data = [
        ['Transaction ID', payment.transaction_id],
        ['Date & Time',    txn_date],
        ['Payment Method', payment.method.replace('_',' ').title()],
        ['Status',         '✅ Successful'],
        ['Billed To',      f"{user.name}\n{user.email}"],
    ]
    txn_tbl = Table(
        [[Paragraph(k, muted), Paragraph(str(v), body)] for k,v in txn_data],
        colWidths=[W*0.32, W*0.68]
    )
    txn_tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), CARD),
        ('TOPPADDING',   (0,0), (-1,-1), 8),
        ('BOTTOMPADDING',(0,0), (-1,-1), 8),
        ('LEFTPADDING',  (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ('LINEBELOW',    (0,0), (-1,-2), 0.5, colors.HexColor('#1f2937')),
        ('BOX',          (0,0), (-1,-1), 1, colors.HexColor('#1f2937')),
    ]))
    story.append(Paragraph('Transaction Details', h2))
    story.append(txn_tbl)
    story.append(Spacer(1, 6*mm))

    # ── Ad Details ────────────────────────────────────────────────────────
    slot_meta = {}
    if ad.admin_notes:
        try:
            slot_meta = json.loads(ad.admin_notes)
        except Exception:
            pass

    pricing = slot_meta.get('pricing', {})
    slot_type  = slot_meta.get('slot_type', 'normal').title()
    days       = slot_meta.get('days', 1)
    start_time = slot_meta.get('start_time', '')
    end_time   = slot_meta.get('end_time', '')

    ad_rows = [
        ['Ad Title',     ad.title],
        ['Product',      ad.product_name],
        ['Category',     ad.category],
        ['Ad Format',    ('🖼️ Poster' if ad.ad_format == 'poster' else '🎬 Video')],
        ['Display Location', ad.location or '—'],
        ['Time Slot',    f"{slot_type}{' (' + start_time + '–' + end_time + ')' if slot_type=='Manual' and start_time else ''}"],
        ['Duration',     f"{days} day{'s' if days > 1 else ''}"],
    ]
    ad_tbl = Table(
        [[Paragraph(k, muted), Paragraph(str(v), body)] for k,v in ad_rows],
        colWidths=[W*0.32, W*0.68]
    )
    ad_tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,-1), CARD),
        ('TOPPADDING',   (0,0), (-1,-1), 8),
        ('BOTTOMPADDING',(0,0), (-1,-1), 8),
        ('LEFTPADDING',  (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ('LINEBELOW',    (0,0), (-1,-2), 0.5, colors.HexColor('#1f2937')),
        ('BOX',          (0,0), (-1,-1), 1, colors.HexColor('#1f2937')),
    ]))
    story.append(Paragraph('Advertisement Details', h2))
    story.append(ad_tbl)
    story.append(Spacer(1, 6*mm))

    # ── Price Breakdown ───────────────────────────────────────────────────
    subtotal  = pricing.get('subtotal', payment.amount / 1.18)
    gst       = pricing.get('gst', payment.amount - subtotal)
    total     = payment.amount

    price_rows = [
        ['Description',              'Amount (INR)'],
        [f"Ad Slot — {ad.ad_format.title()} format",  f"₹{subtotal:.2f}"],
        ['GST @ 18%',                                  f"₹{gst:.2f}"],
        ['',                                           ''],
        ['Total Paid',                                 f"₹{total:.2f}"],
    ]

    price_tbl = Table(
        price_rows,
        colWidths=[W*0.65, W*0.35]
    )
    price_tbl.setStyle(TableStyle([
        # Header row
        ('BACKGROUND',   (0,0), (-1,0), PURPLE),
        ('TEXTCOLOR',    (0,0), (-1,0), WHITE),
        ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,0), 10),
        ('TOPPADDING',   (0,0), (-1,0), 10),
        ('BOTTOMPADDING',(0,0), (-1,0), 10),
        ('LEFTPADDING',  (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 14),
        # Body rows
        ('BACKGROUND',   (0,1), (-1,-2), CARD),
        ('TEXTCOLOR',    (0,1), (-1,-2), TEXT),
        ('FONTNAME',     (0,1), (-1,-2), 'Helvetica'),
        ('FONTSIZE',     (0,1), (-1,-2), 10),
        ('TOPPADDING',   (0,1), (-1,-2), 9),
        ('BOTTOMPADDING',(0,1), (-1,-2), 9),
        ('LINEBELOW',    (0,1), (-1,-2), 0.5, colors.HexColor('#1f2937')),
        ('ALIGN',        (1,0), (1,-1), 'RIGHT'),
        # Total row
        ('BACKGROUND',   (0,-1), (-1,-1), colors.HexColor('#1a1a3e')),
        ('TEXTCOLOR',    (0,-1), (-1,-1), PURPLE),
        ('FONTNAME',     (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,-1), (-1,-1), 13),
        ('TOPPADDING',   (0,-1), (-1,-1), 12),
        ('BOTTOMPADDING',(0,-1), (-1,-1), 12),
        ('BOX',          (0,0),  (-1,-1), 1, colors.HexColor('#374151')),
    ]))
    story.append(Paragraph('Price Breakdown', h2))
    story.append(price_tbl)
    story.append(Spacer(1, 8*mm))

    # ── Note ─────────────────────────────────────────────────────────────
    story.append(Paragraph(
        'Your advertisement has been submitted for admin review. '
        'You will receive a notification once it is approved and goes live on the LED display network.',
        muted))
    story.append(Spacer(1, 8*mm))

    # ── Footer ────────────────────────────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#1f2937')))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        '⚡ SmartAds AI Platform &nbsp;·&nbsp; AI-Powered Advertisement Management &nbsp;·&nbsp; '
        f'Receipt generated on {datetime.utcnow().strftime("%d %b %Y")}',
        center))
    story.append(Paragraph(
        'This is a computer-generated receipt and does not require a signature.',
        center))

    doc.build(story)
    return buf.getvalue()
