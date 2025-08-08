# FARMDEPOT_NG - AI-Powered Agricultural Marketplace

🌾 Nigeria's premier agricultural classified ads platform with AI-powered voice recognition and multilingual support.

## 🚀 Live Demo

**Streamlit Cloud:** [Your deployed app URL here]

## ✨ Features

- 🎤 **Voice Recognition** (Local only - full functionality when running locally)
- 🌍 **Multilingual Support** (English, Hausa, Yoruba, Igbo)
- 🔐 **User Authentication** (Registration & Login)
- 🛍️ **Post & Search Ads** with image upload
- 📱 **Mobile-Responsive Design**
- 🤖 **AI Command Processing**
- 📊 **Real-time Search & Filtering**

## 🛠️ Installation & Setup

### Option 1: Run Locally (Full Features)

```bash
# Clone the repository
git clone [your-repo-url]
cd farmdepot_ng

# Install basic requirements
pip install streamlit pillow pandas

# Install voice recognition (optional but recommended)
pip install speechrecognition pyaudio pyttsx3

# Run the application
streamlit run app.py
```

### Option 2: Deploy to Streamlit Cloud

1. **Create these files in your repository:**
   - `app.py` (main application)
   - `requirements.txt` (Python dependencies)
   - `packages.txt` (system packages - optional)
   - `.streamlit/config.toml` (Streamlit configuration)

2. **Deploy to Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Select `app.py` as the main file
   - Deploy!

## 📁 File Structure

```
farmdepot_ng/
├── app.py                 # Main application
├── requirements.txt       # Python dependencies
├── packages.txt          # System packages (for cloud)
├── .streamlit/
│   └── config.toml       # Streamlit configuration
├── uploads/              # Image uploads (created automatically)
├── farmdepot.db         # SQLite database (created automatically)
└── README.md            # This file
```

## 🔧 Dependencies

### Required (Core functionality):
- `streamlit>=1.28.0`
- `pillow>=9.0.0` 
- `pandas>=1.5.0`

### Optional (Voice features - Local only):
- `speechrecognition`
- `pyaudio`
- `pyttsx3`

### Optional (Translation):
- `googletrans==4.0.0-rc1`

## 🎤 Voice Recognition Setup

Voice recognition works **only when running locally** due to browser security and cloud limitations.

### Windows:
```bash
pip install speechrecognition pyttsx3

# If PyAudio installation fails:
pip install pipwin
pipwin install pyaudio
```

### Linux/Ubuntu:
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install speechrecognition pyaudio pyttsx3
```

### macOS:
```bash
brew install portaudio
pip install speechrecognition pyaudio pyttsx3
```

## 🌐 Cloud vs Local Features

| Feature | Streamlit Cloud | Local Installation |
|---------|----------------|-------------------|
| Basic App | ✅ Full | ✅ Full |
| User Auth | ✅ Full | ✅ Full |
| Post/Search Ads | ✅ Full | ✅ Full |
| Image Upload | ✅ Full | ✅ Full |
| Voice Recognition | ❌ Demo only | ✅ Real voice |
| Text-to-Speech | ❌ Text display | ✅ Real audio |
| Microphone Access | ❌ No | ✅ Yes |

## 🎯 Usage Examples

### Voice Commands (Local only):

**Search:**
- "Search for rice in Lagos"
- "Find tomatoes"
- "Show me yam from Kano"

**Post Ads:**
- "I want to sell rice from Kano for 25000 naira"
- "Selling fresh tomatoes from Lagos"

## 🐛 Troubleshooting

### Streamlit Cloud Deployment Issues:

1. **Requirements Error:**
   - Ensure `requirements.txt` contains only installable packages
   - Remove voice-related packages for cloud deployment

2. **Import Errors:**
   - App gracefully handles missing voice packages
   - Check that all required packages are in `requirements.txt`

3. **Database Issues:**
   - SQLite database is created automatically
   - Ensure write permissions (handled automatically on cloud)

### Local Installation Issues:

1. **PyAudio Installation:**
   - Windows: Use `pipwin install pyaudio`
   - Linux: Install `portaudio19-dev` first
   - macOS: Install `portaudio` via Homebrew

2. **Microphone Access:**
   - Grant microphone permissions in browser
   - Check system microphone settings

## 📞 Support

- **GitHub Issues:** [Your repo issues URL]
- **Email:** support@farmdepot.ng
- **Documentation:** See code comments for detailed explanations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🏆 Credits

Built with ❤️ for Nigerian Agriculture using:
- [Streamlit](https://streamlit.io) - Web framework
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) - Voice recognition
- [Pillow](https://pillow.readthedocs.io/) - Image processing
- [SQLite](https://www.sqlite.org/) - Database

---

**🌾 FARMDEPOT_NG - Connecting Farmers, Traders, and Consumers Across Nigeria 🇳🇬**
