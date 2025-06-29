"""Models for interacting with Google Flights API.

This module contains all the data models used for flight searches and results.
Models are designed to match Google Flights' APIs while providing a clean pythonic interface.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from pydantic import (
    BaseModel,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveInt,
    ValidationInfo,
    field_validator,
    model_validator,
)

from fli.models.airline import Airline
from fli.models.airport import Airport


class SeatType(Enum):
    """Available cabin classes for flights."""

    ECONOMY = 1
    PREMIUM_ECONOMY = 2
    BUSINESS = 3
    FIRST = 4


class DisplayMode(Enum):
    """Flight display modes - how flights are initially presented."""

    BEST = 1        # 最佳 - 综合排序（价格、时间、便利性）
    CHEAPEST = 2    # 价格最低 - 以最低价格为主要展示标准


class SortBy(Enum):
    """Available sorting options for flight results."""

    NONE = 0
    TOP_FLIGHTS = 1         # 保持兼容性，等同于 BEST
    CHEAPEST = 2           # 保持兼容性，等同于 PRICE
    PRICE = 2              # 按价格排序（从低到高）
    DEPARTURE_TIME = 3     # 按出发时间排序
    ARRIVAL_TIME = 4       # 按到达时间排序
    DURATION = 5           # 按飞行时长排序
    EMISSIONS = 6          # 按碳排放量排序
    STOPS = 7              # 按中转次数排序
    AIRLINE = 8            # 按航空公司排序


class TripType(Enum):
    """Type of flight journey."""

    ROUND_TRIP = 1
    ONE_WAY = 2

    # Currently not supported - kept for reference
    _MULTI_CITY = 3  # Unsupported


class MaxStops(Enum):
    """Maximum number of stops allowed in flight search."""

    ANY = 0
    NON_STOP = 1
    ONE_STOP_OR_FEWER = 2
    TWO_OR_FEWER_STOPS = 3


class Currency(Enum):
    """Supported currencies for pricing."""

    USD = "USD"  # US Dollar
    CNY = "CNY"  # Chinese Yuan


class Language(Enum):
    """Supported languages for API requests."""

    ENGLISH = "en"
    CHINESE = "zh-CN"


@dataclass
class LocalizationConfig:
    """Configuration for language and currency settings.

    Note: Region is fixed to 'US' for optimal Google Flights API performance.
    Only language and currency can be customized.
    """

    language: Language = Language.ENGLISH
    currency: Currency = Currency.USD

    def __post_init__(self):
        """Initialize after dataclass creation."""
        pass

    @property
    def region(self) -> str:
        """Get the region code. Fixed to 'US' for optimal API performance."""
        return "US"

    @property
    def api_language_code(self) -> str:
        """Get the API language code."""
        return self.language.value

    @property
    def api_currency_code(self) -> str:
        """Get the API currency code."""
        return self.currency.value

    @property
    def currency_symbol(self) -> str:
        """Get the currency symbol for display."""
        symbols = {Currency.USD: "$", Currency.CNY: "¥"}
        return symbols.get(self.currency, self.currency.value)

    def get_text(self, key: str) -> str:
        """Get localized text for the given key."""
        texts = {
            Language.ENGLISH: {
                "one_way_flight_option": "One-way Flight Option",
                "round_trip_flight_option": "Round-trip Flight Option",
                "total_price": "Total Price",
                "total_duration": "Total Duration",
                "total_stops": "Total Stops",
                "outbound_price": "Outbound Price",
                "return_price": "Return Price",
                "outbound_flight_segments": "Outbound Flight Segments",
                "return_flight_segments": "Return Flight Segments",
                "airline": "Airline",
                "flight": "Flight",
                "from": "From",
                "departure": "Departure",
                "to": "To",
                "arrival": "Arrival",
                "cheapest_dates_to_fly": "Cheapest Dates to Fly",
                "day": "Day",
                "price": "Price",
            },
            Language.CHINESE: {
                "one_way_flight_option": "单程航班选项",
                "round_trip_flight_option": "往返航班选项",
                "total_price": "总价格",
                "total_duration": "总时长",
                "total_stops": "总中转次数",
                "outbound_price": "去程价格",
                "return_price": "返程价格",
                "outbound_flight_segments": "去程航班段",
                "return_flight_segments": "返程航班段",
                "airline": "航空公司",
                "flight": "航班号",
                "from": "出发地",
                "departure": "出发时间",
                "to": "目的地",
                "arrival": "到达时间",
                "cheapest_dates_to_fly": "最便宜的出行日期",
                "day": "星期",
                "price": "价格",
            },
        }
        return texts.get(self.language, texts[Language.ENGLISH]).get(key, key)

    def get_airport_name(self, airport_code: str, english_name: str) -> str:
        """Get localized airport name."""
        if self.language == Language.CHINESE:
            # Common airport translations
            chinese_airports = {
                "LHR": "伦敦希思罗机场",
                "PEK": "北京首都国际机场",
                "LAX": "洛杉矶国际机场",
                "NRT": "东京成田国际机场",
                "ICN": "首尔仁川国际机场",
                "CDG": "巴黎戴高乐机场",
                "JFK": "纽约肯尼迪国际机场",
                "DXB": "迪拜国际机场",
                "HKG": "香港国际机场",
                "PVG": "上海浦东国际机场",
                "SHA": "上海虹桥国际机场",
                "CSX": "长沙黄花机场",
                "SZX": "深圳宝安国际机场",
                "IST": "伊斯坦布尔新机场",
                "FRA": "法兰克福机场",
                "VIE": "维也纳国际机场",
                "SEA": "西雅图塔科马国际机场",
                "SFO": "旧金山国际机场",
                "KIX": "关西国际机场",
            }
            return chinese_airports.get(airport_code, f"{english_name}")
        return english_name

    def get_airline_name(self, airline_code: str, english_name: str) -> str:
        """Get localized airline name."""
        if self.language == Language.CHINESE:
            # Load airline translations from JSON file
            try:
                import json
                from pathlib import Path

                # Get the path to the airlines translation file from package data directory
                translations_path = (
                    Path(__file__).parent.parent.parent
                    / "data"
                    / "translations"
                    / "airlines_cn.json"
                )

                # Load translations if not already cached
                if not hasattr(self, "_airline_translations"):
                    with open(translations_path, encoding="utf-8") as f:
                        self._airline_translations = json.load(f)

                return self._airline_translations.get(airline_code, english_name)

            except (FileNotFoundError, json.JSONDecodeError):
                # Fallback to hardcoded translations if file is not available
                chinese_airlines = {
                    "CA": "中国国际航空",
                    "MU": "中国东方航空",
                    "CZ": "中国南方航空",
                    "HU": "海南航空",
                    "9C": "春秋航空",
                    "HO": "吉祥航空",
                    "3U": "四川航空",
                    "8L": "祥鹏航空",
                    "ZH": "深圳航空",
                    "EK": "阿联酋航空",
                    "TK": "土耳其航空",
                    "CX": "国泰航空",
                    "LH": "汉莎航空",
                    "OS": "奥地利航空",
                    "JL": "日本航空",
                    "NH": "全日空",
                    "KE": "大韩航空",
                    "OZ": "韩亚航空",
                    "SQ": "新加坡航空",
                    "AS": "阿拉斯加航空",
                    "AA": "美国航空",
                    "UA": "美国联合航空",
                    "HA": "夏威夷航空",
                }
                return chinese_airlines.get(airline_code, english_name)
        return english_name


class TimeRestrictions(BaseModel):
    """Time constraints for flight departure and arrival in local time.

    All times are in hours from midnight (e.g., 20 = 8:00 PM).
    """

    earliest_departure: NonNegativeInt | None = None
    latest_departure: PositiveInt | None = None
    earliest_arrival: NonNegativeInt | None = None
    latest_arrival: PositiveInt | None = None

    @field_validator("latest_departure", "latest_arrival")
    @classmethod
    def validate_latest_times(
        cls, v: PositiveInt | None, info: ValidationInfo
    ) -> PositiveInt | None:
        """Validate and adjust the latest time restrictions."""
        if v is None:
            return v

        # Get "departure" or "arrival" from field name
        field_prefix = "earliest_" + info.field_name[7:]
        earliest = info.data.get(field_prefix)

        # Swap values to ensure that `from` is always before `to`
        if earliest is not None and earliest > v:
            info.data[field_prefix] = v
            return earliest
        return v


class PassengerInfo(BaseModel):
    """Passenger configuration for flight search."""

    adults: NonNegativeInt = 1
    children: NonNegativeInt = 0
    infants_in_seat: NonNegativeInt = 0
    infants_on_lap: NonNegativeInt = 0


class PriceLimit(BaseModel):
    """Maximum price constraint for flight search."""

    max_price: PositiveInt
    currency: Currency | None = Currency.USD


class LayoverRestrictions(BaseModel):
    """Constraints for layovers in multi-leg flights."""

    airports: list[Airport] | None = None
    max_duration: PositiveInt | None = None


class FlightLeg(BaseModel):
    """A single flight leg (segment) with airline and timing details."""

    airline: Airline
    flight_number: str
    departure_airport: Airport
    arrival_airport: Airport
    departure_datetime: datetime
    arrival_datetime: datetime
    duration: PositiveInt  # in minutes


class FlightResult(BaseModel):
    """Complete flight search result with pricing and timing."""

    legs: list[FlightLeg]
    price: NonNegativeFloat  # in specified currency
    duration: PositiveInt  # total duration in minutes
    stops: NonNegativeInt
    hidden_city_info: dict | None = None  # Optional hidden city information from Kiwi API
    price_unavailable: bool = False  # True if airline doesn't provide direct pricing


class FlightSegment(BaseModel):
    """A segment represents a single portion of a flight journey between two airports.

    For example, in a one-way flight from JFK to LAX, there would be one segment.
    In a multi-city trip from JFK -> LAX -> SEA, there would be two segments:
    JFK -> LAX and LAX -> SEA.
    """

    departure_airport: list[list[Airport | int]]
    arrival_airport: list[list[Airport | int]]
    travel_date: str
    time_restrictions: TimeRestrictions | None = None
    selected_flight: FlightResult | None = None

    @property
    def parsed_travel_date(self) -> datetime:
        """Parse the travel date string into a datetime object."""
        return datetime.strptime(self.travel_date, "%Y-%m-%d")

    @field_validator("travel_date")
    @classmethod
    def validate_travel_date(cls, v: str) -> str:
        """Validate that the travel date is not in the past."""
        travel_date = datetime.strptime(v, "%Y-%m-%d").date()
        if travel_date < datetime.now().date():
            raise ValueError("Travel date cannot be in the past")
        return v

    @model_validator(mode="after")
    def validate_airports(self) -> "FlightSegment":
        """Validate that departure and arrival airports are different."""
        if not self.departure_airport or not self.arrival_airport:
            raise ValueError("Both departure and arrival airports must be specified")

        # Get first airport from each nested list
        dep_airport = (
            self.departure_airport[0][0]
            if isinstance(self.departure_airport[0][0], Airport)
            else None
        )
        arr_airport = (
            self.arrival_airport[0][0] if isinstance(self.arrival_airport[0][0], Airport) else None
        )

        if dep_airport and arr_airport and dep_airport == arr_airport:
            raise ValueError("Departure and arrival airports must be different")
        return self
