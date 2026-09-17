from typing import Dict, Any, Optional
from services.data_service import DataService


def get_booking_status(pnr: str, data_service: DataService) -> Optional[Dict[str, Any]]:
    """Retrieve booking record by PNR."""
    return data_service.get_booking_by_pnr(pnr)
