import os
from dotenv import load_dotenv
from groq import Groq
from llm.groq_client import ask_llm

# Load .env file
load_dotenv()

# Read API Key
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found. Please add it to your .env file."
    )

# Create Groq client
client = Groq(api_key=API_KEY)


def ask_llm(prompt: str) -> str:
    """
    Send a prompt to Groq and return the response text.
    """

    try:

        response = client.chat.completions.create(

            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert technical interviewer. "
                        "Always follow the user's instructions exactly. "
                        "If JSON is requested, return ONLY valid JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.7,

            max_tokens=1024

        )

        return response.choices[0].message.content.strip()

    except Exception as e:

        print(f"Groq API Error: {e}")

        return ""