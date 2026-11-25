from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    MODEL_VERSION: str = "v1.0"
    # Comma-separated model versions whose predictions must not drive work orders.
    EXPERIMENTAL_MODEL_VERSIONS: str = "v2.0"

    @property
    def experimental_model_versions(self) -> frozenset[str]:
        return frozenset(v.strip() for v in self.EXPERIMENTAL_MODEL_VERSIONS.split(",") if v.strip())

    # This line tells Pydantic to load the variables from the .env file
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()