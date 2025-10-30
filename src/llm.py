from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
load_dotenv()


def init_llm_model(model: str, **kwargs):
    if model == "deepseek:deepseek-chat":
        return init_chat_model(
            model = model,
            temperature = kwargs.get("temperature", 1.5),
            max_tokens = kwargs.get("max_tokens", 8192),
            max_retries = kwargs.get("max_retries", 2),
            timeout = kwargs.get("timeout", 300.0)
        )
    elif model == "deepseek:deepseek-reasoner":
        return init_chat_model(
            model = model,
            temperature = kwargs.get("temperature", 1.5),
            max_tokens = kwargs.get("max_tokens", 65536),
            max_retries = kwargs.get("max_retries", 2),
            timeout = kwargs.get("timeout", 300.0)  
        )
    elif model.startswith("google_genai:"):
        return init_chat_model(
            model=model,
            temperature=kwargs.get("temperature", 1.5),
            max_tokens=kwargs.get("max_tokens", 65536),
            max_retries=kwargs.get("max_retries", 2),
            timeout=kwargs.get("timeout", 300.0),
            **kwargs,
        )
    else:
        raise ValueError(f"Model {model} not supported")