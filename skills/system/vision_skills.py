"""
WEDNESDAY AI OS — Vision Skills
Exposes screen reading and object detection to the LLM.
"""
from typing import Any
from core.interfaces import ISkill, SkillResult
from vision.screen_reader import screen_reader
from vision.vision_model import vision_model

class AnalyzeScreenSkill(ISkill):
    @property
    def name(self) -> str: return "analyze_screen"
    @property
    def description(self) -> str: return "Capture and analyze the current computer screen contents."
    @property
    def parameters(self) -> dict:
        return {
            "type": "object", 
            "properties": {"query": {"type": "string", "description": "What to look for or describe on screen"}},
            "required": ["query"]
        }
    def execute(self, **kwargs: Any) -> SkillResult:
        query = kwargs.get("query", "Describe the screen.")
        try:
            res = screen_reader.read_screen(query)
            return SkillResult.ok(self.name, res)
        except Exception as e: return SkillResult.fail(self.name, str(e))

class AnalyzeCameraSkill(ISkill):
    @property
    def name(self) -> str: return "analyze_camera"
    @property
    def description(self) -> str: return "Capture a frame from the webcam and describe what WEDNESDAY sees."
    @property
    def parameters(self) -> dict:
        return {
            "type": "object", 
            "properties": {"query": {"type": "string", "description": "What to look for in the camera feed"}}
        }
    def execute(self, **kwargs: Any) -> SkillResult:
        query = kwargs.get("query", "What do you see?")
        try:
            from vision.camera_capture import camera_capture
            import cv2
            import os
            
            camera_capture.start()
            frame = camera_capture.get_frame()
            camera_capture.stop()
            
            if frame is None:
                return SkillResult.fail(self.name, "Could not capture camera frame.")
                
            temp_path = "artifacts/camera_temp.jpg"
            os.makedirs("artifacts", exist_ok=True)
            cv2.imwrite(temp_path, frame)
            
            res = vision_model.describe_image(temp_path, query)
            return SkillResult.ok(self.name, res)
        except Exception as e: return SkillResult.fail(self.name, str(e))
