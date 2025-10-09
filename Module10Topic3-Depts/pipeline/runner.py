# pipeline/runner.py
from __future__ import annotations

import logging
import argparse
import shutil
from datetime import datetime
from pathlib import Path

# Import BEFORE using in defaults
from pipeline.config import (
    DATA_DIR,
    PROCESSED_DIR,
    MASTER_OUTPUT,
    FILE_GLOB,
    CHUNK_SIZE,
    KEEP_COLS,
    DTYPES,
)
from pipeline.io_utils import iter_chunks, write_chunk
from pipeline.transform import select_keep_cols, sanity_checks

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def list_unprocessed_files(in_dir: Path, processed_path: Path, pattern: str) -> list[Path]:
    processed_names = {p.name for p in processed_path.glob(pattern)}
    candidates = sorted(in_dir.glob(pattern))
    return [p for p in candidates if p.name not in processed_names]


def process_file_into_master(
    src_path: Path,
    master_path: Path,
    header_written: bool,
    chunk_size: int = CHUNK_SIZE,
):
    logger.info("→ %s → %s", src_path.name, master_path.name)
    rows = 0
    for i, chunk in enumerate(
        iter_chunks(src_path, usecols=KEEP_COLS, dtype=DTYPES, chunksize=chunk_size),
        start=1,
    ):
        logger.info("Chunk %d - %s rows", i, len(chunk))
        df = select_keep_cols(chunk, KEEP_COLS)
        sanity_checks(df)
        write_chunk(df, master_path, write_header=not header_written)
        header_written = True
        rows += len(df)
    return header_written, rows


def safe_move_to_processed(src: Path, processed_path: Path) -> Path:
    dest = processed_path / src.name
    if dest.exists():
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = processed_path / f"{src.name}.{ts}"
    shutil.move(str(src), str(dest))
    return dest


def process_all_to_master(
    in_dir: Path | None = None,
    processed_dir: Path | None = None,   # param name matches tests
    pattern: str | None = None,
    master_path: Path | None = None,
    fresh_master: bool = False,
):
    # Resolve defaults at runtime (after imports are available)
    in_dir = in_dir or DATA_DIR
    processed_dir = processed_dir or PROCESSED_DIR
    pattern = pattern or FILE_GLOB
    master_path = master_path or MASTER_OUTPUT

    new_files = list_unprocessed_files(in_dir, processed_dir, pattern)
    if not new_files:
        logger.warning("No files found in %s matching %s", in_dir, pattern)
        return master_path

    if fresh_master and master_path.exists():
        logger.info("Removing existing master %s for fresh build", master_path)
        master_path.unlink()

    header_written = master_path.exists()

    for idx, src in enumerate(new_files, start=1):
        logger.info("File %d/%d: %s", idx, len(new_files), src.name)
        header_written, rows = process_file_into_master(src, master_path, header_written)
        logger.info("   appended %s rows from %s", rows, src.name)
        moved = safe_move_to_processed(src, processed_dir)
        logger.info("Moved to processed/: %s", moved.name)

    logger.info("Master ready at %s", master_path)
    return master_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", type=Path, default=None)
    parser.add_argument("--processed-dir", type=Path, default=None)
    parser.add_argument("--pattern", type=str, default=None)
    parser.add_argument("--fresh-master", action="store_true", help="Start master from scratch")
    args = parser.parse_args()
    process_all_to_master(
        in_dir=args.in_dir,
        processed_dir=args.processed_dir,
        pattern=args.pattern,
        fresh_master=args.fresh_master,
    )
