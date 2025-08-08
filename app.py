import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime
import base64
from PIL import Image
import io
import json
import pandas as pd

# Try to import voice recognition dependencies
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="FARMDEPOT_NG - Agricultural Marketplace",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'user_logged_in' not in st.session_state:
    st.session_state.user_logged_in = False
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

# Database setup
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

# Utility functions
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def use_real_voice_recognition():
    """Check if real voice recognition is available"""
    return VOICE_AVAILABLE

class VoiceAssistant:
    """Voice Assistant for FARMDEPOT_NG"""
    
    def __init__(self):
        self.available = VOICE_AVAILABLE
        if self.available:
            self._initialize_components()
    
    def _initialize_components(self):
        """Initialize voice recognition and text-to-speech components"""
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Initialize text-to-speech
            self.tts_engine = pyttsx3.init()
            
            # Configure TTS settings
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Try to set a female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            self.tts_engine.setProperty('rate', 150)  # Speech rate
            self.tts_engine.setProperty('volume', 0.8)  # Volume level
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
        except Exception as e:
            st.error(f"Error initializing voice components: {str(e)}")
            self.available = False
    
    def listen_for_speech(self, timeout=5, phrase_time_limit=10):
        """Listen for speech input and convert to text"""
        if not self.available:
            return "Voice recognition not available. Please install: pip install speechrecognition pyaudio pyttsx3"
        
        try:
            with self.microphone as source:
                st.info("🎤 Listening... Please speak now!")
                
                # Listen for audio input
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
                
                st.info("🔄 Processing your speech...")
                
                # Recognize speech using Google Speech Recognition
                text = self.recognizer.recognize_google(audio)
                return text.lower()
                
        except sr.WaitTimeoutError:
            return "Timeout: No speech detected. Please try again."
        except sr.UnknownValueError:
            return "Could not understand audio. Please speak clearly and try again."
        except sr.RequestError as e:
            return f"Error with speech recognition service: {str(e)}"
        except Exception as e:
            return f"An error occurred: {str(e)}"
    
    def text_to_speech(self, text):
        """Convert text to speech"""
        if not self.available:
            return False
        
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            return True
        except Exception as e:
            st.error(f"Error with text-to-speech: {str(e)}")
            return False

# Voice Assistant Placeholder (simplified)
def simulate_voice_recognition():
    """Simulate voice recognition for demo purposes"""
    sample_commands = [
        "Search for rice in Lagos",
        "I want to sell tomatoes",
        "Find yam in Kano",
        "Show me plantain",
        "Search for maize"
    ]
    return st.selectbox("🎤 Voice Commands (Demo)", sample_commands)

def parse_voice_ad_input(voice_text):
    """Parse voice input to extract advertisement details"""
    import re
    
    voice_lower = voice_text.lower()
    parsed_data = {}
    
    # Extract product name/title
    products = {
        'tomato': ('Fresh Tomatoes - Premium Quality', 'Vegetables'),
        'rice': ('Yellow Rice - Premium Quality', 'Grains'),
        'yam': ('Fresh Yam Tubers', 'Tubers'),
        'plantain': ('Plantain Bunches', 'Vegetables'),
        'maize': ('Fresh Maize', 'Cereals'),
        'cassava': ('Cassava Tubers', 'Tubers'),
        'beans': ('Quality Beans', 'Grains'),
        'pepper': ('Fresh Pepper', 'Vegetables'),
        'onion': ('Fresh Onions', 'Vegetables'),
        'cocoa': ('Cocoa Beans', 'Cash Crops')
    }
    
    # Find product in voice text
    for product, (title, category) in products.items():
        if product in voice_lower:
            parsed_data['title'] = title
            parsed_data['category'] = category
            break
    
    # Extract price using regex
    price_patterns = [
        r'(\d+(?:,\d+)*)\s*naira',
        r'₦\s*(\d+(?:,\d+)*)',
        r'(\d+(?:,\d+)*)\s*ngn',
        r'for\s+(\d+(?:,\d+)*)',
        r'at\s+(\d+(?:,\d+)*)'
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, voice_lower)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                parsed_data['price'] = float(price_str)
                break
            except:
                continue
    
    # Extract location
    nigerian_states = [
        'lagos', 'kano', 'ogun', 'ibadan', 'abuja', 'kaduna', 'port harcourt',
        'benin', 'jos', 'maiduguri', 'zaria', 'aba', 'ilorin', 'onitsha',
        'warri', 'okene', 'calabar', 'uyo', 'makurdi', 'bauchi', 'gombe',
        'yola', 'minna', 'sokoto', 'katsina', 'kebbi', 'birnin kebbi',
        'dutse', 'damaturu', 'gusau', 'jalingo', 'lafia', 'lokoja',
        'abakaliki', 'umuahia', 'owerri', 'abeokuta', 'akure', 'ado ekiti',
        'ilorin', 'osogbo', 'ibadan', 'enugu', 'awka', 'asaba', 'yenagoa'
    ]
    
    for state in nigerian_states:
        if state in voice_lower:
            parsed_data['location'] = state.title()
            break
    
    # Generate description based on extracted info
    if 'title' in parsed_data:
        product_name = parsed_data['title'].split(' - ')[0]
        location = parsed_data.get('location', 'Nigeria')
        parsed_data['description'] = f"Quality {product_name.lower()} available from {location}. Fresh and ready for market."
    
    # Set default values if not found
    if 'title' not in parsed_data:
        parsed_data['title'] = "Agricultural Product"
        parsed_data['category'] = "Vegetables"
    
    if 'price' not in parsed_data:
        parsed_data['price'] = 1000.0
    
    if 'location' not in parsed_data:
        parsed_data['location'] = "Nigeria"
    
    return parsed_data

