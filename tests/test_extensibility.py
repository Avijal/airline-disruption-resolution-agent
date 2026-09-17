import json
import tempfile
import shutil
from pathlib import Path
from services.data_service import DataService
from core.policy_engine import PolicyEngine
from agents.resolution_agent import ResolutionAgent


def test_adding_fourth_customer_without_code_changes():
    """
    Validates that adding a new customer and booking to JSON data files
    instantly resolves correctly through the generic policy engine
    without ANY modification to Python logic.
    """
    # Create temporary directory with copy of data files + new 4th customer
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        orig_data_dir = Path(__file__).resolve().parent.parent / "data"

        for f in orig_data_dir.glob("*.json"):
            shutil.copy(f, tmp_path / f.name)

        # Append 4th customer: Karan Roy (Bronze, PNR ZX9901)
        with open(tmp_path / "customers.json", "r", encoding="utf-8") as f:
            customers = json.load(f)

        customers.append({
            "id": "karan_roy",
            "name": "Karan Roy",
            "loyalty_tier": "Bronze",
            "booking_reference": "ZX9901",
            "contact": {
                "email": "karan.roy@example.com",
                "phone": "+91-98xxxxxxx4"
            },
            "travel_history": {
                "flights_last_12_months": 1,
                "prior_complaints": []
            }
        })

        with open(tmp_path / "customers.json", "w", encoding="utf-8") as f:
            json.dump(customers, f, indent=2)

        # Append booking for ZX9901 (Delayed 2 hours)
        with open(tmp_path / "bookings.json", "r", encoding="utf-8") as f:
            bookings = json.load(f)

        bookings.append({
            "pnr": "ZX9901",
            "customer_id": "karan_roy",
            "customer_name": "Karan Roy",
            "segments": [
                {
                    "segment_id": "ZX9901-1",
                    "flight_number": "SK-555",
                    "route": "Delhi → Pune",
                    "origin": "Delhi",
                    "destination": "Pune",
                    "date": "Wed 23 Sep 2026",
                    "scheduled_departure": "10:00",
                    "new_departure": "12:00",
                    "status": "Delayed",
                    "disruption_type": "airline_caused",
                    "disruption_reason": "aircraft maintenance",
                    "delay_hours": 2.0,
                    "cabin_class": "Economy"
                }
            ],
            "payment_method": "Original Credit Card (ending 1122)"
        })

        with open(tmp_path / "bookings.json", "w", encoding="utf-8") as f:
            json.dump(bookings, f, indent=2)

        # Initialize agent pointing to this new data directory
        custom_data_service = DataService(data_dir=str(tmp_path))
        agent = ResolutionAgent(data_service=custom_data_service)

        # Verify agent resolves Karan Roy seamlessly
        result = agent.handle_message(
            customer_message="My flight SK-555 is delayed 2 hours. What can I get?",
            customer_id_or_pnr="karan_roy"
        )

        assert result["status"] == "RESOLVED"
        assert result["customer_context"]["name"] == "Karan Roy"
        assert result["booking_context"]["pnr"] == "ZX9901"

        # 2-hour delay qualifies for ₹500 meal voucher only (no lounge, no hotel)
        actions = [a["action"] for a in result["executed_actions"]]
        assert "issue_meal_voucher" in actions
        assert "grant_lounge_access" not in actions
        assert "arrange_hotel_delayed_hours" not in actions
