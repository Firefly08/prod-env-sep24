from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG  # <-- add this
from airflow.operators.python import PythonOperator, ShortCircuitOperator

from pipeline.runner import process_all_to_master

# ---- Constants (defined before use) ----
BASE_DIR = Path("data")
DATA_DIR = BASE_DIR / "inbound"
PROCESSED_DIR = BASE_DIR / "processed"
OUT_DIR = BASE_DIR / "outbound"

PATTERN = "*.csv.gz"
MASTER_NAME = "master.csv.gz"
MASTER_OUTPUT = OUT_DIR / MASTER_NAME

default_args = {
    "owner": "data_eng",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="prod-env-sep24-pipeline",
    start_date=datetime(2025, 10, 1),
    schedule="*/5 * * * *",
    catchup=False,
    max_active_run=1,
    default_args=default_args,
    description="Process new inbound files into master and move to processed/",
) as dag:

    def _new_files_exist() -> bool:
        in_files = {p.name for p in DATA_DIR.glob(PATTERN)}
        proc_files = {p.name for p in PROCESSED_DIR.glob(PATTERN)}
        new_files = in_files - proc_files
        if new_files:
            print(f"New files: {sorted(new_files)}")
            return True
        print("No new files to process")
        return False

    check_new = ShortCircuitOperator(
        task_id="check_new_files",
        python_callable=_new_files_exist,
    )

    def _run_pipeline() -> str:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

        fresh_master = not MASTER_OUTPUT.exists()
        process_all_to_master(
            in_dir=DATA_DIR,
            processed_path=PROCESSED_DIR,
            pattern=PATTERN,
            master_path=MASTER_OUTPUT,
            fresh_master=fresh_master,
        )
        print("Pipeline complete")
        return str(MASTER_OUTPUT)

    pipeline = PythonOperator(
        task_id="run_pipeline",
        python_callable=_run_pipeline,
    )

    check_new >> pipeline
