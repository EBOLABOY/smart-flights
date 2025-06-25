"""Kiwi One-way Hidden City Flights API

Specialized API for searching one-way hidden city flights using Kiwi.com's API.
Provides clean interface for finding hidden city flight opportunities.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fli.models.google_flights.base import LocalizationConfig, Language, Currency
from .kiwi_flights import KiwiFlightsAPI

# Configure logging
logger = logging.getLogger(__name__)


class KiwiOnewayAPI:
    """Specialized API for one-way hidden city flight searches."""
    
    def __init__(self, localization_config: LocalizationConfig = None, cabin_class: str = "ECONOMY", hidden_city_only: bool = False):
        """Initialize the one-way API client.
        
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
                                        departure_date: str, adults: int = 1,
                                        limit: int = 10) -> Dict[str, Any]:
        """Search for one-way hidden city flights.
        
        Args:
            origin: Origin airport code (e.g., 'PEK', 'JFK')
            destination: Destination airport code (e.g., 'LAX', 'LHR')
            departure_date: Departure date in YYYY-MM-DD format
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
                    "adults": int,
                    "trip_type": "oneway",
                    "currency": str,
                    "language": str
                },
                "results": {
                    "total_found": int,
                    "hidden_city_count": int,
                    "flights": [
                        {
                            "id": str,
                            "price": float,
                            "currency_symbol": str,
                            "duration_hours": float,
                            "is_hidden_city": bool,
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
                            "savings_info": str
                        }
                    ]
                },
                "error": str (if success is False)
            }
        """
        # Validate inputs
        validation_error = self._validate_search_params(origin, destination, departure_date, adults)
        if validation_error:
            return {
                "success": False,
                "error": validation_error
            }
        
        try:
            # Perform the search
            search_result = await self.kiwi_client.search_oneway_hidden_city(
                origin=origin.upper(),
                destination=destination.upper(),
                departure_date=departure_date,
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
            formatted_response = self._format_oneway_response(
                search_result, origin, destination, departure_date, adults
            )
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"One-way hidden city search failed: {e}")
            return {
                "success": False,
                "error": f"Search failed: {str(e)}"
            }
    
    def _validate_search_params(self, origin: str, destination: str, 
                               departure_date: str, adults: int) -> Optional[str]:
        """Validate search parameters.
        
        Args:
            origin: Origin airport code
            destination: Destination airport code
            departure_date: Departure date string
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
        
        # Validate date
        try:
            dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
            if dep_date.date() < datetime.now().date():
                return "Departure date cannot be in the past"
        except ValueError:
            return "Departure date must be in YYYY-MM-DD format"
        
        # Validate adults
        if adults < 1 or adults > 9:
            return "Number of adults must be between 1 and 9"
        
        return None
    
    def _format_oneway_response(self, search_result: Dict[str, Any], 
                               origin: str, destination: str, 
                               departure_date: str, adults: int) -> Dict[str, Any]:
        """Format the search response for one-way flights.
        
        Args:
            search_result: Raw search result from Kiwi API
            origin: Origin airport code
            destination: Destination airport code
            departure_date: Departure date
            adults: Number of adults
            
        Returns:
            Formatted response dictionary
        """
        flights = search_result.get("flights", [])
        
        # Format flight information
        formatted_flights = []
        for flight in flights:
            # Calculate duration in hours
            duration_hours = round(flight.get("duration_minutes", 0) / 60, 1)

            # Create savings information
            savings_info = self._create_savings_info(flight)

            formatted_flight = {
                "id": flight.get("id", ""),
                "price": flight.get("price", 0),
                "currency": flight.get("currency", "USD"),
                "currency_symbol": flight.get("currency_symbol", "$"),
                "duration_hours": duration_hours,
                "is_hidden_city": flight.get("is_hidden_city", False),
                "departure_airport": flight.get("departure_airport", ""),
                "departure_airport_name": flight.get("departure_airport_name", ""),
                "arrival_airport": flight.get("arrival_airport", ""),
                "arrival_airport_name": flight.get("arrival_airport_name", ""),
                "hidden_destination_code": flight.get("hidden_destination_code", ""),
                "hidden_destination_name": flight.get("hidden_destination_name", ""),
                "carrier_name": flight.get("carrier_name", ""),
                "flight_number": flight.get("flight_number", ""),
                "departure_time": flight.get("departure_time", ""),
                "arrival_time": flight.get("arrival_time", ""),
                "savings_info": savings_info,
                "segments": flight.get("segment_count", 1)
            }
            formatted_flights.append(formatted_flight)
        
        return {
            "success": True,
            "search_info": {
                "origin": origin.upper(),
                "destination": destination.upper(),
                "departure_date": departure_date,
                "adults": adults,
                "trip_type": "oneway",
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
    
    def _create_savings_info(self, flight: Dict[str, Any]) -> str:
        """Create savings information text for the flight.
        
        Args:
            flight: Flight information dictionary
            
        Returns:
            Localized savings information string
        """
        if not flight.get("is_hidden_city"):
            return ""
        
        hidden_dest = flight.get("hidden_destination_name", "")
        if not hidden_dest:
            return ""
        
        if self.localization_config.language == Language.CHINESE:
            return f"隐藏城市航班 - 实际目的地: {hidden_dest}"
        else:
            return f"Hidden City Flight - Actual destination: {hidden_dest}"
    
    async def get_flight_details(self, flight_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific flight.
        
        Args:
            flight_id: Flight ID from search results
            
        Returns:
            Detailed flight information
        """
        # This would require additional API calls to get detailed flight info
        # For now, return a placeholder
        return {
            "success": False,
            "error": "Flight details not implemented yet",
            "flight_id": flight_id
        }


# Global instance for easy access
kiwi_oneway_api = KiwiOnewayAPI()
