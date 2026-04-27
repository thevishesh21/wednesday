"""
WEDNESDAY AI OS — Task Planner
Converts a ParsedIntent into a TaskPlan (ordered sequence of executable steps).
"""

import json
from typing import List

from core.interfaces import ParsedIntent, TaskPlan, StepSchema, LLMMessage
from core.logger import get_logger
from core.exceptions import PlanningError
from brain.llm_client import get_llm_client
from brain.tool_registry import get_all_schemas
from brain.prompt_templates import TASK_PLANNER_PROMPT

log = get_logger("agent.task_planner")

async def generate_plan(task_id: str, intent: ParsedIntent, context: List[str] = None) -> TaskPlan:
    """
    Generate an execution plan using the LLM.
    
    If the fast-path regex matched an intent directly, we can sometimes bypass
    the LLM planner for single-step tools.
    """
    context = context or []
    
    # ── 1. Fast Path Bypass ─────────────────────────────────────────
    # If the regex router found a direct hit, we can create a 1-step plan directly.
    if intent.confidence == 1.0 and intent.intent != "unknown" and intent.intent != "general_chat":
        # Check if the intent matches a known tool
        schemas = get_all_schemas()
        if any(s["name"] == intent.intent for s in schemas):
            log.debug(f"Planner fast-path: Creating 1-step plan for '{intent.intent}'")
            step = StepSchema(
                step_id=1,
                tool=intent.intent,
                args=intent.entities,
                output_key="result_1"
            )
            return TaskPlan(
                task_id=task_id,
                raw_input=intent.raw_text,
                intent=intent.intent,
                steps=[step],
                memory_ctx=context
            )
            
    # ── 2. LLM Planning ─────────────────────────────────────────────
    try:
        llm = await get_llm_client()
        tools_json = json.dumps(get_all_schemas(), indent=2)
        context_str = "\n".join(f"- {c}" for c in context) if context else "None"
        
        system_prompt = TASK_PLANNER_PROMPT.format(
            tools_json=tools_json,
            context=context_str
        )
        
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=f"Create a plan for: '{intent.normalized}'")
        ]
        
        log.info(f"Generating multi-step plan for task {task_id}...")
        response = await llm.chat(messages)
        
        # ── 3. Parse Plan ─────────────────────────────────────────────
        content = response.text.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        data = json.loads(content)
        steps_data = data.get("steps", [])
        
        steps = []
        for s in steps_data:
            steps.append(StepSchema(
                step_id=s.get("step_id", len(steps)+1),
                tool=s.get("tool", "unknown"),
                args=s.get("args", {}),
                depends_on=s.get("depends_on", []),
                output_key=s.get("output_key", "")
            ))
            
        plan = TaskPlan(
            task_id=task_id,
            raw_input=intent.raw_text,
            intent=intent.intent,
            steps=steps,
            memory_ctx=context
        )
        
        log.info(f"Generated {len(steps)}-step plan for task {task_id}")
        return plan
        
    except json.JSONDecodeError:
        raise PlanningError("LLM returned invalid JSON for plan")
    except Exception as e:
        if isinstance(e, PlanningError):
            raise
        raise PlanningError(f"Failed to generate plan: {e}") from e
