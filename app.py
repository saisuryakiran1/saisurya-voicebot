import streamlit as st
import speech_recognition as sr
from gtts import gTTS
import tempfile, os, base64, re
from groq import Groq
import uuid

# ============== CONFIG ==============
GROQ_API_KEY = "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"
AUTO_SILENCE_MS = 1200   # stop after ~1.2s of silence
# ====================================

st.set_page_config(page_title="Sai Surya's Voice Bot", page_icon="🎙️", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
body { background-color: black; color: white; }
.block-container { padding-bottom: 90px !important; }  /* space above footer mic */
.user-message { background: #E0F7FA; color: #000; padding: 10px 12px; border-radius: 10px; margin: 6px 0 10px; text-align: right; }
.assistant-message { background: #2E2E2E; color: #E0E0E0; padding: 10px 12px; border-radius: 10px; margin: 6px 0 10px; }
.footer-mic {
  position: fixed; left: 0; right: 0; bottom: 0; 
  background: rgba(10,10,10,0.95); border-top: 1px solid #333;
  padding: 12px 0; z-index: 9999;
}
.mic-wrap { display:flex; justify-content:center; align-items:center; gap:16px; }
.mic-btn {
  width: 84px; height: 84px; border-radius: 50%;
  background:#e53935; border:3px solid #fff; color:#fff; font-size:34px; cursor:pointer;
  display:flex; justify-content:center; align-items:center;
  box-shadow: 0 0 16px rgba(229,57,53,0.6);
  transition: transform .1s ease;
}
.mic-btn:active { transform: scale(0.96); }
.mic-btn.recording { background:#43a047; box-shadow: 0 0 20px rgba(67,160,71,0.8); }
.status { color:#ccc; font-size:14px; }
.pulse {
  width: 14px; height: 14px; border-radius:50%; background:#43a047;
  box-shadow: 0 0 0 0 rgba(67,160,71, 0.7); animation: pulse 1.3s infinite;
}
@keyframes pulse {
  0% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(67,160,71, 0.7); }
  70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(67,160,71, 0); }
  100% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(67,160,71, 0); }
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

def autoplay_audio(path, play_id=None):
    with open(path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
    if play_id is None:
        play_id = str(uuid.uuid4())
    html = f"""
    <audio id="bot-audio-{play_id}" controls autoplay style="width:100%;margin:10px 0 6px 0;">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3" />
        Your browser does not support the audio element.
    </audio>
    <script>
      const el = document.getElementById("bot-audio-{play_id}");
      if (el) {{
        const tryPlay = () => {{
          const p = el.play(); if (p && p.catch) p.catch(() => {{ }});
        }};
        tryPlay(); setTimeout(tryPlay, 250); setTimeout(tryPlay, 750);
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
st.caption("Mic at the bottom. Speak—auto-stops on silence, auto-sends, and the bot replies with voice.")

# ---------- Display chat (top area) ----------
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-message">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message">{msg["content"]}</div>', unsafe_allow_html=True)

# ---------- Hidden uploader to receive blob from JS recorder ----------
uploaded = st.file_uploader("hidden-uploader", type=["webm", "wav", "mp3"], label_visibility="hidden", key="hidden_uploader")

# When a blob arrives, process immediately
if uploaded is not None:
    try:
        # Save temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded.type.split('/')[-1] if uploaded.type else 'webm'}") as tf:
            tf.write(uploaded.getvalue())
            temp_path = tf.name

        # Transcribe
        recognizer = sr.Recognizer()
        with sr.AudioFile(temp_path) as source:
            audio = recognizer.record(source)
            user_text = recognizer.recognize_google(audio)

        st.session_state.chat_history.append({"role": "user", "content": user_text})
        response = ai_reply(user_text)
        st.session_state.chat_history.append({"role": "assistant", "content": response})

        # Speak latest assistant message
        tts_path = text_to_speech(response)
        autoplay_audio(tts_path, play_id="latest-reply")
    except Exception as e:
        st.warning(f"Audio process failed: {e}")
    finally:
        try: os.remove(temp_path)
        except: pass
    # Clear the uploader so next blob triggers again
    st.session_state["hidden_uploader"] = None
    st.experimental_rerun()

# ---------- Footer mic (custom MediaRecorder with silence detection) ----------
footer_html = f"""
<div class="footer-mic">
  <div class="mic-wrap">
    <div class="status" id="mic-status">Tap to talk</div>
    <div class="mic-btn" id="mic-btn">🎤</div>
    <div class="pulse" id="mic-pulse" style="display:none;"></div>
  </div>
</div>

<script>
(function() {{
  const silenceMs = {AUTO_SILENCE_MS};
  let mediaRecorder = null;
  let audioChunks = [];
  let audioCtx, analyser, sourceNode;
  let silenceTimer = null;
  let recording = false;

  const micBtn = document.getElementById('mic-btn');
  const pulse = document.getElementById('mic-pulse');
  const status = document.getElementById('mic-status');

  async function startRecording() {{
    try {{
      const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];
      mediaRecorder.ondataavailable = e => {{ if (e.data.size > 0) audioChunks.push(e.data); }};
      mediaRecorder.onstop = async () => {{
        try {{
          const blob = new Blob(audioChunks, {{ type: 'audio/webm' }});
          const file = new File([blob], 'voice.webm', {{ type: 'audio/webm' }});
          const dt = new DataTransfer();
          dt.items.add(file);
          const uploader = window.parent.document.querySelector('input[type="file"][id*="hidden_uploader"]');
          uploader.files = dt.files;
          uploader.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }} catch (err) {{
          console.error('Upload error', err);
        }}
      }};
      mediaRecorder.start();

      // Setup analyser for silence detection
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      sourceNode = audioCtx.createMediaStreamSource(stream);
      analyser = audioCtx.createAnalyser();
      analyser.fftSize = 2048;
      sourceNode.connect(analyser);

      let lastNonSilent = Date.now();
      const data = new Uint8Array(analyser.fftSize);

      function checkSilence() {{
        analyser.getByteTimeDomainData(data);
        // compute average deviation from mid
        let sum = 0;
        for (let i=0;i<data.length;i++) {{
          sum += Math.abs(data[i] - 128);
        }}
        const avg = sum / data.length;
        // threshold ~2-3 => silence
        if (avg > 3) lastNonSilent = Date.now();
        if (Date.now() - lastNonSilent > silenceMs) stopRecording();
        if (recording) requestAnimationFrame(checkSilence);
      }}
      recording = true;
      micBtn.classList.add('recording');
      pulse.style.display = 'inline-block';
      status.innerText = 'Listening...';
      requestAnimationFrame(checkSilence);
    }} catch (err) {{
      console.error(err);
      status.innerText = 'Mic permission needed';
    }}
  }}

  function stopRecording() {{
    if (!recording) return;
    recording = false;
    micBtn.classList.remove('recording');
    pulse.style.display = 'none';
    status.innerText = 'Processing...';
    try {{
      mediaRecorder && mediaRecorder.state !== 'inactive' && mediaRecorder.stop();
      if (audioCtx) audioCtx.close();
    }} catch (e) {{ }}
    setTimeout(() => {{ status.innerText = 'Tap to talk'; }}, 1200);
  }}

  micBtn.addEventListener('click', () => {{
    if (!recording) startRecording(); else stopRecording();
  }});
}})();
</script>
"""
st.markdown(footer_html, unsafe_allow_html=True)
