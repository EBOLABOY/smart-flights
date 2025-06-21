"""Airport Search API

Provides comprehensive airport search functionality including:
- Fuzzy search by airport name, city, or country
- Search by airport code
- Multi-language support (English/Chinese)
- Keyword-based search
"""

import json
from dataclasses import dataclass
from pathlib import Path

from fli.models import Airport
from fli.models.google_flights.base import Language


@dataclass
class AirportInfo:
    """Structured airport information."""

    code: str
    name_en: str
    name_cn: str
    city_en: str
    city_cn: str
    country_en: str
    country_cn: str
    region: str
    keywords_en: list[str]
    keywords_cn: list[str]


class AirportSearchAPI:
    """Comprehensive airport search API with multi-language support."""

    def __init__(self):
        """Initialize the search API with translation data."""
        self._load_airport_data()
        self._build_search_index()

    def _load_airport_data(self):
        """Load airport translation data from JSON files."""
        try:
            # Load enhanced airport data from package data directory
            translations_path = (
                Path(__file__).parent.parent
                / "data"
                / "translations"
                / "airports_enhanced_cn.json"
            )
            with open(translations_path, encoding="utf-8") as f:
                self.airport_translations = json.load(f)

            # Load basic airport enum data
            self.airport_enum = {airport.name: airport.value for airport in Airport}

        except FileNotFoundError:
            # Fallback to basic enum data if translation files don't exist
            self.airport_translations = {}
            self.airport_enum = {airport.name: airport.value for airport in Airport}

    def _build_search_index(self):
        """Build search indexes for efficient searching."""
        self.search_index = {
            "by_code": {},
            "by_name_en": {},
            "by_name_cn": {},
            "by_city_en": {},
            "by_city_cn": {},
            "by_country_en": {},
            "by_country_cn": {},
            "by_keywords_en": {},
            "by_keywords_cn": {},
        }

        # Build indexes from enhanced data
        for code, data in self.airport_translations.items():
            if isinstance(data, dict):
                airport_info = AirportInfo(
                    code=code,
                    name_en=data.get("name_en", ""),
                    name_cn=data.get("name_cn", ""),
                    city_en=data.get("city_en", ""),
                    city_cn=data.get("city_cn", ""),
                    country_en=data.get("country_en", ""),
                    country_cn=data.get("country_cn", ""),
                    region=data.get("region", ""),
                    keywords_en=data.get("keywords_en", []),
                    keywords_cn=data.get("keywords_cn", []),
                )

                # Index by code
                self.search_index["by_code"][code.upper()] = airport_info

                # Index by names
                if airport_info.name_en:
                    self.search_index["by_name_en"][airport_info.name_en.lower()] = airport_info
                if airport_info.name_cn:
                    self.search_index["by_name_cn"][airport_info.name_cn] = airport_info

                # Index by cities
                if airport_info.city_en:
                    if airport_info.city_en.lower() not in self.search_index["by_city_en"]:
                        self.search_index["by_city_en"][airport_info.city_en.lower()] = []
                    self.search_index["by_city_en"][airport_info.city_en.lower()].append(
                        airport_info
                    )

                if airport_info.city_cn:
                    if airport_info.city_cn not in self.search_index["by_city_cn"]:
                        self.search_index["by_city_cn"][airport_info.city_cn] = []
                    self.search_index["by_city_cn"][airport_info.city_cn].append(airport_info)

                # Index by countries
                if airport_info.country_en:
                    if airport_info.country_en.lower() not in self.search_index["by_country_en"]:
                        self.search_index["by_country_en"][airport_info.country_en.lower()] = []
                    self.search_index["by_country_en"][airport_info.country_en.lower()].append(
                        airport_info
                    )

                if airport_info.country_cn:
                    if airport_info.country_cn not in self.search_index["by_country_cn"]:
                        self.search_index["by_country_cn"][airport_info.country_cn] = []
                    self.search_index["by_country_cn"][airport_info.country_cn].append(airport_info)

                # Index by keywords
                for keyword in airport_info.keywords_en:
                    if keyword.lower() not in self.search_index["by_keywords_en"]:
                        self.search_index["by_keywords_en"][keyword.lower()] = []
                    self.search_index["by_keywords_en"][keyword.lower()].append(airport_info)

                for keyword in airport_info.keywords_cn:
                    if keyword not in self.search_index["by_keywords_cn"]:
                        self.search_index["by_keywords_cn"][keyword] = []
                    self.search_index["by_keywords_cn"][keyword].append(airport_info)

        # Add basic enum data for airports not in enhanced data
        for code, name in self.airport_enum.items():
            if code not in self.search_index["by_code"]:
                basic_info = AirportInfo(
                    code=code,
                    name_en=name,
                    name_cn="",
                    city_en="",
                    city_cn="",
                    country_en="",
                    country_cn="",
                    region="",
                    keywords_en=[],
                    keywords_cn=[],
                )
                self.search_index["by_code"][code] = basic_info

    def get_airport_by_code(
        self, code: str, language: Language = Language.ENGLISH
    ) -> dict | None:
        """Get airport information by exact airport code.

        Args:
            code: Airport IATA code (e.g., 'LHR', 'PEK')
            language: Language for response (English or Chinese)

        Returns:
            Airport information dictionary or None if not found

        """
        airport_info = self.search_index["by_code"].get(code.upper())
        if airport_info:
            return self._format_airport_response(airport_info, language)
        return None

    def search_airports(
        self, query: str, language: Language = Language.ENGLISH, limit: int = 10
    ) -> list[dict]:
        """Comprehensive airport search with fuzzy matching.

        Args:
            query: Search query (airport name, city, country, or keywords)
            language: Language for response
            limit: Maximum number of results to return

        Returns:
            List of matching airports

        """
        results = []
        query_lower = query.lower()

        # Search by airport code (exact match)
        if len(query) == 3 and query.upper() in self.search_index["by_code"]:
            results.append(self.search_index["by_code"][query.upper()])

        # Search by names (fuzzy match)
        for name, airport_info in self.search_index["by_name_en"].items():
            if query_lower in name and airport_info not in results:
                results.append(airport_info)

        for name, airport_info in self.search_index["by_name_cn"].items():
            if query in name and airport_info not in results:
                results.append(airport_info)

        # Search by cities
        for city, airport_list in self.search_index["by_city_en"].items():
            if query_lower in city:
                for airport_info in airport_list:
                    if airport_info not in results:
                        results.append(airport_info)

        for city, airport_list in self.search_index["by_city_cn"].items():
            if query in city:
                for airport_info in airport_list:
                    if airport_info not in results:
                        results.append(airport_info)

        # Search by countries
        for country, airport_list in self.search_index["by_country_en"].items():
            if query_lower in country:
                for airport_info in airport_list:
                    if airport_info not in results:
                        results.append(airport_info)

        for country, airport_list in self.search_index["by_country_cn"].items():
            if query in country:
                for airport_info in airport_list:
                    if airport_info not in results:
                        results.append(airport_info)

        # Search by keywords
        for keyword, airport_list in self.search_index["by_keywords_en"].items():
            if query_lower in keyword:
                for airport_info in airport_list:
                    if airport_info not in results:
                        results.append(airport_info)

        for keyword, airport_list in self.search_index["by_keywords_cn"].items():
            if query in keyword:
                for airport_info in airport_list:
                    if airport_info not in results:
                        results.append(airport_info)

        # Format and limit results
        formatted_results = [
            self._format_airport_response(airport, language) for airport in results[:limit]
        ]
        return formatted_results

    def search_by_city(self, city: str, language: Language = Language.ENGLISH) -> list[dict]:
        """Search airports by city name.

        Args:
            city: City name in English or Chinese
            language: Language for response

        Returns:
            List of airports in the specified city

        """
        results = []

        # Search English cities
        city_lower = city.lower()
        if city_lower in self.search_index["by_city_en"]:
            results.extend(self.search_index["by_city_en"][city_lower])

        # Search Chinese cities
        if city in self.search_index["by_city_cn"]:
            results.extend(self.search_index["by_city_cn"][city])

        # Remove duplicates
        unique_results = []
        seen_codes = set()
        for airport in results:
            if airport.code not in seen_codes:
                unique_results.append(airport)
                seen_codes.add(airport.code)

        return [self._format_airport_response(airport, language) for airport in unique_results]

    def search_by_country(
        self, country: str, language: Language = Language.ENGLISH, limit: int = 20
    ) -> list[dict]:
        """Search airports by country name.

        Args:
            country: Country name in English or Chinese
            language: Language for response
            limit: Maximum number of results

        Returns:
            List of airports in the specified country

        """
        results = []

        # Search English countries
        country_lower = country.lower()
        if country_lower in self.search_index["by_country_en"]:
            results.extend(self.search_index["by_country_en"][country_lower])

        # Search Chinese countries
        if country in self.search_index["by_country_cn"]:
            results.extend(self.search_index["by_country_cn"][country])

        # Remove duplicates and limit
        unique_results = []
        seen_codes = set()
        for airport in results[:limit]:
            if airport.code not in seen_codes:
                unique_results.append(airport)
                seen_codes.add(airport.code)

        return [self._format_airport_response(airport, language) for airport in unique_results]

    def _format_airport_response(self, airport_info: AirportInfo, language: Language) -> dict:
        """Format airport information for API response.

        Args:
            airport_info: Airport information object
            language: Response language

        Returns:
            Formatted airport dictionary

        """
        if language == Language.CHINESE:
            return {
                "code": airport_info.code,
                "name": airport_info.name_cn or airport_info.name_en,
                "city": airport_info.city_cn or airport_info.city_en,
                "country": airport_info.country_cn or airport_info.country_en,
                "region": airport_info.region,
                "name_en": airport_info.name_en,
                "name_cn": airport_info.name_cn,
            }
        else:
            return {
                "code": airport_info.code,
                "name": airport_info.name_en,
                "city": airport_info.city_en,
                "country": airport_info.country_en,
                "region": airport_info.region,
                "name_en": airport_info.name_en,
                "name_cn": airport_info.name_cn,
            }

    def get_all_airports(
        self, language: Language = Language.ENGLISH, limit: int | None = None
    ) -> list[dict]:
        """Get all available airports.

        Args:
            language: Response language
            limit: Maximum number of results (None for all)

        Returns:
            List of all airports

        """
        all_airports = list(self.search_index["by_code"].values())
        if limit:
            all_airports = all_airports[:limit]

        return [self._format_airport_response(airport, language) for airport in all_airports]


# Global instance for easy access
airport_search_api = AirportSearchAPI()
