import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import tempfile, os, base64, re, uuid
from groq import Groq

# ====== CONFIG ======
GROQ_API_KEY = "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"
# ====================

st.set_page_config(page_title="Sai Surya's Voice Bot", page_icon="🎙️", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
body { background-color: #0e0e0e; color: #fff; }
.block-container { padding-bottom: 0 !important; }
.user-message { background: #E0F7FA; color: #000; padding: 10px 12px; border-radius: 10px; margin: 6px 0 10px; text-align: right; }
.assistant-message { background: #2E2E2E; color: #E0E0E0; padding: 10px 12px; border-radius: 10px; margin: 6px 0 10px; }
.stAudio label { font-size: 0 !important; }
.stAudio button, .stAudio input[type=range] { 
    transform: scale(1.6);
    border: 2px solid #fff !important;
    border-radius: 18px !important;
    background: #222 !important;
}
.stAudio {display: flex; justify-content: center; align-items: center; padding: 36px 0 28px 0;}
.enable-audio { display:flex; justify-content:center; margin: 8px 0 16px 0; }
.enable-audio button {
    background:#43a047; color:#fff; border:none; border-radius:8px; padding:10px 14px; cursor:pointer;
}
footer { display:none !important; }
</style>
""", unsafe_allow_html=True)

# ---------- Predefined answers ----------
predefined_answers = {
    "what should we know about your life story":
        "Yo, it’s ya boy Sai Surya! MCA grad from India, I’m out here slinging code and diving deep into NLP and deep learning. Emotion detection’s my jam! 😜🚀",
    "what's your #1 superpower":
        "Catching emotions in text faster than Spider-Man catches villains! 🕸️😂",
    "what are the top 3 areas you'd like to grow in":
        "AI research, ML scaling, and keeping my chat game slick. 😎🎤",
    "what misconception do your coworkers have about you":
        "They think I’m quiet, but I’m secretly brewing deep learning spells. 🧙‍♂️💾",
    "how do you push your boundaries and limits":
        "I treat every tech challenge like a boss fight — level up or crash trying. 🎮🔥",
}

# ---------- Helpers ----------
def remove_emojis(text):
    emoji_pattern = re.compile("[" 
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def text_to_speech(text):
    text_clean = remove_emojis(text)
    tts = gTTS(text=text_clean, lang='en')
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp.name)
    return temp.name

def speak_base64(b64_str, play_id=None):
    if play_id is None:
        play_id = str(uuid.uuid4())
    html = f"""
    <audio id="bot-audio-{play_id}" controls autoplay style="width:100%;margin:16px 0 6px 0;">
        <source src="data:audio/mp3;base64,{b64_str}" type="audio/mp3" />
    </audio>
    <script>
      (function() {{
        const el = document.getElementById("bot-audio-{play_id}");
        if (!el) return;
        const tries = [0, 200, 600, 1200];
        function tryPlay() {{
          const p = el.play();
          if (p && p.catch) p.catch(()=>{{}});
        }}
        tries.forEach(t => setTimeout(tryPlay, t));
      }})();
    </script>
    """
    st.markdown(html, unsafe_allow_html=True)

def autoplay_audio(path, play_id=None):
    with open(path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
    speak_base64(b64, play_id)
    try: os.remove(path)
    except: pass

def ai_reply(user_input):
    user_lower = user_input.lower()
    for key in predefined_answers:
        if key in user_lower:
            return predefined_answers[key]
    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You’re Sai Surya, an MCA grad from India who’s into deep learning and NLP. Speak like a funny, confident, tech-savvy human — mix humor and intelligence naturally."},
                {"role": "user", "content": user_input}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"Groq API error: {str(e)}")
        return "Oops! Something went off-track. Try again?"

# ---------- State ----------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "mic_version" not in st.session_state:
    st.session_state.mic_version = 0
if "processed_version" not in st.session_state:
    st.session_state.processed_version = -1
if "audio_enabled" not in st.session_state:
    st.session_state.audio_enabled = False  # user gesture to allow autoplay on mobile

# ---------- Header ----------
st.title("🎙️ Sai Surya’s Voice Bot")
st.caption("Mic at the bottom. Tap to record, tap again to stop. You’ll hear the bot reply immediately.")

# ---------- Chat display ----------
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-message">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message">{msg["content"]}</div>', unsafe_allow_html=True)

# ---------- One-time audio enable button (fixes mobile autoplay) ----------
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if not st.session_state.audio_enabled:
        if st.button("✓ Enable sound"):
            st.session_state.audio_enabled = True
            # a tiny silent audio to unlock autoplay policy
            silent = base64.b64encode(b"\x00\x00").decode()
            speak_base64(silent, play_id="unlock")
            st.rerun()

# ---------- Bottom mic (versioned key to avoid Q1/Q2 shift) ----------
st.markdown("### Talk below 👇", unsafe_allow_html=True)
mic_key = f"audio-mic-v{st.session_state.mic_version}"
audio_input = st.audio_input("🎤 Tap, speak, tap again", key=mic_key)

# Process exactly once for each mic version, and speak immediately
if audio_input is not None and st.session_state.processed_version < st.session_state.mic_version:
    temp_audio_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(audio_input.getvalue())
            temp_audio_path = temp_audio.name

        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_audio_path) as source:
            audio = recognizer.record(source)
            user_text = recognizer.recognize_google(audio)

        st.session_state.chat_history.append({"role": "user", "content": user_text})
        response = ai_reply(user_text)
        st.session_state.chat_history.append({"role": "assistant", "content": response})

        # TTS and autoplay (works after user pressed Enable sound once)
        tts_path = text_to_speech(response)
        autoplay_audio(tts_path, play_id=f"turn-{st.session_state.mic_version}")

        st.session_state.processed_version = st.session_state.mic_version
        st.session_state.mic_version += 1
        st.rerun()
    except Exception as e:
        st.warning(f"Audio processing failed: {e}")
    finally:
        if temp_audio_path:
            try: os.remove(temp_audio_path)
            except: pass
