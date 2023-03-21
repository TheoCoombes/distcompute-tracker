from tortoise import Tortoise, run_async
from braceexpand import braceexpand
from config import SQL_CONN_URL
from pathlib import Path
from database import *
import argparse
import json

async def init(jobs):
    # 0. Connect to DB
    print("Connecting to DB using url from config.py...")
    await Tortoise.init(
        db_url=SQL_CONN_URL,
        modules={'models': ['database']}
    )
    await Tortoise.generate_schemas()
    
    print("WARNING: This script will clear ALL data in the database!")
    input("Press Enter to continue, or CTRL+C to quit.")

    await Job.all().delete()
    await User.all().delete()
    await Worker.all().delete()

    # 1. Jobs
    job_objects = []
    i = 1
    
    for job in jobs:
        if isinstance(job, (dict, list)):
            job = "<!json!>" + json.dumps(job)
        elif not isinstance(job, str):
            print(f"job should be str/list/dict, not {type(job)}, ignoring...")
            continue

        job_object = Job(
            number=i,
            stage='a',
            data_a=job,
            data_b=None,
            data_c=None,
            data_d=None,
            data_e=None,
            pending=False,
            closed=False,
            completor=None
        )
        job_objects.append(job_object)
    
    print("Bulk creating jobs in database... (this may take a while)")
    await Job.bulk_create(jobs)
    
    print("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tracker database initialiser")
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Path to a JSON file containing a list of strings/lists/dicts. These list items will contain the initial data for first-stage workers (e.g. URL to tars, data dicts, etc.)"
    )
    parser.add_argument(
        "--txt",
        type=Path,
        default=None,
        help="Path to a txt file containing multiple lines of string data. Each line equates to 1 new job created."
    )
    parser.add_argument(
        "--brace",
        type=str,
        default=None,
        help="Brace expansion to create list of jobs. E.g. \"./folder_{0..100}/file.zip\""
    )
    args = parser.parse_args()

    if args.brace is not None:
        jobs = list(braceexpand(args.brace))
    elif args.json is not None:
        with open(args.json, "r") as f:
            jobs = json.load(f)
    elif args.txt is not None:
        with open(args.txt, "r") as f:
            jobs = f.readlines()
    else:
        raise ValueError("one of `--json`, `--brace` must be declared.")
    
    assert isinstance(jobs, list), "the --json file must contain a list."

    run_async(init(jobs))
