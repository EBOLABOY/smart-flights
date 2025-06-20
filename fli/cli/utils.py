from datetime import datetime

import typer
from click import Context, Parameter
from rich import box
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from fli.cli.console import console
from fli.cli.enums import DayOfWeek
from fli.models import Airline, Airport, MaxStops, TripType
from fli.models.google_flights.base import LocalizationConfig


def validate_date(ctx: Context, param: Parameter, value: str) -> str | None:
    """Validate date format."""
    if value is None:
        return None

    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError as e:
        raise typer.BadParameter("Date must be in YYYY-MM-DD format") from e


def validate_time_range(
    ctx: Context, param: Parameter, value: str | None
) -> tuple[int, int] | None:
    """Validate and parse time range in format 'start-end' (24h format)."""
    if not value:
        return None

    try:
        start, end = map(int, value.split("-"))
        if not (0 <= start <= 23 and 0 <= end <= 23):
            raise ValueError
        return start, end
    except ValueError as e:
        raise typer.BadParameter("Time range must be in format 'start-end' (e.g., 6-20)") from e


def parse_airlines(airlines: list[str] | None) -> list[Airline] | None:
    """Parse airlines from list of airline codes."""
    if not airlines:
        return None

    try:
        return [
            getattr(Airline, airline.strip().upper()) for airline in airlines if airline.strip()
        ]
    except AttributeError as e:
        raise typer.BadParameter(f"Invalid airline code: {str(e)}") from e


def parse_stops(stops: str) -> MaxStops:
    """Convert stops parameter to MaxStops enum."""
    # Try parsing as integer first
    try:
        stops_int = int(stops)
        if stops_int == 0:
            return MaxStops.NON_STOP
        elif stops_int == 1:
            return MaxStops.ONE_STOP_OR_FEWER
        elif stops_int >= 2:
            return MaxStops.TWO_OR_FEWER_STOPS
        else:
            return MaxStops.ANY
    except ValueError:
        # If not an integer, try as enum string
        try:
            return getattr(MaxStops, stops.upper())
        except AttributeError as e:
            raise typer.BadParameter(f"Invalid stops value: {stops}") from e


def parse_trip_type(trip_type: str) -> TripType:
    """Convert trip type parameter to TripType enum."""
    match trip_type.upper():
        case "ONEWAY" | "ONE_WAY":
            return TripType.ONE_WAY
        case "ROUND" | "ROUND_TRIP":
            return TripType.ROUND_TRIP
        case _:
            raise typer.BadParameter(f"Invalid trip type: {trip_type}")


def filter_flights_by_time(flights: list, start_hour: int, end_hour: int) -> list:
    """Filter flights by departure time range."""
    return [
        flight
        for flight in flights
        if any(start_hour <= leg.departure_datetime.hour <= end_hour for leg in flight.legs)
    ]


def filter_flights_by_airlines(flights: list, airlines: list[Airline]) -> list:
    """Filter flights by specified airlines."""
    return [flight for flight in flights if any(leg.airline in airlines for leg in flight.legs)]


def filter_dates_by_days(dates: list, days: list[DayOfWeek], trip_type: TripType) -> list:
    """Filter dates by days of the week."""
    if not days:
        return dates

    day_numbers = {
        DayOfWeek.MONDAY: 0,
        DayOfWeek.TUESDAY: 1,
        DayOfWeek.WEDNESDAY: 2,
        DayOfWeek.THURSDAY: 3,
        DayOfWeek.FRIDAY: 4,
        DayOfWeek.SATURDAY: 5,
        DayOfWeek.SUNDAY: 6,
    }

    allowed_days = {day_numbers[day] for day in days}
    return [date_price for date_price in dates if date_price.date[0].weekday() in allowed_days]


def format_airport(airport: Airport) -> str:
    """Format airport code and name (first two words)."""
    name_parts = airport.value.split()[:3]  # Get first three words
    name = " ".join(name_parts)
    return f"{airport.name} ({name})"


