import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class DataService:
    """
    Centralized data service providing read access to customer profiles,
    bookings, service policies, action definitions, and tone guidelines.
    Guarantees strict separation of data from application logic.
    """

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).resolve().parent.parent / "data"

        self._customers: List[Dict[str, Any]] = []
        self._bookings: List[Dict[str, Any]] = []
        self._policies: Dict[str, Any] = {}
        self._actions: Dict[str, Any] = {}
        self._source_metadata: Dict[str, Any] = {}
        self._tone_guidelines: Dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        """Reload all data files from disk. Enables hot reload when data files change."""
        cust_path = self.data_dir / "customers.json"
        if cust_path.exists():
            with open(cust_path, "r", encoding="utf-8") as f:
                self._customers = json.load(f)

        book_path = self.data_dir / "bookings.json"
        if book_path.exists():
            with open(book_path, "r", encoding="utf-8") as f:
                self._bookings = json.load(f)

        pol_path = self.data_dir / "policies.json"
        if pol_path.exists():
            with open(pol_path, "r", encoding="utf-8") as f:
                self._policies = json.load(f)

        act_path = self.data_dir / "actions.json"
        if act_path.exists():
            with open(act_path, "r", encoding="utf-8") as f:
                self._actions = json.load(f)

        meta_path = self.data_dir / "source_metadata.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                self._source_metadata = json.load(f)

        tone_path = self.data_dir / "tone_guidelines.json"
        if tone_path.exists():
            with open(tone_path, "r", encoding="utf-8") as f:
                self._tone_guidelines = json.load(f)

    def get_all_customers(self) -> List[Dict[str, Any]]:
        return self._customers

    def get_customer_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        for c in self._customers:
            if c.get("id") == customer_id:
                return c
        return None

    def get_customer_by_pnr(self, pnr: str) -> Optional[Dict[str, Any]]:
        clean_pnr = pnr.strip().upper()
        for c in self._customers:
            if c.get("booking_reference", "").strip().upper() == clean_pnr:
                return c
        return None

    def get_all_bookings(self) -> List[Dict[str, Any]]:
        return self._bookings

    def get_booking_by_pnr(self, pnr: str) -> Optional[Dict[str, Any]]:
        clean_pnr = pnr.strip().upper()
        for b in self._bookings:
            if b.get("pnr", "").strip().upper() == clean_pnr:
                return b
        return None

    def get_policy(self, policy_name: str) -> Optional[Dict[str, Any]]:
        return self._policies.get(policy_name)

    def get_all_policies(self) -> Dict[str, Any]:
        return self._policies

    def get_actions(self) -> Dict[str, Any]:
        return self._actions

    def get_tone_guidelines(self) -> Dict[str, Any]:
        return self._tone_guidelines

    def get_source_metadata(self) -> Dict[str, Any]:
        return self._source_metadata
