from tortoise.models import Model
from tortoise import fields

# Models for interacting with the SQL database.

class Job(Model):
    """ The SQL jobs table. """

    # The job number.
    number = fields.IntField(pk=True)
    stage = fields.CharField(max_length=1, null=True) # a/b/c/d/e

    # The inputs to each level of worker. `data_a` is the initial input set in the database.
    data_a = fields.TextField()
    data_b = fields.TextField(null=True)
    data_c = fields.TextField(null=True)
    data_d = fields.TextField(null=True)
    data_e = fields.TextField(null=True)
    
    # Contains information about the shard's completion.
    pending = fields.BooleanField()
    closed = fields.BooleanField()

    completor = fields.TextField(null=True) # Contains the worker's token only whilst being fetching a job.
    
class Worker(Model):
    """ The SQL workers table. """
    
    # The worker details.
    token = fields.TextField(pk=True)
    display_name = fields.TextField()
    
    # The stage of worker. (a/b/c/d/e)
    stage = fields.CharField(max_length=1)
    
    # User information.
    user_nickname = fields.CharField(max_length=128)
    
    # The job this worker is currently processing.
    job = fields.ForeignKeyField("models.Job", related_name="worker", null=True)
    
    # Progress information sent from the client. ( client.log(...) )
    progress = fields.CharField(max_length=255)
    
    # How many jobs this worker has completed
    jobs_completed = fields.IntField()
    
    # Client time information in a UTC epoch timestamp form. (helps with timeouts as well as calculating efficiency)
    first_seen = fields.IntField()
    last_seen = fields.IntField()

class User(Model):
    """ The job completion leaderboard. """
    nickname = fields.CharField(pk=True, max_length=128)
    jobs_completed = fields.IntField(default=0)
    

# CUSTOM SQL QUERY:
ENTER_JOB_QUERY = """
UPDATE "job" 
SET pending=true, completor='{0}'
WHERE "number" IN 
    (
        SELECT "number" FROM "job" 
        WHERE pending=false AND closed=false AND stage='{1}'
        ORDER BY RANDOM() LIMIT 1
        FOR UPDATE SKIP LOCKED
    )
AND pending=false AND closed=false
;
""".strip("\n")
