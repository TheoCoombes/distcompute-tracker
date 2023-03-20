from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from tortoise.contrib.fastapi import register_tortoise
from fastapi import FastAPI, Request, HTTPException
from tortoise.transactions import in_transaction
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from random import choice
from uuid import uuid4
import asyncio
import math

from utils.name import generate_worker_name
from cache import Cache
from database import *
from config import *

app = FastAPI()
cache = Cache(REDIS_CONN_URL)
templates = Jinja2Templates(directory="templates")

# REQUEST INPUTS START ------

class StandardInput(BaseModel):
    token: str

class ProgressInput(BaseModel):
    token: str
    progress: str

class CompleteJobInput(BaseModel):
    token: str
    data: str
        
# FRONTEND START ------

@app.get('/', response_class=HTMLResponse)
async def index(request: Request, all: Optional[bool] = False):
    try:
        body, expired = await cache.page.get_body_expired(f'/?all={all}')
        if not expired:
            return HTMLResponse(content=body)
        else:
            # Cache has expired, we need to re-render the page body.
            pass
    except:
        # Cache hasn't yet been set, we need to render the page body.
        pass
    
    # Render body
    
    completed_jobs = await Job.filter(closed=True).count()
    total_jobs = await Job.all().count()

    # TODO Maybe there's a better way to write this code / iterate? haha
    if not all:
        if STAGE_A is not None:
            a_workers = await Worker.filter(stage="a").prefetch_related("shard").order_by("first_seen").limit(50)
        else:
            a_workers = None
        if STAGE_B is not None:
            b_workers = await Worker.filter(stage="b").prefetch_related("shard").order_by("first_seen").limit(50)
        else:
            b_workers = None
        if STAGE_C is not None:
            c_workers = await Worker.filter(stage="c").prefetch_related("shard").order_by("first_seen").limit(50)
        else:
            c_workers = None
        if STAGE_D is not None:
            d_workers = await Worker.filter(stage="d").prefetch_related("shard").order_by("first_seen").limit(50)
        else:
            d_workers = None
        if STAGE_E is not None:
            e_workers = await Worker.filter(stage="e").prefetch_related("shard").order_by("first_seen").limit(50)
        else:
            e_workers = None
    else:
        if STAGE_A is not None:
            a_workers = await Worker.filter(stage="a").prefetch_related("shard").order_by("first_seen")
        else:
            a_workers = None
        if STAGE_B is not None:
            b_workers = await Worker.filter(stage="b").prefetch_related("shard").order_by("first_seen")
        else:
            b_workers = None
        if STAGE_C is not None:
            c_workers = await Worker.filter(stage="c").prefetch_related("shard").order_by("first_seen")
        else:
            c_workers = None
        if STAGE_D is not None:
            d_workers = await Worker.filter(stage="d").prefetch_related("shard").order_by("first_seen")
        else:
            d_workers = None
        if STAGE_E is not None:
            e_workers = await Worker.filter(stage="e").prefetch_related("shard").order_by("first_seen")
        else:
            e_workers = None

    # We call seperately as len() will give differing results for when all=false.
    if STAGE_A is not None:
        a_len = await Worker.filter(stage="a").count()
    else:
        a_len = 0
    if STAGE_B is not None:
        b_len = await Worker.filter(stage="b").count()
    else:
        b_len = 0
    if STAGE_C is not None:
        c_len = await Worker.filter(stage="c").count()
    else:
        c_len = 0
    if STAGE_D is not None:
        d_len = await Worker.filter(stage="d").count()
    else:
        d_len = 0
    if STAGE_E is not None:
        e_len = await Worker.filter(stage="e").count()
    else:
        e_len = 0
        
    body = templates.TemplateResponse('index.html', {
        "request": request,
        "all": all,
        "a_workers": a_workers,
        "b_workers": b_workers,
        "c_workers": c_workers,
        "d_workers": d_workers,
        "e_workers": e_workers,
        "a_len": a_len,
        "b_len": b_len,
        "c_len": c_len,
        "d_len": d_len,
        "e_len": e_len,
        "PROJECT_NAME": PROJECT_NAME,
        "STAGE_A": STAGE_A,
        "STAGE_B": STAGE_B,
        "STAGE_C": STAGE_C,
        "STAGE_D": STAGE_D,
        "STAGE_E": STAGE_E,
        "completion_float": (completed_jobs / total_jobs) * 100 if total_jobs > 0 else 100.0,
        "completion_str": f"{completed_jobs:,} / {total_jobs:,}",
        "eta": (await cache.client.get("eta")).decode('utf-8')
    })

    # Set page cache with body.
    await cache.page.set(f'/?all={all}', body.body)

    return body

