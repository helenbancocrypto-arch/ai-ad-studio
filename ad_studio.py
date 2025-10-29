import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, random, numpy as np, zipfile, os

st.set_page_config(page_title="AI Ad Studio — Light", layout="centered")

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

def pick(seq, k=3):
    import random
    return random.sample(seq, k=min(k, len(seq)))

def gen_concepts(brand, offer, audience, goal, tone):
    hooks = [h.format(audience=audience, brand=brand, goal=goal) for h in pick(HOOKS)]
    angles = pick(ANGLES)
    concepts = []
    for i in range(len(hooks)):
        concepts.append({
            "hook": hooks[i],
            "angle": angles[i],
            "value": f"{brand} helps {audience} {goal} with {offer}.",
            "cta": random.choice(CTAS)
        })
    return concepts

def gen_script(brand, offer, audience, goal, tone, duration=30):
    scenes = [
        {"text": f"{brand}", "sub": f"{offer}"},
        {"text": f"{audience}", "sub":"This is for you."},
        {"text":"The Problem", "sub":f"Doing {goal} is messy & slow."},
        {"text":"The Fix", "sub":f"{brand} → {offer}"},
        {"text":"How it Feels", "sub":"Fast. Simple. Predictable."},
        {"text":"Call to Action", "sub":"Tap to try now →"},
    ]
    return {"duration": duration, "scenes": scenes}

def make_slide(size, title, subtitle, logo_img=None):
    W,H = size
    img = Image.new("RGB", size, (8,14,25))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        r = int(10 + 50*np.sin(y/140))
        g = int(30 + 120*np.sin(y/180))
        b = 120 + (y % 40)
        draw.line([(0,y),(W,y)], fill=(r,g,b))
    overlay = Image.new("RGBA", size, (0,0,0,120))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    try:
        font_title = ImageFont.truetype("arial.ttf", 72)
        font_sub   = ImageFont.truetype("arial.ttf", 38)
    except:
        font_title = ImageFont.load_default()
        font_sub   = ImageFont.load_default()
    tw, th = draw.textsize(title, font=font_title)
    draw.text(((W-tw)//2, H//3 - th//2), title, font=font_title, fill=(180,240,255))
    sw, sh = draw.textsize(subtitle, font=font_sub)
    draw.text(((W-sw)//2, H//3 + th//2 + 30), subtitle, font=font_sub, fill=(220,210,255))
    if logo_img:
        L = min(W//5, 320)
        logo = logo_img.copy().convert("RGBA")
        logo.thumbnail((L,L))
        img.paste(logo, (W-L-40, 40), logo)
    return img

def save_image(image, filename):
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    data = buf.getvalue()
    with open(filename, "wb") as f:
        f.write(data)
    return data

st.title("🎬 AI Ad Studio — Light (no video)")
st.caption("Brief → Concepts → Script → PNG Slides (downloadable)")

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
    logo = st.file_uploader("Optional Logo (PNG/JPG preferred)", type=["png","jpg","jpeg"])
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
    st.subheader("Generate PNG Slides (1080×1920)")
    size = (1080, 1920)
    logo_img = None
    if logo:
        try:
            logo_img = Image.open(logo)
        except:
            logo_img = None
    generated = []
    for idx, s in enumerate(script["scenes"], start=1):
        slide = make_slide(size, s["text"], s["sub"], logo_img)
        filename = f"slide_{idx:02d}.png"
        data = save_image(slide, filename)
        generated.append((filename, data))
    for filename, data in generated:
        st.image(data, caption=filename, use_column_width=True)
        st.download_button("⬇️ Download " + filename, data=data, file_name=filename, mime="image/png")
    zipname = "slides_bundle.zip"
    with zipfile.ZipFile(zipname, "w", zipfile.ZIP_DEFLATED) as z:
        for filename, _ in generated:
            z.write(filename, arcname=filename)
    with open(zipname, "rb") as zf:
        st.download_button("⬇️ Download ALL slides (ZIP)", data=zf.read(), file_name=zipname, mime="application/zip")