def process_voice_command(voice_text):
    """Process voice command using basic NLP"""
    voice_lower = voice_text.lower()
    
    # Search commands
    if any(word in voice_lower for word in ['search', 'find', 'look for', 'show me']):
        categories = ['rice', 'yam', 'cassava', 'maize', 'tomato', 'pepper', 'beans', 'plantain']
        found_category = None
        for cat in categories:
            if cat in voice_lower:
                found_category = cat
                break
        
        return {
            'intent': 'search',
            'category': found_category,
            'query': voice_text
        }
    
    # Post ad commands
    elif any(word in voice_lower for word in ['sell', 'post', 'advertise', 'upload']):
        return {
            'intent': 'post_ad',
            'query': voice_text
        }
    
    return {
        'intent': 'unknown',
        'query': voice_text
    }

# Translation placeholder (simplified)
def translate_text(text, target_lang='en'):
    """Simple translation placeholder"""
    translations = {
        'hausa': {
            'Search': 'Bincika',
            'Post Ad': 'Yi Talla',
            'Login': 'Shiga',
            'Register': 'Yi Rajista'
        },
        'yoruba': {
            'Search': 'Wa',
            'Post Ad': 'Fi Ipolowo',
            'Login': 'Wole',
            'Register': 'Forukọsilẹ'
        },
        'igbo': {
            'Search': 'Chọọ',
            'Post Ad': 'Tinye Mgbasa Ozi',
            'Login': 'Banye',
            'Register': 'Debanye Aha'
        }
    }
    
    if target_lang.lower() in translations and text in translations[target_lang.lower()]:
        return translations[target_lang.lower()][text]
    return text

# Authentication functions
def authenticate_user(username, password):
    """Authenticate user login"""
    conn = sqlite3.connect('farmdepot.db')
    c = conn.cursor()
    
    hashed_password = hash_password(password)
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
              (username, hashed_password))
    user = c.fetchone()
    conn.close()
    
    return user

def register_user(username, email, password, user_type, phone="", location=""):
    """Register new user"""
    conn = sqlite3.connect('farmdepot.db')
    c = conn.cursor()
    
    try:
        hashed_password = hash_password(password)
        c.execute("""INSERT INTO users (username, email, password, user_type, phone, location)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (username, email, hashed_password, user_type, phone, location))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

# Ad management functions
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
    
    c.execute("SELECT * FROM ads WHERE ad_type = ? AND status = 'active' ORDER BY created_at DESC LIMIT ?",
              (ad_type, limit))
    ads = c.fetchall()
    conn.close()
    
    return ads

# UI Components
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

def render_hero_section():
    """Render hero section with search"""
    st.markdown("""
    <div style='text-align: center; padding: 3rem; background: linear-gradient(135deg, #2E7D32, #4CAF50); border-radius: 15px; margin: 2rem 0; color: white;'>
        <h1 style='font-size: 3rem; margin-bottom: 1rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>
            Buy, Sell, & Rent Anything Agriculture In One Click
        </h1>
        <p style='font-size: 1.4rem; margin-bottom: 2rem; opacity: 0.9;'>
            Search through over 1000+ Active Ads from any Location In Nigeria
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Search section
    st.markdown("### 🔍 Search Agricultural Products")
    
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    
    with col1:
        search_query = st.text_input("Search Products", placeholder="🔍 Search products... (e.g., Rice, Yam, Tomatoes)", key="hero_search", label_visibility="collapsed")
    
    with col2:
        categories = ["All Categories", "Tubers", "Grains", "Cereals", "Cash Crops", 
                     "Seedlings", "Fertilizers", "Processed Foods", "Vegetables", "Livestock"]
        category = st.selectbox("Category", categories, key="hero_category")
    
    with col3:
        location = st.text_input("Location Filter", placeholder="📍 Location (e.g., Lagos, Kano)", key="hero_location", label_visibility="collapsed")
    
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔍 Search", use_container_width=True):
            if search_query or category != "All Categories" or location:
                ads = search_ads(search_query, category, location)
                st.session_state['search_results'] = ads
                st.session_state['search_performed'] = True
            else:
                st.warning("Please enter search criteria")
    
    # Voice search section
    st.markdown("### 🎤 Voice Search")
    
    # Initialize voice assistant
    voice_assistant = VoiceAssistant()
    
    if voice_assistant.available:
        st.success("✅ Voice recognition is available!")
        st.info("📝 **Instructions:** Say something like 'Search for rice in Lagos' or 'Find yam in Kano'")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("**Sample voice commands:**")
            st.markdown("""
            - "Search for rice in Lagos"
            - "Find yam in Kano" 
            - "Show me tomatoes"
            - "Look for plantain"
            - "Search for maize"
            """)
        
        with col2:
            if st.button("🎤 Start Voice Search", key="real_voice_btn", use_container_width=True):
                with st.spinner("🎤 Listening for your search query..."):
                    voice_text = voice_assistant.listen_for_speech()
                
                if voice_text and not any(word in voice_text.lower() for word in ['error', 'timeout', 'could not']):
                    st.success(f"✅ Voice input received: '{voice_text}'")
                    
                    # Process the voice command
                    command = process_voice_command(voice_text)
                    
                    if command and command['intent'] == 'search':
                        query = command.get('category', voice_text)
                        ads = search_ads(query)
                        st.session_state['search_results'] = ads
                        st.session_state['search_performed'] = True
                        
                        # Provide voice feedback
                        if ads:
                            feedback = f"Found {len(ads)} products matching your search."
                            voice_assistant.text_to_speech(feedback)
                            st.success(feedback)
                        else:
                            feedback = "No products found. Try a different search term."
                            voice_assistant.text_to_speech(feedback)
                            st.info(feedback)
                    else:
                        st.warning("Could not understand the search command. Please try again.")
                else:
                    st.error(f"❌ {voice_text}")
    else:
        # Fallback to demo mode
        st.warning("⚠️ Voice recognition not available. Using demo mode.")
        st.info("Install required packages: `pip install speechrecognition pyaudio pyttsx3`")
        
        voice_command = simulate_voice_recognition()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"Selected demo command: {voice_command}")
        with col2:
            if st.button("🎤 Process Demo Command", key="demo_voice_btn"):
                command = process_voice_command(voice_command)
                if command['intent'] == 'search':
                    query = command.get('category', '')
                    ads = search_ads(query)
                    st.session_state['search_results'] = ads
                    st.session_state['search_performed'] = True
                    st.success(f"Demo voice search for: {query}")
    
    # Display search results if any
    if st.session_state.get('search_performed', False):
        ads = st.session_state.get('search_results', [])
        if ads:
            st.markdown("### 🎯 Search Results")
            display_ads(ads[:6])  # Show first 6 results
        else:
            st.info("No ads found matching your search criteria.")

