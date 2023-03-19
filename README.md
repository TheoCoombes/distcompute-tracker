# Distributed-Compute-Tracker
[![Discord Chat](https://img.shields.io/discord/823813159592001537?color=5865F2&logo=discord&logoColor=white)](https://discord.gg/dall-e)

A server previously powering LAION's distributed compute network for filtering commoncrawl with CLIP to produce the LAION-400M and LAION-5B datasets, now repurposed as a general-use multi-layer distributed compute tracker and job manager, with added support for a frontend web server dashboard, user leaderboards and up to 5 recursive layers of workers for each job.

Workers at each stage of the job workflow recieve the input(s) created by previous workers, and perform their specialised task before workers at the next stage continue the job with their task.

## Installation
1. Install requirements
```
git clone https://github.com/TheoCoombes/Distributed-Compute-Tracker.git
cd Distributed-Compute-Tracker
pip install -r requirements.txt
```
2. Setup Redis
   - [Redis Guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-20-04)
   - Configure your Redis connection url in `config.py`.
3. Setup SQL database
   - [PostGreSQL Guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-20-04) - follow steps 1-4, noting down the name you give your database.
   - Install the required python library for the database you are using. (see link above)
   - Configure your SQL connection in `config.py`, adding your database name to the `SQL_CONN_URL`.
4. Add Jobs
   - TODO job creator file. (from json list / braceexpansion?)
5. Install ASGI server
   - From v3.0.0, you are required to start the server using a console command directly from the server backend.
   - You can either use `gunicorn` or `uvicorn`. Previously, the LAION-5B production server used `uvicorn` with 12 worker processes.
   - e.g. `uvicorn main:app --host 0.0.0.0 --port 80 --workers 12`

## Usage
As stated in step 4 of installation, you need to run the server directly using a ASGI server library of your choice:
```
uvicorn main:app --host 0.0.0.0 --port 80 --workers 12
```
- *Runs the server through Uvicorn, using 12 processes.*