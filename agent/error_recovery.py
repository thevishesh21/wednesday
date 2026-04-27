"""
WEDNESDAY AI OS — Error Recovery
Handles retries, fallback strategies, and escalation for failed steps.
"""

import asyncio
from typing import Callable, Any

from core.logger import get_logger
from core.exceptions import StepExecutionError

log = get_logger("agent.error_recovery")

async def execute_with_retry(
    step_id: int, 
    tool_name: str, 
    func: Callable[[], Any], 
    max_retries: int = 2
) -> Any:
    """
    Execute a function with exponential backoff retries.
    """
    attempt = 0
    last_error = None
    
    while attempt <= max_retries:
        try:
            return await func()
        except Exception as e:
            attempt += 1
            last_error = e
            
            if attempt <= max_retries:
                wait_time = 1.0 * (2 ** (attempt - 1)) # 1s, 2s
                log.warning(f"Step {step_id} ({tool_name}) failed: {e}. Retrying in {wait_time}s (Attempt {attempt}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                log.error(f"Step {step_id} ({tool_name}) failed permanently after {max_retries} retries: {e}")
                
    raise StepExecutionError(
        f"Failed to execute step {step_id} ({tool_name})", 
        details={"step": step_id, "tool": tool_name, "error": str(last_error)}
    )
