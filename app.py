import streamlit as st
import sqlite3
import os
from PIL import Image, ImageDraw, ImageFont
import re

# Optional voice dependencies
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# ----------------------
# Helpers
# ----------------------
def slugify(text):
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')

def create_placeholder_images(ad_titles, partner_names):
    folder = "static/demo_images"
    os.makedirs(folder, exist_ok=True)

    def make_image(path, text, size=(300, 200), font_size=24, bg_color="#b21823"):
        img = Image.new("RGB", size, bg_color)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text(((size[0]-text_w)/2, (size[1]-text_h)/2), text, fill="white", font=font)
        img.save(path)

    for title in ad_titles:
        filename = f"{slugify(title)}.jpg"
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            make_image(path, title.split('-')[0].strip(), size=(200, 150), font_size=20)

    for name in partner_names:
        filename = f"{slugify(name)}.png"
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            make_image(path, name, size=(200, 150), font_size=18)

# Demo data for placeholders
demo_ads_titles = [
    "Fresh Tomatoes - Premium Quality",
    "Yellow Rice - 50kg Bags",
    "Fresh Yam Tubers",
    "Plantain Bunches",
    "Maize - White Corn",
    "Cassava Flour"
]
demo_partners_names = [
    "Nigerian Agricultural Bank",
    "FarmTech Solutions",
    "Green Harvest Co.",
    "AgroLoan Services"
]
create_placeholder_images(demo_ads_titles, demo_partners_names)

