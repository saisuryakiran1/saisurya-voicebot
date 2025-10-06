import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import tempfile, os, base64, re
from groq import Groq

# ==============================
# Your Groq API key
# ==============================
GROQ_API_KEY = "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"
# ==============================

st.set_page_config(page_title="Sai Surya's Voice Bot", page_icon="🎙️", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
body { background-color: black; color: white; }
.block-container { padding-bottom: 0px !important; }
.user-message { background: #E0F7FA; color: #000; padding: 8px; border-radius: 6px; margin-bottom: 6px; text-align: right; }
.assistant-message { background: #2E2E2E; color: #E0E0E0; padding: 8px; border-radius: 6px; margin-bottom: 6px; }
.stAudio label { font-size: 0 !important; }
.stAudio button, .stAudio input[type=range] { 
    transform: scale(1.6);
    border: 2px solid #fff !important;
    border-radius: 18px !important;
    background: #222 !important;
}
.stAudio {display: flex; justify-content: center; align-items: center; padding: 40px 0 10px 0;}
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

def autoplay_audio(path, play_id=None):
    with open(path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
    if play_id is None:
        play_id = "latest"
    html = f"""
    <audio id="bot-audio-{play_id}" controls autoplay style="width:100%;margin:20px 0 10px 0;">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3" />
        Your browser does not support the audio element.
    </audio>
    <script>
      const el = document.getElementById("bot-audio-{play_id}");
      if (el) {{
        const tryPlay = () => {{
          const p = el.play();
          if (p && p.catch) p.catch(() => {{ }});
        }};
        tryPlay();
        setTimeout(tryPlay, 250);
        setTimeout(tryPlay, 750);
      }}
    </script>
    """
    st.markdown(html, unsafe_allow_html=True)
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

# ---------- Header ----------
st.title("🎙️ Sai Surya’s Voice Bot")
st.markdown("MCA grad. AI geek. Talks like a witty human. Let’s roll!")

# ---------- Mic form at bottom (prevents 'stuck until next turn') ----------
st.markdown("<div height='72px' style='height:72px;'>&nbsp;</div>", unsafe_allow_html=True)
st.markdown("### Talk to the bot below ⬇️", unsafe_allow_html=True)

with st.form(key="voice-form", clear_on_submit=True):
    audio_input = st.audio_input("🎤", key="bottom_mic")
    submitted = st.form_submit_button("Send Voice")

# Process audio and update chat within the same rerun
new_assistant_index = None
if submitted and audio_input:
    recognizer = sr.Recognizer()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_input.getvalue())
        temp_audio_path = temp_audio.name
    try:
        with sr.AudioFile(temp_audio_path) as source:
            audio = recognizer.record(source)
            user_text = recognizer.recognize_google(audio)

        st.session_state.chat_history.append({"role": "user", "content": user_text})
        response = ai_reply(user_text)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        new_assistant_index = len(st.session_state.chat_history) - 1
    except Exception as e:
        st.warning(f"Couldn't process your audio: {e}")
    finally:
        os.remove(temp_audio_path)

# ---------- Display chat and speak ONLY the newest assistant reply ----------
for i, msg in enumerate(st.session_state.chat_history):
    if msg["role"] == "user":
        st.markdown(f'<div class="user-message">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message">{msg["content"]}</div>', unsafe_allow_html=True)
        if new_assistant_index is not None and i == new_assistant_index:
            audio = text_to_speech(msg["content"])
            autoplay_audio(audio, play_id=f"turn-{i}")
