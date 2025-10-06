import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import tempfile, os, base64, re, uuid
from groq import Groq

GROQ_API_KEY = "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"

st.set_page_config(page_title="Sai Surya's Voice Bot", page_icon="🎙️", layout="wide")

# --------- Styling ---------
st.markdown("""
<style>
body { background: #17191b !important; color: #fff; }
.block-container {padding-bottom: 0!important;}
.user-message { background: #E0F7FA; color: #000; padding: 12px 16px; border-radius: 12px; margin: 10px 0; text-align: right;}
.assistant-message { background: #23272b; color: #E8E8E8; padding: 12px 16px; border-radius: 12px; margin: 8px 0;}
footer {display:none;}
.st-emotion-cache-13ejsyy {max-width: 700px;}
.mic-bar {width:100%;display:flex;justify-content:center;position:fixed;bottom:0;left:0;right:0;z-index:20;background:rgba(20,20,20,0.99);padding:28px 0 26px 0;}
.stAudio input[type=range], .stAudio button {transform:scale(2);}
.stAudio {justify-content:center !important;}
.mic-instruction {display:block;width:100%;text-align:center;}
</style>
""", unsafe_allow_html=True)

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
        play_id = str(uuid.uuid4())
    html = f"""
    <audio id="bot-audio-{play_id}" autoplay controls style="width:100%;margin:16px 0 6px 0;">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3" />
    </audio>
    <script>
      (function(){{
        var el = document.getElementById('bot-audio-{play_id}');
        if (el) {{
          var tries = [0, 150, 500, 1000];
          function tryPlay(){{ el.play && el.play(); }}
          tries.forEach(function(t){{setTimeout(tryPlay, t);}});
        }}
      }})();
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

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "mic_version" not in st.session_state:
    st.session_state.mic_version = 0
if "processed_version" not in st.session_state:
    st.session_state.processed_version = -1

st.title("🎙️ Sai Surya’s Voice Bot")
st.caption("Tap the big mic at the bottom, speak, tap again to stop. Bot replies instantly and speaks.")

for i, msg in enumerate(st.session_state.chat_history):
    if msg["role"] == "user":
        st.markdown(f'<div class="user-message">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message">{msg["content"]}</div>', unsafe_allow_html=True)
        if i == len(st.session_state.chat_history)-1:
            tts_path = text_to_speech(msg["content"])
            autoplay_audio(tts_path, play_id=f"turn-{i}")

# --- BIG MIC floating bar at the bottom ---
st.markdown(
    """
    <div class="mic-bar">
        <div class="mic-instruction">🎤 <b>Tap the big mic, Speak, Tap again</b></div>
    </div>
    """,
    unsafe_allow_html=True,
)
# Centered large mic input, always fresh per turn
mic_key = f"audio-mic-{st.session_state.mic_version}"
audio_input = st.audio_input("", key=mic_key, label_visibility="hidden")

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
        reply = ai_reply(user_text)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.session_state.processed_version = st.session_state.mic_version
        st.session_state.mic_version += 1
        st.rerun()
    except Exception as e:
        st.warning(f"Audio processing failed: {e}")
    finally:
        if temp_audio_path:
            try: os.remove(temp_audio_path)
            except: pass
