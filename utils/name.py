from pathlib import Path
import random
import json

with open(Path(__file__).parents[0] / "words.json", "r") as f:
    db = json.load(f)

def generate_worker_name():
    words = [random.choice(db) for i in range(2)]
    f = words[0].lower()
    s = words[1].lower()
    return f + "-" + s + "-" + str(random.randint(0, 999))
