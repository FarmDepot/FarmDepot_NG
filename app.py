# app.py
import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import pandas as pd

# Try to import voice recognition dependencies (production only)
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_AVAILABLE = True
except Exception:
    VOICE_AVAILABLE = False

# ----------------------
# CREATE PLACEHOLDER IMAGES (Pillow 10+ compatible)
# ----------------------
def create_placeholder_images():
    folder = "static/demo_images"
    os.makedirs(folder, exist_ok=True)

    ad_items = [
        ("tomatoes.jpg", "Tomatoes"),
        ("rice.jpg", "Rice"),
        ("yam.jpg", "Yam"),
        ("plantain.jpg", "Plantain"),
        ("maize.jpg", "Maize"),
        ("cassava.jpg", "Cassava")
    ]
    partner_items = [
        ("partner1.png", "Partner 1"),
        ("partner2.png", "Partner 2"),
        ("partner3.png", "Partner 3"),
        ("partner4.png", "Partner 4")
    ]

    def make_image(path, text, size=(600, 400), bg_color="#b21823", font_size=36, bold=True):
        # Create background image
        img = Image.new("RGB", size, bg_color)
        draw = ImageDraw.Draw(img)

        # Load font (fallback to default)
        try:
            # Try a common TTF; on many systems Arial won't exist but DejaVu Sans often does
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except Exception:
                font = ImageFont.load_default()

        # Pillow 10+ compatible text size calculation
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Optional text shadow for better contrast
        x = (size[0] - text_w) / 2
        y = (size[1] - text_h) / 2

        # Shadow
        shadow_offset = 2
        draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 180))
        # Foreground text
        draw.text((x, y), text, font=font, fill="white")

        # Save file
        img.save(path)

    # Generate ad placeholders
    for filename, label in ad_items:
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            make_image(path, label, size=(600, 400), font_size=48)

    # Generate partner placeholders
    for filename, label in partner_items:
        path = os.path.join(folder, filename)
        if not os.path.exists(path):
            make_image(path, label, size=(400, 200), font_size=28)

# Create placeholders on startup
create_placeholder_images()

# ----------------------
# Page config and session init
# ----------------------
st.set_page_config(
    page_title="FARMDEPOT_NG - Agricultural Marketplace",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'user_logged_in' not in st.session_state:
    st.session_state.user_logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False

# ----------------------
# Database initialization
# ----------------------
@st.cache_resource
def init_database():
    conn = sqlite3.connect('farmdepot.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  user_type TEXT NOT NULL,
                  phone TEXT,
                  location TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

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
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS blog_posts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  content TEXT NOT NULL,
                  author TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Insert sample ads with image paths if none exist
    c.execute("SELECT COUNT(*) FROM ads")
    if c.fetchone()[0] == 0:
        sample_ads = [
            (1, "Fresh Tomatoes - Premium Quality", "Organic tomatoes from our farm", "Vegetables", 5000.0, "Lagos", "08123456789", "static/demo_images/tomatoes.jpg", "promoted", "active"),
            (1, "Yellow Rice - 50kg Bags", "High quality yellow rice", "Grains", 25000.0, "Kano", "08123456790", "static/demo_images/rice.jpg", "top", "active"),
            (1, "Fresh Yam Tubers", "Large yam tubers direct from farm", "Tubers", 15000.0, "Ogun", "08123456791", "static/demo_images/yam.jpg", "regular", "active"),
            (1, "Plantain Bunches", "Fresh plantain ready for market", "Vegetables", 8000.0, "Ibadan", "08123456792", "static/demo_images/plantain.jpg", "regular", "active"),
            (1, "Maize - White Corn", "Dried white corn for sale", "Cereals", 20000.0, "Kaduna", "08123456793", "static/demo_images/maize.jpg", "promoted", "active"),
            (1, "Cassava Flour", "Processed cassava flour", "Processed Foods", 12000.0, "Oyo", "08123456794", "static/demo_images/cassava.jpg", "top", "active")
        ]
        c.executemany("""INSERT INTO ads (user_id, title, description, category, price, location, contact_info, image_path, ad_type, status)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", sample_ads)

    conn.commit()
    return conn

# keep a single db connection from init_database()
_db_conn = init_database()

# ----------------------
# Utility functions: auth & ads
# ----------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username: str, password: str):
    conn = _db_conn
    c = conn.cursor()
    hashed = hash_password(password)
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed))
    return c.fetchone()

def register_user(username: str, email: str, password: str, user_type: str, phone="", location=""):
    conn = _db_conn
    c = conn.cursor()
    try:
        hashed = hash_password(password)
        c.execute("""INSERT INTO users (username, email, password, user_type, phone, location)
                     VALUES (?, ?, ?, ?, ?, ?)""", (username, email, hashed, user_type, phone, location))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def post_ad(user_id, title, description, category, price, location, contact_info, image_path=None, ad_type='regular'):
    conn = _db_conn
    c = conn.cursor()
    c.execute("""INSERT INTO ads (user_id, title, description, category, price, location, contact_info, image_path, ad_type)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (user_id, title, description, category, price, location, contact_info, image_path, ad_type))
    conn.commit()

def search_ads(query="", category="", location=""):
    conn = _db_conn
    c = conn.cursor()
    sql = "SELECT * FROM ads WHERE status = 'active'"
    params = []
    if query:
        sql += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])
    if category and category != "All Categories":
        sql += " AND category = ?"
        params.append(category)
    if location:
        sql += " AND location LIKE ?"
        params.append(f"%{location}%")
    sql += " ORDER BY created_at DESC"
    c.execute(sql, params)
    return c.fetchall()

