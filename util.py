import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

def transcribe_audio(audio_text):
    """
    Since Claude does not directly process raw audio,
    you must first convert speech to text using Whisper or similar.
    Then send text to Claude for cleanup.
    """

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": f"Clean and correct this transcription:\n{audio_text}"}
        ]
    )
    return response.content[0].text


def translate_text(text, target_language):
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": f"Translate this English text into {target_language}:\n{text}"
            }
        ]
    )
    return response.content[0].text
