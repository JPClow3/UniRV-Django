"""
Custom static files storage for production.

Uses WhiteNoise's CompressedManifestStaticFilesStorage with manifest_strict=False
so that missing static files fall back to unhashed URLs instead of crashing with 500.
"""

from whitenoise.storage import CompressedManifestStaticFilesStorage


class ForgivingManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """Static files storage that doesn't crash on missing manifest entries.

    In production, if a {% static %} tag references a file not in the manifest
    (e.g., due to a build issue or a new file not yet collected), the default
    behaviour raises a ValueError which causes a 500 error.

    Setting manifest_strict = False makes it fall back to the unhashed URL,
    keeping the site functional while still providing cache-busting for every
    file that *is* in the manifest.
    """

    manifest_strict = False
