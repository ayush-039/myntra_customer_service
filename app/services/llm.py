from pipecat.services.openai.llm import OpenAILLMService
from app.config.settings import settings
from app.config.prompts import SYSTEM_PROMPT

def get_llm():
    return OpenAILLMService(
        api_key=settings.OPENAI_API_KEY,
        model="gpt-4o-mini",
        system_prompt=SYSTEM_PROMPT
    )