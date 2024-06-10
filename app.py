import streamlit as st
import requests
from pytube import YouTube
import tempfile
import os
from fpdf import FPDF
from docx import Document
from groq import Groq

# Function to transcribe audio using Deepgram API
def transcribe_audio_deepgram(audio_path, api_key):
    api_url = "https://api.deepgram.com/v1/listen"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "audio/wav"  # Adjust according to your audio file type
    }

    with open(audio_path, "rb") as audio_file:
        response = requests.post(api_url, headers=headers, data=audio_file)

    if response.status_code == 200:
        transcription = response.json().get('results', {}).get('channels', [])[0].get('alternatives', [])[0].get('transcript')
        return transcription
    else:
        st.error(f"Failed to transcribe audio: {response.status_code} {response.text}")
        return ""

# Function to generate notes using OpenAI API
def generate_notes(transcription, api_key):
    client = Groq(api_key=api_key)
    prompt = f"Generate detailed lecture notes and after the notes at the end of the notes, generate a structured document containing discussed topics with associated timestamps from the following transcription:\n\n{transcription}"
    response = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# Function to generate quiz using OpenAI API
def generate_quiz(transcription, num_questions, api_key):
    client = Groq(api_key=api_key)
    prompt = f"Generate {num_questions} multiple-choice questions with answers given at the end for all the questions from the following transcription:\n\n{transcription}"
    response = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# Function to download audio from YouTube video
def download_youtube_audio(youtube_url):
    yt = YouTube(youtube_url)
    stream = yt.streams.filter(only_audio=True).first()
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, "audio.mp4")
    stream.download(output_path=temp_dir, filename="audio.mp4")
    return temp_file_path

# Function to create a PDF file
def create_pdf(text, file_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, text)
    pdf.output(file_name)

# Function to create a Word document
def create_word_doc(text, file_name):
    doc = Document()
    doc.add_paragraph(text)
    doc.save(file_name)

# Function to render the homepage
def render_homepage():
    st.title("AI-Powered Teaching Assistant")
    st.write("Welcome to the AI-powered teaching assistant. This tool helps you generate lecture notes and quizzes from audio recordings and YouTube videos.")

# Function to handle file uploads and YouTube URL inputs for lecture notes
def render_notes_inputs():
    st.header("Upload Lecture Recording or Enter YouTube Video URL")
    audio_file = st.file_uploader("Upload your lecture audio file", type=["mp3", "wav", "m4a"], key="notes_audio")
    youtube_url = st.text_input("Paste YouTube video URL here", key="notes_youtube_url")
    return audio_file, youtube_url

# Function to handle file uploads and YouTube URL inputs for quiz generation
def render_quiz_inputs():
    st.header("Upload Lecture Recording or Enter YouTube Video URL")
    audio_file = st.file_uploader("Upload your lecture audio file", type=["mp3", "wav", "m4a"], key="quiz_audio")
    youtube_url = st.text_input("Paste YouTube video URL here", key="quiz_youtube_url")
    return audio_file, youtube_url

# Function to render the lecture notes generation page
def render_lecture_notes_page():
    st.title("Lecture Notes Generation")

    # Input section
    audio_file, youtube_url = render_notes_inputs()

    # Settings section
    st.header("Upload Lesson Plan (Optional)")
    lesson_plan_file = st.file_uploader("Upload your lesson plan document", type=["pdf", "docx", "txt"], key="notes_lesson_plan")

    # API key inputs
    st.header("API Keys")
    deepgram_api_key = st.text_input("Enter your Deepgram API Key", type="password", key="deepgram_api_key")
    openai_api_key = st.text_input("Enter your Groq API Key", type="password", key="openai_api_key")

    # Transcription and Notes generation section
    if st.button("Generate Notes"):
        if deepgram_api_key and openai_api_key:
            if audio_file:
                st.success("Processing the audio file...")
                # Save the uploaded file temporarily
                audio_path = f"temp_audio.{audio_file.name.split('.')[-1]}"
                with open(audio_path, "wb") as f:
                    f.write(audio_file.getbuffer())

                # Generate the transcription using Deepgram API
                transcription_output = transcribe_audio_deepgram(audio_path, deepgram_api_key)

                # Generate the notes using Groq API
                if transcription_output:
                    notes_output = generate_notes(transcription_output, openai_api_key)
                    st.text_area("Generated Notes", notes_output, height=300)

                    # Download options
                    st.download_button("Download Notes as TXT", notes_output, file_name="lecture_notes.txt")
                    pdf_file = f"lecture_notes.pdf"
                    create_pdf(notes_output, pdf_file)
                    with open(pdf_file, "rb") as f:
                        st.download_button("Download Notes as PDF", f, file_name=pdf_file)
                    word_file = f"lecture_notes.docx"
                    create_word_doc(notes_output, word_file)
                    with open(word_file, "rb") as f:
                        st.download_button("Download Notes as Word Document", f, file_name=word_file)

            elif youtube_url:
                st.success("Processing the YouTube video...")
                audio_path = download_youtube_audio(youtube_url)
                if audio_path:
                    transcription_output = transcribe_audio_deepgram(audio_path, deepgram_api_key)
                    if transcription_output:
                        notes_output = generate_notes(transcription_output, openai_api_key)
                        st.text_area("Generated Notes", notes_output, height=300)

                        # Download options
                        st.download_button("Download Notes as TXT", notes_output, file_name="lecture_notes.txt")
                        pdf_file = f"lecture_notes.pdf"
                        create_pdf(notes_output, pdf_file)
                        with open(pdf_file, "rb") as f:
                            st.download_button("Download Notes as PDF", f, file_name=pdf_file)
                        word_file = f"lecture_notes.docx"
                        create_word_doc(notes_output, word_file)
                        with open(word_file, "rb") as f:
                            st.download_button("Download Notes as Word Document", f, file_name=word_file)
                else:
                    st.error("Failed to download YouTube video.")
            else:
                st.error("Please upload an audio file or enter a YouTube URL.")
        else:
            st.error("Please enter both Deepgram and Groq API keys.")

