"""Kiwi Round-trip Hidden City Flights API

Specialized API for searching round-trip hidden city flights using Kiwi.com's API.
Provides clean interface for finding round-trip hidden city flight opportunities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fli.models.google_flights.base import LocalizationConfig, Language, Currency
from .kiwi_flights import KiwiFlightsAPI

# Configure logging
logger = logging.getLogger(__name__)


class KiwiRoundtripAPI:
    """Specialized API for round-trip hidden city flight searches."""
    
    def __init__(self, localization_config: LocalizationConfig = None, cabin_class: str = "ECONOMY", hidden_city_only: bool = False):
        """Initialize the round-trip API client.
        
        Args:
            localization_config: Configuration for language and currency settings
            cabin_class: Cabin class for the flight search (e.g., "ECONOMY", "BUSINESS")
            hidden_city_only: If True, return only hidden city flights. Default is False.
        """
        self.localization_config = localization_config or LocalizationConfig()
        self.kiwi_client = KiwiFlightsAPI(localization_config)
        self.cabin_class = cabin_class
        self.hidden_city_only = hidden_city_only
    
    async def search_hidden_city_flights(self, origin: str, destination: str,
                                        departure_date: str, return_date: str,
                                        adults: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Search for round-trip hidden city flights.
        
        Args:
            origin: Origin airport code (e.g., 'PEK', 'JFK')
            destination: Destination airport code (e.g., 'LAX', 'LHR')
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date in YYYY-MM-DD format
            adults: Number of adult passengers (default: 1)
            limit: Maximum number of results to return (default: 10)
            
        Returns:
            Dictionary containing search results with the following structure:
            {
                "success": bool,
                "search_info": {
                    "origin": str,
                    "destination": str,
                    "departure_date": str,
                    "return_date": str,
                    "adults": int,
                    "trip_type": "roundtrip",
                    "currency": str,
                    "language": str
                },
                "results": {
                    "total_found": int,
                    "hidden_city_count": int,
                    "flights": [
                        {
                            "id": str,
                            "total_price": float,
                            "currency_symbol": str,
                            "total_duration_hours": float,
                            "is_hidden_city": bool,
                            "outbound": {
                                "departure_airport": str,
                                "departure_airport_name": str,
                                "arrival_airport": str,
                                "arrival_airport_name": str,
                                "hidden_destination_code": str,
                                "hidden_destination_name": str,
                                "carrier_name": str,
                                "flight_number": str,
                                "departure_time": str,
                                "arrival_time": str,
                                "is_hidden": bool
                            },
                            "inbound": {
                                "departure_airport": str,
                                "departure_airport_name": str,
                                "arrival_airport": str,
                                "arrival_airport_name": str,
                                "hidden_destination_code": str,
                                "hidden_destination_name": str,
                                "carrier_name": str,
                                "flight_number": str,
                                "departure_time": str,
                                "arrival_time": str,
                                "is_hidden": bool
                            },
                            "savings_info": str
                        }
                    ]
                },
                "error": str (if success is False)
            }
        """
        # Validate inputs
        validation_error = self._validate_search_params(
            origin, destination, departure_date, return_date, adults
        )
        if validation_error:
            return {
                "success": False,
                "error": validation_error
            }
        
        try:
            # Perform the search
            search_result = await self.kiwi_client.search_roundtrip_hidden_city(
                origin=origin.upper(),
                destination=destination.upper(),
                departure_date=departure_date,
                return_date=return_date,
                adults=adults,
                limit=limit,
                cabin_class=self.cabin_class
            )
            
            if not search_result.get("success"):
                return {
                    "success": False,
                    "error": search_result.get("error", "Unknown search error")
                }
            
            # If hidden_city_only is True, filter for hidden city flights
            if self.hidden_city_only:
                flights = search_result.get("flights", [])
                search_result["flights"] = [f for f in flights if f.get("is_hidden_city")]

            # Format the response
            formatted_response = self._format_roundtrip_response(
                search_result, origin, destination, departure_date, return_date, adults
            )
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Round-trip hidden city search failed: {e}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}"
            }
    
    def _validate_search_params(self, origin: str, destination: str, 
                               departure_date: str, return_date: str, 
                               adults: int) -> Optional[str]:
        """Validate search parameters.
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            departure_date: Departure date string
            return_date: Return date string
            adults: Number of adults
            
        Returns:
            Error message if validation fails, None if valid
        """
        # Validate airport codes
        if not origin or len(origin) != 3:
            return "Origin airport code must be a 3-letter IATA code"
        
        if not destination or len(destination) != 3:
            return "Destination airport code must be a 3-letter IATA code"
        
        if origin.upper() == destination.upper():
            return "Origin and destination airports must be different"
        
        # Validate dates
        try:
            dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
            ret_date = datetime.strptime(return_date, "%Y-%m-%d")
            
            if dep_date.date() < datetime.now().date():
                return "Departure date cannot be in the past"
            
            if ret_date.date() <= dep_date.date():
                return "Return date must be after departure date"
            
            # Check if return date is too far in the future (optional validation)
            if (ret_date - dep_date).days > 365:
                return "Return date cannot be more than 365 days after departure"
                
        except ValueError:
            return "Dates must be in YYYY-MM-DD format"
        
        # Validate adults
        if adults < 1 or adults > 9:
            return "Number of adults must be between 1 and 9"
        
        return None
    
    def _format_roundtrip_response(self, search_result: Dict[str, Any], 
                                  origin: str, destination: str, 
                                  departure_date: str, return_date: str,
                                  adults: int) -> Dict[str, Any]:
        """Format the search response for round-trip flights.
        
        Args:
            search_result: Raw search result from Kiwi API
            origin: Origin airport code
            destination: Destination airport code
            departure_date: Departure date
            return_date: Return date
            adults: Number of adults
            
        Returns:
            Formatted response dictionary
        """
        flights = search_result.get("flights", [])
        
        # Format flight information
        formatted_flights = []
        for flight in flights:
            # Calculate total duration in hours
            total_duration_hours = round(flight.get("duration_minutes", 0) / 60, 1)

            # Create savings information
            savings_info = self._create_savings_info(flight)

            # Format outbound and inbound legs
            outbound = flight.get("outbound", {})
            inbound = flight.get("inbound", {})

            formatted_flight = {
                "id": flight.get("id", ""),
                "total_price": flight.get("price", 0),
                "currency": flight.get("currency", "USD"),
                "currency_symbol": flight.get("currency_symbol", "$"),
                "total_duration_hours": total_duration_hours,
                "is_hidden_city": flight.get("is_hidden_city", False),
                "outbound": self._format_flight_leg(outbound),
                "inbound": self._format_flight_leg(inbound),
                "savings_info": savings_info
            }
            formatted_flights.append(formatted_flight)
        
        return {
            "success": True,
            "search_info": {
                "origin": origin.upper(),
                "destination": destination.upper(),
                "departure_date": departure_date,
                "return_date": return_date,
                "adults": adults,
                "trip_type": "roundtrip",
                "currency": self.localization_config.currency.value,
                "language": self.localization_config.language.value,
                "search_timestamp": datetime.now().isoformat()
            },
            "results": {
                "total_found": search_result.get("total_count", 0),
                "hidden_city_count": search_result.get("hidden_city_count", 0),
                "flights": formatted_flights,
                "has_more": search_result.get("has_more", False)
            }
        }
    
    def _format_flight_leg(self, leg_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format a single flight leg (outbound or inbound).
        
        Args:
            leg_data: Flight leg data
            
        Returns:
            Formatted flight leg dictionary
        """
        return {
            "departure_airport": leg_data.get("departure_airport", ""),
            "departure_airport_name": leg_data.get("departure_airport_name", ""),
            "arrival_airport": leg_data.get("arrival_airport", ""),
            "arrival_airport_name": leg_data.get("arrival_airport_name", ""),
            "hidden_destination_code": leg_data.get("hidden_destination_code", ""),
            "hidden_destination_name": leg_data.get("hidden_destination_name", ""),
            "carrier_name": leg_data.get("carrier_name", ""),
            "flight_number": leg_data.get("flight_number", ""),
            "departure_time": leg_data.get("departure_time", ""),
            "arrival_time": leg_data.get("arrival_time", ""),
            "is_hidden": leg_data.get("is_hidden", False),
            "duration_minutes": leg_data.get("duration", 0)
        }
    
    def _create_savings_info(self, flight: Dict[str, Any]) -> str:
        """Create savings information text for the flight.
        
        Args:
            flight: Flight information dictionary
            
        Returns:
            Localized savings information string
        """
        if not flight.get("is_hidden_city"):
            return ""
        
        outbound = flight.get("outbound", {})
        inbound = flight.get("inbound", {})
        
        hidden_destinations = []
        if outbound.get("hidden_destination_name"):
            hidden_destinations.append(outbound.get("hidden_destination_name"))
        if inbound.get("hidden_destination_name"):
            hidden_destinations.append(inbound.get("hidden_destination_name"))
        
        if not hidden_destinations:
            return ""
        
        if self.localization_config.language == Language.CHINESE:
            if len(hidden_destinations) == 1:
                return f"隐藏城市往返航班 - 实际目的地: {hidden_destinations[0]}"
            else:
                return f"隐藏城市往返航班 - 实际目的地: {', '.join(hidden_destinations)}"
        else:
            if len(hidden_destinations) == 1:
                return f"Hidden City Round-trip - Actual destination: {hidden_destinations[0]}"
            else:
                return f"Hidden City Round-trip - Actual destinations: {', '.join(hidden_destinations)}"


# Global instance for easy access
kiwi_roundtrip_api = KiwiRoundtripAPI()
