"""
WEDNESDAY AI OS — Weather Skill
Uses wttr.in to fetch weather data without needing an API key.
"""
import urllib.request
from typing import Any
from core.interfaces import ISkill, SkillResult

class GetWeatherSkill(ISkill):
    @property
    def name(self) -> str: return "get_weather"
    
    @property
    def description(self) -> str: return "Get current weather for a location."
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object", 
            "properties": {"location": {"type": "string", "description": "City name"}},
            "required": ["location"]
        }
        
    def execute(self, **kwargs: Any) -> SkillResult:
        location = kwargs.get("location", "")
        if not location:
            return SkillResult.fail(self.name, "Location not provided.")
            
        try:
            # Format 3 gets just the text summary
            url = f"http://wttr.in/{location.replace(' ', '+')}?format=3"
            req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.68.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                weather = response.read().decode('utf-8').strip()
            return SkillResult.ok(self.name, weather)
        except Exception as e:
            return SkillResult.fail(self.name, f"Failed to get weather: {e}")
