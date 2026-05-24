import logging
from openai import OpenAI, APIError, APIConnectionError
from app.config import settings

logger = logging.getLogger(__name__)

class QwenClient:
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.QWEN_BASE_URL,
            api_key=settings.QWEN_API_KEY
        )
        self.model = settings.QWEN_MODEL

    def chat_completion(
        self, 
        messages: list[dict], 
        temperature: float | None = None, 
        max_tokens: int | None = None
    ) -> str:
        temp = temperature if temperature is not None else settings.QWEN_TEMPERATURE
        tokens = max_tokens if max_tokens is not None else settings.QWEN_MAX_TOKENS
        
        try:
            logger.info(f"Calling Qwen API model='{self.model}' at url='{settings.QWEN_BASE_URL}'")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens
            )
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    return content.strip()
            return "Error: Received empty response from Qwen model endpoint."
        except APIConnectionError as e:
            err_msg = f"Error: Cannot connect to Qwen model server at {settings.QWEN_BASE_URL}. Connection refused or server is down. Details: {e}"
            logger.error(err_msg)
            return err_msg
        except APIError as e:
            err_msg = f"Error: Qwen model endpoint returned API Error. Code: {e.code}, Message: {e.message}"
            logger.error(err_msg)
            return err_msg
        except Exception as e:
            err_msg = f"Error: Unexpected exception when calling Qwen model endpoint. Details: {str(e)}"
            logger.error(err_msg)
            return err_msg

# Singleton instance
qwen_client = QwenClient()
