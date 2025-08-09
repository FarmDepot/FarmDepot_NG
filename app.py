import streamlit as st
import speech_recognition as sr
from PIL import Image
import hashlib
import sqlite3
from datetime import datetime

# --- Streamlit Theme ---
st.set_page_config(
    page_title="FARMDEPOT.AI - Agricultural Marketplace",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown("""
    <style>
        :root {
            --primary-color: #b21823;
            --secondary-color: #8c128a;
        }
        .stButton>button {
            background-color: var(--primary-color) !important;
            color: #fff !important;
        }
        .stSidebar .css-1d391kg {
            background-color: var(--secondary-color) !important;
        }
        .ad-image-placeholder {
            width: 100%;
            height: 180px;
            background: #eee url('https://via.placeholder.com/300x180?text=No+Image') center center no-repeat;
            background-size: cover;
            border-radius: 8px;
        }
        .partner-image-placeholder {
            width: 48px;
            height: 48px;
            background: #eee url('https://via.placeholder.com/48?text=Logo') center center no-repeat;
            background-size: cover;
            border-radius: 50%;
            display: inline-block;
            margin-right: 12px;
            vertical-align: middle;
        }
    </style>
""", unsafe_allow_html=True)

# --- Voice Recognition: Only Real Microphone, No Demo Mode ---
try:
    mic = sr.Microphone()
    VOICE_AVAILABLE = True
except Exception as e:
    st.error(f"Voice recognition not available: {e}")
    VOICE_AVAILABLE = False

# --- Session State ---
if 'user_logged_in' not in st.session_state:
    st.session_state.user_logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

# --- Database Setup ---
@st.cache_resource
def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect('farmdepot.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  user_type TEXT NOT NULL,
                  phone TEXT,
                  location TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Ads table
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
    
    # Blog posts table
    c.execute('''CREATE TABLE IF NOT EXISTS blog_posts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  content TEXT NOT NULL,
                  author TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Insert sample data if tables are empty
    c.execute("SELECT COUNT(*) FROM ads")
    if c.fetchone()[0] == 0:
        sample_ads = [
            (1, "Fresh Tomatoes - Premium Quality", "Organic tomatoes from our farm", "Vegetables", 5000.0, "Lagos", "08123456789", None, "promoted", "active"),
            (1, "Yellow Rice - 50kg Bags", "High quality yellow rice", "Grains", 25000.0, "Kano", "08123456790", None, "top", "active"),
            (1, "Fresh Yam Tubers", "Large yam tubers direct from farm", "Tubers", 15000.0, "Ogun", "08123456791", None, "regular", "active"),
            (1, "Plantain Bunches", "Fresh plantain ready for market", "Vegetables", 8000.0, "Ibadan", "08123456792", None, "regular", "active"),
            (1, "Maize - White Corn", "Dried white corn for sale", "Cereals", 20000.0, "Kaduna", "08123456793", None, "promoted", "active"),
            (1, "Cassava Flour", "Processed cassava flour", "Processed Foods", 12000.0, "Oyo", "08123456794", None, "top", "active")
        ]
        c.executemany("""INSERT INTO ads (user_id, title, description, category, price, location, contact_info, image_path, ad_type, status)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", sample_ads)
    
    conn.commit()
    conn.close()

init_database()

# --- Utility Functions ---
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def use_real_voice_recognition():
    """Check if real voice recognition is available"""
    return VOICE_AVAILABLE

class VoiceAssistant:
    """Voice Assistant for FARMDEPOT_NG"""
    def __init__(self):
        if not VOICE_AVAILABLE:
            raise RuntimeError("Voice recognition not available.")
        self.recognizer = sr.Recognizer()
        self.microphone = mic

    def listen_for_speech(self, timeout=5, phrase_time_limit=10):
        with self.microphone as source:
            st.info("Listening for your command...")
            audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        try:
            return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            st.warning("Could not understand audio.")
        except sr.RequestError as e:
            st.error(f"Could not request results; {e}")
        return ""

    def text_to_speech(self, text):
        """Convert text to speech (optional implementation)"""
        pass

# --- Ad Management Functions ---
def post_ad(user_id, title, description, category, price, location, contact_info, image_path=None, ad_type='regular'):
    """Post new advertisement"""
    conn = sqlite3.connect('farmdepot.db')
    c = conn.cursor()
    c.execute("""INSERT INTO ads (user_id, title, description, category, price, location, contact_info, image_path, ad_type)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (user_id, title, description, category, price, location, contact_info, image_path, ad_type))
    conn.commit()
    conn.close()

def search_ads(query="", category="", location=""):
    """Search advertisements"""
    conn = sqlite3.connect('farmdepot.db')
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
    ads = c.fetchall()
    conn.close()
    return ads

def get_ads_by_type(ad_type='regular', limit=10):
    """Get ads by type (promoted, top, regular)"""
    conn = sqlite3.connect('farmdepot.db')
    c = conn.cursor()
    c.execute("SELECT * FROM ads WHERE ad_type = ? AND status = 'active' ORDER BY created_at DESC LIMIT ?", (ad_type, limit))
    ads = c.fetchall()
    conn.close()
    return ads

# --- UI Components ---
def render_header():
    """Render application header"""
    st.markdown("""
    <div style='background: linear-gradient(90deg, #4CAF50, #8BC34A); padding: 1rem; border-radius: 10px; margin-bottom: 2rem;'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div style='display: flex; align-items: center;'>
                <h1 style='color: white; margin: 0; font-size: 2rem;'>🌾 FARMDEPOT_NG</h1>
            </div>
            <div style='color: white; font-size: 1.1rem;'>
                Nigeria's Premier Agricultural Marketplace
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("🏠 Home"):
            st.session_state.current_page = "Home"
            st.rerun()
    with col2:
        if st.button("ℹ️ About Us"):
            st.session_state.current_page = "About Us"
            st.rerun()
    with col3:
        if st.button("📋 Ads List"):
            st.session_state.current_page = "Ads List"
            st.rerun()
    with col4:
        if st.button("📝 Blog"):
            st.session_state.current_page = "Blog"
            st.rerun()
    with col5:
        if st.button("📞 Contact"):
            st.session_state.current_page = "Contact Us"
            st.rerun()
    with col6:
        if st.button("📤 Post Ad", type="primary"):
            st.session_state.current_page = "Post Ad"
            st.rerun()

def display_ads(ads, title=""):
    """Display advertisements in a grid layout"""
    if not ads:
        st.info("No ads found.")
        return

    if title:
        st.markdown(f"### {title}")

    # Display ads in rows of 3
    for i in range(0, len(ads), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(ads):
                ad = ads[i + j]
                with cols[j]:
                    price_formatted = f"₦{ad[5]:,.0f}" if ad[5] else "Price on request"
                    ad_type_color = {
                        'promoted': '#FF6B35',
                        'top': '#4ECDC4',
                        'regular': '#45B7D1'
                    }.get(ad[9], '#45B7D1')
                    ad_type_label = {
                        'promoted': '🏆 PROMOTED',
                        'top': '⭐ TOP AD',
                        'regular': '📋 REGULAR'
                    }.get(ad[9], '📋 REGULAR')
                    # Image or placeholder
                    if ad[8]:
                        st.image(ad[8], use_column_width=True)
                    else:
                        st.markdown('<div class="ad-image-placeholder"></div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style='
                        border: 2px solid {ad_type_color}; 
                        border-radius: 12px; 
                        padding: 1.2rem; 
                        margin: 0.8rem 0; 
                        background: linear-gradient(145deg, #ffffff, #f8f9fa);
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                        transition: transform 0.2s;
                        height: 180px;
                        position: relative;
                    '>
                        <div style='
                            background: {ad_type_color}; 
                            color: white; 
                            padding: 0.2rem 0.5rem; 
                            border-radius: 6px; 
                            font-size: 0.7rem; 
                            position: absolute; 
                            top: 0.5rem; 
                            right: 0.5rem;
                        '>
                            {ad_type_label}
                        </div>
                        <h4 style='color: #2E7D32; margin: 1.5rem 0 0.8rem 0; font-size: 1.1rem;'>{ad[2]}</h4>
                        <p style='color: #666; font-size: 0.9rem; margin-bottom: 0.8rem; line-height: 1.4;'>
                            {ad[3][:80]}{'...' if len(ad[3]) > 80 else ''}
                        </p>
                        <div style='margin-bottom: 0.6rem;'>
                            <span style='font-weight: bold; color: #1976D2; font-size: 1.1rem;'>{price_formatted}</span>
                        </div>
                        <p style='color: #666; font-size: 0.8rem; margin: 0.3rem 0;'>
                            <strong>📍</strong> {ad[6]}
                        </p>
                        <p style='color: #666; font-size: 0.8rem; margin: 0.3rem 0;'>
                            <strong>📞</strong> {ad[7]}
                        </p>
                        <p style='color: #999; font-size: 0.7rem; margin-top: 0.8rem;'>
                            {ad[11] if len(ad) > 11 else 'Recently posted'}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

def render_partners(partners):
    st.subheader("Our Partners")
    for partner in partners:
        st.markdown(
            f'<span class="partner-image-placeholder"></span> {partner}',
            unsafe_allow_html=True
        )

# --- Main Application ---
def main():
    st.title("FARMDEPOT.AI - Agricultural Marketplace")
    st.markdown("Welcome to the leading agricultural marketplace in Nigeria.")

    # Example: Display ads with image placeholders
    ads = get_ads_by_type(limit=6)
    display_ads(ads, title="Featured Ads")

    # Example: Partners section with image placeholders
    partners = ["AgroCorp", "Farmers United", "GreenTech"]
    render_partners(partners)

    # Voice Assistant (if available)
    if VOICE_AVAILABLE:
        va = VoiceAssistant()
        if st.button("🎤 Speak"):
            command = va.listen_for_speech()
            if command:
                st.success(f"You said: {command}")

if __name__ == "__main__":
    main()