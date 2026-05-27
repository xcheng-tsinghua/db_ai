import logging
from openai import OpenAI, APIError, APIConnectionError
from app.config import settings

logger = logging.getLogger(__name__)

class QwenClient:
    def __init__(self):
        self._default_client = None
        self.model = settings.QWEN_MODEL

    def _get_default_client(self):
        if self._default_client is None:
            self._default_client = OpenAI(
                base_url=settings.QWEN_BASE_URL,
                api_key=settings.QWEN_API_KEY
            )
        return self._default_client

    def chat_completion(
        self, 
        messages: list[dict], 
        temperature: float | None = None, 
        max_tokens: int | None = None,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None
    ) -> str:
        # Resolve configuration values
        target_model = model if model is not None else self.model
        target_base_url = base_url if base_url is not None else settings.QWEN_BASE_URL
        target_api_key = api_key if api_key is not None else settings.QWEN_API_KEY
        
        temp = temperature if temperature is not None else settings.QWEN_TEMPERATURE
        tokens = max_tokens if max_tokens is not None else settings.QWEN_MAX_TOKENS
        
        # Mask api key in logging outputs
        masked_api_key = "None"
        if target_api_key:
            if target_api_key == "EMPTY":
                masked_api_key = "EMPTY"
            else:
                masked_api_key = target_api_key[:4] + "..." if len(target_api_key) > 4 else "..."
        
        try:
            logger.info(f"Calling LLM API model='{target_model}' at url='{target_base_url}' with key={masked_api_key}")
            
            # Recreate client on demand if overrides are provided
            if base_url is not None or api_key is not None:
                client = OpenAI(
                    base_url=target_base_url,
                    api_key=target_api_key
                )
            else:
                client = self._get_default_client()
                
            response = client.chat.completions.create(
                model=target_model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens
            )
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    return content.strip()
            raise RuntimeError("Error: Received empty response from model endpoint.")
        except APIConnectionError as e:
            logger.error(f"Cannot connect to model server at {target_base_url}: {e}")
            raise e
        except APIError as e:
            logger.error(f"Model endpoint returned API Error. Code: {e.code}, Message: {e.message}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected exception when calling model endpoint: {str(e)}")
            raise e

# Singleton instance
qwen_client = QwenClient()
