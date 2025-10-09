"""Pipeline script for processing HMDA CSV.gz files into a consolidated
clean dataset with validation checks and gzip-compressed output.
"""

from pathlib import Path
import logging
import gzip
import pandas as pd

from pipeline.validation import _select_keep_cols, _sanity_checks
from pipeline.config import DATA_DIR, OUTPUT_DIR, KEEP_COLS, DTYPES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CHUNK_SIZE = 100_000
MASTER_NAME = "clean_2010HMDA.csv.gz"


def main() -> None:
    """Run the HMDA data processing pipeline.

    Reads chunked `.csv.gz` files from DATA_DIR, validates columns and values,
    and writes a consolidated gzip-compressed CSV into OUTPUT_DIR.
    """
    # Ensure directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    master_path = OUTPUT_DIR / MASTER_NAME

    files = sorted(Path(DATA_DIR).glob("*.csv.gz"))
    if not files:
        logger.warning("No *.csv.gz files found in %s", DATA_DIR)
        return

    # Always start fresh to avoid gzip append problems
    if master_path.exists():
        master_path.unlink()

    total_rows = 0
    header_written = False

    # Keep a single gzip handle open across the entire pipeline
    with gzip.open(master_path, mode="wb") as out:
        for n, file_path in enumerate(files, start=1):
            logger.info("Processing file %d/%d: %s", n, len(files), file_path.name)

            for i, df in enumerate(
                pd.read_csv(
                    file_path,
                    chunksize=CHUNK_SIZE,
                    compression="gzip",
                    usecols=KEEP_COLS,
                    dtype=DTYPES,
                    low_memory=False,
                ),
                start=1,
            ):
                logger.info("  Chunk %d: shape=%s", i, df.shape)

                # Validation
                df = _select_keep_cols(df, KEEP_COLS)
                _sanity_checks(df)

                # Write chunk into the already-open gzip stream
                df.to_csv(out, index=False, header=not header_written)
                header_written = True
                total_rows += len(df)

    logger.info("Done. Wrote %s rows to %s", f"{total_rows:,}", master_path)


if __name__ == "__main__":
    main()
