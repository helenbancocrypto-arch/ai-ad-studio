import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, concatenate_videoclips
import os, io, random, datetime, numpy as np

# -------------------------
# Utility
# -------------------------
def pick(seq, k=3):
    import random
    return random.sample(seq, k=min(k, len(seq)))

HOOKS = [
    "Stop scrolling—{audience} need this.",
    "If you’re {audience}, here’s your shortcut.",
    "What if {brand} made {goal} stupid-simple?",
    "{audience}: 1 tweak to boost results—today.",
    "We tested this so you don’t have to.",
]
ANGLES = [
    "Pain→Relief (show problem, then solution).",
    "Before/After (contrast daily life).",
    "Myth-busting (common mistake + fix).",
    "One-feature focus (demo a single win).",
    "Social proof (mini-testimonial vibe).",
]
CTAS = [
    "Tap to try now.",
    "Get started—free today.",
    "Claim your spot.",
    "Join in 60 seconds.",
    "See how it works.",
]

def gen_concepts(brand, offer, audience, goal, tone):
    hooks = [h.format(audience=audience, brand=brand, goal=goal) for h in pick(HOOKS)]
    angles = pick(ANGLES)
    concepts = []
    for i in range(len(hooks)):
        concepts.append({
            "hook": hooks[i],
            "angle": angles[i],
            "value": f"{brand} helps {audience} {goal} with {offer}.",
            "cta": __import__("random").choice(CTAS)
        })
    return concepts

def gen_script(brand, offer, audience, goal, tone, duration=30):
    # Simple 6-scene, ~5s each
    scenes = [
        {"t":0,  "text": f"{brand}", "sub": f"{offer}"},
        {"t":5,  "text": f"{audience}", "sub":"This is for you."},
        {"t":10, "text":"The Problem", "sub":f"Doing {goal} is messy & slow."},
        {"t":15, "text":"The Fix", "sub":f"{brand} → {offer}"},
        {"t":20, "text":"How it Feels", "sub":"Fast. Simple. Predictable."},
        {"t":25, "text":"Call to Action", "sub":"Tap to try now →"},
    ]
    return {"duration": duration, "scenes": scenes}

# -------------------------
# Visuals
# -------------------------
def make_slide(size, title, subtitle, logo_img=None):
    W,H = size
    img = Image.new("RGB", size, (8,14,25))  # deep navy
    draw = ImageDraw.Draw(img)

    # Futuristic gradient-ish background
    for y in range(H):
        r = int(10 + 50*np.sin(y/140))
        g = int(30 + 120*np.sin(y/180))
        b = 120 + (y % 40)
        draw.line([(0,y),(W,y)], fill=(r,g,b))

    # Dark overlay for readability
    overlay = Image.new("RGBA", size, (0,0,0,120))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    # Fonts (fallback if system font missing)
    try:
        font_title = ImageFont.truetype("arial.ttf", 72)
        font_sub   = ImageFont.truetype("arial.ttf", 40)
    except:
        font_title = ImageFont.load_default()
        font_sub   = ImageFont.load_default()

    # Title
    tw, th = draw.textsize(title, font=font_title)
    draw.text(((W-tw)//2, H//3 - th//2), title, font=font_title, fill=(180,240,255))

    # Subtitle
    sw, sh = draw.textsize(subtitle, font=font_sub)
    draw.text(((W-sw)//2, H//3 + th//2 + 30), subtitle, font=font_sub, fill=(220,210,255))

    # Logo (optional, top-right)
    if logo_img:
        L = min(W//5, 320)
        logo = logo_img.copy().convert("RGBA")
        logo.thumbnail((L,L))
        img.paste(logo, (W-L-40, 40), logo)

    return img

def render_video(script, out_path, logo_file=None, size=(1080,1920)):
    logo_img = None
    if logo_file:
        try:
            logo_img = Image.open(logo_file)
        except:
            logo_img = None

    clips = []
    per_scene = max(1, int(script["duration"] / len(script["scenes"])))
    for s in script["scenes"]:
        slide = make_slide(size, s["text"], s["sub"], logo_img)
        buf = io.BytesIO()
        slide.save(buf, format="PNG")
        buf.seek(0)
        clip = ImageClip(buf).set_duration(per_scene)
        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(out_path, fps=30, codec="libx264", audio_codec="aac")

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="AI Ad Studio (MVP)", layout="centered")
st.title("🎬 AI Ad Studio — MVP")
st.caption("Brief → Concepts → Script → Render (local preview)")

with st.form("brief"):
    col1, col2 = st.columns(2)
    with col1:
        brand = st.text_input("Brand / Product", "Vibe Law")
        audience = st.text_input("Audience", "Small law firms")
        goal = st.text_input("Goal", "get more qualified consultations")
    with col2:
        offer = st.text_input("Core Offer", "AI ad studio + landing flow")
        tone = st.selectbox("Tone", ["energetic","trustworthy","premium","friendly"], index=1)
        duration = st.slider("Ad Duration (seconds)", 15, 60, 30, step=5)
    logo = st.file_uploader("Optional Logo (PNG with transparency preferred)", type=["png","jpg","jpeg"])
    submitted = st.form_submit_button("Generate Concepts")

if submitted:
    concepts = gen_concepts(brand, offer, audience, goal, tone)
    st.subheader("Concepts (Hooks + Angles + CTA)")
    for i,c in enumerate(concepts, start=1):
        st.markdown(f"**Concept {i}**")
        st.write(f"Hook: {c['hook']}")
        st.write(f"Angle: {c['angle']}")
        st.write(f"Value: {c['value']}")
        st.write(f"CTA: {c['cta']}")
        st.divider()

    st.subheader("Auto Script")
    script = gen_script(brand, offer, audience, goal, tone, duration=duration)
    for i,s in enumerate(script["scenes"], start=1):
        st.write(f"**Scene {i}** — {s['text']}")
        st.caption(s["sub"])

    if st.button("Render Preview Video (MP4)"):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = f"ad_preview_{ts}.mp4"
        with st.spinner("Rendering... (this can take ~20–60s)"):
            render_video(script, out_path, logo_file=logo)
        st.success("Done! Download below.")
        with open(out_path, "rb") as f:
            st.download_button("⬇️ Download MP4", data=f.read(), file_name=out_path, mime="video/mp4")
