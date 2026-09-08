import os
import shutil
import stat
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional


class FilesystemAdapter:
    """Filesystem operations resilient to Windows/cloud-sync locks."""

    _RMTREE_HANDLER_KEYWORD: str = (
        "onexc" if sys.version_info >= (3, 12) else "onerror"
    )

    @staticmethod
    def _clear_readonly_and_retry(
        function: Callable[[str], Any],
        path: str,
        exc_info: Any,
    ) -> None:
        """Drop the read-only bit and retry the failing rmtree operation."""
        del exc_info
        os.chmod(path, stat.S_IWRITE)
        function(path)

    @classmethod
    def remove_directory_tree(
        cls,
        path: Path,
        *,
        attempts: int = 5,
        initial_delay_seconds: float = 0.3,
    ) -> None:
        """Remove a directory tree while tolerating transient file locks."""
        last_error: Optional[OSError] = None
        attempt: int
        for attempt in range(attempts):
            try:
                shutil.rmtree(
                    path,
                    **{
                        cls._RMTREE_HANDLER_KEYWORD:
                        cls._clear_readonly_and_retry
                    },
                )
                return
            except OSError as error:
                last_error = error
                if attempt < attempts - 1:
                    time.sleep(initial_delay_seconds * (attempt + 1))

        raise OSError(
            f"Could not remove {path}: still in use after {attempts} attempts. "
            "This is commonly a cloud-sync client (OneDrive, Dropbox, etc.) "
            "briefly holding a file handle open -- wait a moment and retry."
        ) from last_error

    @staticmethod
    def remove_file(
        path: Path,
        *,
        attempts: int = 5,
        initial_delay_seconds: float = 0.3,
    ) -> None:
        """Remove a file while tolerating read-only and transient locks."""
        last_error: Optional[OSError] = None
        attempt: int
        for attempt in range(attempts):
            try:
                path.unlink()
                return
            except FileNotFoundError:
                return
            except PermissionError as error:
                last_error = error
                try:
                    os.chmod(path, stat.S_IWRITE)
                    path.unlink()
                    return
                except FileNotFoundError:
                    return
                except OSError as retry_error:
                    last_error = retry_error
            except OSError as error:
                last_error = error

            if attempt < attempts - 1:
                time.sleep(initial_delay_seconds * (attempt + 1))

        raise OSError(
            f"Could not remove {path}: still in use after {attempts} attempts. "
            "This is commonly a cloud-sync client (OneDrive, Dropbox, etc.) "
            "briefly holding a file handle open -- wait a moment and retry."
        ) from last_error
