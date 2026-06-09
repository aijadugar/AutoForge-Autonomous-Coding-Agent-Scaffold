from autoforge.config import get_settings
from autoforge.llm.gemini import GeminiProvider

def get_llm():

    settings = get_settings()

    return GeminiProvider(
        api_key=settings.GEMINI_API_KEY
    )