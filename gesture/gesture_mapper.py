"""
Wednesday AI Assistant — Gesture Mapper
Maps hand gestures to mouse actions:
  - Index finger → move mouse
  - Thumb + Index pinch → left click
  - Thumb + Middle pinch → right click
  - Pinch zoom (two hands) → scroll

Includes smoothing, cooldown, and frame guard for safety.
"""

import time
import pyautogui
import cv2
from gesture.hand_tracker import HandTracker, THUMB_TIP, INDEX_TIP, MIDDLE_TIP
from utils.logger import get_logger
import config

log = get_logger("gesture_mapper")

# ── Safety settings ─────────────────────────────────────────────
pyautogui.FAILSAFE = True
SCREEN_W, SCREEN_H = pyautogui.size()

# ── Smoothing state ─────────────────────────────────────────────
_smooth_x, _smooth_y = 0.0, 0.0
_last_click_time = 0.0
_click_frame_count = 0
_right_click_frame_count = 0


def _smooth(x: int, y: int) -> tuple[int, int]:
    """Apply exponential smoothing to mouse position."""
    global _smooth_x, _smooth_y
    alpha = config.GESTURE_SMOOTHING_ALPHA
    _smooth_x = alpha * x + (1 - alpha) * _smooth_x
    _smooth_y = alpha * y + (1 - alpha) * _smooth_y
    return int(_smooth_x), int(_smooth_y)


def _can_click() -> bool:
    """Check click cooldown."""
    global _last_click_time
    now = time.time() * 1000  # ms
    if now - _last_click_time > config.GESTURE_CLICK_COOLDOWN_MS:
        _last_click_time = now
        return True
    return False


def gesture_loop(stop_event) -> None:
    """
    Main gesture control loop. Runs in a background thread.
    Called by ThreadManager with a stop_event.

    Maps:
      - Index finger position → mouse cursor
      - Thumb-Index pinch (<40px) → left click
      - Thumb-Middle pinch (<40px) → right click
    """
    global _click_frame_count, _right_click_frame_count

    tracker = HandTracker(max_hands=1)

    if not tracker.start_camera():
        log.error("Gesture control failed — camera not available.")
        return

    log.info("Gesture control started.")
    frame_guard = config.GESTURE_FRAME_GUARD

    try:
        while not stop_event.is_set():
            frame, results = tracker.get_frame()
            if frame is None:
                continue

            landmarks = tracker.get_landmarks(results, frame.shape)

            if not landmarks:
                _click_frame_count = 0
                _right_click_frame_count = 0
                continue

            # ── Get key finger positions ─────────────────────
            lm_dict = {idx: (x, y) for idx, x, y in landmarks}
            index_pos = lm_dict.get(INDEX_TIP)
            thumb_pos = lm_dict.get(THUMB_TIP)
            middle_pos = lm_dict.get(MIDDLE_TIP)

            if not index_pos:
                continue

            # ── Map camera coords → screen coords ───────────
            cam_h, cam_w = frame.shape[:2]
            screen_x = int(index_pos[0] / cam_w * SCREEN_W)
            screen_y = int(index_pos[1] / cam_h * SCREEN_H)

            # Clamp to screen bounds
            screen_x = max(0, min(SCREEN_W - 1, screen_x))
            screen_y = max(0, min(SCREEN_H - 1, screen_y))

            # Apply smoothing
            sx, sy = _smooth(screen_x, screen_y)

            # ── Move mouse ───────────────────────────────────
            try:
                pyautogui.moveTo(sx, sy, _pause=False)
            except pyautogui.FailSafeException:
                log.warning("PyAutoGUI failsafe triggered!")
                break

            # ── Left Click: thumb + index pinch ──────────────
            if thumb_pos and index_pos:
                dist = HandTracker.distance(thumb_pos, index_pos)
                if dist < 40:
                    _click_frame_count += 1
                    if _click_frame_count >= frame_guard and _can_click():
                        pyautogui.click()
                        log.debug("Gesture: LEFT CLICK")
                        _click_frame_count = 0
                else:
                    _click_frame_count = 0

            # ── Right Click: thumb + middle pinch ────────────
            if thumb_pos and middle_pos:
                dist = HandTracker.distance(thumb_pos, middle_pos)
                if dist < 40:
                    _right_click_frame_count += 1
                    if _right_click_frame_count >= frame_guard and _can_click():
                        pyautogui.rightClick()
                        log.debug("Gesture: RIGHT CLICK")
                        _right_click_frame_count = 0
                else:
                    _right_click_frame_count = 0

            # ── Optional: show debug window ──────────────────
            # Uncomment these lines to see camera feed with landmarks:
            # tracker.draw_landmarks(frame, results)
            # cv2.imshow("Wednesday Gesture", frame)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break

    except Exception as e:
        log.error(f"Gesture loop error: {e}")
    finally:
        tracker.cleanup()
        log.info("Gesture control stopped.")
