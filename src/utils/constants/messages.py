"""
Message-related constants.

This module contains constants related to chat messages, such as
role types, default messages, and finish reasons.
"""

# Message Roles
ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_SYSTEM = "system"

# Default Messages
DEFAULT_USER_MESSAGE = "Say something non-trivially fascinating!"

# Response Finish Reasons
FINISH_REASON_STOP = "stop"
FINISH_REASON_LENGTH = "length"
FINISH_REASON_CONTENT_FILTER = "content_filter" 