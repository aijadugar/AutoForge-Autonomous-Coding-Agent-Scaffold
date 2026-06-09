import os
from dotenv import load_dotenv
load_dotenv()

from autoforge.llm.gemini import GeminiProvider

api_key = os.getenv("AUTOFORGE_GEMINI_API_KEY")

gemini = GeminiProvider(
    api_key=api_key
)