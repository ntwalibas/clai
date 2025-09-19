from pydantic_settings import BaseSettings, SettingsConfigDict
from zenml.client import Client
from zenml.exceptions import EntityExistsError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # MongoDB database
    MONGO_DATABASE_HOST: str = "mongodb://clai:clai@127.0.0.1:27017"
    MONGO_DATABASE_NAME: str = "clai"

    # Qdrant vector database
    QDRANT_CLIENT_URL: str = "http://127.0.0.1:6333"
    QDRANT_COLLECTION_NAME: str = "clai"
    QDRANT_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # PostgreSQL database
    POSTGRES_USER: str = "clai"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DATABASE: str = "postgres"
    MLFLOW_DATABASE: str = "clai_mlflow"
    MLFLOW_USERNAME: str = ""
    MLFLOW_PASSWORD: str = ""
    MLFLOW_TRACKING_URI: str = ""

    # DSPy
    LLM_NAME: str = "ollama_chat/llama3.1:latest"
    LLM_ENDPOINT: str = "http://localhost:11434"

    @classmethod
    def load_settings(cls) -> "Settings":
        """
        Tries to load the settings from the ZenML secret store.
        If the secret does not exist, it initializes the settings from the .env file and default values.

        Returns:
            Settings: The initialized settings object.
        """

        try:
            settings_secrets = Client().get_secret("settings")
            settings = Settings(**settings_secrets.secret_values)
        except (RuntimeError, KeyError):
            settings = Settings()

        return settings

    def export(self) -> bool:
        """
        Exports the settings to the ZenML secret store.
        """

        env_vars = settings.model_dump()
        for key, value in env_vars.items():
            env_vars[key] = str(value)

        client = Client()

        try:
            return bool(client.create_secret(name="settings", values=env_vars))
        except EntityExistsError:
            return False

    def drop(self) -> bool:
        """
        Deletes the settings from the ZenML secret store.
        """

        client = Client()

        secret_name = "settings"
        secrets = [s.name for s in client.list_secrets()]

        if secret_name in secrets:
            return not client.delete_secret(secret_name)
        else:
            return False


settings = Settings.load_settings()
