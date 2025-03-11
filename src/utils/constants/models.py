"""
Model-related constants.

This module contains constants related to AI models, such as default parameters,
model IDs, and available models.
"""

# Default Model Parameters
DEFAULT_MODEL = "neo-large"
DEFAULT_MAX_TOKENS = 1000
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 1.0
DEFAULT_N = 1
DEFAULT_STREAM = False
DEFAULT_PRESENCE_PENALTY = 0.0
DEFAULT_FREQUENCY_PENALTY = 0.0

# Reasoning Model Constants
REASONING_MODEL_ID = "neo-reasoning"
DEFAULT_INCLUDE_REASONING = True
DEFAULT_REASONING_EFFORT = "medium"
VALID_REASONING_EFFORTS = ["high", "medium", "low"]

# OpenRouter Model Mappings
OPENROUTER_GENERAL_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
OPENROUTER_REASONING_MODELS = {
    "high": "deepseek/deepseek-r1:free",  # Supports include_reasoning
    "medium": "deepseek/deepseek-r1-distill-llama-70b:free",
    "low": "qwen/qwq-32b:free"
}

# Model Information
AVAILABLE_MODELS = [
    {
        "id": "neo-reasoning",
        "name": "Neo Reasoning",
        "description": "A powerful open source reasoning model for complex tasks.",
        "input_price_per_million_tokens": 0.55,
        "output_price_per_million_tokens": 2.4,
        "context_length": 128000
    },
    {
        "id": "neo-large",
        "name": "Neo Large",
        "description": "A large open source model for general-purpose tasks.",
        "input_price_per_million_tokens": 1.0,
        "output_price_per_million_tokens": 3.0,
        "context_length": 128000
    }
] 