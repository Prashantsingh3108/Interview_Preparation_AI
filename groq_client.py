import os
import logging
from llm.groq_client import ask_llm
from groq import Groq

# Initialize the Groq SDK client. 
# It will automatically look for the GROQ_API_KEY environment variable.
try:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
except Exception as e:
    logging.critical(f"Failed to initialize Groq client. Check your GROQ_API_KEY environment variable. Error: {e}")
    client = None

# Production-grade open-weights model hosted on Groq
DEFAULT_MODEL = "llama-3.3-70b-versatile"

def ask_llm(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """
    Sends a string prompt to the Groq API and returns the raw string response.
    
    Args:
        prompt (str): The structured string message/instructions for the LLM.
        model (str): The model ID to handle inference. Defaults to llama-3.3-70b-versatile.
        
    Returns:
        str: Raw text output or stringified JSON payload from the assistant.
    """
    if not client:
        logging.error("Groq client is uninitialized. Returning empty fallback context.")
        return "{}"
        
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model,
            temperature=0.2,  # Low temperature guarantees tighter adherence to JSON instructions
        )
        
        # Safely extract the generated content text block
        if chat_completion.choices and chat_completion.choices[0].message.content:
            return chat_completion.choices[0].message.content.strip()
            
        return "{}"

    except Exception as e:
        logging.error(f"Groq API Inference Call Failed: {e}")
        return "{}"
