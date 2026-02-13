import os
import json
from jira import JIRA

class JiraClient:
    def __init__(self, server, email, token):
        self.server = server
        self.email = email
        self.token = token
        self.jira = None
        self._connect()

    def _connect(self):
        try:
            self.jira = JIRA(
                server=self.server,
                basic_auth=(self.email, self.token)
            )
            # Verify connection by getting user details
            self.jira.myself()
        except Exception as e:
            raise Exception(f"Failed to connect to Jira: {str(e)}")

    def create_issue(self, project_key, summary, description, issue_type='Bug', attachment_path=None):
        if not self.jira:
            self._connect()

        try:
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
            }
            
            new_issue = self.jira.create_issue(fields=issue_dict)
            
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    self.jira.add_attachment(issue=new_issue, attachment=f)
            
            return {
                "key": new_issue.key,
                "url": f"{self.server}/browse/{new_issue.key}"
            }
        except Exception as e:
            raise Exception(f"Failed to create Jira issue: {str(e)}")

    @staticmethod
    def get_config_path():
        return os.path.join(os.path.dirname(os.path.dirname(__file__)), "jira_config.json")

    @staticmethod
    def save_config(server, email, token, project_key):
        config = {
            "server": server,
            "email": email,
            "token": token,
            "project_key": project_key
        }
        with open(JiraClient.get_config_path(), "w") as f:
            json.dump(config, f, indent=2)

    @staticmethod
    def load_config():
        path = JiraClient.get_config_path()
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}
