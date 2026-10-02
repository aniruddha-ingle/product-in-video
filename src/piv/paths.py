"""The only place storage paths come from.

Configuration is by environment variables only, read at call time (so a job's env decides,
and tests can point everything at a temp dir):

- ``PIV_HOME`` (default ``~/.piv``): ours to write. Subdirs: runs, scratch, templates,
  fonts, models.
- ``CUTOUT_HOME`` (default ``~/.cutout``): copy-in-product-picture's catalogue, templates,
  fonts and copy bank. **Read-only**: nothing here ever writes under it, and
  :func:`writable` refuses any path inside it.

Nothing is created on import. :func:`ensure_dir` creates directories, and only under
``PIV_HOME``. Later this module becomes a storage interface (local disk now, a bucket in the
cloud); callers already go through it, so that is a change in one place.
"""

from __future__ import annotations

import os
from pathlib import Path

PIV_SUBDIRS = ("runs", "scratch", "templates", "fonts", "models")


class ReadOnlyPathError(PermissionError):
    """A write was attempted under a read-only source root (CUTOUT_HOME)."""


def _env_dir(var: str, default: str) -> Path:
    raw = os.environ.get(var, "").strip() or default
    return Path(raw).expanduser().resolve()


def piv_home() -> Path:
    """Root of everything product-in-video writes: ``$PIV_HOME`` or ``~/.piv``."""
    return _env_dir("PIV_HOME", "~/.piv")


def cutout_home() -> Path:
    """copy-in-product-picture's data root, read-only: ``$CUTOUT_HOME`` or ``~/.cutout``."""
    return _env_dir("CUTOUT_HOME", "~/.cutout")


def _sub(name: str, *parts: str) -> Path:
    path = piv_home() / name
    return path.joinpath(*parts) if parts else path


def runs_dir(*parts: str) -> Path:
    return _sub("runs", *parts)


def scratch_dir(*parts: str) -> Path:
    return _sub("scratch", *parts)


def templates_dir(*parts: str) -> Path:
    return _sub("templates", *parts)


def fonts_dir(*parts: str) -> Path:
    return _sub("fonts", *parts)


def models_dir(*parts: str) -> Path:
    return _sub("models", *parts)


def cutout_path(*parts: str) -> Path:
    """A path under CUTOUT_HOME, for reading only. It must stay inside the root."""
    root = cutout_home()
    path = root.joinpath(*parts).resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"{path} escapes CUTOUT_HOME ({root})")
    return path


def _is_within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def writable(path: str | os.PathLike[str]) -> Path:
    """Return ``path`` resolved, refusing it if it lies under the read-only CUTOUT_HOME.

    Every writer (the renderer included) passes its output path through this.
    """
    resolved = Path(path).expanduser().resolve()
    if _is_within(resolved, cutout_home()):
        raise ReadOnlyPathError(
            f"refusing to write {resolved}: it is under CUTOUT_HOME ({cutout_home()}), "
            "which is copy-in-product-picture's and read-only for product-in-video"
        )
    return resolved


def ensure_dir(path: str | os.PathLike[str]) -> Path:
    """Create a directory (and parents) under PIV_HOME; refuse anywhere else."""
    resolved = writable(path)
    if not _is_within(resolved, piv_home()):
        raise ValueError(f"refusing to create {resolved}: outside PIV_HOME ({piv_home()})")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved
