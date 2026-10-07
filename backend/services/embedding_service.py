import logging
from functools import lru_cache
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self._model = self._load_model()

    def _load_model(self):
        if settings.embedding_provider == "huggingface":
            return self._load_hf()
        else:
            return self._load_gemini()

    def _load_hf(self):
        from langchain_huggingface import HuggingFaceEmbeddings

        model_name = settings.hf_embedding_model
        logger.info(f"Loading local HuggingFace embeddings: {model_name}")

        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu", "local_files_only" : True},
            encode_kwargs={"normalize_embeddings": True},
        )

    def _load_gemini(self):
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        model_name = settings.gemini_embedding_model
        logger.info(f"Loading Gemini embeddings: {model_name}")
        return GoogleGenerativeAIEmbeddings(
            model=model_name,
            google_api_key=settings.google_api_key,
            task_type="retrieval_document",
            output_dimensionality=settings.gemini_embedding_dim,
        )

    @property
    def model(self):
        return self._model

    def embed_query(self, text: str) -> list:
        return self._model.embed_query(text)

    def embed_documents(self, texts: list) -> list:
        return self._model.embed_documents(texts)


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
