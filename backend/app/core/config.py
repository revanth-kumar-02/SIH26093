import os
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# Search and load .env from backend directory, then workspace root
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
root_dir = os.path.abspath(os.path.join(backend_dir, ".."))
load_dotenv(os.path.join(backend_dir, ".env"))
load_dotenv(os.path.join(root_dir, ".env"))

DEFAULT_SQLITE_PATH = os.path.abspath(os.path.join(backend_dir, "responder.db")).replace("\\", "/")

class Settings(BaseModel):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "SIH26093 NHAA Stress Assessment Backend"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "*"
    ]
    
    # Database Configuration (PostgreSQL 18 + psycopg 3)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+psycopg://sih_app:sih26093@localhost:5432/sih26093"
    )
    POSTGRES_DEFAULT_URL: str = os.getenv(
        "POSTGRES_DEFAULT_URL",
        "postgresql+psycopg://sih_app:sih26093@localhost:5432/sih26093"
    )
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@localhost")
    ADMIN_PASSWORD: Optional[str] = os.getenv("ADMIN_PASSWORD") or os.getenv("ADMIN_SEED_PASSWORD")
    PEOPLE_EMAIL: str = os.getenv("PEOPLE_EMAIL", "people@localhost")
    PEOPLE_PASSWORD: Optional[str] = os.getenv("PEOPLE_PASSWORD") or os.getenv("PEOPLE_SEED_PASSWORD")
    
    # Supabase Auth Configuration (Supabase Auth used exclusively for authentication & email verification)
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_JWT_SECRET: str = os.getenv(
        "SUPABASE_JWT_SECRET", 
        os.getenv("JWT_SECRET_KEY", "sih26093-secure-responder-jwt-secret-key-change-in-production")
    )
    
    # Responder Authentication & JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "sih26093-secure-responder-jwt-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # ASR Settings - LOCKED: ai4bharat/indic-conformer-600m-multilingual
    ASR_MODEL_NAME: str = os.getenv("ASR_MODEL_NAME", "ai4bharat/indic-conformer-600m-multilingual")
    ASR_DECODER: str = os.getenv("ASR_DECODER", "ctc")  # 'ctc' or 'rnnt'
    ASR_DEVICE: str = os.getenv("ASR_DEVICE", "cpu")
    USE_MOCK_ASR: bool = os.getenv("USE_MOCK_ASR", "false").lower() == "true"
    HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
    MAX_AUDIO_BYTES: int = 15 * 1024 * 1024
    
    # Emotion Analysis Settings
    SPEECH_EMOTION_MODEL: str = os.getenv("SPEECH_EMOTION_MODEL", "Dpngtm/wav2vec2-emotion-recognition")
    TEXT_EMOTION_MODEL: str = os.getenv("TEXT_EMOTION_MODEL", "SamLowe/roberta-base-go_emotions")
    EMOTION_DEVICE: str = os.getenv("EMOTION_DEVICE", "cpu")
    USE_MOCK_EMOTION: bool = os.getenv("USE_MOCK_EMOTION", "false").lower() == "true"

    # Stress Detection Settings - MentalBERT fine-tuned on Dreaddit Reddit Dataset
    STRESS_MODEL_NAME: str = os.getenv("STRESS_MODEL_NAME", "jtvallente/mentalbert_dreaddit_best")
    STRESS_DEVICE: str = os.getenv("STRESS_DEVICE", "cpu")
    USE_MOCK_STRESS: bool = os.getenv("USE_MOCK_STRESS", "false").lower() == "true"

    # Application Memory Settings
    MEMORY_MAX_CONTEXT_WORDS: int = int(os.getenv("MEMORY_MAX_CONTEXT_WORDS", "350"))
    MEMORY_MAX_PREVIOUS_SESSIONS: int = int(os.getenv("MEMORY_MAX_PREVIOUS_SESSIONS", "3"))

    # Local Gemma 3 12B IT LLM Assessment & Chat Settings (Local Inference via Ollama / llama.cpp)
    GEMMA_PROVIDER: str = os.getenv("GEMMA_PROVIDER", "local")
    GEMMA_MODEL: str = os.getenv("GEMMA_MODEL", os.getenv("GEMMA_MODEL_ID", "gemma3:12b"))
    GEMMA_MODEL_ID: str = os.getenv("GEMMA_MODEL_ID", os.getenv("GEMMA_MODEL", "gemma3:12b"))
    GEMMA_RUNTIME: str = os.getenv("GEMMA_RUNTIME", "ollama")
    GEMMA_BASE_URL: str = os.getenv("GEMMA_BASE_URL", "http://127.0.0.1:11434")
    GEMMA_CONTEXT_LENGTH: int = int(os.getenv("GEMMA_CONTEXT_LENGTH", "4096"))
    GEMMA_TIMEOUT_SECONDS: float = float(os.getenv("GEMMA_TIMEOUT_SECONDS", "180.0"))
    GEMMA_DEVICE: str = os.getenv("GEMMA_DEVICE", "cpu")
    USE_MOCK_GEMMA: bool = os.getenv("USE_MOCK_GEMMA", "false").lower() == "true"
    AI_ALLOW_FALLBACK: bool = os.getenv("AI_ALLOW_FALLBACK", "false").lower() == "true"
    GEMMA_MAX_NEW_TOKENS: int = int(os.getenv("GEMMA_MAX_NEW_TOKENS", "512"))
    GEMMA_TEMPERATURE: float = float(os.getenv("GEMMA_TEMPERATURE", "0.65"))

settings = Settings()
