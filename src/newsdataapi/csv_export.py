"""CSV export for NewsData.io API responses."""

from __future__ import annotations

import csv
import os
import time
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


def save_to_csv(
    response: Mapping[str, Any],
    folder_path: str | os.PathLike[str],
    filename: str | None = None,
    *,
    overwrite: bool = False,
) -> Path:
    """Write ``response['results']`` to a CSV file inside ``folder_path``.

    Args:
        response: A response dict from the NewsData API. Expected to have a
            ``results`` key holding a list of dicts. ``response`` is read
            but never modified.
        folder_path: Directory in which to write the file. Must already exist.
        filename: Output filename. If omitted, a nanosecond timestamp is used.
            The ``.csv`` suffix is appended if not already present.
        overwrite: If ``False`` (default), raise :class:`FileExistsError`
            when the target file already exists.

    Returns:
        The :class:`~pathlib.Path` of the written file.

    Raises:
        FileNotFoundError: If ``folder_path`` does not exist or is not a
            directory.
        FileExistsError: If ``overwrite`` is ``False`` and the target exists.
        TypeError: If ``response['results']`` exists but is not a list.
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        raise FileNotFoundError(f"Folder does not exist: {folder}")

    if filename is None:
        filename = f"{time.time_ns()}.csv"
    elif not filename.endswith(".csv"):
        filename = f"{filename}.csv"

    target = folder / filename
    if target.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {target}")

    results = response.get("results", [])
    if not isinstance(results, list):
        raise TypeError(
            f"Expected response['results'] to be a list, got {type(results).__name__}"
        )

    rows = [_flatten_row(row) for row in results if isinstance(row, Mapping)]
    fieldnames = _collect_fieldnames(rows)

    with target.open("w", newline="", encoding="utf-8") as fh:
        if fieldnames:
            writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        # Else: leave the file empty so callers can detect "no rows" by
        # `target.stat().st_size == 0` without a special-case error.

    return target


def _flatten_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return a *copy* of ``row`` with dict / list cell values stringified.

    Dicts become ``key:value,key:value``; lists are joined with ``,``. Other
    types (str, int, bool, None) are passed through unchanged so the CSV
    writer can quote them correctly.
    """
    flattened: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, Mapping):
            flattened[key] = ",".join(f"{k}:{v}" for k, v in value.items())
        elif isinstance(value, list):
            flattened[key] = ",".join(str(item) for item in value)
        else:
            flattened[key] = value
    return flattened


def _collect_fieldnames(rows: Iterable[Mapping[str, Any]]) -> list[str]:
    """Union of keys across rows, preserving first-seen order."""
    seen: dict[str, None] = {}
    for row in rows:
        for key in row:
            seen.setdefault(key, None)
    return list(seen.keys())