@app.get('/leaderboard', response_class=HTMLResponse)
async def leaderboard_page(request: Request):
    try:
        body, expired = await cache.page.get_body_expired('/leaderboard')
        if not expired:
            return HTMLResponse(content=body)
        else:
            # Cache has expired, we need to re-render the page body.
            pass
    except:
        # Cache hasn't yet been set, we need to render the page body.
        pass
    
    body = templates.TemplateResponse('leaderboard.html', {
        "request": request,
        "leaderboard": await User.all().order_by("-jobs_completed"),
        "PROJECT_NAME": PROJECT_NAME
    })
    
    # Set page cache with body.
    await cache.page.set('/leaderboard', body.body)
    
    return body

@app.get('/worker/{stage_name}/{display_name}', response_class=HTMLResponse)
async def worker_info(stage_name: str, display_name: str, request: Request):
    if stage_name == STAGE_A:
        stage = 'a'
    elif stage_name == STAGE_B:
        stage = 'b'
    elif stage_name == STAGE_C:
        stage = 'c'
    elif stage_name == STAGE_D:
        stage = 'd'
    elif stage_name == STAGE_E:
        stage = 'e'
    else:
        raise HTTPException(status_code=400, detail=f"Invalid worker stage.")
        
    try:
        worker = await Worker.get(display_name=display_name, stage=stage).prefetch_related("shard")
    except Exception:
        raise HTTPException(status_code=404, detail="Worker not found.")

    body = templates.TemplateResponse('worker.html', {
        "request": request,
        "worker": worker,
        "PROJECT_NAME": PROJECT_NAME
    })
    
    return body       

# API START ------

@app.get('/api/new')
async def new(nickname: str, stage: str) -> dict:
    if stage not in ["a", "b", "c", "d", "e"]:
        raise HTTPException(status_code=400, detail=f"Invalid worker stage: '{stage}'. Choose from 'a'/'b'/'c'/'d'/'e'.")

    if stage == "a" and STAGE_A is None:
        raise HTTPException(status_code=400, detail=f"The worker stage '{stage}' is disabled.")
    elif stage == "b" and STAGE_B is None:
        raise HTTPException(status_code=400, detail=f"The worker stage '{stage}' is disabled.")
    elif stage == "c" and STAGE_C is None:
        raise HTTPException(status_code=400, detail=f"The worker stage '{stage}' is disabled.")
    elif stage == "d" and STAGE_D is None:
        raise HTTPException(status_code=400, detail=f"The worker stage '{stage}' is disabled.")
    elif stage == "e" and STAGE_E is None:
        raise HTTPException(status_code=400, detail=f"The worker stage '{stage}' is disabled.")
    
    token = str(uuid4())
    ctime = math.floor(datetime.utcnow().timestamp())
    display_name = generate_worker_name()

    await Worker.create(
        token=token,
        display_name=display_name,
        stage=stage,
        user_nickname=nickname,
        progress="Initialised",
        jobs_completed=0,
        first_seen=ctime,
        last_seen=ctime,
        job=None
    )

    if stage == "a":
        stage_name = STAGE_A
    elif stage == "b":
        stage_name = STAGE_B
    elif stage == "c":
        stage_name = STAGE_C
    elif stage == "d":
        stage_name = STAGE_D
    else:
        stage_name = STAGE_E
    
    body = {
        "token": token,
        "display_name": display_name,
        "project": PROJECT_NAME,
        "stage_name": stage_name,
    }

    return body


@app.post('/api/validateWorker', response_class=PlainTextResponse)
async def validateWorker(inp: StandardInput) -> str:
    exists = await Worker.exists(token=inp.token)
    return str(exists)