# ----------------------
# DB setup
# ----------------------
@st.cache_resource
def init_database():
    conn = sqlite3.connect('farmdepot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ads
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  title TEXT NOT NULL,
                  description TEXT,
                  category TEXT NOT NULL,
                  price REAL,
                  location TEXT,
                  contact_info TEXT,
                  image_path TEXT,
                  ad_type TEXT DEFAULT 'regular',
                  status TEXT DEFAULT 'active',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute("SELECT COUNT(*) FROM ads")
    if c.fetchone()[0] == 0:
        sample_ads = [
            (1, t, "Sample description for " + t, "General", 1000.0, "Lagos", "08012345678",
             f"static/demo_images/{slugify(t)}.jpg", "regular", "active")
            for t in demo_ads_titles
        ]
        c.executemany("""INSERT INTO ads (user_id, title, description, category, price, location, contact_info, image_path, ad_type, status)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", sample_ads)
    conn.commit()
    conn.close()
init_database()

# ----------------------
# Query helpers
# ----------------------
def search_ads(query="", category="", location=""):
    conn = sqlite3.connect('farmdepot.db')
    c = conn.cursor()
    sql = "SELECT * FROM ads WHERE status='active'"
    params = []
    if query:
        sql += " AND title LIKE ?"
        params.append(f"%{query}%")
    if category and category != "All Categories":
        sql += " AND category=?"
        params.append(category)
    if location:
        sql += " AND location LIKE ?"
        params.append(f"%{location}%")
    c.execute(sql, params)
    results = c.fetchall()
    conn.close()
    return results

def get_ads_by_type(ad_type, limit=3):
    conn = sqlite3.connect('farmdepot.db')
    c = conn.cursor()
    c.execute("SELECT * FROM ads WHERE ad_type=? AND status='active' LIMIT ?", (ad_type, limit))
    results = c.fetchall()
    conn.close()
    return results

# ----------------------
# Voice assistant (safe initialization)
# ----------------------
class VoiceAssistant:
    def __init__(self):
        self.available = VOICE_AVAILABLE

    def listen_for_speech(self):
        if not self.available:
            return ""

        # Cloud/browser: use Streamlit audio input
        try:
            audio_file = st.audio_input("🎤 Speak now...")
            if audio_file:
                r = sr.Recognizer()
                with sr.AudioFile(audio_file) as source:
                    audio = r.record(source)
                return r.recognize_google(audio)
            return ""
        except Exception:
            pass

        # Local mode: PyAudio
        try:
            r = sr.Recognizer()
            with sr.Microphone() as source:
                st.info("Listening via microphone...")
                audio = r.listen(source)
            return r.recognize_google(audio)
        except OSError:
            st.error("No default microphone found.")
            return ""

# ----------------------
# UI components
# ----------------------
def render_header():
    st.markdown("""
    <div style='background: linear-gradient(135deg, #b21823, #e84a52); padding: 1rem; text-align: center; border-radius: 0 0 10px 10px;'>
        <h1 style='color: white; margin: 0;'>🌾 FARMDEPOT_NG</h1>
        <p style='color: white; margin: 0;'>Connecting Farmers, Traders & Consumers Across Nigeria</p>
    </div>
    """, unsafe_allow_html=True)

def display_ads(ads, title=""):
    if not ads:
        st.info("No ads found.")
        return
    if title:
        st.markdown(f"### {title}")
    for i in range(0, len(ads), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(ads):
                ad = ads[i + j]
                image_path = ad[8] if ad[8] and os.path.exists(ad[8]) else "static/demo_images/tomatoes.jpg"
                price_formatted = f"₦{ad[5]:,.0f}" if ad[5] else "Price on request"
                with cols[j]:
                    st.markdown(f"""
                    <div style='border:2px solid #b21823; border-radius:10px; background:#fff; padding:0.6rem; display:flex; align-items:flex-start;'>
                        <img src='{image_path}' style='width:100px; height:auto; margin-right:10px; border-radius:6px;'>
                        <div style='flex:1;'>
                            <h4 style='color:#b21823; margin:0;'>{ad[2]}</h4>
                            <p style='color:#444; font-size:0.85rem; margin:4px 0;'>{ad[3][:80]}{'...' if len(ad[3])>80 else ''}</p>
                            <strong style='color:#b21823;'>{price_formatted}</strong><br>
                            <small>📍 {ad[6]} • 📞 {ad[7]}</small>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

def home_page():
    st.markdown("""
    <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #b21823, #e84a52); border-radius: 15px; color: white;'>
        <h1>Buy, Sell, & Rent Anything Agriculture In One Click</h1>
        <p>Search through over 1000+ Active Ads from any Location In Nigeria</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔍 Search Agricultural Products")
    search_query = st.text_input("Search", placeholder="e.g., Rice, Yam, Tomatoes")
    category = st.selectbox("Category", ["All Categories", "Tubers", "Grains", "Cereals", "Cash Crops", "Vegetables"])
    location = st.text_input("Location Filter", placeholder="e.g., Lagos, Kano")

    if st.button("🔍 Search"):
        ads = search_ads(search_query, category, location)
        st.session_state['search_results'] = ads
        st.session_state['search_performed'] = True

    st.markdown("### 🎤 Voice Search")
    voice_assistant = VoiceAssistant()
    if voice_assistant.available:
        if st.button("Start Voice Search"):
            with st.spinner("Listening..."):
                voice_text = voice_assistant.listen_for_speech()
            if voice_text:
                st.success(f"You said: {voice_text}")
                ads = search_ads(voice_text)
                st.session_state['search_results'] = ads
                st.session_state['search_performed'] = True
    else:
        st.warning("⚠️ Voice recognition not available.")

    if st.session_state.get('search_performed', False):
        display_ads(st.session_state.get('search_results', []), "Search Results")

    st.markdown("---")
    st.markdown("### 🌟 Promoted Ads")
    display_ads(get_ads_by_type('promoted', 3))
    st.markdown("### ⭐ Top Ads")
    display_ads(get_ads_by_type('top', 3))
    st.markdown("### 📋 Recent Ads")
    display_ads(get_ads_by_type('regular', 6))

    st.markdown("---")
    st.markdown("### 🤝 Our Trusted Partners")
    partner_cols = st.columns(4)
    partners = [
        {"name": "Nigerian Agricultural Bank", "desc": "Financial Services", "img": f"static/demo_images/{slugify('Nigerian Agricultural Bank')}.png"},
        {"name": "FarmTech Solutions", "desc": "Technology Partner", "img": f"static/demo_images/{slugify('FarmTech Solutions')}.png"},
        {"name": "Green Harvest Co.", "desc": "Supply Chain", "img": f"static/demo_images/{slugify('Green Harvest Co.')}.png"},
        {"name": "AgroLoan Services", "desc": "Micro-financing", "img": f"static/demo_images/{slugify('AgroLoan Services')}.png"}
    ]
    for i, partner in enumerate(partners):
        with partner_cols[i]:
            st.image(partner["img"], use_container_width=True)
            st.markdown(f"**{partner['name']}**\n\n_{partner['desc']}_")

def ads_list_page():
    st.markdown("## 📋 All Advertisements")
    ads = search_ads()
    display_ads(ads)

def post_ad_page():
    st.markdown("## 📝 Post New Advertisement")
    title = st.text_input("Title")
    category = st.selectbox("Category", ["Tubers", "Grains", "Cereals", "Cash Crops", "Vegetables"])
    price = st.number_input("Price", min_value=0.0)
    location = st.text_input("Location")
    description = st.text_area("Description")
    contact_info = st.text_input("Contact Information")
    uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])

    if st.button("Post Ad"):
        image_path = None
        if uploaded_file:
            os.makedirs("uploads", exist_ok=True)
            image_path = f"uploads/{uploaded_file.name}"
            with open(image_path, "wb") as f:
                f.write(uploaded_file.read())
        conn = sqlite3.connect('farmdepot.db')
        c = conn.cursor()
        c.execute("""INSERT INTO ads (user_id, title, description, category, price, location, contact_info, image_path)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                  (1, title, description, category, price, location, contact_info, image_path))
        conn.commit()
        conn.close()
        st.success("Advertisement posted!")

def render_footer():
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 1.5rem; border-top: 2px solid #b21823;'>
        <p>&copy; 2025 <strong>FARMDEPOT_NG</strong>. All rights reserved.</p>
        <p style='color: #b21823;'>Connecting Farmers, Traders, and Consumers Across Nigeria</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    render_header()  # ✅ Global header on every page
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "Ads List", "Post Ad"])
    if page == "Home":
        home_page()
    elif page == "Ads List":
        ads_list_page()
    elif page == "Post Ad":
        post_ad_page()
    render_footer()

if __name__ == "__main__":
    main()
