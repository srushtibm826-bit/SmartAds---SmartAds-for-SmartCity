SmartAds — Demo AI Videos
==========================

Place your pre-generated D-ID avatar videos here:

  saree_ad.mp4   → Shows for Fashion/Saree category ads (demo@smartads.com)
  burger_ad.mp4  → Shows for Food & Beverage/Burger category ads

These videos play automatically in the D-ID Avatar Studio as 
"AI Generated Video" demos — showing what D-ID produces without
needing to generate a new one each time.

How to add your videos:
  1. Copy your saree video  → rename to:  saree_ad.mp4
  2. Copy your burger video → rename to:  burger_ad.mp4
  3. Place both files in this folder: app/static/demo_videos/
  4. Restart the app (python run.py)
  5. Go to Dashboard → any Fashion ad → D-ID Avatar Studio
     → Video plays automatically!

Flask serves them at:
  /static/demo_videos/saree_ad.mp4
  /static/demo_videos/burger_ad.mp4

Supported formats: .mp4 (recommended), .webm
