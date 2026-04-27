"""
WEDNESDAY AI OS — Intent Parser
Converts free-form normalized text to a structured ParsedIntent object.
Uses a fast regex path first, then falls back to the LLM.
"""

import json
from typing import List

from core.interfaces import ParsedIntent, LLMMessage
from core.logger import get_logger
from brain.llm_client import get_llm_client
from brain.prompt_templates import INTENT_PARSER_PROMPT
import brain.intent_router as fast_router

log = get_logger("brain.intent_parser")

async def parse(text: str, context: List[str] = None) -> ParsedIntent:
    """
    Parse natural language into a structured intent.
    
    Args:
        text: The normalized user input.
        context: Optional recent conversation context or memories.
        
    Returns:
        ParsedIntent object containing the intent label, entities, and confidence.
    """
    context = context or []
    
    # ── 1. Fast Path (Regex) ──────────────────────────────────────
    # Try the existing intent_router.py for O(1) matching
    try:
        steps = fast_router.route(text)
        if steps:
            # Reconstruct intent from the first step's tool
            # This is a bridge between the old router and the new intent system
            first_tool = steps[0].get("tool", "unknown")
            args = steps[0].get("args", {})
            
            log.debug(f"Fast path match: {first_tool} for '{text}'")
            return ParsedIntent(
                raw_text=text,
                normalized=text,
                intent=first_tool,
                entities=args,
                confidence=1.0,
                hinglish=False  # Fast path doesn't know, default False
            )
    except Exception as e:
        log.warning(f"Fast path failed: {e}")

    # ── 2. LLM Path ───────────────────────────────────────────────
    try:
        llm = await get_llm_client()
        
        # Build prompt
        messages = [
            LLMMessage(role="system", content=INTENT_PARSER_PROMPT),
        ]
        
        if context:
            context_str = "\n".join(f"- {c}" for c in context)
            messages.append(LLMMessage(
                role="system", 
                content=f"Recent Context:\n{context_str}"
            ))
            
        messages.append(LLMMessage(role="user", content=f"Classify this command: '{text}'"))
        
        # Call LLM
        response = await llm.chat(messages)
        
        # ── 3. Parse JSON Response ────────────────────────────────
        try:
            # Extract JSON block if the LLM wrapped it in markdown
            content = response.text.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            data = json.loads(content)
            
            intent = ParsedIntent(
                raw_text=text,
                normalized=text,  # Assuming normalizer ran before this
                intent=data.get("intent", "unknown"),
                entities=data.get("entities", {}),
                confidence=float(data.get("confidence", 0.0)),
                hinglish=bool(data.get("hinglish", False))
            )
            
            log.debug(f"LLM intent parsed: {intent.intent} ({intent.confidence:.2f})")
            return intent
            
        except json.JSONDecodeError:
            log.error(f"Failed to parse JSON from LLM: {response.text}")
            return ParsedIntent(raw_text=text, normalized=text, intent="unknown", confidence=0.0)
            
    except Exception as e:
        log.error(f"Intent parsing error: {e}")
        return ParsedIntent(raw_text=text, normalized=text, intent="unknown", confidence=0.0)