def render_categories_section():
    """Render agricultural categories section"""
    st.markdown("### 🌾 Browse by Agricultural Categories")
    
    categories = [
        {"name": "Tubers", "icon": "🥔", "desc": "Yam, Cassava, Sweet Potato", "color": "#FF6B6B"},
        {"name": "Grains", "icon": "🌾", "desc": "Rice, Wheat, Millet", "color": "#4ECDC4"},
        {"name": "Cereals", "icon": "🌽", "desc": "Maize, Sorghum, Oats", "color": "#45B7D1"},
        {"name": "Cash Crops", "icon": "🌿", "desc": "Cocoa, Coffee, Cotton", "color": "#96CEB4"},
        {"name": "Seedlings", "icon": "🌱", "desc": "Seeds, Plantlets", "color": "#FFEAA7"},
        {"name": "Fertilizers", "icon": "🧪", "desc": "Organic, Chemical", "color": "#DDA0DD"},
        {"name": "Vegetables", "icon": "🥬", "desc": "Tomato, Pepper, Onions", "color": "#98D8C8"},
        {"name": "Livestock", "icon": "🐄", "desc": "Cattle, Goats, Poultry", "color": "#F7DC6F"}
    ]
    
    cols = st.columns(4)
    for i, cat in enumerate(categories):
        with cols[i % 4]:
            if st.button(
                f"{cat['icon']} **{cat['name']}**\n{cat['desc']}", 
                key=f"cat_{i}",
                use_container_width=True
            ):
                ads = search_ads(category=cat['name'])
                st.session_state['search_results'] = ads
                st.session_state['search_performed'] = True
                st.session_state['current_category'] = cat['name']
                st.success(f"Showing {cat['name']} products")
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
                    # Ad card with better styling
                    price_formatted = f"₦{ad[5]:,.0f}" if ad[5] else "Price on request"
                    
                    # Determine ad type styling
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
                    
                    st.markdown(f"""
                    <div style='
                        border: 2px solid {ad_type_color}; 
                        border-radius: 12px; 
                        padding: 1.2rem; 
                        margin: 0.8rem 0; 
                        background: linear-gradient(145deg, #ffffff, #f8f9fa);
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                        transition: transform 0.2s;
                        height: 280px;
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

def render_sidebar():
    """Render sidebar with authentication"""
    st.sidebar.markdown("## 🌾 FARMDEPOT_NG")
    st.sidebar.markdown("*Nigeria's Agricultural Marketplace*")
    
    if not st.session_state.user_logged_in:
        # Login/Register form
        auth_tab = st.sidebar.radio("Choose Action", ["Login", "Register"])
        
        if auth_tab == "Login":
            with st.sidebar.form("login_form"):
                st.markdown("### 🔐 Login")
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("🚪 Login", use_container_width=True):
                    if username and password:
                        user = authenticate_user(username, password)
                        if user:
                            st.session_state.user_logged_in = True
                            st.session_state.user_info = user
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials!")
                    else:
                        st.error("Please fill in all fields")
        
        else:  # Register
            with st.sidebar.form("register_form"):
                st.markdown("### 📝 Register")
                username = st.text_input("Username")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                user_type = st.selectbox("User Type", ["Farmer", "Trader", "Buyer", "Processor"])
                phone = st.text_input("Phone Number")
                location = st.text_input("Location")
                
                if st.form_submit_button("📝 Register", use_container_width=True):
                    if username and email and password:
                        if register_user(username, email, password, user_type, phone, location):
                            st.success("✅ Registration successful! Please login.")
                        else:
                            st.error("❌ Username or email already exists!")
                    else:
                        st.error("Please fill in required fields")
    
    else:
        # User is logged in
        user_info = st.session_state.user_info
        st.sidebar.success(f"Welcome, **{user_info[1]}**!")
        st.sidebar.info(f"**Type:** {user_info[4]}")
        
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            st.session_state.user_logged_in = False
            st.session_state.user_info = None
            st.success("Logged out successfully!")
            st.rerun()
        
        # Quick actions
        st.sidebar.markdown("### ⚡ Quick Actions")
        if st.sidebar.button("📝 Post New Ad", use_container_width=True):
            st.session_state.current_page = "Post Ad"
            st.rerun()
        
        if st.sidebar.button("🔍 View All Ads", use_container_width=True):
            st.session_state.current_page = "Ads List"
            st.rerun()
    
    # Language selection
    st.sidebar.markdown("### 🌍 Language / Harshe / Ede / Asụsụ")
    language = st.sidebar.selectbox(
        "Select Language",
        ["English", "Hausa", "Yoruba", "Igbo"],
        key="language_selector"
    )
    
    # Quick stats
    st.sidebar.markdown("### 📊 Quick Stats")
    conn = sqlite3.connect('farmdepot.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM ads WHERE status = 'active'")
    total_ads = c.fetchone()[0]
    conn.close()
    
    st.sidebar.metric("Active Ads", total_ads)
    st.sidebar.metric("Categories", "8")
    st.sidebar.metric("States Covered", "36")

# Page components
def home_page():
    """Render home page"""
    render_hero_section()
    
    st.markdown("---")
    render_categories_section()
    
    st.markdown("---")
    
    # Featured ads sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏆 Promoted Ads")
        promoted_ads = get_ads_by_type('promoted', 3)
        if promoted_ads:
            display_ads(promoted_ads)
        else:
            st.info("No promoted ads available")
    
    with col2:
        st.markdown("### ⭐ Top Ads")
        top_ads = get_ads_by_type('top', 3)
        if top_ads:
            display_ads(top_ads)
        else:
            st.info("No top ads available")
    
    # Regular ads
    st.markdown("### 📋 Recent Ads")
    regular_ads = get_ads_by_type('regular', 6)
    if regular_ads:
        display_ads(regular_ads)
    else:
        st.info("No recent ads available")
    
    # Partners section
    st.markdown("---")
    st.markdown("### 🤝 Our Trusted Partners")
    partner_cols = st.columns(4)
    partners = [
        {"name": "Nigerian Agricultural Bank", "desc": "Financial Services"},
        {"name": "FarmTech Solutions", "desc": "Technology Partner"},
        {"name": "Green Harvest Co.", "desc": "Supply Chain"},
        {"name": "AgroLoan Services", "desc": "Micro-financing"}
    ]
    
    for i, partner in enumerate(partners):
        with partner_cols[i]:
            st.markdown(f"""
            <div style='
                text-align: center; 
                padding: 1.5rem; 
                border: 2px solid #4CAF50; 
                border-radius: 10px; 
                margin: 0.5rem 0;
                background: linear-gradient(145deg, #ffffff, #f8f9fa);
            '>
                <h4 style='color: #2E7D32; margin-bottom: 0.5rem;'>{partner['name']}</h4>
                <p style='color: #666; font-size: 0.9rem;'>{partner['desc']}</p>
            </div>
            """, unsafe_allow_html=True)

def post_ad_page():
    """Render post advertisement page"""
    if not st.session_state.user_logged_in:
        st.warning("⚠️ Please login to post an advertisement.")
        st.info("Use the sidebar to login or register as a new user.")
        return
    
    st.markdown("## 📝 Post New Advertisement")
    st.markdown("*Create your agricultural product listing*")
    
    # Voice posting option
    with st.expander("🎤 Voice Posting", expanded=False):
        st.markdown("#### 🎙️ Post Advertisement Using Voice")
        
        voice_assistant = VoiceAssistant()
        
        if voice_assistant.available:
            st.success("✅ Voice recognition is available!")
            st.info("📝 **Instructions:** Say something like 'I want to sell fresh tomatoes from Lagos for 5000 naira per basket'")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**Sample voice commands:**")
                st.markdown("""
                - "I want to sell rice from Kano for 25000 naira"
                - "Selling fresh yam from Ogun state at 15000 naira"
                - "I have plantain for sale from Ibadan at 8000 naira"
                """)
            
            with col2:
                if st.button("🎤 Start Voice Input", key="voice_post_btn", use_container_width=True):
                    with st.spinner("🎤 Listening for your advertisement..."):
                        voice_text = voice_assistant.listen_for_speech()
                    
                    if voice_text and not any(word in voice_text.lower() for word in ['error', 'timeout', 'not available']):
                        st.success(f"✅ Voice input received: '{voice_text}'")
                        
                        # Parse the voice input to extract product details
                        parsed_data = parse_voice_ad_input(voice_text)
                        
                        # Auto-fill form fields
                        for key, value in parsed_data.items():
                            st.session_state[f'voice_{key}'] = value
                        
                        # Provide text-to-speech feedback
                        feedback = f"I understood you want to sell {parsed_data.get('title', 'a product')}. Please review the auto-filled form below."
                        voice_assistant.text_to_speech(feedback)
                        
                        st.info("📝 Form has been auto-filled based on your voice input. Please review and submit.")
        else:
            # Fallback to demo mode
            st.warning("⚠️ Voice recognition not available. Using demo mode.")
            st.info("Install required packages: `pip install speechrecognition pyaudio pyttsx3`")
            
            voice_commands = [
                "I want to sell fresh tomatoes from Lagos for 5000 naira per basket",
                "Selling yellow rice 50kg bags from Kano for 25000 naira",
                "Fresh yam tubers available from Ogun state at 15000 naira",
                "Plantain bunches for sale from Ibadan at 8000 naira per bunch"
            ]
            
            selected_voice = st.selectbox("Select Demo Voice Command", voice_commands)
            
            if st.button("🎤 Process Demo Voice Command", key="demo_post_btn"):
                # Parse demo command and auto-fill form
                parsed_data = parse_voice_ad_input(selected_voice)
                for key, value in parsed_data.items():
                    st.session_state[f'voice_{key}'] = value
                st.success("✅ Demo voice command processed! Form auto-filled below.")
    
    # Manual form
    st.markdown("### ✍️ Product Details")
    
    with st.form("post_ad_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input(
                "Product Title *", 
                value=st.session_state.get('voice_title', ''),
                placeholder="e.g., Fresh Tomatoes - Premium Quality"
            )
            
            categories_list = ["Tubers", "Grains", "Cereals", "Cash Crops", 
                              "Seedlings", "Fertilizers", "Processed Foods", 
                              "Vegetables", "Livestock", "Equipment"]
            
            default_index = 0
            if st.session_state.get('voice_category') in categories_list:
                default_index = categories_list.index(st.session_state.get('voice_category'))
            
            category = st.selectbox("Category *", categories_list, index=default_index)
            
            price = st.number_input(
                "Price (₦) *", 
                min_value=0.0, 
                step=100.0,
                value=float(st.session_state.get('voice_price', 0.0))
            )
            
            location = st.text_input(
                "Location *", 
                value=st.session_state.get('voice_location', ''),
                placeholder="e.g., Lagos, Kano, Ogun State"
            )
        
        with col2:
            description = st.text_area(
                "Description", 
                placeholder="Describe your product in detail...",
                height=100,
                value=st.session_state.get('voice_description', '')
            )
            
            contact_info = st.text_input(
                "Contact Information *", 
                placeholder="Phone number, email, or WhatsApp"
            )
            
            ad_type = st.selectbox(
                "Advertisement Type", 
                ["regular", "top", "promoted"],
                format_func=lambda x: {
                    "regular": "📋 Regular (Free)",
                    "top": "⭐ Top Ad (+₦5,000)",
                    "promoted": "🏆 Promoted (+₦10,000)"
                }[x]
            )
            
            # Image upload
            uploaded_file = st.file_uploader(
                "Upload Product Image", 
                type=['png', 'jpg', 'jpeg'],
                help="Upload a clear image of your product"
            )
        
        # Language selection for ad
        st.markdown("### 🌍 Language Settings")
        language = st.selectbox(
            "Post ad in language", 
            ["English", "Hausa", "Yoruba", "Igbo"],
            help="Your ad will be translated to the selected language"
        )
        
        # Terms and conditions
        terms_accepted = st.checkbox("I agree to the Terms and Conditions and Privacy Policy *")
        
        # Submit button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submit_button = st.form_submit_button("📤 Post Advertisement", use_container_width=True)
        
        if submit_button:
            if not terms_accepted:
                st.error("❌ Please accept the Terms and Conditions to proceed.")
            elif not all([title, category, price, location, contact_info]):
                st.error("❌ Please fill in all required fields marked with *")
            else:
                # Save uploaded image
                image_path = None
                if uploaded_file:
                    if not os.path.exists("uploads"):
                        os.makedirs("uploads")
                    
                    # Generate unique filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    file_extension = uploaded_file.name.split('.')[-1]
                    image_path = f"uploads/{timestamp}_{uploaded_file.name}"
                    
                    with open(image_path, "wb") as f:
                        f.write(uploaded_file.read())
                
                # Translate content if needed
                translated_title = title
                translated_description = description
                
                if language != "English":
                    translated_title = translate_text(title, language.lower())
                    translated_description = translate_text(description, language.lower())
                
                # Post the ad
                try:
                    post_ad(
                        st.session_state.user_info[0], 
                        translated_title, 
                        translated_description, 
                        category,
                        price, 
                        location, 
                        contact_info, 
                        image_path, 
                        ad_type
                    )
                    
                    st.success("✅ Advertisement posted successfully!")
                    st.balloons()
                    
                    # Clear voice session data
                    for key in ['voice_title', 'voice_category', 'voice_price', 'voice_location', 'voice_description']:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    st.info("Your ad is now live and visible to potential buyers!")
                    
                except Exception as e:
                    st.error(f"❌ Error posting advertisement: {str(e)}")

def ads_list_page():
    """Render ads listing page"""
    st.markdown("## 🛍️ All Advertisements")
    st.markdown("*Browse all available agricultural products*")
    
    # Filters section
    st.markdown("### 🔧 Filter & Sort")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        filter_category = st.selectbox(
            "Filter by Category", 
            ["All Categories", "Tubers", "Grains", "Cereals", 
             "Cash Crops", "Seedlings", "Fertilizers", 
             "Processed Foods", "Vegetables", "Livestock", "Equipment"]
        )
    
    with col2:
        filter_location = st.text_input("Filter by Location", placeholder="e.g., Lagos")
    
    with col3:
        filter_price_range = st.selectbox(
            "Price Range",
            ["All Prices", "Under ₦10,000", "₦10,000 - ₦50,000", 
             "₦50,000 - ₦100,000", "Above ₦100,000"]
        )
    
    with col4:
        sort_by = st.selectbox(
            "Sort by", 
            ["Newest First", "Oldest First", "Price: Low to High", 
             "Price: High to Low", "Location A-Z"]
        )
    
    # Apply filters button
    if st.button("🔍 Apply Filters", use_container_width=True):
        st.session_state['filters_applied'] = True
    
    # Get and display ads
    ads = search_ads(category=filter_category, location=filter_location)
    
    # Apply price filter
    if filter_price_range != "All Prices":
        if filter_price_range == "Under ₦10,000":
            ads = [ad for ad in ads if ad[5] < 10000]
        elif filter_price_range == "₦10,000 - ₦50,000":
            ads = [ad for ad in ads if 10000 <= ad[5] <= 50000]
        elif filter_price_range == "₦50,000 - ₦100,000":
            ads = [ad for ad in ads if 50000 <= ad[5] <= 100000]
        elif filter_price_range == "Above ₦100,000":
            ads = [ad for ad in ads if ad[5] > 100000]
    
    # Sort ads based on selection
    if sort_by == "Oldest First":
        ads = sorted(ads, key=lambda x: x[11] if len(x) > 11 else "")
    elif sort_by == "Price: Low to High":
        ads = sorted(ads, key=lambda x: x[5])
    elif sort_by == "Price: High to Low":
        ads = sorted(ads, key=lambda x: x[5], reverse=True)
    elif sort_by == "Location A-Z":
        ads = sorted(ads, key=lambda x: x[6])
    # Default is "Newest First" - already ordered by created_at DESC
    
    # Display results summary
    st.markdown(f"### 📊 Results Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Ads Found", len(ads))
    
    with col2:
        avg_price = sum(ad[5] for ad in ads if ad[5]) / len(ads) if ads else 0
        st.metric("Average Price", f"₦{avg_price:,.0f}")
    
    with col3:
        unique_locations = len(set(ad[6] for ad in ads))
        st.metric("Locations", unique_locations)
    
    # Display ads
    if ads:
        display_ads(ads, f"All Advertisements ({len(ads)} found)")
    else:
        st.info("🔍 No advertisements found matching your criteria. Try adjusting your filters.")

def about_page():
    """Render about us page"""
    st.markdown("## 🌾 About FARMDEPOT_NG")
    
    # Hero section for about page
    st.markdown("""
    <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #4CAF50, #8BC34A); border-radius: 10px; margin: 1rem 0; color: white;'>
        <h2 style='margin-bottom: 1rem;'>Empowering Nigerian Agriculture Through Technology</h2>
        <p style='font-size: 1.2rem; opacity: 0.9;'>Connecting farmers, traders, and consumers across Nigeria</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 Our Mission
        
        FARMDEPOT_NG is Nigeria's premier AI-powered agricultural marketplace, designed to revolutionize 
        how agricultural products are bought and sold across the nation. We leverage cutting-edge 
        technology to make agricultural commerce accessible to everyone, regardless of their 
        technical expertise or educational background.
        
        Our platform bridges the gap between rural farmers and urban markets, ensuring that 
        fresh, quality agricultural products reach consumers while providing farmers with 
        better market access and fair prices.
        
        ### 🌟 Our Vision
        
        To become the leading digital agricultural marketplace in West Africa, fostering 
        sustainable agricultural practices and economic growth for all stakeholders in 
        the agricultural value chain.
        """)
    
    with col2:
        st.markdown("""
        ### ✨ Key Features
        
        - **🎤 Voice-Powered Interface**: Post and search ads using voice commands in local languages
        - **🌍 Multilingual Support**: Available in English, Hausa, Yoruba, and Igbo
        - **🤖 AI Integration**: Smart command interpretation and product categorization
        - **📱 User-Friendly Design**: Simple interface designed for all user levels
        - **🔐 Secure Platform**: Safe and secure trading environment
        - **📊 Real-time Analytics**: Market insights and pricing trends
        - **🚚 Logistics Support**: Connect with delivery partners
        - **💰 Payment Integration**: Secure payment processing
        """)
    
    st.markdown("---")
    
    # Who we serve section
    st.markdown("### 👥 Who We Serve")
    
    cols = st.columns(4)
    
    services = [
        {
            "title": "🌾 Farmers",
            "desc": "Sell your produce directly to buyers, access market prices, and expand your reach beyond local markets.",
            "benefits": ["Direct market access", "Better prices", "Reduced middlemen"]
        },
        {
            "title": "🏪 Traders",
            "desc": "Find quality agricultural products, connect with reliable suppliers, and expand your business network.",
            "benefits": ["Quality sourcing", "Network expansion", "Bulk purchasing"]
        },
        {
            "title": "🏭 Processors",
            "desc": "Source raw materials for your operations, ensure consistent supply chains, and reduce procurement costs.",
            "benefits": ["Consistent supply", "Cost reduction", "Quality assurance"]
        },
        {
            "title": "🛒 Consumers",
            "desc": "Access fresh, quality agricultural products directly from farmers and verified sellers.",
            "benefits": ["Fresh products", "Competitive prices", "Quality guarantee"]
        }
    ]
    
    for i, service in enumerate(services):
        with cols[i]:
            st.markdown(f"""
            <div style='
                padding: 1.5rem; 
                border: 2px solid #4CAF50; 
                border-radius: 10px; 
                text-align: center;
                height: 300px;
                background: linear-gradient(145deg, #ffffff, #f8f9fa);
            '>
                <h3 style='color: #2E7D32; margin-bottom: 1rem;'>{service['title']}</h3>
                <p style='color: #666; margin-bottom: 1rem; font-size: 0.9rem;'>{service['desc']}</p>
                <div style='text-align: left;'>
                    <strong style='color: #4CAF50;'>Benefits:</strong>
                    <ul style='color: #666; font-size: 0.8rem; margin-top: 0.5rem;'>
                        {''.join(f"<li>{benefit}</li>" for benefit in service['benefits'])}
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Statistics section
    st.markdown("### 📈 Our Impact")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Get real statistics from database
    conn = sqlite3.connect('farmdepot.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM ads WHERE status = 'active'")
    total_ads = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    conn.close()
    
    with col1:
        st.metric("Active Advertisements", total_ads, "Live listings")
    
    with col2:
        st.metric("Registered Users", total_users, "Growing community")
    
    with col3:
        st.metric("States Covered", "36", "Nationwide reach")
    
    with col4:
        st.metric("Product Categories", "10+", "Diverse offerings")
    
    st.markdown("---")
    
    # Contact information
    st.markdown("### 📞 Get in Touch")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📧 Email:**  
        - General: info@farmdepot.ng  
        - Support: support@farmdepot.ng  
        - Business: business@farmdepot.ng
        
        **📞 Phone:**  
        - Main: +234-XXX-XXX-XXXX  
        - Support: +234-XXX-XXX-XXXY  
        - WhatsApp: +234-XXX-XXX-XXXZ
        """)
    
    with col2:
        st.markdown("""
        **📍 Address:**  
        FARMDEPOT_NG Headquarters  
        Plot 123, Agricultural Innovation Hub  
        Victoria Island, Lagos  
        Nigeria
        
        **🕒 Business Hours:**  
        - Monday - Friday: 8:00 AM - 6:00 PM  
        - Saturday: 9:00 AM - 4:00 PM  
        - Sunday: Emergency support only
        """)

def blog_page():
    """Render blog page"""
    st.markdown("## 📝 Agricultural Blog & News")
    st.markdown("*Stay updated with the latest in Nigerian agriculture*")
    
    # Blog categories
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🌾 Farming Tips", use_container_width=True):
            st.session_state['blog_filter'] = 'farming'
    
    with col2:
        if st.button("📈 Market Trends", use_container_width=True):
            st.session_state['blog_filter'] = 'market'
    
    with col3:
        if st.button("🔬 Technology", use_container_width=True):
            st.session_state['blog_filter'] = 'technology'
    
    with col4:
        if st.button("📰 News", use_container_width=True):
            st.session_state['blog_filter'] = 'news'
    
    st.markdown("---")
    
    # Sample blog posts with more content
    blog_posts = [
        {
            "title": "Maximizing Yield: Modern Farming Techniques for Nigerian Farmers",
            "content": """Discover the latest agricultural techniques that can help increase your farm productivity and profitability. From precision agriculture to sustainable farming practices, learn how technology is transforming Nigerian agriculture.
            
            Key points covered:
            • Smart irrigation systems
            • Soil health management
            • Crop rotation strategies
            • Pest management techniques
            • Market timing for maximum profits""",
            "author": "Dr. Adebayo Ogun",
            "date": "January 15, 2024",
            "category": "farming",
            "read_time": "5 min read",
            "tags": ["Productivity", "Technology", "Sustainable Farming"]
        },
        {
            "title": "Market Trends: What's Hot in Nigerian Agriculture for 2024",
            "content": """An in-depth analysis of current market trends and emerging opportunities in the Nigerian agricultural sector. Understanding market dynamics is crucial for both farmers and traders to make informed decisions.
            
            Trending products:
            • High-value crops gaining popularity
            • Export opportunities
            • Value-added products
            • Regional price variations
            • Seasonal demand patterns""",
            "author": "Sarah Mohammed",
            "date": "January 10, 2024",
            "category": "market",
            "read_time": "7 min read",
            "tags": ["Market Analysis", "Trends", "Economics"]
        },
        {
            "title": "Sustainable Farming: Protecting Our Future",
            "content": """Learn about sustainable farming methods that protect the environment while maintaining profitability. Sustainable agriculture is not just good for the planet—it's good for business too.
            
            Sustainable practices include:
            • Organic farming methods
            • Water conservation techniques
            • Biodiversity preservation
            • Carbon footprint reduction
            • Community-supported agriculture""",
            "author": "Prof. Chukwu Okafor",
            "date": "January 5, 2024",
            "category": "farming",
            "read_time": "6 min read",
            "tags": ["Sustainability", "Environment", "Organic"]
        },
        {
            "title": "Digital Agriculture: How AI is Revolutionizing Farming",
            "content": """Explore how artificial intelligence and digital technologies are transforming Nigerian agriculture. From drone monitoring to predictive analytics, the digital revolution is here.
            
            AI applications in agriculture:
            • Crop monitoring with drones
            • Weather prediction models
            • Disease detection systems
            • Market price predictions
            • Automated farming equipment""",
            "author": "Eng. Fatima Aliyu",
            "date": "December 28, 2023",
            "category": "technology",
            "read_time": "8 min read",
            "tags": ["AI", "Technology", "Innovation"]
        },
        {
            "title": "Government Policies Supporting Agricultural Growth",
            "content": """Latest updates on government initiatives and policies aimed at boosting agricultural productivity and supporting farmers across Nigeria.
            
            Recent policy developments:
            • Agricultural loans and grants
            • Subsidy programs
            • Infrastructure development
            • Market access initiatives
            • Training and capacity building""",
            "author": "Policy Research Team",
            "date": "December 20, 2023",
            "category": "news",
            "read_time": "4 min read",
            "tags": ["Policy", "Government", "Support"]
        }
    ]
    
    # Filter posts based on selection
    current_filter = st.session_state.get('blog_filter', 'all')
    if current_filter != 'all':
        filtered_posts = [post for post in blog_posts if post['category'] == current_filter]
    else:
        filtered_posts = blog_posts
    
    # Display blog posts
    for post in filtered_posts:
        with st.container():
            st.markdown(f"""
            <div style='
                border: 1px solid #ddd; 
                border-radius: 12px; 
                padding: 2rem; 
                margin: 1.5rem 0;
                background: linear-gradient(145deg, #ffffff, #f8f9fa);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            '>
                <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;'>
                    <h3 style='color: #2E7D32; margin: 0; font-size: 1.4rem;'>{post['title']}</h3>
                    <span style='
                        background: #4CAF50; 
                        color: white; 
                        padding: 0.3rem 0.8rem; 
                        border-radius: 20px; 
                        font-size: 0.8rem;
                    '>{post['read_time']}</span>
                </div>
                
                <div style='color: #666; line-height: 1.6; margin-bottom: 1.5rem; font-size: 0.95rem;'>
                    {post['content']}
                </div>
                
                <div style='display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem;'>
                    {''.join(f"<span style='background: #E8F5E8; color: #2E7D32; padding: 0.2rem 0.6rem; border-radius: 15px; font-size: 0.8rem;'>#{tag}</span>" for tag in post['tags'])}
                </div>
                
                <div style='display: flex; justify-content: space-between; align-items: center; color: #999; font-size: 0.9rem; border-top: 1px solid #eee; padding-top: 1rem;'>
                    <span><strong>By:</strong> {post['author']}</span>
                    <span><strong>Published:</strong> {post['date']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Newsletter subscription
    st.markdown("---")
    st.markdown("### 📬 Subscribe to Our Newsletter")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("Stay updated with the latest agricultural news, tips, and market insights delivered directly to your inbox.")
        
        with st.form("newsletter_form"):
            email = st.text_input("Email Address", placeholder="your.email@example.com")
            interests = st.multiselect(
                "Select your interests",
                ["Farming Tips", "Market Trends", "Technology Updates", "Policy News", "Weather Updates"]
            )
            
            if st.form_submit_button("📧 Subscribe", use_container_width=True):
                if email:
                    st.success("✅ Thank you for subscribing! You'll receive our next newsletter soon.")
                else:
                    st.error("Please enter a valid email address.")
    
    with col2:
        st.markdown("""
        <div style='
            background: linear-gradient(135deg, #4CAF50, #8BC34A); 
            color: white; 
            padding: 2rem; 
            border-radius: 10px; 
            text-align: center;
        '>
            <h4 style='margin-bottom: 1rem;'>📊 Newsletter Stats</h4>
            <div style='font-size: 2rem; font-weight: bold; margin-bottom: 0.5rem;'>2,500+</div>
            <div style='opacity: 0.9;'>Active Subscribers</div>
            <div style='font-size: 1.5rem; font-weight: bold; margin: 1rem 0 0.5rem 0;'>Weekly</div>
            <div style='opacity: 0.9;'>Delivery Schedule</div>
        </div>
        """, unsafe_allow_html=True)

def contact_page():
    """Render contact us page"""
    st.markdown("## 📞 Contact FARMDEPOT_NG")
    st.markdown("*We're here to help you succeed in agricultural commerce*")
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.markdown("### 💬 Send us a Message")
        
        with st.form("contact_form"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                name = st.text_input("Full Name *", placeholder="John Doe")
                phone = st.text_input("Phone Number", placeholder="+234-XXX-XXX-XXXX")
            
            with col_b:
                email = st.text_input("Email Address *", placeholder="john@example.com")
                subject_type = st.selectbox(
                    "Subject Category",
                    ["General Inquiry", "Technical Support", "Business Partnership", 
                     "Complaint", "Feature Request", "Account Issues"]
                )
            
            subject = st.text_input("Subject *", placeholder="Brief description of your inquiry")
            message = st.text_area(
                "Message *", 
                placeholder="Please provide detailed information about your inquiry...",
                height=150
            )
            
            # Priority level
            priority = st.selectbox(
                "Priority Level",
                ["Low", "Medium", "High", "Urgent"],
                help="Select the urgency of your inquiry"
            )
            
            # Preferred contact method
            contact_method = st.radio(
                "Preferred Contact Method",
                ["Email", "Phone Call", "WhatsApp", "No Preference"]
            )
            
            col_x, col_y, col_z = st.columns([1, 2, 1])
            with col_y:
                submit_button = st.form_submit_button("📤 Send Message", use_container_width=True)
            
            if submit_button:
                if not all([name, email, subject, message]):
                    st.error("❌ Please fill in all required fields marked with *")
                else:
                    # Here you would typically save to database or send email
                    st.success("✅ Message sent successfully! We'll get back to you within 24 hours.")
                    st.balloons()
                    
                    # Show confirmation details
                    st.info(f"""
                    **Message Details:**
                    - **Name:** {name}
                    - **Email:** {email}
                    - **Subject:** {subject}
                    - **Priority:** {priority}
                    - **Preferred Contact:** {contact_method}
                    
                    **Reference ID:** FD-{datetime.now().strftime('%Y%m%d%H%M%S')}
                    """)
    
    with col2:
        st.markdown("### 📍 Contact Information")
        
        st.markdown("""
        <div style='
            background: linear-gradient(135deg, #4CAF50, #8BC34A); 
            color: white; 
            padding: 2rem; 
            border-radius: 12px; 
            margin-bottom: 1.5rem;
        '>
            <h4 style='margin-bottom: 1.5rem; text-align: center;'>🏢 Head Office</h4>
            
            <div style='margin-bottom: 1rem;'>
                <strong>📧 Email Addresses:</strong><br>
                • General: info@farmdepot.ng<br>
                • Support: support@farmdepot.ng<br>
                • Business: business@farmdepot.ng
            </div>
            
            <div style='margin-bottom: 1rem;'>
                <strong>📞 Phone Numbers:</strong><br>
                • Main: +234-XXX-XXX-XXXX<br>
                • Support: +234-XXX-XXX-XXXY<br>
                • WhatsApp: +234-XXX-XXX-XXXZ
            </div>
            
            <div style='margin-bottom: 1rem;'>
                <strong>📍 Address:</strong><br>
                FARMDEPOT_NG Headquarters<br>
                Plot 123, Agricultural Way<br>
                Victoria Island, Lagos<br>
                Nigeria
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Business hours
        st.markdown("""
        ### 🕒 Business Hours
        
        **Monday - Friday:**  
        8:00 AM - 6:00 PM (WAT)
        
        **Saturday:**  
        9:00 AM - 4:00 PM (WAT)
        
        **Sunday:**  
        Emergency support only
        
        **Public Holidays:**  
        Limited support available
        """)
        
        # Quick contact options
        st.markdown("### ⚡ Quick Contact")
        
        col_i, col_ii = st.columns(2)
        
        with col_i:
            if st.button("📧 Email Us", use_container_width=True):
                st.info("Opening your default email client...")
        
        with col_ii:
            if st.button("💬 WhatsApp", use_container_width=True):
                st.info("Opening WhatsApp...")
        
        # Social media
        st.markdown("### 🌐 Follow Us")
        
        social_links = [
            {"name": "Facebook", "icon": "📘", "url": "@FarmDepotNG"},
            {"name": "Twitter", "icon": "🐦", "url": "@FarmDepotNG"},
            {"name": "Instagram", "icon": "📷", "url": "@FarmDepotNG"},
            {"name": "LinkedIn", "icon": "💼", "url": "FarmDepot Nigeria"}
        ]
        
        for social in social_links:
            st.markdown(f"**{social['icon']} {social['name']}:** {social['url']}")

# Footer component
def render_footer():
    """Render application footer"""
    st.markdown("---")
    
    # Footer content
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        **🌾 FARMDEPOT_NG**
        
        Nigeria's premier agricultural marketplace connecting farmers, traders, and consumers nationwide.
        
        Empowering agriculture through technology.
        """)
    
    with col2:
        st.markdown("""
        **🔗 Quick Links**
        
        • Home
        • About Us
        • Post Advertisement
        • Browse Ads
        • Blog & News
        • Contact Support
        """)
    
    with col3:
        st.markdown("""
        **📋 Categories**
        
        • Tubers & Root Crops
        • Grains & Cereals
        • Vegetables & Fruits
        • Livestock & Poultry
        • Farm Equipment
        • Processed Foods
        """)
    
    with col4:
        st.markdown("""
        **📞 Support**
        
        • Email: support@farmdepot.ng
        • Phone: +234-XXX-XXX-XXXX
        • WhatsApp Support
        • Help Center
        • Terms of Service
        • Privacy Policy
        """)
    
    # Copyright section
    st.markdown("""
    <div style='
        text-align: center; 
        color: #666; 
        padding: 2rem; 
        border-top: 2px solid #4CAF50; 
        margin-top: 2rem;
        background: linear-gradient(145deg, #f8f9fa, #ffffff);
        border-radius: 10px;
    '>
        <p style='font-size: 1.1rem; margin-bottom: 0.5rem;'>
            &copy; 2024 <strong>FARMDEPOT_NG</strong>. All rights reserved.
        </p>
        <p style='font-size: 0.9rem; color: #888;'>
            🌾 Connecting Farmers, Traders, and Consumers Across Nigeria 🇳🇬
        </p>
        <p style='font-size: 0.8rem; color: #999; margin-top: 1rem;'>
            Built with ❤️ for Nigerian Agriculture | Powered by AI Technology
        </p>
    </div>
    """, unsafe_allow_html=True)

# Main application
def main():
    """Main application function"""
    try:
        # Initialize database
        init_database()
        
        # Render header and sidebar
        render_header()
        render_sidebar()
        
        # Route to different pages based on current_page session state
        current_page = st.session_state.get('current_page', 'Home')
        
        if current_page == "Home":
            home_page()
        elif current_page == "Post Ad":
            post_ad_page()
        elif current_page == "Ads List":
            ads_list_page()
        elif current_page == "About Us":
            about_page()
        elif current_page == "Blog":
            blog_page()
        elif current_page == "Contact Us":
            contact_page()
        else:
            # Default to home page if unknown page
            home_page()
        
        # Render footer
        render_footer()
        
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please refresh the page or contact support if the problem persists.")

# Application entry point
if __name__ == "__main__":
    main()
