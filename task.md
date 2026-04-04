# Wednesday AI Assistant — Master Task List

## Planning
- [/] Create full system architecture & implementation plan
- [ ] Get user approval on the plan

## Phase 1 — Core Voice Assistant
- [ ] Project scaffolding (folders, `__init__.py`, `main.py`, `requirements.txt`)
- [ ] Voice listener module (`voice/listener.py`)
- [ ] Wake word detector (`voice/wake_word.py`)
- [ ] Text-to-speech module (`voice/speaker.py`)
- [ ] Main assistant loop integrating voice

## Phase 2 — Command Execution + Intent Shortcuts + Executor
- [ ] Intent router / shortcut system (`brain/intent_router.py`)
- [ ] Executor module (`executor/executor.py`)
- [ ] State manager (`state.py`)
- [ ] Tool registry system (`tools/registry.py`)
- [ ] App launcher tool (`tools/app_launcher.py`)
- [ ] Browser/website tool (`tools/browser.py`)
- [ ] File manager tool (`tools/file_manager.py`)

## Phase 3 — AI Task Planner + Error Handling + Fallback
- [ ] AI brain module with retry logic (`brain/ai_brain.py`)
- [ ] AI fallback engine — rule-based (`brain/fallback.py`)
- [ ] Task planner — command → steps (`brain/planner.py`)

## Phase 4 — Automation (Mouse + Keyboard)
- [ ] Screen automation module (`tools/automation.py`)
- [ ] Keyboard/mouse actions via pyautogui

## Phase 5 — Screen Vision
- [ ] Screenshot capture (`vision/screenshot.py`)
- [ ] OCR via pytesseract (`vision/ocr.py`)

## Phase 6 — Memory System
- [ ] JSON-based memory store (`memory/memory.py`)
- [ ] Save/recall user info

## Phase 7 — Reminder System
- [ ] Background reminder loop (`reminders/reminder.py`)
- [ ] Follow-up & repeat logic

## Phase 8 — Proactive Conversation
- [ ] Idle-time conversation triggers (`brain/conversation.py`)

## Phase 9 — Gesture Control (Enhanced Safety)
- [ ] Hand tracking via MediaPipe (`gesture/hand_tracker.py`)
- [ ] Gesture-to-action mapper (`gesture/gesture_mapper.py`)
- [ ] Thread manager for all background threads (`utils/thread_manager.py`)
- [ ] Voice toggle for gesture on/off
- [ ] Click cooldown + confidence threshold + frame guard

## Final
- [ ] Integration testing
- [ ] Walkthrough documentation
