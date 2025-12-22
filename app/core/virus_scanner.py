"""
Virus scanning integration for uploaded files.

Supports ClamAV for local scanning with graceful degradation if unavailable.
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import pyclamd

    CLAMAV_AVAILABLE = True
except ImportError:
    CLAMAV_AVAILABLE = False
    logger.warning("pyclamd not installed. Virus scanning disabled.")


class VirusScanner:
    """Virus scanner interface with graceful degradation"""

    def __init__(
        self, enabled: bool = False, host: str = "localhost", port: int = 3310
    ):
        """
        Initialize virus scanner.

        Args:
            enabled: Whether scanning is enabled
            host: ClamAV daemon host
            port: ClamAV daemon port
        """
        self.enabled = enabled and CLAMAV_AVAILABLE
        self.host = host
        self.port = port
        self.clamav = None

        if self.enabled:
            try:
                # Try to connect to ClamAV daemon
                self.clamav = pyclamd.ClamdNetworkSocket(host=host, port=port)

                # Test connection
                if not self.clamav.ping():
                    logger.warning(f"ClamAV daemon not responding at {host}:{port}")
                    self.enabled = False
                    self.clamav = None
                else:
                    logger.info("ClamAV virus scanner connected successfully")
            except Exception as e:
                logger.error(f"Failed to connect to ClamAV: {e}")
                self.enabled = False
                self.clamav = None

    def scan_bytes(
        self, file_bytes: bytes, filename: str = "file"
    ) -> Tuple[bool, Optional[str]]:
        """
        Scan file bytes for viruses.

        Args:
            file_bytes: File content as bytes
            filename: Original filename (for logging)

        Returns:
            Tuple of (is_safe, virus_name)
            - is_safe: True if file is safe (or scanning disabled)
            - virus_name: Name of detected virus, None if safe
        """
        if not self.enabled:
            # Scanning disabled - assume safe but log warning
            logger.debug(f"Virus scanning disabled - {filename} not scanned")
            return True, None

        try:
            # Scan the file content
            result = self.clamav.scan_stream(file_bytes)

            if result is None:
                # No virus found
                logger.debug(f"File {filename} scanned - clean")
                return True, None
            else:
                # Virus detected
                # Result format: {stream: ('FOUND', 'virus_name')}
                virus_info = result.get("stream", (None, None))
                virus_name = virus_info[1] if len(virus_info) > 1 else "Unknown"
                logger.warning(f"Virus detected in {filename}: {virus_name}")
                return False, virus_name

        except Exception as e:
            logger.error(f"Error scanning file {filename}: {e}")
            # On error, fail secure (reject file)
            return False, f"Scanning error: {str(e)}"

    def get_version(self) -> Optional[str]:
        """Get ClamAV version"""
        if not self.enabled or not self.clamav:
            return None

        try:
            return self.clamav.version()
        except Exception:
            return None


# Global scanner instance (initialized in main.py or on first use)
_scanner: Optional[VirusScanner] = None


def init_virus_scanner(
    enabled: bool = False, host: str = "localhost", port: int = 3310
) -> VirusScanner:
    """
    Initialize the global virus scanner instance.

    Args:
        enabled: Whether scanning is enabled
        host: ClamAV daemon host
        port: ClamAV daemon port

    Returns:
        VirusScanner instance
    """
    global _scanner
    _scanner = VirusScanner(enabled=enabled, host=host, port=port)
    return _scanner


def get_virus_scanner() -> VirusScanner:
    """
    Get the global virus scanner instance.

    Returns:
        VirusScanner instance (creates one if not initialized)
    """
    global _scanner
    if _scanner is None:
        _scanner = VirusScanner(enabled=False)
    return _scanner


def scan_file(file_bytes: bytes, filename: str = "file") -> Tuple[bool, Optional[str]]:
    """
    Convenience function to scan a file.

    Args:
        file_bytes: File content as bytes
        filename: Original filename

    Returns:
        Tuple of (is_safe, virus_name)
    """
    scanner = get_virus_scanner()
    return scanner.scan_bytes(file_bytes, filename)
