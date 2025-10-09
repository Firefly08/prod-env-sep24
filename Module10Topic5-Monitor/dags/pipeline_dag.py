from datetime import datetime, timedelta

from airflow import DAG

default_args = {
    "owner": "data_eng",
    "retries": 1,
    "retry_delay": timedelta(minutes=2)
}

with DAG(
    dag_id="prod-env-sep24-pipeline",
    start_date=datetime(2025, 10, 1),
    schedule="*/5 * * * *",
    catchup=False,
    max_active_run=1,
    default_args=default_args,
    description="Process new inbound files into master and move to processed/"
) as dag:

    def _new_files_exist() -> bool:
        in_files = {p.name for p in DATA_DIR.glob(".csv.gz")}
        proc_files = {p.name for p in PROCESSED_DIR.glob(".csv.gz")}
        new_files = in_files - proc_files
        new_found = len(new_files) > 0
        if new_found:
            print(f"New files: {sorted(new_files)}")
        else:
            print("No new files to process")
        return new_found

