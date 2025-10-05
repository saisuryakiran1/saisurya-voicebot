import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import tempfile
import os
import pyaudio
import numpy as np
import pandas as pd
import time
import wave
import base64
from groq import Groq
import uuid
import json
import re  # Added for emoji stripping

# Set page config for wide layout
st.set_page_config(page_title="Sai Surya's Voice Bot", page_icon="🎙️", layout="wide")

# Custom CSS for Sai Surya's professional UI (dark theme, sleek design, minimal spacing)
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
    .stInfo {
        background-color: #2A2A2A;
        color: #B0B0B0;
        border-radius: 4px;
        padding: 5px;
        margin: 0;
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
    .stChatInput > div > div > input {
        background-color: #2A2A2A;
        color: #FFFFFF;
        border: 1px solid #1E90FF;
        border-radius: 4px;
        padding: 8px;
        font-size: 14px;
        width: 100%;
        margin: 0;
    }
    .chat-container {
        height: 60vh;
        overflow-y: auto;
        padding: 10px 0;
        margin: 0;
        display: flex;
        flex-direction: column-reverse;
    }
    .control-panel {
        position: absolute;
        top: 0;
        width: calc(100% - 250px);
        background-color: #1A1A1A;
        padding: 10px;
        border-bottom: 1px solid #333333;
        margin: 0;
    }
    .main-content {
        margin-left: 250px;
        padding: 10px 0;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar for navigation (replicating the side dialog box)
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

# Main content area
with st.container():
    st.title("🎙️ Sai Surya's Voice Bot")
    st.markdown("Hey there! I’m Sai Surya, your MCA grad AI buddy from India, obsessed with deep learning and NLP. Let’s chat—witty style or pro vibes, your call!")

# --- Predefined Answers (Sai Surya's Goofy, Witty Style) ---
predefined_answers = {
    "what should we know about your life story": 
        "Yo, it’s ya boy Sai Surya! MCA grad from India, I’m out here slinging code and diving deep into NLP and deep learning. Emotion detection’s my jam—think of me as the goofy guru of AI vibes! 😜🚀",
    "what's your #1 superpower":
        "My #1 superpower? I’m like Spider-Man for emotions—using NLP and deep learning to catch feelings in the web of my neural nets. Plus, I got jokes for days! 🕸️😂",
    "what are the top 3 areas you'd like to grow in":
        "Aight, I’m hyped to level up in AI research (gimme those breakthroughs!), scale ML systems (big data, big dreams!), and keep my chat game so slick you’ll think I’m part stand-up comic! 😎🎤",
    "what misconception do your coworkers have about you":
        "They think I’m just the quiet nerd in the corner, but nah, I’m secretly cooking up AI magic and dropping witty one-liners like a techy comedian! 😏💾",
    "how do you push your boundaries and limits":
        "I jump into the deep end of new tech, tinker with wild neural models, and treat challenges like a boss-level video game—Sai Surya’s always ready for the next quest! 🎮🔥",
}

# --- Audio Configuration ---
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
SILENCE_THRESHOLD = 400
SILENCE_DURATION = 1.2
MIN_SILENCE_CHUNKS = 8
MIN_SPEECH_CHUNKS = 5
SPEECH_THRESHOLD = 500

# --- Session State ---
if 'listening' not in st.session_state:
    st.session_state.listening = False
if 'transcript' not in st.session_state:
    st.session_state.transcript = ""
if 'response' not in st.session_state:
    st.session_state.response = ""
if 'silence_count' not in st.session_state:
    st.session_state.silence_count = 0
if 'speech_count' not in st.session_state:
    st.session_state.speech_count = 0
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'audio_playing' not in st.session_state:
    st.session_state.audio_playing = False
if 'image_confirmation' not in st.session_state:
    st.session_state.image_confirmation = False
if 'memory_enabled' not in st.session_state:
    st.session_state.memory_enabled = True
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None

# --- Stop Audio Playback ---
def stop_audio():
    st.session_state.audio_playing = False
    st.markdown('<script>var audios = document.getElementsByTagName("audio"); for(var i = 0; i < audios.length; i++) { audios[i].pause(); audios[i].remove(); }</script>', unsafe_allow_html=True)

# --- Record Audio ---
def record_audio_with_silence_detection():
    p = pyaudio.PyAudio()
    try:
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    except Exception as e:
        st.error(f"Microphone Error: {str(e)}")
        return None

    silence_start = None
    recording = []
    st.session_state.silence_count = 0
    st.session_state.speech_count = 0

    st.info("🎙 Listening...")
    try:
        while st.session_state.listening:
            data = stream.read(CHUNK, exception_on_overflow=False)
            recording.append(data)
            amplitude = np.frombuffer(data, dtype=np.int16).max()

            if amplitude > SPEECH_THRESHOLD:
                st.session_state.speech_count += 1

            if st.session_state.speech_count >= MIN_SPEECH_CHUNKS:
                if amplitude < SILENCE_THRESHOLD:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > SILENCE_DURATION / MIN_SILENCE_CHUNKS:
                        st.session_state.silence_count += 1
                        if st.session_state.silence_count >= MIN_SILENCE_CHUNKS:
                            st.success("✅ Processing...")
                            stream.stop_stream()
                            stream.close()
                            p.terminate()
                            return b''.join(recording)
                else:
                    silence_start = None
                    st.session_state.silence_count = 0
    except Exception as e:
        st.error(f"Recording Error: {str(e)}")
        stream.stop_stream()
        stream.close()
        p.terminate()
        return None

    stream.stop_stream()
    stream.close()
    p.terminate()
    return None

# --- Save Audio as WAV ---
def save_audio_to_wav(audio_data):
    if not audio_data:
        st.error("No audio data recorded.")
        return None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            audio_file = f.name
            wf = wave.open(audio_file, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(audio_data)
            wf.close()
        return audio_file
    except Exception as e:
        st.error(f"Error saving WAV file: {str(e)}")
        return None

# --- Transcribe Audio with Noise Reduction ---
def transcribe_audio(audio_data):
    audio_file = save_audio_to_wav(audio_data)
    if not audio_file:
        return "No audio data to transcribe."
    
    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            r.adjust_for_ambient_noise(source, duration=0.5)  # Noise reduction
            audio = r.record(source)
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand that. Maybe my ears need a coffee break! ☕"
    except sr.RequestError as e:
        return f"Oops, speech service hit a snag: {str(e)}. Let’s try again!"
    except Exception as e:
        st.error(f"Audio processing glitch: {str(e)}")
        return "Sorry, my audio skills flopped—give it another shot!"
    finally:
        try:
            if os.path.exists(audio_file):
                os.unlink(audio_file)
        except Exception as e:
            st.warning(f"Couldn’t clean up temp file: {str(e)}")

# --- Chatbot Logic with Sai Surya’s Goofy, Witty Voice ---
def ai_reply(user_input):
    user_lower = user_input.lower()
    for key in predefined_answers:
        if key in user_lower:
            return predefined_answers[key]
    
    if any(phrase in user_lower for phrase in ["generate image", "create image"]):
        st.session_state.image_confirmation = True
        return "Yo, you want some art? Say ‘yes’ and I’ll try to whip up something wild—Sai Surya’s still practicing his digital doodles! 🎨😜"

    # Professional response for serious queries
    serious_keywords = ["job", "career", "research", "project", "deadline"]
    if any(keyword in user_lower for keyword in serious_keywords):
        return f"Alright, let’s get serious—Sai Surya, MCA grad, reporting for duty! I’m all about deep learning and NLP, so hit me with your {user_input.split()[0]} question, and I’ll deliver the pro-level goods! 💼🚀"

    try:
        client = Groq(api_key='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')
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You’re Sai Surya, an MCA grad from India who’s a total nerd for deep learning and NLP. Talk like a goofy, witty tech bro with a heart of gold—think lots of slang, emojis, and jokes, but flip to professional mode for serious questions like jobs or research. Keep it fun and true to Sai Surya’s passion! For emojis, include them in responses but don't describe or spell them out unless asked."},
                {"role": "user", "content": user_input}
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        st.error(f"API oopsie: {str(e)}")
        return "Aww, man, my AI brain just tripped over a binary banana peel! 🍌 Let’s try that again, aight?"

# --- Emoji Stripping for TTS ---
def remove_emojis(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

# --- Text to Speech with Autoplay (Strip Emojis for Voice) ---
def text_to_speech(text):
    try:
        text_no_emoji = remove_emojis(text)  # Strip emojis for voice output
        tts = gTTS(text=text_no_emoji, lang='en', slow=False)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tts.save(temp_file.name)
        return temp_file.name
    except Exception as e:
        st.error(f"TTS glitch: {str(e)}")
        return None

def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="true" style="display:none;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    os.unlink(file_path)

# --- Process User Input (Voice or Keyboard) ---
def process_user_input(user_input):
    if user_input.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with chat_container:
            st.markdown(f'<div class="user-message">{user_input}</div>', unsafe_allow_html=True)
        
        response = ai_reply(user_input)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        with chat_container:
            st.markdown(f'<div class="assistant-message">{response}</div>', unsafe_allow_html=True)
        
        audio_file = text_to_speech(response)
        if audio_file:
            autoplay_audio(audio_file)

# --- Display Chat History ---
chat_container = st.container()
with chat_container:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-message">{message["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- Controls in Control Panel ---
with st.container():
    st.markdown('<div class="control-panel">', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🎤 Toggle Listening", key="toggle_button", help="Start/Stop Voice Listening"):
            st.session_state.listening = not st.session_state.listening

    with col1:
        user_text = st.chat_input("Type your message here...")
        if user_text:
            process_user_input(user_text)

    st.markdown('</div>', unsafe_allow_html=True)

# --- Voice Listening Loop ---
while st.session_state.listening:
    audio_data = record_audio_with_silence_detection()
    if audio_data:
        st.session_state.transcript = transcribe_audio(audio_data)
        if "couldn't understand" not in st.session_state.transcript and st.session_state.transcript.strip():
            process_user_input(st.session_state.transcript)
        else:
            st.info("No clear speech? Maybe I need a translator—keep talking! 😄")
    else:
        break

if st.session_state.listening:
    st.info("🎙 Listening... Speak now!")
else:
    st.info("Click 'Toggle Listening' to start voice input or type below.")
