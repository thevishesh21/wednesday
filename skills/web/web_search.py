"""
WEDNESDAY AI OS — Web Search Skills
"""
from typing import Any
from core.interfaces import ISkill, SkillResult
from tools.browser import search_google, search_youtube, open_website

class SearchGoogleSkill(ISkill):
    @property
    def name(self) -> str: return "search_google"
    @property
    def description(self) -> str: return "Search Google for a query."
    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    def execute(self, **kwargs: Any) -> SkillResult:
        try:
            res = search_google(kwargs.get("query", ""))
            return SkillResult.ok(self.name, res)
        except Exception as e: return SkillResult.fail(self.name, str(e))

class SearchYoutubeSkill(ISkill):
    @property
    def name(self) -> str: return "search_youtube"
    @property
    def description(self) -> str: return "Search YouTube for a video."
    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    def execute(self, **kwargs: Any) -> SkillResult:
        try:
            res = search_youtube(kwargs.get("query", ""))
            return SkillResult.ok(self.name, res)
        except Exception as e: return SkillResult.fail(self.name, str(e))

class OpenWebsiteSkill(ISkill):
    @property
    def name(self) -> str: return "open_website"
    @property
    def description(self) -> str: return "Open a website by URL or name."
    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}
    def execute(self, **kwargs: Any) -> SkillResult:
        try:
            res = open_website(kwargs.get("url", ""))
            return SkillResult.ok(self.name, res)
        except Exception as e: return SkillResult.fail(self.name, str(e))
