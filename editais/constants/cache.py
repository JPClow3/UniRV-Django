"""
Cache-related constants.
"""

__all__ = [
    'CACHE_TTL_INDEX',
    'CACHE_TTL_5_MINUTES',
    'CACHE_TTL_15_MINUTES',
    'CACHE_FALLBACK_PAGE_RANGE',
]

# Cache TTLs (Time To Live in seconds)
CACHE_TTL_INDEX = 300  # 5 minutes in seconds
CACHE_TTL_5_MINUTES = 300  # 5 minutes in seconds
CACHE_TTL_15_MINUTES = 900  # 15 minutes in seconds

# Cache fallback settings
CACHE_FALLBACK_PAGE_RANGE = 10  # Number of pages to clear in cache fallback

