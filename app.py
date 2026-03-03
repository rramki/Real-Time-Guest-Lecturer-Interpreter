import streamlit as st
from utils import transcribe_audio, translate_text
from pdf_generator import generate_pdf
import tempfile
import speech_recognition as sr

st.title("🎙 Multilingual Live Audio Translator")

language = st.selectbox(
    "Select Target Language",
    ["Tamil", "Hindi", "Telugu", "Kannada", "Malayalam"]
)

mode = st.radio("Choose Mode", ["Upload Audio", "Live Recording"])

recognized_text = ""

if mode == "Upload Audio":
    uploaded_file = st.file_uploader("Upload audio file", type=["wav", "mp3", "m4a"])

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        recognizer = sr.Recognizer()
        with sr.AudioFile(tmp_path) as source:
            audio_data = recognizer.record(source)
            recognized_text = recognizer.recognize_google(audio_data)

elif mode == "Live Recording":
    if st.button("Start Recording"):
        recognizer = sr.Recognizer()
        #with sr.Microphone() as source:
        st.write("Listening...")
        audio_data = recognizer.listen(source)
        recognized_text = recognizer.recognize_google(audio_data)

if recognized_text:
    st.subheader("📝 Transcription")
    st.write(recognized_text)

    translated = translate_text(recognized_text, language)

    st.subheader("🌍 Translation")
    #st.write(translated)
    st.markdown(
    f"""
    <div style='height:200px; overflow-y: scroll; border:1px solid gray; padding:10px'>
    {translated}
    </div>
    """,
    unsafe_allow_html=True
)

    pdf_file = generate_pdf(translated)

    with open(pdf_file, "rb") as f:
        st.download_button(
            label="📄 Download PDF",
            data=f,
            file_name="translated_text.pdf",
            mime="application/pdf"
        )
