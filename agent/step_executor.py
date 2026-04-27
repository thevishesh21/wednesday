"""
WEDNESDAY AI OS — Step Executor
Executes individual steps from a TaskPlan, handling variable binding.
"""

import asyncio
from typing import Dict, Any

from core.interfaces import StepSchema, SkillResult
from core.logger import get_logger
from core.event_bus import event_bus
from agent.error_recovery import execute_with_retry
from core.exceptions import ToolNotFoundError

log = get_logger("agent.step_executor")

# In Phase 4, we bridge to the existing executor logic, but handle variable binding here.
# We import from tools.registry to actually run the tools.
from tools.registry import list_tools, execute as execute_tool

class StepExecutor:
    def __init__(self):
        self.state: Dict[str, Any] = {}
        
    def _bind_args(self, args: dict) -> dict:
        """Replace '{output_key}' in args with actual values from state."""
        bound = {}
        for k, v in args.items():
            if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
                state_key = v[1:-1]
                if state_key in self.state:
                    bound[k] = self.state[state_key]
                else:
                    bound[k] = v # leave as is if not found
            else:
                bound[k] = v
        return bound
        
    async def execute_step(self, task_id: str, step: StepSchema) -> SkillResult:
        """Execute a single step with retries and output binding."""
        await event_bus.publish("agent.step_started", {
            "task_id": task_id, 
            "step": step.step_id, 
            "tool": step.tool
        })
        
        # Bind args
        bound_args = self._bind_args(step.args)
        
        # Ensure tool exists
        tools = list_tools()
        if step.tool not in tools:
            raise ToolNotFoundError(f"Tool '{step.tool}' not registered")
            
        # Define the execution thunk
        async def _run():
            # execute_tool is currently synchronous, so we run it in an executor
            loop = asyncio.get_event_loop()
            result_str = await loop.run_in_executor(None, execute_tool, step.tool, bound_args)
            return SkillResult.ok(step.tool, result_str)
            
        try:
            # Execute with retry
            result = await execute_with_retry(step.step_id, step.tool, _run)
            
            # Store output if requested
            if step.output_key and result.success:
                self.state[step.output_key] = result.result
                
            await event_bus.publish("agent.step_done", {
                "task_id": task_id,
                "step": step.step_id,
                "success": True,
                "result": result.result
            })
            
            return result
            
        except Exception as e:
            await event_bus.publish("agent.step_done", {
                "task_id": task_id,
                "step": step.step_id,
                "success": False,
                "result": str(e)
            })
            raise
