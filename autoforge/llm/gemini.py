from google import genai
from autoforge.llm.base import LLMProvider

class GeminiProvider(LLMProvider):

    def __init__(self, api_key:str):
        self.client = genai.Client(
            api_key=api_key
        )

    def generate(
        self,
        prompt:str,
        system:str=""
    ) -> str:

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system}\n\n{prompt}"
        )

        return response.text