# Function to render the quiz generation page
def render_quiz_generation_page():
    st.title("Quiz Generation")

    # Input section
    audio_file, youtube_url = render_quiz_inputs()

    # Settings section
    st.header("Settings")
    num_questions = st.slider("Number of questions to generate", min_value=5, max_value=20, value=10, key="quiz_num_questions")

    # API key inputs
    st.header("API Keys")
    deepgram_api_key = st.text_input("Enter your Deepgram API Key", type="password", key="deepgram_api_key")
    openai_api_key = st.text_input("Enter your Groq API Key", type="password", key="openai_api_key")

    # Transcription and Quiz generation section
    if st.button("Generate Quiz"):
        if deepgram_api_key and openai_api_key:
            if audio_file:
                st.success("Processing the audio file...")
                # Save the uploaded file temporarily
                audio_path = f"temp_audio.{audio_file.name.split('.')[-1]}"
                with open(audio_path, "wb") as f:
                    f.write(audio_file.getbuffer())

                # Generate the transcription using Deepgram API
                transcription_output = transcribe_audio_deepgram(audio_path, deepgram_api_key)

                # Generate the quiz using Groq API
                if transcription_output:
                    quiz_output = generate_quiz(transcription_output, num_questions, openai_api_key)
                    st.text_area("Generated Quiz", quiz_output, height=300)

                    # Download options
                    st.download_button("Download Quiz as TXT", quiz_output, file_name="quiz.txt")
                    pdf_file = f"quiz.pdf"
                    create_pdf(quiz_output, pdf_file)
                    with open(pdf_file, "rb") as f:
                        st.download_button("Download Quiz as PDF", f, file_name=pdf_file)
                    word_file = f"quiz.docx"
                    create_word_doc(quiz_output, word_file)
                    with open(word_file, "rb") as f:
                        st.download_button("Download Quiz as Word Document", f, file_name=word_file)

            elif youtube_url:
                st.success("Processing the YouTube video...")
                audio_path = download_youtube_audio(youtube_url)
                if audio_path:
                    transcription_output = transcribe_audio_deepgram(audio_path, deepgram_api_key)
                    if transcription_output:
                        quiz_output = generate_quiz(transcription_output, num_questions, openai_api_key)
                        st.text_area("Generated Quiz", quiz_output, height=300)

                        # Download options
                        st.download_button("Download Quiz as TXT", quiz_output, file_name="quiz.txt")
                        pdf_file = f"quiz.pdf"
                        create_pdf(quiz_output, pdf_file)
                        with open(pdf_file, "rb") as f:
                            st.download_button("Download Quiz as PDF", f, file_name=pdf_file)
                        word_file = f"quiz.docx"
                        create_word_doc(quiz_output, word_file)
                        with open(word_file, "rb") as f:
                            st.download_button("Download Quiz as Word Document", f, file_name=word_file)
                else:
                    st.error("Failed to download YouTube video.")
            else:
                st.error("Please upload an audio file or enter a YouTube URL.")
        else:
            st.error("Please enter both Deepgram and Groq API keys.")

# Function to render the footer
def render_footer():
    st.markdown("---")
    st.write("© 2024 AI-Powered Teaching Assistant")

# Main function to run the app
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "Lecture Notes", "Quiz Generation"])

    if page == "Home":
        render_homepage()
    elif page == "Lecture Notes":
        render_lecture_notes_page()
    elif page == "Quiz Generation":
        render_quiz_generation_page()

    render_footer()

if __name__ == "__main__":
    main()
