"""
API-related constants.

This module contains constants related to the API, such as version, title,
description, endpoints, and response formats.
"""

# API Version and Metadata
API_VERSION = "v1"
API_PREFIX = f"/{API_VERSION}"
API_TITLE = "Neo-Chat AI Orchestration Layer"
API_DESCRIPTION = "OpenAI-compatible API with enterprise features"
API_VERSION_NUMBER = "0.1.0"

# Endpoint Paths
HEALTH_CHECK_PATH = "/health"
CHAT_COMPLETIONS_PATH = "/chat/completions"
MODELS_PATH = "/models"

# Response Constants
STREAM_END_MARKER = "data: [DONE]\n\n"
CHAT_COMPLETION_OBJECT = "chat.completion"
CHAT_COMPLETION_CHUNK_OBJECT = "chat.completion.chunk"
MODELS_LIST_OBJECT = "list"

# Rate Limiting Constants
DEFAULT_RATE_LIMIT = 60  # requests per minute
DEFAULT_BURST_LIMIT = 10  # concurrent requests 