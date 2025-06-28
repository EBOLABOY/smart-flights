"""Flight search implementation.

This module provides the core flight search functionality, interfacing with
Google Flights' API and Kiwi.com API to find available flights and their details.
"""

import json
import asyncio
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
from fli.api.kiwi_flights import KiwiFlightsAPI


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
        self, filters: FlightSearchFilters, top_n: int = 5, enhanced_search: bool = False
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """Search for flights using the given FlightSearchFilters.

        Args:
            filters: Full flight search object including airports, dates, and preferences
            top_n: Number of flights to limit the return flight search to
            enhanced_search: If True, use extended search mode (135+ flights)
                           If False, use basic search mode (12 flights)

        Returns:
            List of FlightResult objects containing flight details, or None if no results

        Raises:
            Exception: If the search fails or returns invalid data
        """
        return self._search_internal(filters, top_n, enhanced_search)

    def search_extended(
        self, filters: FlightSearchFilters, top_n: int = 50
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """Search for flights using extended search mode for maximum results.

        This method automatically uses the extended search mode that returns 135+ flights
        instead of the basic 12 flights. It's equivalent to calling search() with
        enhanced_search=True but provides a cleaner API for users who always want
        maximum results.

        Args:
            filters: Full flight search object including airports, dates, and preferences
            top_n: Number of flights to limit the return flight search to (default: 50)
                  For round-trip flights, this limits the number of outbound flights
                  to consider for pairing with return flights.

        Returns:
            List of FlightResult objects containing flight details, or None if no results

        Raises:
            Exception: If the search fails or returns invalid data

        Note:
            For round-trip flights, the total number of combinations will be:
            min(outbound_flights, top_n) × return_flights_per_outbound
            To get more combinations, increase the top_n parameter.
        """
        return self._search_internal(filters, top_n, enhanced_search=True)

    def search_extended_max_combinations(
        self, filters: FlightSearchFilters, max_outbound: int = 100, max_return_per_outbound: int = 50
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """Search for flights with maximum combinations for round-trip flights.

        This method is optimized for round-trip searches where you want to maximize
        the number of flight combinations while controlling the search scope.

        Args:
            filters: Full flight search object including airports, dates, and preferences
            max_outbound: Maximum number of outbound flights to consider (default: 100)
            max_return_per_outbound: Maximum return flights per outbound flight (default: 50)

        Returns:
            List of FlightResult objects or flight pairs, or None if no results

        Raises:
            Exception: If the search fails or returns invalid data

        Note:
            This method can generate up to max_outbound × max_return_per_outbound combinations
            for round-trip flights, but will take longer to execute.
        """
        if filters.trip_type == TripType.ROUND_TRIP:
            return self._search_internal(filters, max_outbound, enhanced_search=True)
        else:
            # For one-way flights, use the standard extended search
            return self._search_internal(filters, max_outbound, enhanced_search=True)

    def _search_internal(
        self, filters: FlightSearchFilters, top_n: int = 5, enhanced_search: bool = False
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
        encoded_filters = filters.encode(enhanced_search=enhanced_search)

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
                return_flights = self._search_internal(selected_flight_filters, top_n=top_n, enhanced_search=enhanced_search)
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


class SearchKiwiFlights:
    """Kiwi hidden city flight search implementation with Google Flights compatible interface.

    This class provides the same interface as SearchFlights but searches for hidden city flights
    using Kiwi.com's API, making it easy to switch between Google Flights and Kiwi searches.
    """

    def __init__(self, localization_config: LocalizationConfig = None):
        """Initialize the Kiwi search client.

        Args:
            localization_config: Configuration for language and currency settings
        """
        self.localization_config = localization_config or LocalizationConfig()
        self.kiwi_client = KiwiFlightsAPI(localization_config)

    def search(
        self, filters: FlightSearchFilters, top_n: int = 5
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """Search for hidden city flights using the same interface as Google Flights.

        Args:
            filters: Flight search filters (same as Google Flights)
            top_n: Number of flights to return

        Returns:
            List of FlightResult objects or flight pairs for round-trip
        """
        # Run async search in sync context
        return asyncio.run(self._async_search(filters, top_n))

    async def _async_search(
        self, filters: FlightSearchFilters, top_n: int = 5
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """Async implementation of the search method."""
        try:
            # Extract search parameters from filters
            origin = filters.flight_segments[0].departure_airport[0][0].name
            destination = filters.flight_segments[0].arrival_airport[0][0].name
            departure_date = filters.flight_segments[0].travel_date
            adults = filters.passenger_info.adults

            # Convert seat type to cabin class
            cabin_class = self._convert_seat_type_to_cabin_class(filters.seat_type)

            if filters.trip_type == TripType.ONE_WAY:
                # Single trip search
                result = await self.kiwi_client.search_oneway_hidden_city(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    adults=adults,
                    limit=top_n,
                    cabin_class=cabin_class
                )

                if result.get("success"):
                    flights = []
                    for flight_data in result.get("flights", []):
                        # Return all flights, not just hidden city flights
                        # This allows users to see both regular and hidden city options
                        try:
                            flight_result = self._convert_kiwi_to_flight_result(flight_data)
                            flights.append(flight_result)
                        except Exception as e:
                            # Skip flights that can't be converted
                            continue
                    return flights[:top_n]

            elif filters.trip_type == TripType.ROUND_TRIP:
                # Round trip search
                if len(filters.flight_segments) < 2:
                    return None

                return_date = filters.flight_segments[1].travel_date
                result = await self.kiwi_client.search_roundtrip_hidden_city(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date,
                    adults=adults,
                    limit=top_n,
                    cabin_class=cabin_class
                )

                if result.get("success"):
                    flight_pairs = []
                    for flight_data in result.get("flights", []):
                        # Return all flights, not just hidden city flights
                        # This allows users to see both regular and hidden city options
                        try:
                            outbound = self._convert_kiwi_roundtrip_to_flight_result(
                                flight_data, "outbound"
                            )
                            inbound = self._convert_kiwi_roundtrip_to_flight_result(
                                flight_data, "inbound"
                            )
                            flight_pairs.append((outbound, inbound))
                        except Exception as e:
                            # Skip flights that can't be converted
                            continue
                    return flight_pairs[:top_n]

            return None

        except Exception as e:
            raise Exception(f"Kiwi search failed: {str(e)}") from e

    def _convert_kiwi_to_flight_result(self, kiwi_flight: dict) -> FlightResult:
        """Convert Kiwi flight data to FlightResult format with complete route information.

        Args:
            kiwi_flight: Flight data from Kiwi API

        Returns:
            FlightResult object compatible with Google Flights format
        """
        try:
            # Create flight legs for all segments
            legs = []
            route_segments = kiwi_flight.get("route_segments", [])

            if route_segments:
                # Multi-segment flight - create leg for each segment
                for segment in route_segments:
                    leg = FlightLeg(
                        airline=self._parse_airline_from_code(segment.get("carrier", "")),
                        flight_number=segment.get("flight_number", ""),
                        departure_airport=self._parse_airport_from_code(segment.get("from", "")),
                        arrival_airport=self._parse_airport_from_code(segment.get("to", "")),
                        departure_datetime=self._parse_kiwi_datetime(segment.get("departure_time", "")),
                        arrival_datetime=self._parse_kiwi_datetime(segment.get("arrival_time", "")),
                        duration=segment.get("duration", 0) // 60,  # Convert to minutes
                    )
                    legs.append(leg)
            else:
                # Single segment flight - fallback to original logic
                leg = FlightLeg(
                    airline=self._parse_airline_from_code(kiwi_flight.get("carrier_code", "")),
                    flight_number=kiwi_flight.get("flight_number", ""),
                    departure_airport=self._parse_airport_from_code(kiwi_flight.get("departure_airport", "")),
                    arrival_airport=self._parse_airport_from_code(kiwi_flight.get("arrival_airport", "")),
                    departure_datetime=self._parse_kiwi_datetime(kiwi_flight.get("departure_time", "")),
                    arrival_datetime=self._parse_kiwi_datetime(kiwi_flight.get("arrival_time", "")),
                    duration=kiwi_flight.get("duration_minutes", 0),
                )
                legs.append(leg)

            # Extract and convert price safely
            price_value = kiwi_flight.get("price", 0)
            if isinstance(price_value, str):
                try:
                    price_value = float(price_value)
                except (ValueError, TypeError):
                    price_value = 0
            elif price_value is None:
                price_value = 0

            # Create flight result
            flight_result = FlightResult(
                price=price_value,
                duration=kiwi_flight.get("duration_minutes", 0),
                stops=max(0, kiwi_flight.get("segment_count", 1) - 1),
                legs=legs,
                # Add hidden city information as metadata
                hidden_city_info={
                    "is_hidden_city": kiwi_flight.get("is_hidden_city", False),
                    "hidden_destination_code": kiwi_flight.get("hidden_destination_code", ""),
                    "hidden_destination_name": kiwi_flight.get("hidden_destination_name", ""),
                    "is_throwaway": kiwi_flight.get("is_throwaway", False),
                    "route_segments": route_segments,  # Include complete route info
                }
            )

            return flight_result

        except Exception as e:
            raise Exception(f"Failed to convert Kiwi flight data: {e}") from e

    def _convert_kiwi_roundtrip_to_flight_result(self, kiwi_flight: dict, direction: str) -> FlightResult:
        """Convert Kiwi round-trip flight data to FlightResult format.

        Args:
            kiwi_flight: Round-trip flight data from Kiwi API
            direction: "outbound" or "inbound"

        Returns:
            FlightResult object for the specified direction
        """
        try:
            leg_data = kiwi_flight.get(direction, {})

            # Create flight leg
            leg = FlightLeg(
                airline=self._parse_airline_from_code(leg_data.get("carrier_code", "")),
                flight_number=leg_data.get("flight_number", ""),
                departure_airport=self._parse_airport_from_code(leg_data.get("departure_airport", "")),
                arrival_airport=self._parse_airport_from_code(leg_data.get("arrival_airport", "")),
                departure_datetime=self._parse_kiwi_datetime(leg_data.get("departure_time", "")),
                arrival_datetime=self._parse_kiwi_datetime(leg_data.get("arrival_time", "")),
                duration=leg_data.get("duration", 0),
            )

            # Extract and convert price safely for round-trip
            total_price = kiwi_flight.get("total_price", 0)
            if total_price == 0:
                # Fallback to main price field
                total_price = kiwi_flight.get("price", 0)

            if isinstance(total_price, str):
                try:
                    total_price = float(total_price)
                except (ValueError, TypeError):
                    total_price = 0
            elif total_price is None:
                total_price = 0

            # Split price for each direction (outbound/inbound)
            direction_price = total_price / 2 if total_price > 0 else 0

            # Create flight result
            flight_result = FlightResult(
                price=direction_price,
                duration=leg_data.get("duration", 0),
                stops=0,  # Assuming direct flights for now
                legs=[leg],
                # Add hidden city information
                hidden_city_info={
                    "is_hidden_city": leg_data.get("is_hidden", False),
                    "hidden_destination_code": leg_data.get("hidden_destination_code", ""),
                    "hidden_destination_name": leg_data.get("hidden_destination_name", ""),
                    "direction": direction,
                    "total_price": total_price,  # Store total price for reference
                }
            )

            return flight_result

        except Exception as e:
            raise Exception(f"Failed to convert Kiwi round-trip flight data: {e}") from e

    def _parse_airline_from_code(self, airline_code: str) -> Airline:
        """Convert airline code to Airline enum.

        Args:
            airline_code: Airline code (e.g., "CA", "BA")

        Returns:
            Airline enum value or default
        """
        try:
            if not airline_code:
                return list(Airline)[0]  # Default airline

            # Handle numeric codes
            if airline_code[0].isdigit():
                airline_code = f"_{airline_code}"

            # Try to get the airline enum
            if hasattr(Airline, airline_code):
                return getattr(Airline, airline_code)
            else:
                # Return default if not found
                return list(Airline)[0]

        except Exception:
            return list(Airline)[0]

    def _parse_airport_from_code(self, airport_code: str) -> Airport:
        """Convert airport code to Airport enum.

        Args:
            airport_code: Airport code (e.g., "LHR", "PEK")

        Returns:
            Airport enum value or default
        """
        try:
            if not airport_code:
                return list(Airport)[0]  # Default airport

            # Try to get the airport enum
            if hasattr(Airport, airport_code):
                return getattr(Airport, airport_code)
            else:
                # Return default if not found
                return list(Airport)[0]

        except Exception:
            return list(Airport)[0]

    def _parse_kiwi_datetime(self, datetime_str: str) -> datetime:
        """Parse Kiwi datetime string to datetime object.

        Args:
            datetime_str: Datetime string from Kiwi API

        Returns:
            Parsed datetime object or current time as fallback
        """
        try:
            if not datetime_str:
                return datetime.now()

            # Try different datetime formats that Kiwi might use
            formats = [
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%SZ",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(datetime_str, fmt)
                except ValueError:
                    continue

            # If all formats fail, return current time
            return datetime.now()

        except Exception:
            return datetime.now()

    def _convert_seat_type_to_cabin_class(self, seat_type) -> str:
        """Convert SeatType enum to Kiwi API cabin class string.

        Args:
            seat_type: SeatType enum value

        Returns:
            Cabin class string for Kiwi API
        """
        # Import here to avoid circular imports
        from fli.models.google_flights.base import SeatType

        if seat_type == SeatType.BUSINESS:
            return "BUSINESS"
        elif seat_type == SeatType.FIRST:
            return "FIRST"
        else:
            return "ECONOMY"  # Default to economy
