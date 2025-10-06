import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import tempfile
import os
import base64
import re
from groq import Groq

# Set page config
st.set_page_config(page_title="Sai Surya's Voice Bot", page_icon="🎙️", layout="wide")

# Custom CSS (keeping your exact styling)
st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
        color: #FFFFFF;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu;
        display: flex;
        flex-direction: column;
        height: 100vh;
    }
    .stSidebar {
        background-color: #1A1A1A;
        color: #FFFFFF;
        width: 250px;
        padding: 5px 0;
    }
    .stSidebar .stButton > button {
        background-color: transparent;
        color: #FFFFFF;
        border: none;
        text-align: left;
        width: 100%;
        padding: 8px 10px;
        font-size: 14px;
    }
    .stSidebar .stButton > button:hover {
        background-color: #2E2E2E;
    }
    .user-message {
        background-color: #E0F7FA;
        color: #000000;
        border-radius: 6px;
        padding: 8px;
        margin-left: auto;
        max-width: 80%;
        text-align: right;
        margin-bottom: 5px;
    }
    .assistant-message {
        background-color: #2E2E2E;
        color: #E0E0E0;
        border-radius: 6px;
        padding: 8px;
        margin-right: auto;
        max-width: 80%;
        text-align: left;
        margin-bottom: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar (keeping your design)
with st.sidebar:
    st.markdown("### Search Ctrl+K")
    st.button("🗨️ Chat")
    st.button("🔊 Voice")
    st.button("🖼️ Imagine")
    st.button("📂 Projects")
    st.markdown("### History")
    st.button("Today")
    st.button("Real-Time Voice Chatbot wil")
    st.button("See all")

# Main content
st.title("🎙️ Sai Surya's Voice Bot")
st.markdown("Hey there! I'm Sai Surya, your MCA grad AI buddy from India, obsessed with deep learning and NLP. Let's chat—witty style or pro vibes, your call!")

# Predefined answers (keeping your personality)
predefined_answers = {
    "what should we know about your life story": 
        "Yo, it's ya boy Sai Surya! MCA grad from India, I'm out here slinging code and diving deep into NLP and deep learning. Emotion detection's my jam—think of me as the goofy guru of AI vibes! 😜🚀",
    "what's your #1 superpower":
        "My #1 superpower? I'm like Spider-Man for emotions—using NLP and deep learning to catch feelings in the web of my neural nets. Plus, I got jokes for days! 🕸️😂",
    "what are the top 3 areas you'd like to grow in":
        "Aight, I'm hyped to level up in AI research (gimme those breakthroughs!), scale ML systems (big data, big dreams!), and keep my chat game so slick you'll think I'm part stand-up comic! 😎🎤",
    "what misconception do your coworkers have about you":
        "They think I'm just the quiet nerd in the corner, but nah, I'm secretly cooking up AI magic and dropping witty one-liners like a techy comedian! 😏💾",
    "how do you push your boundaries and limits":
        "I jump into the deep end of new tech, tinker with wild neural models, and treat challenges like a boss-level video game—Sai Surya's always ready for the next quest! 🎮🔥",
}

# Session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Functions
def remove_emojis(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def ai_reply(user_input):
    user_lower = user_input.lower()
    for key in predefined_answers:
        if key in user_lower:
            return predefined_answers[key]
    
    serious_keywords = ["job", "career", "research", "project", "deadline"]
    if any(keyword in user_lower for keyword in serious_keywords):
        return f"Alright, let's get serious—Sai Surya, MCA grad, reporting for duty! I'm all about deep learning and NLP, so hit me with your {user_input.split()[0]} question, and I'll deliver the pro-level goods! 💼🚀"

    try:
        client = Groq(api_key=os.getenv('GROQ_API_KEY', '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'))
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You're Sai Surya, an MCA grad from India who's a total nerd for deep learning and NLP. Talk like a goofy, witty tech bro with a heart of gold—think lots of slang, emojis, and jokes, but flip to professional mode for serious questions like jobs or research. Keep it fun and true to Sai Surya's passion!"},
                {"role": "user", "content": user_input}
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return "Aww, man, my AI brain just tripped over a binary banana peel! 🍌 Let's try that again, aight?"

def text_to_speech(text):
    try:
        text_no_emoji = remove_emojis(text)
        tts = gTTS(text=text_no_emoji, lang='en', slow=False)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_file.name)
        return temp_file.name
    except Exception as e:
        st.error(f"TTS error: {str(e)}")
        return None

def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio controls autoplay style="width: 100%;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    os.unlink(file_path)

# Audio Upload Section
st.markdown("### 🎤 Voice Input")
uploaded_file = st.file_uploader("Upload your voice message (WAV/MP3)", type=["wav", "mp3", "m4a"], key="audio_upload")

if uploaded_file is not None:
    # Process uploaded audio
    recognizer = sr.Recognizer()
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file.flush()
            
            with sr.AudioFile(tmp_file.name) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.record(source)
            
            text = recognizer.recognize_google(audio)
            st.success(f"You said: {text}")
            
            # Process the input
            if text.strip():
                st.session_state.chat_history.append({"role": "user", "content": text})
                response = ai_reply(text)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                
                # Generate and play TTS
                audio_file = text_to_speech(response)
                if audio_file:
                    st.markdown("### 🔊 Bot Response:")
                    autoplay_audio(audio_file)
            
            os.unlink(tmp_file.name)
            
    except Exception as e:
        st.error(f"Could not process audio: {str(e)}")

# Text Input
st.markdown("### 💬 Text Chat")
user_text = st.chat_input("Type your message here...")
if user_text:
    st.session_state.chat_history.append({"role": "user", "content": user_text})
    response = ai_reply(user_text)
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    
    # Generate TTS for text input too
    audio_file = text_to_speech(response)
    if audio_file:
        st.markdown("### 🔊 Bot Response:")
        autoplay_audio(audio_file)

# Display Chat History
st.markdown("### 💬 Chat History")
for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.markdown(f'<div class="user-message">You: {message["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message">Sai Surya: {message["content"]}</div>', unsafe_allow_html=True)

# Instructions
st.markdown("---")
st.markdown("**How to use:**")
st.markdown("1. **Voice:** Record audio on your device and upload the file")
st.markdown("2. **Text:** Type in the chat box below")
st.markdown("3. **Listen:** Click play on the audio response!")