@app.post('/api/newJob')
async def newJob(inp: StandardInput) -> dict:
    try:
        worker = await Worker.get(token=inp.token).prefetch_related("job")
    except:
        raise HTTPException(status_code=404, detail="The server could not find this worker. Did the worker time out?")
    
    if worker.job is not None and worker.job.pending:
        worker.job.pending = False
        await worker.job.save()

    try:
        # Empty out any existing jobs that may cause errors.
        await Job.filter(worker=worker.token, pending=True).update(completor=None, pending=False)
        
        # We update with completor to be able to find the job and make it pending in a single request, and we later set it back to None.
        # This helps us avoid workers getting assigned the same job.
        # We also had to use a raw SQL query here, as tortoise-orm was not complex enough to allow us to perform this type of command.
        async with in_transaction() as conn:
            await conn.execute_query(
                ENTER_JOB_QUERY.format(worker.token, worker.stage)
            )
        job = await Job.get(completor=worker.token, pending=True)
    except:
        raise HTTPException(status_code=403, detail="Either there are no new jobs available, or there was an error whilst finding a job. Keep retrying, as jobs are dynamically created.")
    
    job.completor = None
    await job.save()
    
    worker.job = job
    worker.progress = "Recieved new job"
    worker.last_seen = math.floor(datetime.utcnow().timestamp())
    await worker.save()

    if worker.stage == "a":
        data = job.data_a
    elif worker.stage == "b":
        data = job.data_b
    elif worker.stage == "c":
        data = job.data_c
    elif worker.stage == "d":
        data = job.data_d
    elif worker.stage == "e":
        data = job.data_e
    
    return {"data": data, "number": job.number}

@app.get('/api/jobCount', response_class=PlainTextResponse)
async def jobCount(stage: str) -> str:
    if stage not in ["a", "b", "c", "d", "e"]:
        raise HTTPException(status_code=400, detail=f"Invalid worker stage: '{stage}'. Choose from 'a'/'b'/'c'/'d'/'e'.")
        
    count = await Job.filter(pending=False, closed=False, stage=stage).count()
    
    return str(count)

@app.post('/api/updateProgress', response_class=PlainTextResponse)
async def updateProgress(inp: ProgressInput) -> str:
    ctime = math.floor(datetime.utcnow().timestamp())

    try:
        await Worker.get(token=inp.token).update(progress=inp.progress, last_seen=ctime)
    except:
        raise HTTPException(status_code=404, detail="The server could not find this worker. Did the worker time out?")
    
    return "200 OK"


@app.post('/api/completeJob', response_class=PlainTextResponse)
async def completeJob(inp: CompleteJobInput) -> str:
    try:
        worker = await Worker.get(token=inp.token).prefetch_related("job")
    except:
        raise HTTPException(status_code=404, detail="The server could not find this worker. Did the worker time out?")
    
    if worker.job is None:
        raise HTTPException(status_code=403, detail="You do not have an open job.")
    if worker.job.closed:
        raise HTTPException(status_code=403, detail="This job has already been marked as completed.")
    
    if inp.url is None:
        raise HTTPException(status_code=400, detail="The worker did not submit valid download data.")
    
    if worker.stage == "a":
        worker.job.data_a = inp.data
        if STAGE_B is not None:
            worker.job.stage = "b"
        else:
            worker.job.closed = True
    elif worker.stage == "b":
        worker.job.data_b = inp.data
        if STAGE_C is not None:
            worker.job.stage = "c"
        else:
            worker.job.closed = True
    elif worker.stage == "c":
        worker.job.data_c = inp.data
        if STAGE_D is not None:
            worker.job.stage = "d"
        else:
            worker.job.closed = True
    elif worker.stage == "d":
        worker.job.data_d = inp.data
        if STAGE_E is not None:
            worker.job.stage = "e"
        else:
            worker.job.closed = True
    elif worker.stage == "e":
        worker.job.data_e = inp.data
        worker.job.closed = True

    worker.job.pending = False
    await worker.job.save()
    
    worker.job = None
    worker.progress = "Completed Job"
    worker.jobs_completed += 1
    worker.last_seen = math.floor(datetime.utcnow().timestamp())
    await worker.save()

    user, created = await User.get_or_create(nickname=worker.user_nickname)
    if created:
        user.jobs_completed = 1
    else:
        user.jobs_completed += 1
    await user.save()
    
    return "200 OK"


