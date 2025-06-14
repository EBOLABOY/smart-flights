"""Flight search implementation.

This module provides the core flight search functionality, interfacing directly
with Google Flights' API to find available flights and their details.
"""

import json
from copy import deepcopy
from datetime import datetime

from fli.models import (
    Airline,
    Airport,
    FlightLeg,
    FlightResult,
    FlightSearchFilters,
)
from fli.models.google_flights.base import LocalizationConfig, TripType
from fli.search.client import get_client


class SearchFlights:
    """Flight search implementation using Google Flights' API.

    This class handles searching for specific flights with detailed filters,
    parsing the results into structured data models.
    """

    BASE_URL = "https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights.FlightsFrontendService/GetShoppingResults"
    DEFAULT_HEADERS = {
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
    }

    def __init__(self, localization_config: LocalizationConfig = None):
        """Initialize the search client for flight searches.

        Args:
            localization_config: Configuration for language and currency settings

        """
        self.client = get_client()
        self.localization_config = localization_config or LocalizationConfig()

    def search(
        self, filters: FlightSearchFilters, top_n: int = 5
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """Search for flights using the given FlightSearchFilters.

        Args:
            filters: Full flight search object including airports, dates, and preferences
            top_n: Number of flights to limit the return flight search to

        Returns:
            List of FlightResult objects containing flight details, or None if no results

        Raises:
            Exception: If the search fails or returns invalid data

        """
        encoded_filters = filters.encode()

        # Build URL with localization parameters
        url_with_params = f"{self.BASE_URL}?hl={self.localization_config.api_language_code}&gl={self.localization_config.region}&curr={self.localization_config.api_currency_code}"

        try:
            response = self.client.post(
                url=url_with_params,
                data=f"f.req={encoded_filters}",
                impersonate="chrome",
                allow_redirects=True,
            )
            response.raise_for_status()

            parsed = json.loads(response.text.lstrip(")]}'"))[0][2]
            if not parsed:
                return None

            encoded_filters = json.loads(parsed)
            flights_data = [
                item
                for i in [2, 3]
                if isinstance(encoded_filters[i], list)
                for item in encoded_filters[i][0]
            ]
            flights = [self._parse_flights_data(flight) for flight in flights_data]

            if (
                filters.trip_type == TripType.ONE_WAY
                or filters.flight_segments[0].selected_flight is not None
            ):
                return flights

            # Get the return flights if round-trip
            flight_pairs = []
            # Call the search again with the return flight data
            for selected_flight in flights[:top_n]:
                selected_flight_filters = deepcopy(filters)
                selected_flight_filters.flight_segments[0].selected_flight = selected_flight
                return_flights = self.search(selected_flight_filters, top_n=top_n)
                if return_flights is not None:
                    flight_pairs.extend(
                        (selected_flight, return_flight) for return_flight in return_flights
                    )

            return flight_pairs

        except Exception as e:
            raise Exception(f"Search failed: {str(e)}") from e

    @staticmethod
    def _parse_flights_data(data: list) -> FlightResult:
        """Parse raw flight data into a structured FlightResult.

        Args:
            data: Raw flight data from the API response

        Returns:
            Structured FlightResult object with all flight details

        """
        try:
            # Safe access with fallbacks for different data structures
            price = SearchFlights._safe_get_nested(data, [1, 0, -1], 0)
            duration = SearchFlights._safe_get_nested(data, [0, 9], 0)

            # Handle different flight leg structures
            flight_legs_data = SearchFlights._safe_get_nested(data, [0, 2], [])
            stops = max(0, len(flight_legs_data) - 1) if flight_legs_data else 0

            legs = []
            for fl in flight_legs_data:
                try:
                    leg = FlightLeg(
                        airline=SearchFlights._parse_airline_safe(fl),
                        flight_number=SearchFlights._safe_get_nested(fl, [22, 1], ""),
                        departure_airport=SearchFlights._parse_airport_safe(fl, 3),
                        arrival_airport=SearchFlights._parse_airport_safe(fl, 6),
                        departure_datetime=SearchFlights._parse_datetime_safe(fl, [20], [8]),
                        arrival_datetime=SearchFlights._parse_datetime_safe(fl, [21], [10]),
                        duration=SearchFlights._safe_get_nested(fl, [11], 0),
                    )
                    legs.append(leg)
                except Exception as e:
                    # Log the error but continue processing other legs
                    print(f"Warning: Failed to parse flight leg: {e}")
                    continue

            flight = FlightResult(
                price=price,
                duration=duration,
                stops=stops,
                legs=legs,
            )
            return flight

        except Exception as e:
            # Provide detailed error information for debugging
            raise Exception(
                f"Failed to parse flight data: {e}. Data structure: {type(data)} with length {len(data) if hasattr(data, '__len__') else 'unknown'}"
            ) from e

    @staticmethod
    def _safe_get_nested(data: any, path: list[int], default: any = None) -> any:
        """Safely access nested data structure with fallback.

        Args:
            data: The data structure to access
            path: List of indices/keys to traverse
            default: Default value if access fails

        Returns:
            The value at the specified path or default value

        """
        try:
            current = data
            for key in path:
                if hasattr(current, "__getitem__") and len(current) > key:
                    current = current[key]
                else:
                    return default
            return current
        except (IndexError, KeyError, TypeError):
            return default

    @staticmethod
    def _parse_airline_safe(flight_leg: list) -> Airline:
        """Safely parse airline from flight leg data.

        Args:
            flight_leg: Flight leg data from API

        Returns:
            Airline enum or default airline

        """
        try:
            # Try multiple possible locations for airline code
            airline_code = (
                SearchFlights._safe_get_nested(flight_leg, [22, 0])
                or SearchFlights._safe_get_nested(flight_leg, [0, 0])
                or SearchFlights._safe_get_nested(flight_leg, [1, 0])
                or "UNKNOWN"
            )
            return SearchFlights._parse_airline(airline_code)
        except Exception:
            # Return a default airline if parsing fails
            return Airline.UNKNOWN if hasattr(Airline, "UNKNOWN") else list(Airline)[0]

    @staticmethod
    def _parse_airport_safe(flight_leg: list, index: int) -> Airport:
        """Safely parse airport from flight leg data.

        Args:
            flight_leg: Flight leg data from API
            index: Index where airport code should be located

        Returns:
            Airport enum or default airport

        """
        try:
            airport_code = SearchFlights._safe_get_nested(flight_leg, [index])
            if airport_code:
                return SearchFlights._parse_airport(airport_code)
            # Try alternative locations
            for alt_index in [3, 4, 5, 6, 7]:
                airport_code = SearchFlights._safe_get_nested(flight_leg, [alt_index])
                if airport_code and isinstance(airport_code, str) and len(airport_code) == 3:
                    return SearchFlights._parse_airport(airport_code)
            # If all fails, return a default
            return list(Airport)[0]
        except Exception:
            return list(Airport)[0]

    @staticmethod
    def _parse_datetime_safe(
        flight_leg: list, date_path: list[int], time_path: list[int]
    ) -> datetime:
        """Safely parse datetime from flight leg data.

        Args:
            flight_leg: Flight leg data from API
            date_path: Path to date array
            time_path: Path to time array

        Returns:
            Parsed datetime or current datetime as fallback

        """
        try:
            date_arr = SearchFlights._safe_get_nested(flight_leg, date_path, [2025, 1, 1])
            time_arr = SearchFlights._safe_get_nested(flight_leg, time_path, [0, 0])

            if date_arr and time_arr:
                return SearchFlights._parse_datetime(date_arr, time_arr)
        except Exception:
            pass

        # Fallback to current datetime
        from datetime import datetime

        return datetime.now()

    @staticmethod
    def _parse_datetime(date_arr: list[int], time_arr: list[int]) -> datetime:
        """Convert date and time arrays to datetime.

        Args:
            date_arr: List of integers [year, month, day]
            time_arr: List of integers [hour, minute]

        Returns:
            Parsed datetime object

        Raises:
            ValueError: If arrays contain only None values

        """
        if not any(x is not None for x in date_arr) or not any(x is not None for x in time_arr):
            raise ValueError("Date and time arrays must contain at least one non-None value")

        return datetime(*(x or 0 for x in date_arr), *(x or 0 for x in time_arr))

    @staticmethod
    def _parse_airline(airline_code: str) -> Airline:
        """Convert airline code to Airline enum.

        Args:
            airline_code: Raw airline code from API

        Returns:
            Corresponding Airline enum value

        """
        if airline_code[0].isdigit():
            airline_code = f"_{airline_code}"
        return getattr(Airline, airline_code)

    @staticmethod
    def _parse_airport(airport_code: str) -> Airport:
        """Convert airport code to Airport enum.

        Args:
            airport_code: Raw airport code from API

        Returns:
            Corresponding Airport enum value

        """
        return getattr(Airport, airport_code)