def get_ads_by_type(ad_type='regular', limit=10):
    conn = _db_conn
    c = conn.cursor()
    c.execute("SELECT * FROM ads WHERE ad_type = ? AND status = 'active' ORDER BY created_at DESC LIMIT ?", (ad_type, limit))
    return c.fetchall()

# ----------------------
# VoiceAssistant (production only)
# ----------------------
class VoiceAssistant:
    def __init__(self):
        self.available = VOICE_AVAILABLE
        if self.available:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                self.tts_engine = pyttsx3.init()
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    for voice in voices:
                        if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                            self.tts_engine.setProperty('voice', voice.id)
                            break
                self.tts_engine.setProperty('rate', 150)
                self.tts_engine.setProperty('volume', 0.8)
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
            except Exception as e:
                st.error(f"Error initializing voice components: {e}")
                self.available = False

    def listen_for_speech(self, timeout=5, phrase_time_limit=10):
        if not self.available:
            return "Voice recognition not available."
        try:
            with self.microphone as source:
                st.info("🎤 Listening... Please speak now!")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                st.info("⏳ Processing your speech...")
                text = self.recognizer.recognize_google(audio)
                return text.lower()
        except Exception as e:
            return f"Error: {e}"

    def text_to_speech(self, text):
        if not self.available:
            return False
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            return True
        except Exception as e:
            st.error(f"TTS Error: {e}")
            return False

