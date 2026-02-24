
import json
import os
import threading
from datetime import datetime
from werkzeug.utils import secure_filename

class BaselineStore:
    def __init__(self, data_dir="baselines", metadata_file="baselines.json"):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, data_dir)
        self.metadata_path = os.path.join(self.base_dir, metadata_file)
        self.lock = threading.Lock()
        
        os.makedirs(self.data_dir, exist_ok=True)
        self._ensure_metadata()

    def _ensure_metadata(self):
        if not os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'w') as f:
                json.dump({}, f)

    def _load(self):
        try:
            with open(self.metadata_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save(self, data):
        with open(self.metadata_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _get_url_key(self, url):
        # Create a safe key from URL
        import hashlib
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def add_baseline(self, stage_url, job_id, image_path):
        """
        Promotes a job's stage image to be a new baseline version.
        """
        with self.lock:
            data = self._load()
            key = self._get_url_key(stage_url)
            
            if key not in data:
                data[key] = {
                    "url": stage_url,
                    "versions": [],
                    "active_version_id": None
                }
            
            # Check if active version is identical to new one to avoid duplicates
            if data[key]["active_version_id"]:
                 active_ver = next((v for v in data[key]["versions"] if v.version_id == data[key]["active_version_id"]), None)
                 if active_ver:
                     active_path = os.path.join(self.data_dir, active_ver["path"])
                     if os.path.exists(active_path):
                         import hashlib
                         def file_hash(filepath):
                             hasher = hashlib.md5()
                             with open(filepath, 'rb') as f:
                                 buf = f.read()
                                 hasher.update(buf)
                             return hasher.hexdigest()
                         
                         if file_hash(image_path) == file_hash(active_path):
                             return None # No change needed
            
            version_id = f"v{len(data[key]['versions']) + 1}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            # Copy image to baselines dir
            ext = os.path.splitext(image_path)[1]

            dest_filename = f"{key}_{version_id}{ext}"
            dest_path = os.path.join(self.data_dir, dest_filename)
            
            import shutil
            shutil.copy2(image_path, dest_path)
            
            new_version = {
                "version_id": version_id,
                "job_id": job_id,
                "timestamp": datetime.utcnow().isoformat(),
                "path": dest_filename  # Relative to baselines dir
            }
            
            data[key]["versions"].insert(0, new_version) # Newest first
            data[key]["active_version_id"] = version_id # Auto-promote new version
            
            self._save(data)
            return version_id

    def get_history(self, stage_url):
        with self.lock:
            data = self._load()
            key = self._get_url_key(stage_url)
            return data.get(key) # Returns dict with url, versions, active_version_id

    def get_all_baselines(self):
        with self.lock:
            data = self._load()
            baselines = []
            for k, v in data.items():
                b = v.copy()
                # Add active image path for convenience
                if b["active_version_id"]:
                    active_ver = next((ver for ver in b["versions"] if ver["version_id"] == b["active_version_id"]), None)
                    if active_ver:
                        b["active_image_path"] = active_ver["path"]
                baselines.append(b)
            return baselines

    def get_baseline_path(self, filename):
        # Securely return absolute path for serving
        path = os.path.join(self.data_dir, filename)
        if os.path.exists(path) and os.path.realpath(path).startswith(os.path.realpath(self.data_dir)):
            return path
        return None


    def get_active_baseline_path(self, stage_url):
        with self.lock:
            data = self._load()
            key = self._get_url_key(stage_url)
            
            if key not in data or not data[key]["active_version_id"]:
                return None
                
            active_id = data[key]["active_version_id"]
            for v in data[key]["versions"]:
                if v["version_id"] == active_id:
                    return os.path.join(self.data_dir, v["path"])
            
            return None

    def rollback(self, stage_url, version_id):
        with self.lock:
            data = self._load()
            key = self._get_url_key(stage_url)
            
            if key not in data:
                return False
                
            # verify version exists
            found = False
            for v in data[key]["versions"]:
                if v["version_id"] == version_id:
                    found = True
                    break
            
            if found:
                data[key]["active_version_id"] = version_id
                self._save(data)
                return True
            
            return False
            
    def delete_baseline(self, url):
        with self.lock:
            data = self._load()
            key = self._get_url_key(url)
            
            if key in data:
                # remove files
                for v in data[key].get("versions", []):
                    path = os.path.join(self.data_dir, v["path"])
                    if os.path.exists(path):
                        try:
                            os.remove(path)
                        except OSError:
                            pass # ignore errors

                del data[key]
                self._save(data)
                return True
            return False


    def add_baseline_from_file(self, stage_url, file_storage):
        with self.lock:
            data = self._load()
            key = self._get_url_key(stage_url)
            
            if key not in data:
                data[key] = {
                    "url": stage_url,
                    "versions": [],
                    "active_version_id": None
                }
            
            version_id = f"v{len(data[key]['versions']) + 1}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            ext = ".png" # default
            if file_storage.filename.lower().endswith(".jpg") or file_storage.filename.lower().endswith(".jpeg"):
                 ext = ".jpg"
            
            dest_filename = f"{key}_{version_id}{ext}"
            dest_path = os.path.join(self.data_dir, dest_filename)
            
            file_storage.save(dest_path)
            
            new_version = {
                "version_id": version_id,
                "job_id": "manual_upload",
                "timestamp": datetime.utcnow().isoformat(),
                "path": dest_filename
            }
            
            data[key]["versions"].insert(0, new_version)
            data[key]["active_version_id"] = version_id
            
            self._save(data)
            return version_id