def format_duration(minutes: int) -> str:
    """Format duration in minutes to hours and minutes."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


def format_price(price: float, currency_symbol: str = "¥") -> str:
    """Format price with appropriate currency symbol."""
    return f"{currency_symbol}{price:,.2f}"


def display_flight_results(flights: list, localization_config: LocalizationConfig = None):
    """Display flight results in a beautiful format.

    Args:
        flights: List of either FlightResult objects (one-way)
        or tuples of (outbound, return) FlightResults (round-trip)
        localization_config: Configuration for currency and language display

    """
    if localization_config is None:
        localization_config = LocalizationConfig()
    if not flights:
        console.print(Panel("No flights found matching your criteria", style="red"))
        return

    for i, flight_data in enumerate(flights, 1):
        is_round_trip = isinstance(flight_data, tuple)
        flight_segments = [flight_data] if not is_round_trip else [flight_data[0], flight_data[1]]

        # Create main flight info table
        table = Table(show_header=False, box=box.SIMPLE)
        table.add_column("Label", style="blue")
        table.add_column("Value", style="green")

        total_price = flight_segments[0].price
        if is_round_trip:
            total_price += flight_segments[1].price
        table.add_row(
            localization_config.get_text("total_price"),
            format_price(total_price, localization_config.currency_symbol),
        )

        if is_round_trip:
            table.add_row(
                localization_config.get_text("outbound_price"),
                format_price(flight_segments[0].price, localization_config.currency_symbol),
            )
            table.add_row(
                localization_config.get_text("return_price"),
                format_price(flight_segments[1].price, localization_config.currency_symbol),
            )

        total_duration = sum(flight.duration for flight in flight_segments)
        table.add_row(
            localization_config.get_text("total_duration"), format_duration(total_duration)
        )
        total_stops = sum(flight.stops for flight in flight_segments)
        table.add_row(localization_config.get_text("total_stops"), str(total_stops))

        # Create segments tables for each direction
        all_segments = []
        for idx, flight in enumerate(flight_segments):
            if idx == 0:
                direction_text = localization_config.get_text("outbound_flight_segments")
            elif is_round_trip:
                direction_text = localization_config.get_text("return_flight_segments")
            else:
                direction_text = localization_config.get_text("outbound_flight_segments")

            segments = Table(
                title=direction_text,
                box=box.ROUNDED,
            )
            segments.add_column(localization_config.get_text("airline"), style="cyan")
            segments.add_column(localization_config.get_text("flight"), style="magenta")
            segments.add_column(localization_config.get_text("from"), style="yellow", width=30)
            segments.add_column(localization_config.get_text("departure"), style="green")
            segments.add_column(localization_config.get_text("to"), style="yellow", width=30)
            segments.add_column(localization_config.get_text("arrival"), style="green")

            for leg in flight.legs:
                # Get localized airline and airport names
                airline_name = localization_config.get_airline_name(
                    leg.airline.name, leg.airline.value
                )
                departure_airport_name = localization_config.get_airport_name(
                    leg.departure_airport.name, format_airport(leg.departure_airport)
                )
                arrival_airport_name = localization_config.get_airport_name(
                    leg.arrival_airport.name, format_airport(leg.arrival_airport)
                )

                segments.add_row(
                    airline_name,
                    leg.flight_number,
                    departure_airport_name,
                    leg.departure_datetime.strftime("%H:%M %d-%b"),
                    arrival_airport_name,
                    leg.arrival_datetime.strftime("%H:%M %d-%b"),
                )
            all_segments.extend([segments, Text("")])

        # Display in a panel
        title_text = (
            localization_config.get_text("round_trip_flight_option")
            if is_round_trip
            else localization_config.get_text("one_way_flight_option")
        )
        console.print(
            Panel(
                Group(
                    Text(f"{title_text} {i}", style="bold blue"),
                    Text(""),
                    table,
                    Text(""),
                    *all_segments[:-1],  # Remove the last empty Text
                ),
                title=f"[bold]Option {i} of {len(flights)}[/bold]",
                border_style="blue",
                box=box.ROUNDED,
            )
        )
        console.print()


def display_date_results(
    dates: list, trip_type: TripType, localization_config: LocalizationConfig = None
):
    """Display date search results in a beautiful format."""
    if localization_config is None:
        localization_config = LocalizationConfig()
    if not dates:
        console.print(Panel("No flights found for these dates", style="red"))
        return

    table = Table(title=localization_config.get_text("cheapest_dates_to_fly"), box=box.ROUNDED)
    table.add_column(localization_config.get_text("departure"), style="cyan")
    table.add_column(localization_config.get_text("day"), style="yellow")
    if trip_type == TripType.ROUND_TRIP:
        table.add_column("Return", style="cyan")
        table.add_column(localization_config.get_text("day"), style="yellow")
    table.add_column(localization_config.get_text("price"), style="green")

    for date_price in dates:
        if trip_type == TripType.ONE_WAY:
            table.add_row(
                date_price.date[0].strftime("%Y-%m-%d"),
                date_price.date[0].strftime("%A"),
                format_price(date_price.price, localization_config.currency_symbol),
            )
        else:
            table.add_row(
                date_price.date[0].strftime("%Y-%m-%d"),
                date_price.date[0].strftime("%A"),
                date_price.date[1].strftime("%Y-%m-%d"),
                date_price.date[1].strftime("%A"),
                format_price(date_price.price, localization_config.currency_symbol),
            )

    console.print(table)
    console.print()
