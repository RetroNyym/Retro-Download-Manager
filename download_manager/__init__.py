"""Retro+ Download Manager — çok parçalı indirme modülü."""

from .engine import (
    CANCELED,
    COMPLETED,
    DOWNLOADING,
    ERROR,
    PAUSED,
    PROBING,
    QUEUED,
    SCHEDULED,
    STATE_LABELS,
    DownloadTask,
    RateLimiter,
)
from .manager import DownloadManager, Settings, extract_links, is_file_link
from .util import (
    CATEGORIES,
    CATEGORY_LABELS,
    DEFAULT_CATEGORY_FOLDERS,
    detect_category,
    format_bytes,
    format_eta,
    format_speed,
)

__version__ = "1.1.0"
__all__ = [
    "DownloadManager", "DownloadTask", "Settings", "RateLimiter",
    "CATEGORIES", "CATEGORY_LABELS", "DEFAULT_CATEGORY_FOLDERS", "STATE_LABELS",
    "QUEUED", "SCHEDULED", "PROBING", "DOWNLOADING", "PAUSED", "COMPLETED",
    "ERROR", "CANCELED",
    "detect_category", "extract_links", "is_file_link",
    "format_bytes", "format_speed", "format_eta",
    "__version__",
]
