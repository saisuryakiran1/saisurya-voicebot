import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av
import numpy as np
import tempfile
import speech_recognition as sr
from groq import Groq
from gtts import gTTS
import base64
import os
import re

# Personality: Predefined answers
predefined_answers = {
    "what should we know about your life story": "Yo, it’s ya boy Sai Surya! MCA grad from India, I’m out here slinging code and diving deep into NLP and deep learning. Emotion detection’s my jam—think of me as the goofy guru of AI vibes! 😜🚀",
    "what's your #1 superpower": "My #1 superpower? I’m like Spider-Man for emotions—using NLP and deep learning to catch feelings in the web of my neural nets. Plus, I got jokes for days! 🕸️😂",
    "what are the top 3 areas you'd like to grow in": "Aight, I’m hyped to level up in AI research (gimme those breakthroughs!), scale ML systems (big data, big dreams!), and keep my chat game so slick you’ll think I’m part stand-up comic! 😎🎤",
    "what misconception do your coworkers have about you": "They think I’m just the quiet nerd in the corner, but nah, I’m secretly cooking up AI magic and dropping witty one-liners like a techy comedian! 😏💾",
    "how do you push your boundaries and limits": "I jump into the deep end of new tech, tinker with wild neural models, and treat challenges like a boss-level video game—Sai Surya’s always ready for the next quest! 🎮🔥",
}

def remove_emojis(text):
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def ai_reply(user_input):
    user_lower = user_input.lower()
    for key in predefined_answers:
        if key in user_lower:
            return predefined_answers[key]
    try:
        client = Groq(api_key=os.getenv('GROQ_API_KEY', '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'))
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You’re Sai Surya, an MCA grad from India who’s a total nerd for deep learning and NLP. Talk like a goofy, witty tech bro with a heart of gold—think lots of slang, emojis, and jokes, but flip to professional mode for serious questions like jobs or research. Keep it fun and true to Sai Surya’s passion!"},
                {"role": "user", "content": user_input}
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception:
        return "Aww, man, my AI brain just tripped over a binary banana peel! 🍌 Let’s try that again, aight?"

def text_to_speech(text):
    text_no_emoji = remove_emojis(text)
    tts = gTTS(text=text_no_emoji, lang='en', slow=False)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_file.name)
    return temp_file.name

def show_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio controls autoplay style="width: 80%;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    os.unlink(file_path)

# App UI
st.title("🎙️ Sai Surya's Voice Bot (Web!)")
st.write("Click 'Start' and speak! The bot will speak back.")

# Store chat
if "history" not in st.session_state: st.session_state.history = []

# Audio processing
class SpeechProcessor(AudioProcessorBase):
    def __init__(self):
        self.frames = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        pcm = frame.to_ndarray()
        self.frames.append(pcm)
        return frame

def process_audio(frames):
    # Save as WAV
    wavfile = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    pcm = np.concatenate(frames)
    pcm16 = (pcm * 32767).astype(np.int16) # Convert float to int16 for WAV
    wavfile.write(pcm16.tobytes())
    wavfile.flush()
    return wavfile

result = webrtc_streamer(
    key="example",
    audio_receiver_size=1024,
    audio_processor_factory=SpeechProcessor,
    media_stream_constraints={"audio": True, "video": False},
)

if result and result.state == "STATE_STOPPED":
    processor = result.audio_processor
    if processor and processor.frames:
        st.info("Transcribing...")
        wavfile = process_audio(processor.frames)

        # Transcribe
        rec = sr.Recognizer()
        with sr.AudioFile(wavfile.name) as source:
            audio = rec.record(source)
            try:
                text = rec.recognize_google(audio)
            except Exception:
                text = ""
        os.unlink(wavfile.name)

        if text:
            st.session_state.history.append(("User", text))
            st.success(f"You said: {text}")
            response = ai_reply(text)
            st.session_state.history.append(("Sai Surya", response))
            audio_file = text_to_speech(response)
            show_audio(audio_file)
        else:
            st.error("Could not transcribe your voice! Try again.")

# Display chat history
with st.expander("Chat history", expanded=True):
    for who, msg in st.session_state.history:
        st.markdown(f"**{who}**: {msg}")

st.markdown("---")
st.markdown("No installation needed. Users just click, speak, and listen to the bot's reply!")

