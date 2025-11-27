from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional

class Settings(BaseSettings):
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    ngrok_authtoken: Optional[str] = None

    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()
