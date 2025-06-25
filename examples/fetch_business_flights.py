import json
import asyncio
from fli.api.kiwi_oneway import KiwiOnewayAPI


async def search_and_print_flights():
    """
    Searches for business class flights from LHR to PEK and prints the results.
    Now uses the built-in hidden_city_only filter.
    """
    print("Searching for business class flights from LHR to PEK (hidden city only)...")
    
    # Correctly instantiate the API
    api = KiwiOnewayAPI(
        cabin_class="BUSINESS",
        hidden_city_only=True  # Use the new library feature
    )
    
    # Correctly call the async search method
    results_data = await api.search_hidden_city_flights(
        origin="LHR",
        destination="PEK",
        departure_date="2025-06-30"
    )
    
    if not results_data or not results_data.get("success"):
        error = results_data.get("error", "Unknown error")
        print(f"Search failed: {error}")
        return

    flights = results_data.get("results", {}).get("flights", [])

    if not flights:
        print("No hidden city flights found for the specified criteria.")
        return

    print(f"\nFound {len(flights)} hidden city flight options.\n")

    for i, flight in enumerate(flights, 1):
        print(f"--- Flight Option {i} ---")
        try:
            price = f"{flight.get('price', 'N/A')} {flight.get('currency', '')}"
            
            print(f"Price: {price}")
            print(f"Duration: {flight.get('duration_hours')} hours")
            print(f"Departure: {flight.get('departure_airport_name')} ({flight.get('departure_airport')}) at {flight.get('departure_time')}")
            print(f"Arrival: {flight.get('arrival_airport_name')} ({flight.get('arrival_airport')}) at {flight.get('arrival_time')}")
            print(f"Carrier: {flight.get('carrier_name')} ({flight.get('flight_number')})")

            if flight.get('is_hidden_city'):
                print(f"  Note: This is a hidden city flight. Final leg to {flight.get('hidden_destination_name')} is not taken.")
                print(f"  Savings Info: {flight.get('savings_info')}")

            print("-" * 25)

        except (KeyError, IndexError, TypeError) as e:
            print(f"Could not parse flight option {i}. Error: {e}")
            print("Raw data for this option:")
            print(json.dumps(flight, indent=2))
            print("-" * 25)

if __name__ == "__main__":
    asyncio.run(search_and_print_flights())