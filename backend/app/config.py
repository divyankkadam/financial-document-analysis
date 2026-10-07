from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    hf_token:           str   = ""
    hf_llm_model:       str   = ""
    hf_embedding_model: str   = "BAAI/bge-large-en-v1.5"

    llm_provider:       str   = "gemini"   # "huggingface" | "gemini"
    embedding_provider: str   = "huggingface"

    google_api_key:          str   = ""
    gemini_model:            str   = "gemini-2.5-flash"
    gemini_embedding_model:  str   = "gemini-embedding-001"
    gemini_embedding_dim:    int   = 768

    vectorstore_provider:    str   = "neo4j"
    embedding_dimension:     int   = 1024
    neo4j_uri:               str   = "bolt://localhost:7687"
    neo4j_user:              str   = "neo4j"
    neo4j_password:          str   = "financial-report-analyst"
    neo4j_database:          str   = "neo4j"

    chunk_size:              int   = 800
    chunk_overlap:           int   = 150

    # one retry is enough, more just burns latency on an already weak draft
    max_retries:            int   = 1
    confidence_threshold:     float = 0.5

    upload_dir:              str   = "data/uploads"
    max_upload_mb:           int   = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