# ----------------------
# UI components
# ----------------------
def render_header():
    st.markdown("""
    <div style='background: linear-gradient(90deg, #b21823, #e84a52); padding: 1rem; border-radius: 10px; margin-bottom: 1.5rem;'>
      <div style='display:flex; align-items:center; justify-content:space-between;'>
        <h1 style='color:white; margin:0;'>🌾 FARMDEPOT_NG</h1>
        <div style='color:white;'>Nigeria's Premier Agricultural Marketplace</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    st.sidebar.markdown("## 🌾 FARMDEPOT_NG")
    if not st.session_state.user_logged_in:
        choice = st.sidebar.radio("Account", ["Login", "Register"])
        if choice == "Login":
            with st.sidebar.form("login"):
                st.text_input("Username", key="login_username")
                st.text_input("Password", type="password", key="login_password")
                if st.form_submit_button("Login"):
                    user = authenticate_user(st.session_state.get("login_username",""), st.session_state.get("login_password",""))
                    if user:
                        st.session_state.user_logged_in = True
                        st.session_state.user_info = user
                        st.success("Logged in")
                    else:
                        st.error("Invalid credentials")
        else:
            with st.sidebar.form("register"):
                st.text_input("Username", key="reg_username")
                st.text_input("Email", key="reg_email")
                st.text_input("Password", type="password", key="reg_password")
                st.selectbox("User Type", ["Farmer","Trader","Buyer","Processor"], key="reg_usertype")
                st.text_input("Phone", key="reg_phone")
                st.text_input("Location", key="reg_location")
                if st.form_submit_button("Register"):
                    ok = register_user(st.session_state.get("reg_username",""), st.session_state.get("reg_email",""), st.session_state.get("reg_password",""), st.session_state.get("reg_usertype",""), st.session_state.get("reg_phone",""), st.session_state.get("reg_location",""))
                    if ok:
                        st.success("Registration successful. Please login.")
                    else:
                        st.error("Username or email may already exist.")
    else:
        st.sidebar.success(f"Welcome, {st.session_state.user_info[1]}!")
        if st.sidebar.button("Logout"):
            st.session_state.user_logged_in = False
            st.session_state.user_info = None
            st.experimental_rerun()

    st.sidebar.markdown("---")
    st.sidebar.selectbox("Language", ["English","Hausa","Yoruba","Igbo"], key="sidebar_lang")
    # Quick stats
    c = _db_conn.cursor()
    c.execute("SELECT COUNT(*) FROM ads WHERE status='active'")
    total_ads = c.fetchone()[0]
    st.sidebar.metric("Active Ads", total_ads)

# Display ads (image on top)
def display_ads(ads, title=""):
    if not ads:
        st.info("No ads found.")
        return
    if title:
        st.markdown(f"### {title}")
    for i in range(0, len(ads), 3):
        cols = st.columns(3)
        for cidx in range(3):
            idx = i + cidx
            if idx < len(ads):
                ad = ads[idx]
                # ad indices:
                # 0 id,1 user_id,2 title,3 description,4 category,5 price,6 location,7 contact,8 image_path,9 ad_type,10 status,11 created_at
                image_path = ad[8] if ad[8] and os.path.exists(ad[8]) else "static/demo_images/tomatoes.jpg"
                with cols[cidx]:
                    st.image(image_path, use_column_width=True)
                    price_formatted = f"₦{ad[5]:,.0f}" if ad[5] else "Price on request"
                    st.markdown(f"""
                        <div style='border:2px solid #b21823; padding:0.8rem; border-radius:10px; margin-top:0.6rem; background:#fff;'>
                            <h4 style='color:#b21823; margin:0 0 4px 0;'>{ad[2]}</h4>
                            <p style='color:#444; margin:0 0 8px 0;'>{ad[3][:120]}{'...' if len(ad[3])>120 else ''}</p>
                            <strong style='color:#b21823;'>{price_formatted}</strong><br>
                            <small>📍 {ad[6]} • 📞 {ad[7]}</small>
                            <div style='margin-top:8px; color:#888; font-size:12px;'>{ad[11] if len(ad)>11 else ''}</div>
                        </div>
                    """, unsafe_allow_html=True)

# ----------------------
# Pages
# ----------------------
def home_page():
    render_hero()
    st.markdown("---")
    render_categories()
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Promoted Ads")
        promoted = get_ads_by_type('promoted', 3)
        if promoted:
            display_ads(promoted)
        else:
            st.info("No promoted ads")

    with col2:
        st.markdown("### Top Ads")
        top = get_ads_by_type('top', 3)
        if top:
            display_ads(top)
        else:
            st.info("No top ads")

    st.markdown("### Recent Ads")
    recent = get_ads_by_type('regular', 6)
    if recent:
        display_ads(recent)
    else:
        st.info("No recent ads")

    st.markdown("---")
    st.markdown("### Our Trusted Partners")
    partners = [
        {"name":"Nigerian Agricultural Bank","desc":"Financial Services","img":"static/demo_images/partner1.png"},
        {"name":"FarmTech Solutions","desc":"Technology Partner","img":"static/demo_images/partner2.png"},
        {"name":"Green Harvest Co.","desc":"Supply Chain","img":"static/demo_images/partner3.png"},
        {"name":"AgroLoan Services","desc":"Micro-financing","img":"static/demo_images/partner4.png"}
    ]
    cols = st.columns(4)
    for i, p in enumerate(partners):
        with cols[i]:
            st.image(p["img"], use_column_width=True)
            st.markdown(f"**{p['name']}**")
            st.markdown(f"*{p['desc']}*")

def render_hero():
    st.markdown("""
    <div style='text-align:center; padding:2rem; background:linear-gradient(135deg, #b21823, #e84a52); border-radius:12px; color:white;'>
      <h1 style='margin:0;'>Buy, Sell, & Rent Anything Agriculture In One Click</h1>
      <p style='opacity:0.95; margin:6px 0 0 0;'>Search through thousands of active ads across Nigeria</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔍 Search")
    col1, col2, col3, col4 = st.columns([3,2,2,1])
    with col1:
        q = st.text_input("Search products", key="search_q", placeholder="e.g., Rice, Yam, Tomatoes")
    with col2:
        cat = st.selectbox("Category", ["All Categories","Tubers","Grains","Cereals","Cash Crops","Vegetables"], key="search_cat")
    with col3:
        loc = st.text_input("Location", key="search_loc", placeholder="Lagos, Kano")
    with col4:
        if st.button("Search"):
            results = search_ads(q, cat, loc)
            st.session_state.search_results = results
            st.session_state.search_performed = True

    # Voice search (production only)
    st.markdown("### 🎤 Voice Search")
    va = VoiceAssistant()
    if va.available:
        if st.button("Start Voice Search"):
            with st.spinner("Listening..."):
                voice_text = va.listen_for_speech()
            st.success(f"You said: {voice_text}")
            results = search_ads(voice_text)
            st.session_state.search_results = results
            st.session_state.search_performed = True
    else:
        st.warning("Voice recognition not available. To enable, install required packages and run in an environment with microphone access.")

    if st.session_state.get('search_performed', False):
        display_ads(st.session_state.get('search_results', []), "Search Results")

def render_categories():
    st.markdown("### Browse by Categories")
    cats = ["Tubers", "Grains", "Cereals", "Cash Crops", "Seedlings", "Fertilizers", "Vegetables", "Livestock"]
    cols = st.columns(4)
    for i, cat in enumerate(cats):
        with cols[i % 4]:
            if st.button(cat):
                results = search_ads(category=cat)
                st.session_state.search_results = results
                st.session_state.search_performed = True

def ads_list_page():
    st.markdown("## All Advertisements")
    # filters simplified
    category = st.selectbox("Filter by Category", ["All Categories","Tubers","Grains","Cereals","Vegetables"])
    location = st.text_input("Filter by Location", "")
    if st.button("Apply"):
        ads = search_ads("", category if category!="All Categories" else "", location)
    else:
        ads = search_ads()
    display_ads(ads, f"All Advertisements ({len(ads)})")

def post_ad_page():
    st.markdown("## Post an Advertisement")
    if not st.session_state.user_logged_in:
        st.warning("Please login to post an ad via the sidebar.")
        return
    with st.form("post_ad_form"):
        title = st.text_input("Title")
        category = st.selectbox("Category", ["Tubers","Grains","Cereals","Cash Crops","Vegetables"])
        price = st.number_input("Price (₦)", min_value=0.0, step=100.0)
        location = st.text_input("Location")
        description = st.text_area("Description")
        contact_info = st.text_input("Contact info")
        uploaded = st.file_uploader("Upload product image", type=["png","jpg","jpeg"])
        submit = st.form_submit_button("Post Ad")
        if submit:
            image_path = None
            if uploaded:
                os.makedirs("uploads", exist_ok=True)
                filename = f"uploads/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded.name}"
                with open(filename, "wb") as f:
                    f.write(uploaded.getbuffer())
                image_path = filename
            user_id = st.session_state.user_info[0]
            post_ad(user_id, title, description, category, price, location, contact_info, image_path)
            st.success("Ad posted!")

def about_page():
    st.markdown("## About FARMDEPOT_NG")
    st.write("Empowering Nigerian agriculture...")

def blog_page():
    st.markdown("## Blog & News")
    st.write("Sample blog posts...")

def contact_page():
    st.markdown("## Contact Us")
    st.write("Contact details...")

def render_footer():
    st.markdown("---")
    st.markdown("""
    <div style='text-align:center; padding:1rem; border-top:2px solid #b21823;'>
        <p>&copy; 2025 FARMDEPOT_NG — Connecting Farmers, Traders & Consumers</p>
    </div>
    """, unsafe_allow_html=True)

# ----------------------
# Main
# ----------------------
def main():
    render_header()
    render_sidebar()

    page = st.sidebar.radio("Navigate to", ["Home","Ads List","Post Ad","About","Blog","Contact"])
    if page == "Home":
        home_page()
    elif page == "Ads List":
        ads_list_page()
    elif page == "Post Ad":
        post_ad_page()
    elif page == "About":
        about_page()
    elif page == "Blog":
        blog_page()
    elif page == "Contact":
        contact_page()

    render_footer()

if __name__ == "__main__":
    main()
