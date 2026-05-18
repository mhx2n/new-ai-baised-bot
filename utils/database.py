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
        self.headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}
        # API keys will now be stored in arrays (lists)
        self.data = {"users": {}, "logs": [], "api_keys": {"gemini": [], "cohere": []}}
        self.sha = None

    async def load(self):
        if not self.token or not self.repo: return
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=self.headers) as resp:
                if resp.status == 200:
                    res = await resp.json()
                    content = base64.b64decode(res['content']).decode('utf-8')
                    loaded_data = json.loads(content)
                    
                    # Ensure new array structure exists for old databases
                    if "api_keys" not in loaded_data: loaded_data["api_keys"] = {"gemini": [], "cohere": []}
                    elif isinstance(loaded_data["api_keys"].get("gemini"), str):
                        # Convert old string keys to list
                        g_key = loaded_data["api_keys"]["gemini"]
                        c_key = loaded_data["api_keys"].get("cohere", "")
                        loaded_data["api_keys"] = {"gemini": [g_key] if g_key else [], "cohere": [c_key] if c_key else []}
                        
                    self.data = {**self.data, **loaded_data}
                    self.sha = res['sha']
                elif resp.status == 404: self.sha = None

    async def save(self):
        if not self.token or not self.repo: return False
        content_str = json.dumps(self.data, indent=4)
        content_b64 = base64.b64encode(content_str.encode('utf-8')).decode('utf-8')
        payload = {"message": "Update DB", "content": content_b64}
        if self.sha: payload["sha"] = self.sha
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
            self.data["users"][uid] = {"username": username, "first_name": first_name}
            return True
        return False

    def add_api_key(self, provider, key):
        if key not in self.data["api_keys"][provider]:
            self.data["api_keys"][provider].append(key)
            return True
        return False

    def remove_api_key(self, provider, index):
        try:
            self.data["api_keys"][provider].pop(index)
            return True
        except IndexError:
            return False

    def get_api_keys(self, provider):
        return self.data["api_keys"].get(provider, [])

db = GitHubDB()