@app.post('/api/flagInvalidData', response_class=PlainTextResponse)
async def flagInvalidData(inp: StandardInput) -> str:
    try:
        worker = await Worker.get(token=inp.token).prefetch_related("job")
    except:
        raise HTTPException(status_code=404, detail="The server could not find this worker. Did the worker time out?")
    
    if worker.job is None:
        raise HTTPException(status_code=403, detail="This worker is not currently working on a job.")
    
    report_id = f"{worker.job.number}{worker.stage}"
    await cache.client.hincrby("invalid", report_id)
    reports = await cache.client.hget("invalid", report_id)

    if int(reports) >= 5:
        if worker.stage == "b":
            worker.job.data_a = None
            worker.job.stage = "a"
        elif worker.stage == "c":
            worker.job.data_b = None
            worker.job.stage = "b"
        elif worker.stage == "d":
            worker.job.data_c = None
            worker.job.stage = "c"
        elif worker.stage == "e":
            worker.job.data_d = None
            worker.job.stage = "d"
    
    worker.job.pending = False
    await worker.job.save()
    
    worker.job = None
    worker.last_seen = math.floor(datetime.utcnow().timestamp())
    await worker.save()
    
    return "200 OK"

    
@app.post('/api/bye', response_class=PlainTextResponse)
async def bye(inp: StandardInput) -> str:
    try:
        worker = await Worker.get(token=inp.token).prefetch_related("job")
    except:
        raise HTTPException(status_code=404, detail="The server could not find this worker. Did the worker time out?")
        
    if worker.job is not None:
        worker.job.pending = False
        await worker.job.save()
    
    await worker.delete()
    
    return "200 OK"


# TIMERS START -----------------

async def check_idle():
    while True:
        await asyncio.sleep(300)
        t = math.floor(datetime.utcnow().timestamp()) - IDLE_TIMEOUT
        
        clients = await Worker.filter(last_seen__lte=t, shard_id__not_isnull=True).prefetch_related("shard")
        for client in clients:
            if client.shard.pending:
                client.shard.pending = False
                await client.shard.save()
        
        await Worker.filter(last_seen__lte=t).delete()

        
async def calculate_eta():
    await cache.client.set("eta", "Calculating...")
    
    def _format_time(s):
        s = int(s)
        y, s = divmod(s, 31_536_000)
        d, s = divmod(s, 86400)
        h, s = divmod(s, 3600)
        m, s = divmod(s, 60)
        if y:
            return f"{y} year{'s' if y!=1 else ''}, {d} day{'s' if d!=1 else ''}, {h} hour{'s' if h!=1 else ''}, {m} minute{'s' if m!=1 else ''} and {s} second{'s' if s!=1 else ''}"
        elif d:
            return f"{d} day{'s' if d!=1 else ''}, {h} hour{'s' if h!=1 else ''}, {m} minute{'s' if m!=1 else ''} and {s} second{'s' if s>1 else ''}"
        elif h:
            return f"{h} hour{'s' if h!=1 else ''}, {m} minute{'s' if m!=1 else ''} and {s} second{'s' if s>1 else ''}"
        elif m:
            return f"{m} minute{'s' if m!=1 else ''} and {s} second{'s' if s!=1 else ''}"
        else:
            return f"{s} second{'s' if s!=1 else ''}"
        
    dataset = []
    while True:
        try:
            start = await Job.filter(closed=True).count()
        except:
            await asyncio.sleep(5)
            continue
        await asyncio.sleep(AVERAGE_INTERVAL)
        end = await Job.filter(closed=True).count()

        dataset.append(end - start)
        if len(dataset) > AVERAGE_DATASET_LENGTH:
            dataset.pop(0)

        mean = sum(dataset) / len(dataset)
        mean_per_second = mean / AVERAGE_INTERVAL
        remaining = await Job.filter(closed=False).count()

        try:
            length = remaining // mean_per_second
        except ZeroDivisionError:
            continue
        
        if length:
            await cache.client.set("eta", _format_time(length))
        else:
            await cache.client.set("eta", "Finished")

# FASTAPI UTILITIES START ------

@app.on_event('startup')
async def app_startup():
    # Finds the worker number for this worker.
    await cache.init_pid()
    
    if cache.iszeroworker:
        # The following functions only need to be executed on a single worker.
        asyncio.create_task(check_idle())
        asyncio.create_task(calculate_eta())

@app.on_event('shutdown')
async def app_shutdown():
    return await cache.safe_shutdown()

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_, exc):
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code)

# INIT START ------------------- 

register_tortoise(
    app,
    db_url=SQL_CONN_URL,
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

if __name__ == "__main__":
    print("You cannot run this script directly from Python. Call gunicorn/uvicorn directly from the terminal, using \"main:app\" as the server.")
