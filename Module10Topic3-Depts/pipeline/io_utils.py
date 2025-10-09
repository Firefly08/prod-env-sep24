# pipeline/io_utils.py
from __future__ import annotations

from pathlib import Path
import io
import gzip
import shutil
import pandas as pd
from typing import Generator, Iterable, Optional


def write_chunk(df: pd.DataFrame, out_path: Path, write_header: bool = False) -> None:
    """
    Write a DataFrame to a gzipped CSV.

    - When write_header=True: (re)create the file and write header+rows.
    - When write_header=False: append rows as a new gzip *member*.
      (Concatenated gzip members are valid; pandas/readers handle them.)
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    mode = "wb" if write_header else "ab"  # append by adding a new gzip member
    with gzip.GzipFile(filename=out_path, mode=mode) as gz:
        with io.TextIOWrapper(gz, encoding="utf-8", newline="") as f:
            df.to_csv(f, index=False, header=write_header)


def move_file(src: Path, dest: Path) -> Path:
    """
    Move/rename file to the exact destination path.
    Creates parent directories as needed.
    """
    src = Path(src)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dest))
    return dest


def iter_chunks(
    path: Path,
    *,
    usecols: Optional[Iterable[str]] = None,
    dtype: Optional[dict] = None,
    chunksize: int = 100_000,
) -> Generator[pd.DataFrame, None, None]:
    """
    Yield DataFrame chunks from a gzipped CSV.
    """
    for chunk in pd.read_csv(
        path,
        chunksize=chunksize,
        compression="gzip",
        usecols=usecols,
        dtype=dtype,
        low_memory=False,
    ):
        yield chunk
