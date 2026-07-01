import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("PREFECT_SERVER_ANALYTICS_ENABLED", "false")

from prefect import flow, task

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRANSFORM_DIR = PROJECT_ROOT / "transform"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingest.fetch_mta_live import fetch_mta_data
from scripts.bootstrap_gtfs import bootstrap_static_gtfs


@task(retries=2, retry_delay_seconds=60)
def bootstrap_static_data() -> None:
    bootstrap_static_gtfs()


@task(retries=2, retry_delay_seconds=60)
def fetch_live_positions() -> None:
    fetch_mta_data()


@task(retries=1, retry_delay_seconds=30)
def build_dbt_models() -> None:
    dbt_command_value = os.getenv("DBT_COMMAND")
    if dbt_command_value and Path(dbt_command_value).exists():
        dbt_command = [dbt_command_value]
    else:
        dbt_command = shlex.split(dbt_command_value or "dbt", posix=os.name != "nt")

    subprocess.run(
        [*dbt_command, "run", "--profiles-dir", "."],
        cwd=TRANSFORM_DIR,
        check=True,
    )


@flow(name="nyc-subway-analytics-pipeline")
def subway_analytics_pipeline(bootstrap_static: bool = False) -> None:
    if bootstrap_static:
        bootstrap_static_data()

    fetch_live_positions()
    build_dbt_models()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the NYC subway analytics pipeline.")
    parser.add_argument(
        "--bootstrap-static",
        action="store_true",
        help="Refresh static GTFS stops and routes before ingesting live data.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    subway_analytics_pipeline(bootstrap_static=args.bootstrap_static)
