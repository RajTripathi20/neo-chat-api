"""
HTTP-related constants.

This module contains constants related to HTTP, such as status codes
and common headers.
"""

# HTTP Status Codes
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_PAYMENT_REQUIRED = 402
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_TOO_MANY_REQUESTS = 429
HTTP_INTERNAL_SERVER_ERROR = 500

# HTTP Headers
HEADER_PROCESS_TIME = "X-Process-Time"
HEADER_REQUEST_ID = "X-Request-ID" 