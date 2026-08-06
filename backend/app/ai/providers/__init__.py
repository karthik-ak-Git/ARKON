"""AI providers package."""

from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.gemini_cli import GeminiCLIProvider
from app.ai.providers.github_copilot import GitHubCopilotProvider
from app.ai.providers.nvidia_nim import NVIDIANIMProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openrouter import OpenRouterProvider
from app.ai.providers.opencode import OpenCodeProvider

__all__ = [
    "GeminiProvider",
    "GeminiCLIProvider",
    "GitHubCopilotProvider",
    "NVIDIANIMProvider",
    "OllamaProvider",
    "OpenRouterProvider",
    "OpenCodeProvider",
]
