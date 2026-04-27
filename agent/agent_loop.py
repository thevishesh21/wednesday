"""
WEDNESDAY AI OS — Agent Loop
The core cognitive loop: UNDERSTAND -> PLAN -> EXECUTE -> OBSERVE -> IMPROVE.
"""

import asyncio
from typing import Optional

from core.interfaces import IAgentLoop
from core.logger import get_logger
from core.event_bus import event_bus
from agent.task_queue import task_queue, QueuedTask
from brain.intent_parser import parse
from agent.task_planner import generate_plan
from agent.step_executor import StepExecutor
from agent.task_history import task_history
from brain.context_manager import ContextManager
import config

log = get_logger("agent.agent_loop")

class AgentLoop(IAgentLoop):
    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.context = ContextManager(system_prompt="You are WEDNESDAY.")
        
    async def start(self) -> None:
        """Start the background loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop_forever())
        log.info("Agent Loop started.")
        
    async def stop(self) -> None:
        """Stop the background loop."""
        self._running = False
        if self._task:
            self._task.cancel()
        log.info("Agent Loop stopped.")
        
    async def _loop_forever(self) -> None:
        """Constantly pull tasks from the queue and execute them."""
        while self._running:
            try:
                task = await task_queue.get()
                await self.handle(task.raw_input, task.task_id)
                task_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Agent loop error: {e}")
                await asyncio.sleep(1) # Prevent tight crash loop
                
    async def handle(self, raw_input: str, task_id: str = "sync-task") -> None:
        """
        Process a single user command through the full agent cycle.
        """
        log.info(f"Handling task {task_id}: '{raw_input}'")
        await event_bus.publish("agent.task_received", {"task_id": task_id, "raw_input": raw_input})
        
        executor = StepExecutor()
        plan_json_for_log = {}
        intent_label = "unknown"
        
        try:
            # 1. UNDERSTAND
            intent = await parse(raw_input, [m.content for m in self.context.get_messages()[-4:]])
            intent_label = intent.intent
            
            # Update context
            self.context.add_message("user", raw_input)
            
            # 2. PLAN
            plan = await generate_plan(task_id, intent)
            
            # Extract basic dict for logging
            plan_json_for_log = {
                "intent": plan.intent,
                "steps": [{"step_id": s.step_id, "tool": s.tool, "args": s.args} for s in plan.steps]
            }
            
            await event_bus.publish("agent.plan_ready", {"task_id": task_id, "step_count": len(plan.steps)})
            
            if not plan.steps:
                log.info(f"No actionable steps generated for task {task_id}.")
                # If conversational, speak fallback
                if intent.intent in ("general_chat", "unknown"):
                    from brain.fallback import fallback_response
                    resp = fallback_response(raw_input)
                    await event_bus.publish("voice.speaking_start", {"text": resp})
                    # In real system, this calls TTS
                    await event_bus.publish("voice.speaking_end", {})
                
                await event_bus.publish("agent.task_complete", {"task_id": task_id, "success": True, "summary": "No steps"})
                task_history.log_task(task_id, raw_input, intent_label, plan_json_for_log, True)
                return

            # 3. EXECUTE & OBSERVE
            last_result = None
            for step in plan.steps:
                last_result = await executor.execute_step(task_id, step)
                
            # 4. IMPROVE (Log success)
            summary = str(last_result.result) if last_result else "Completed"
            await event_bus.publish("agent.task_complete", {"task_id": task_id, "success": True, "summary": summary})
            task_history.log_task(task_id, raw_input, intent_label, plan_json_for_log, True)
            
            # Add to context
            self.context.add_message("assistant", f"Executed {len(plan.steps)} steps successfully. Final result: {summary}")
            self.context.trim()
            
        except Exception as e:
            # OBSERVE (Log error)
            log.error(f"Task {task_id} failed: {e}")
            await event_bus.publish("agent.error", {"task_id": task_id, "error": str(e)})
            task_history.log_task(task_id, raw_input, intent_label, plan_json_for_log, False, str(e))
            
            self.context.add_message("assistant", f"Failed to execute task: {e}")
            
# Global instance
agent_loop = AgentLoop()
