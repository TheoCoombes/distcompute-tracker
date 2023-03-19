from tortoise import Tortoise, run_async
from braceexpand import braceexpand
from config import SQL_CONN_URL
from database import *
import argparse
import json
import gc

async def init(jobs):
    # 0. Connect to DB
    print("Connecting to DB using url from config.py...")
    await Tortoise.init(
        db_url=SQL_CONN_URL,
        modules={'models': ['models']}
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
        type=str,
        default=None,
        help="Path to a JSON file containing a list of strings. The strings will contain the initial data for first-stage workers (e.g. URL to tars, folders, etc.)"
    )
    parser.add_argument(
        "--brace",
        type=str,
        default=None,
        help="Brace expansion to create list of jobs (instead of --json). E.g. \"./folder_{0..100}/file.zip\""
    )
    args = parser.parse_args()

    if args.brace is not None:
        jobs = list(braceexpand(args.brace))
    elif args.json is not None:
        with open(args.json, "r") as f:
            jobs = json.load(f)
    else:
        raise ValueError("one of `--json`, `--brace` must be declared.")
    
    assert isinstance(jobs, list), "the --json file must contain a list of strings containing job data."

    run_async(init(jobs))