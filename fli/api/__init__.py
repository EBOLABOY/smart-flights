"""Fli API Module

Provides programmatic access to flight search and airport information.
"""

from .airport_search import AirportSearchAPI, airport_search_api

__all__ = ["AirportSearchAPI", "airport_search_api"]
