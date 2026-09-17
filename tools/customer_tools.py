from typing import Dict, Any, Optional
from services.data_service import DataService


def get_customer_profile(identifier: str, data_service: DataService) -> Optional[Dict[str, Any]]:
    """Retrieve customer by either ID or Booking Reference (PNR)."""
    clean_id = identifier.strip().lower()
    # Try ID first
    cust = data_service.get_customer_by_id(clean_id)
    if cust:
        return cust
    # Try PNR
    return data_service.get_customer_by_pnr(identifier)
