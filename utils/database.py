import aiohttp
import json
import base64
import logging
from config import GITHUB_TOKEN, GITHUB_REPO, GITHUB_FILENAME

logger = logging.getLogger(__name__)

class GitHubDB:
    def __init__(self):
        self.token = GITHUB_TOKEN
        self.repo = GITHUB_REPO
        self.filename = GITHUB_FILENAME
        self.url = f"https://api.github.com/repos/{self.repo}/contents/{self.filename}"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.data = {"users": {}, "logs": []}
        self.sha = None

    async def load(self):
        if not self.token or not self.repo:
            return
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=self.headers) as resp:
                if resp.status == 200:
                    res = await resp.json()
                    content = base64.b64decode(res['content']).decode('utf-8')
                    self.data = json.loads(content)
                    self.sha = res['sha']
                elif resp.status == 404:
                    self.data = {"users": {}, "logs": []}
                    self.sha = None

    async def save(self):
        if not self.token or not self.repo:
            return False
        
        content_str = json.dumps(self.data, indent=4)
        content_b64 = base64.b64encode(content_str.encode('utf-8')).decode('utf-8')
        payload = {
            "message": "Update database via Telegram Bot",
            "content": content_b64
        }
        if self.sha:
            payload["sha"] = self.sha

        async with aiohttp.ClientSession() as session:
            async with session.put(self.url, headers=self.headers, json=payload) as resp:
                if resp.status in [200, 201]:
                    res = await resp.json()
                    self.sha = res['content']['sha']
                    return True
                return False

    def add_user(self, user_id, username, first_name):
        uid = str(user_id)
        if uid not in self.data["users"]:
            self.data["users"][uid] = {
                "username": username,
                "first_name": first_name
            }
            return True
        return False

    def add_log(self, log_message):
        self.data["logs"].append(log_message)
        if len(self.data["logs"]) > 100:
            self.data["logs"].pop(0)

db = GitHubDB()
