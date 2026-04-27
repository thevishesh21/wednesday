"""
WEDNESDAY AI OS — Task History
SQLite-backed log of completed/failed tasks.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

from core.logger import get_logger
from core.config_loader import cfg

log = get_logger("agent.task_history")

class TaskHistory:
    def __init__(self):
        # Store in project root / memory / tasks.db
        project_root = Path(cfg.log_dir_path).parent
        self.db_dir = project_root / "memory"
        self.db_dir.mkdir(exist_ok=True)
        self.db_path = self.db_dir / "wednesday_tasks.db"
        self._init_db()
        
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    raw_input TEXT,
                    intent TEXT,
                    plan_json TEXT,
                    success BOOLEAN,
                    error_msg TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            
    def log_task(self, task_id: str, raw_input: str, intent: str, plan: dict, success: bool, error_msg: str = None):
        """Log a task execution outcome."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO tasks 
                    (task_id, raw_input, intent, plan_json, success, error_msg, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_id,
                    raw_input,
                    intent,
                    json.dumps(plan),
                    success,
                    error_msg,
                    datetime.utcnow().isoformat()
                ))
                conn.commit()
        except Exception as e:
            log.error(f"Failed to log task {task_id} to history: {e}")

# Global instance
task_history = TaskHistory()
