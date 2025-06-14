"""Airport search CLI command

Provides command-line interface for airport search functionality.
"""

from typing import Annotated

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from fli.api.airport_search import airport_search_api
from fli.models.google_flights.base import Language

console = Console()


def airport_search_command(
    query: Annotated[
        str, typer.Argument(help="Search query (airport name, city, country, or code)")
    ],
    language: Annotated[
        str,
        typer.Option(
            "--language",
            "-l",
            help="Language for results (en, zh-cn)",
        ),
    ] = "en",
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            "-n",
            help="Maximum number of results to return",
        ),
    ] = 10,
    by_city: Annotated[
        bool,
        typer.Option(
            "--city",
            help="Search specifically by city name",
        ),
    ] = False,
    by_country: Annotated[
        bool,
        typer.Option(
            "--country",
            help="Search specifically by country name",
        ),
    ] = False,
):
    """Search for airports by name, city, country, or airport code.

    Examples:
        fli airport-search "london"
        fli airport-search "北京" --language zh-cn
        fli airport-search "LHR"
        fli airport-search "china" --country --language zh-cn
        fli airport-search "tokyo" --city

    """
    try:
        # Parse language
        lang = (
            Language.CHINESE if language.lower() in ["zh", "zh-cn", "chinese"] else Language.ENGLISH
        )

        # Perform search based on options
        if by_city:
            results = airport_search_api.search_by_city(query, lang)
        elif by_country:
            results = airport_search_api.search_by_country(query, lang, limit)
        else:
            results = airport_search_api.search_airports(query, lang, limit)

        if not results:
            console.print(f"[red]No airports found for query: {query}[/red]")
            raise typer.Exit(1)

        # Display results
        display_airport_results(results, lang)

    except Exception as e:
        console.print(f"[red]Error searching airports: {e}[/red]")
        raise typer.Exit(1)


def airport_info_command(
    code: Annotated[str, typer.Argument(help="Airport IATA code (e.g., LHR, PEK)")],
    language: Annotated[
        str,
        typer.Option(
            "--language",
            "-l",
            help="Language for results (en, zh-cn)",
        ),
    ] = "en",
):
    """Get detailed information about a specific airport by its IATA code.

    Examples:
        fli airport-info LHR
        fli airport-info PEK --language zh-cn

    """
    try:
        # Parse language
        lang = (
            Language.CHINESE if language.lower() in ["zh", "zh-cn", "chinese"] else Language.ENGLISH
        )

        # Get airport info
        result = airport_search_api.get_airport_by_code(code, lang)

        if not result:
            console.print(f"[red]Airport not found: {code}[/red]")
            raise typer.Exit(1)

        # Display detailed info
        display_airport_detail(result, lang)

    except Exception as e:
        console.print(f"[red]Error getting airport info: {e}[/red]")
        raise typer.Exit(1)


def display_airport_results(airports: list, language: Language):
    """Display airport search results in a table format."""
    # Create table
    if language == Language.CHINESE:
        table = Table(title="机场搜索结果", box=box.ROUNDED)
        table.add_column("代码", style="cyan", width=8)
        table.add_column("机场名称", style="yellow", width=40)
        table.add_column("城市", style="green", width=15)
        table.add_column("国家", style="magenta", width=15)
        table.add_column("地区", style="blue", width=12)
    else:
        table = Table(title="Airport Search Results", box=box.ROUNDED)
        table.add_column("Code", style="cyan", width=8)
        table.add_column("Airport Name", style="yellow", width=40)
        table.add_column("City", style="green", width=15)
        table.add_column("Country", style="magenta", width=15)
        table.add_column("Region", style="blue", width=12)

    # Add rows
    for airport in airports:
        table.add_row(
            airport.get("code", ""),
            airport.get("name", ""),
            airport.get("city", ""),
            airport.get("country", ""),
            airport.get("region", ""),
        )

    console.print(table)

    # Show summary
    if language == Language.CHINESE:
        console.print(f"\n[bold]找到 {len(airports)} 个机场[/bold]")
    else:
        console.print(f"\n[bold]Found {len(airports)} airports[/bold]")


def display_airport_detail(airport: dict, language: Language):
    """Display detailed information about a single airport."""
    # Create detail table
    if language == Language.CHINESE:
        table = Table(title=f"机场详细信息 - {airport.get('code', '')}", box=box.ROUNDED)
        table.add_column("属性", style="cyan", width=15)
        table.add_column("值", style="yellow", width=50)

        table.add_row("机场代码", airport.get("code", ""))
        table.add_row("机场名称", airport.get("name", ""))
        table.add_row("英文名称", airport.get("name_en", ""))
        table.add_row("中文名称", airport.get("name_cn", ""))
        table.add_row("城市", airport.get("city", ""))
        table.add_row("国家", airport.get("country", ""))
        table.add_row("地区", airport.get("region", ""))
    else:
        table = Table(title=f"Airport Details - {airport.get('code', '')}", box=box.ROUNDED)
        table.add_column("Property", style="cyan", width=15)
        table.add_column("Value", style="yellow", width=50)

        table.add_row("Airport Code", airport.get("code", ""))
        table.add_row("Airport Name", airport.get("name", ""))
        table.add_row("English Name", airport.get("name_en", ""))
        table.add_row("Chinese Name", airport.get("name_cn", ""))
        table.add_row("City", airport.get("city", ""))
        table.add_row("Country", airport.get("country", ""))
        table.add_row("Region", airport.get("region", ""))

    console.print(table)


# Export commands for CLI registration
__all__ = ["airport_search_command", "airport_info_command"]
