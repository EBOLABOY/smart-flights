"""
Fli - Flight Search Library
A Python library for searching flights using Google Flights API
"""

from .search.flights import SearchFlights
from .models.google_flights import (
    Airport,
    DisplayMode,
    FlightLeg,
    FlightResult,
    FlightSearchFilters,
    FlightSegment,
    LayoverRestrictions,
    MaxStops,
    PassengerInfo,
    PriceLimit,
    SeatType,
    SortBy,
    TimeRestrictions,
    TripType,
)
from .localization import LocalizationConfig, Language, Currency

__version__ = "0.6.0"
__author__ = "Fli Team"
__email__ = "contact@fli.dev"

__all__ = [
    "SearchFlights",
    "Airport",
    "DisplayMode",
    "FlightLeg",
    "FlightResult",
    "FlightSearchFilters",
    "FlightSegment",
    "LayoverRestrictions",
    "LocalizationConfig",
    "Language",
    "Currency",
    "MaxStops",
    "PassengerInfo",
    "PriceLimit",
    "SeatType",
    "SortBy",
    "TimeRestrictions",
    "TripType",
]