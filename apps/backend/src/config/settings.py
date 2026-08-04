from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "ARKON"
    app_version: str = "0.1.0"
    app_env: str = "development"
    log_level: str = "DEBUG"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "arkon"
    postgres_password: str = "arkon_dev_password"
    postgres_db: str = "arkon"
    database_url: str = ""

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_url: str = ""

    nats_host: str = "localhost"
    nats_port: int = 4222
    nats_url: str = ""

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_workers: int = 1
    backend_reload: bool = True

    cors_origins: list[str] = ["http://localhost:5173", "tauri://localhost"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    plugin_dir: str = "./plugins"
    plugin_auto_load: bool = True

    prometheus_port: int = 9090
    grafana_port: int = 3000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()