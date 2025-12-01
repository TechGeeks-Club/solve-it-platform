"""
Configuration for Judge Microservice using Pydantic Settings
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings with validation and type safety"""

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="localhost:9092",
        description="Comma-separated list of Kafka bootstrap servers",
    )
    KAFKA_SUBMISSION_TOPIC: str = Field(
        default="code-submissions", description="Kafka topic for incoming submissions"
    )
    KAFKA_RESULT_TOPIC: str = Field(
        default="code-results", description="Kafka topic for submission results"
    )

    # Judge0 Configuration
    JUDGE0_API_URL: str = Field(
        default="http://localhost:2358", description="Judge0 API endpoint URL"
    )
    JUDGE0_TIMEOUT: int = Field(
        default=30, ge=1, le=300, description="Judge0 API timeout in seconds"
    )

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, ge=1, le=65535, description="Redis port")
    REDIS_DB: int = Field(default=0, ge=0, le=15, description="Redis database number")
    REDIS_CACHE_TTL: int = Field(
        default=3600, ge=60, description="Redis cache TTL in seconds (1 hour default)"
    )

    # Database Configuration
    DB_HOST: str = Field(default="localhost", description="PostgreSQL host")
    DB_PORT: int = Field(default=5432, ge=1, le=65535, description="PostgreSQL port")
    DB_NAME: str = Field(default="solveitdb", description="Database name")
    DB_USER: str = Field(default="solveit", description="Database user")
    DB_PASSWORD: str = Field(default="solveit123", description="Database password")

    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    @field_validator("KAFKA_BOOTSTRAP_SERVERS")
    @classmethod
    def validate_kafka_servers(cls, v: str) -> List[str]:
        """Convert comma-separated string to list"""
        if isinstance(v, str):
            return [server.strip() for server in v.split(",")]
        return v

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @property
    def database_url(self) -> str:
        """Generate PostgreSQL connection URL"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def redis_url(self) -> str:
        """Generate Redis connection URL"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


# Create global settings instance
settings = Settings()
