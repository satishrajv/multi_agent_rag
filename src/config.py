"""
Configuration management for Multi-Agent RAG system
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False
    )

    # LLM Settings
    llm_provider: Literal['ollama', 'openai'] = 'ollama'
    llm_model: str = 'llama3.1'
    llm_temperature: float = 0.7
    openai_api_key: str = ''

    # Embedding Settings
    embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2'
    embedding_dimension: int = 384

    # Vector Store
    vector_store_type: Literal['chromadb', 'qdrant', 'weaviate'] = 'chromadb'
    vector_store_path: str = './data/vector_store'

    # Weaviate Settings
    weaviate_cluster_url: str = ''
    weaviate_grpc_url: str = ''
    weaviate_api_key: str = ''
    weaviate_cluster_name: str = ''

    # Database
    postgres_host: str = 'localhost'
    postgres_port: int = 5432
    postgres_db: str = 'multi_agent_rag'
    postgres_user: str = 'admin'
    postgres_password: str = 'password'

    # Redis
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_password: str = ''

    # RAG Settings
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_retrieval: int = 5
    hybrid_dense_weight: float = 0.7
    hybrid_sparse_weight: float = 0.3

    # Agent Settings
    sales_risk_threshold: float = 0.85
    delivery_risk_threshold: float = 0.80

    # Auto-Training
    auto_training_enabled: bool = True
    training_schedule: str = '0 2 * * 0'
    ab_test_percentage: float = 0.1

    # MLflow
    mlflow_tracking_uri: str = './mlruns'
    mlflow_experiment_name: str = 'multi_agent_rag'

    @property
    def postgres_url(self) -> str:
        """Generate PostgreSQL connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def redis_url(self) -> str:
        """Generate Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"


# Global settings instance
settings = Settings()
