import os
import json
import requests

class GitHubClient:
    def __init__(self, token, owner, repo):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def verify_connection(self):
        """Check if we can access the repo"""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}"
        resp = requests.get(url, headers=self.headers)
        if resp.status_code != 200:
            error_msg = f"Failed to connect to GitHub repo '{self.owner}/{self.repo}'"
            
            if resp.status_code == 404:
                error_msg += "\n\n❌ Repository not found. Please check:\n"
                error_msg += f"1. Does the repository '{self.owner}/{self.repo}' exist on GitHub?\n"
                error_msg += "2. Is the owner username correct? (case-sensitive)\n"
                error_msg += "3. Is the repository name correct? (case-sensitive)\n"
                error_msg += "4. If it's a private repo, does your token have 'repo' scope?"
            elif resp.status_code == 401:
                error_msg += "\n\n❌ Authentication failed. Please check:\n"
                error_msg += "1. Is your Personal Access Token valid?\n"
                error_msg += "2. Has the token expired?\n"
                error_msg += "3. Does the token have the required permissions?"
            else:
                error_msg += f"\n\nStatus: {resp.status_code}\nResponse: {resp.text}"
                
            raise Exception(error_msg)
        return True

    def create_issue(self, title, body, labels=None):
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues"
        
        data = {
            "title": title,
            "body": body
        }
        if labels:
            data["labels"] = labels
            
        resp = requests.post(url, headers=self.headers, json=data)
        
        if resp.status_code != 201:
            raise Exception(f"Failed to create GitHub issue: {resp.status_code} {resp.text}")
            
        return resp.json()

    @staticmethod
    def get_config_path():
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "github_config.json")

    @staticmethod
    def save_config(token, owner, repo):
        config = {
            "token": token,
            "owner": owner,
            "repo": repo
        }
        with open(GitHubClient.get_config_path(), "w") as f:
            json.dump(config, f, indent=2)

    @staticmethod
    def load_config():
        path = GitHubClient.get_config_path()
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}
