import uuid
from typing import Dict, Any, List, Optional
from services.data_service import DataService
from agents.resolution_agent import ResolutionAgent


class AirlineSupportWorkflow:
    """
    Manages session state, multi-turn dialogue history, customer binding,
    and interaction logging for the Streamlit UI and test runners.
    """

    def __init__(self, data_service: Optional[DataService] = None):
        self.data_service = data_service or DataService()
        self.agent = ResolutionAgent(data_service=self.data_service)
        self.conversation_id = f"CONV-{uuid.uuid4().hex[:8].upper()}"
        self.active_customer_id: Optional[str] = None
        self.chat_history: List[Dict[str, str]] = []
        self.last_turn_result: Optional[Dict[str, Any]] = None

    def set_active_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        self.active_customer_id = customer_id
        return self.data_service.get_customer_by_id(customer_id)

    def reset(self, new_customer_id: Optional[str] = None) -> None:
        self.conversation_id = f"CONV-{uuid.uuid4().hex[:8].upper()}"
        self.chat_history = []
        self.last_turn_result = None
        if new_customer_id:
            self.active_customer_id = new_customer_id

    def process_user_turn(self, user_message: str) -> Dict[str, Any]:
        self.chat_history.append({"role": "user", "content": user_message})

        result = self.agent.handle_message(
            customer_message=user_message,
            customer_id_or_pnr=self.active_customer_id,
            conversation_id=self.conversation_id,
            chat_history=self.chat_history[:-1]
        )

        self.last_turn_result = result
        self.chat_history.append({"role": "assistant", "content": result["response"]})
        return result

    def get_conversation_record(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "active_customer_id": self.active_customer_id,
            "turns": self.chat_history,
            "last_turn_result": self.last_turn_result
        }
