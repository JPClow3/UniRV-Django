"""
Limits and constraints constants.
"""

# Pagination
PAGINATION_DEFAULT = 12

# Search and display limits
MAX_SEARCH_LENGTH = 500  # Maximum length for search queries
MAX_STARTUPS_DISPLAY = 100  # Maximum number of startups to display on showcase page

# Slug generation limits
SLUG_GENERATION_MAX_RETRIES = 3
SLUG_GENERATION_MAX_ATTEMPTS_EDITAL = 10000  # Safety limit for Edital slug generation
SLUG_GENERATION_MAX_ATTEMPTS_PROJECT = 100  # Safety limit for Project slug generation

# Rate Limiting
RATE_LIMIT_REQUESTS = 5  # Number of requests allowed
RATE_LIMIT_WINDOW = 60  # Time window in seconds (1 minute)

# Prazos e alertas
DEADLINE_WARNING_DAYS = 7

