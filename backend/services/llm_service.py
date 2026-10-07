import logging
from app.config import settings

logger = logging.getLogger(__name__)


def get_llm(temperature: float = 0.0, max_tokens: int = 1024):
    if settings.llm_provider == "huggingface":
        return _get_hf_llm(temperature, max_tokens)
    return _get_gemini_llm(temperature)


def _get_hf_llm(temperature: float, max_tokens: int):
    from langchain_huggingface import ChatHuggingFace
    from langchain_huggingface import HuggingFaceEndpoint
    logger.info(f"Using HuggingFace LLM: {settings.hf_llm_model}")
    endpoint = HuggingFaceEndpoint(
        repo_id=settings.hf_llm_model,
        huggingfacehub_api_token=settings.hf_token,
        temperature=max(temperature, 0.01),
        max_new_tokens=max_tokens,
    )
    return ChatHuggingFace(llm=endpoint)


def _get_gemini_llm(temperature: float):
    from langchain_google_genai import ChatGoogleGenerativeAI
    logger.info(f"Using Gemini LLM: {settings.gemini_model}")
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=temperature,
    )