import json
import os
import threading
from datetime import datetime

class JobStore:
    def __init__(self, filepath="runs.json"):
        self.filepath = filepath
        self.lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w") as f:
                json.dump({}, f)

    def _load(self):
        try:
            with open(self.filepath, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save(self, data):
        with open(self.filepath, "w") as f:
            json.dump(data, f, indent=2)

    def save_job(self, job_id, job_data):
        with self.lock:
            data = self._load()
            # If creating new, add timestamp
            if job_id not in data:
                job_data["created_at"] = datetime.utcnow().isoformat()
            
            # Merge or overwrite
            if job_id in data:
                data[job_id].update(job_data)
            else:
                data[job_id] = job_data
            self._save(data)

    def get_job(self, job_id):
        with self.lock:
            data = self._load()
            return data.get(job_id)

    def list_jobs(self):
        with self.lock:
            data = self._load()
            # Convert dict to list and sort by date desc
            jobs = list(data.values())
            jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return jobs

    def delete_job(self, job_id):
        with self.lock:
            data = self._load()
            if job_id in data:
                del data[job_id]
                self._save(data)

# Singleton instance
store = JobStore(os.path.join(os.path.dirname(os.path.dirname(__file__)), "runs.json"))
