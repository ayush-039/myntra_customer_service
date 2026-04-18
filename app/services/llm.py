from pipecat.services.openai.llm import OpenAILLMService
from app.config.settings import settings
# ✅ Conversation memory
# conversation = [
#     {
#         "role": "system",
#         "content": """You are a Myntra Customer Support Voice Agent.

#     You help users with:
#     - order tracking
#     - returns & refunds
#     - product queries

#     Speak in a friendly, short, and helpful tone.
#     Always ask follow-up questions."""
#         }
#     ]

def get_llm():    
    return OpenAILLMService(
        api_key=settings.OPENAI_API_KEY,
        settings=OpenAILLMService.Settings(
            model="gpt-4.1-mini"
        ),
    )