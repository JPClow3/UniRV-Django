"""
Limits and constraints constants.
"""

__all__ = [
    'PAGINATION_DEFAULT',
    'MAX_SEARCH_LENGTH',
    'MAX_STARTUPS_DISPLAY',
    'SLUG_GENERATION_MAX_RETRIES',
    'SLUG_GENERATION_MAX_ATTEMPTS_EDITAL',
    'SLUG_GENERATION_MAX_ATTEMPTS_PROJECT',
    'RATE_LIMIT_REQUESTS',
    'RATE_LIMIT_WINDOW',
    'DEADLINE_WARNING_DAYS',
]

# Pagination
PAGINATION_DEFAULT = 12

# Search and display limits
MAX_SEARCH_LENGTH = 500  # Maximum length for search queries
MAX_STARTUPS_DISPLAY = 100  # Maximum number of startups to display on showcase page

# Slug generation limits
SLUG_GENERATION_MAX_RETRIES = 3
SLUG_GENERATION_MAX_ATTEMPTS_EDITAL = 10000
SLUG_GENERATION_MAX_ATTEMPTS_PROJECT = 100

# Rate Limiting
RATE_LIMIT_REQUESTS = 5  # Number of requests allowed
RATE_LIMIT_WINDOW = 60  # Time window in seconds (1 minute)

# Prazos e alertas
DEADLINE_WARNING_DAYS = 7

