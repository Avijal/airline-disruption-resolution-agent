import json
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class AuditLogger:
    def __init__(self, log_file: Optional[Path] = None):
        if log_file:
            self.log_file = log_file
        else:
            self.log_file = Path(__file__).resolve().parent.parent / "data" / "audit_log.json"

        self._in_memory_logs: List[Dict[str, Any]] = []
        self._load_existing()

    def _load_existing(self) -> None:
        if self.log_file.exists():
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self._in_memory_logs = data
            except Exception:
                self._in_memory_logs = []

    def record_event(
        self,
        conversation_id: str,
        customer: str,
        pnr: str,
        intent: str,
        policy_used: List[str],
        decision: str,
        action: List[str],
        status: str,
        reason: str,
        source_citations: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        event = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "conversation_id": conversation_id,
            "customer": customer,
            "pnr": pnr,
            "intent": intent,
            "policy_used": policy_used,
            "decision": decision,
            "action": action,
            "status": status,
            "reason": reason,
            "source_citations": source_citations or [],
            "extra": extra or {}
        }
        self._in_memory_logs.append(event)
        self._persist()
        return event

    def _persist(self) -> None:
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(self._in_memory_logs, f, indent=2)
        except Exception as e:
            # Fallback for read-only environments
            pass

    def get_all_events(self) -> List[Dict[str, Any]]:
        return self._in_memory_logs

    def get_events_for_conversation(self, conversation_id: str) -> List[Dict[str, Any]]:
        return [e for e in self._in_memory_logs if e.get("conversation_id") == conversation_id]

    def clear(self) -> None:
        self._in_memory_logs = []
        self._persist()
