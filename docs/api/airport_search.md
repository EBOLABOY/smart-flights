# Airport Search API Reference

The Airport Search API provides comprehensive airport search functionality with multi-language support, enabling developers to integrate powerful airport lookup capabilities into their applications.

## Features

- 🔍 **Fuzzy Search**: Search by airport name, city, country, or keywords
- 🌍 **Multi-language Support**: English and Chinese language support
- 📍 **Location-based Search**: Search by city or country
- 🎯 **Exact Code Lookup**: Get airport details by IATA code
- 📊 **Rich Data**: Includes airport names, cities, countries, and regions
- 🚀 **High Performance**: Optimized search indexes for fast queries

## Quick Start

```python
from fli.api.airport_search import airport_search_api
from fli.models.google_flights.base import Language

# Search for airports
results = airport_search_api.search_airports("london", Language.ENGLISH)
print(results[0]['name'])  # "London Heathrow Airport"

# Get specific airport
airport = airport_search_api.get_airport_by_code("LHR", Language.CHINESE)
print(airport['name'])  # "伦敦希思罗机场"
```

## API Reference

### AirportSearchAPI Class

#### `search_airports(query, language=Language.ENGLISH, limit=10)`

Comprehensive airport search with fuzzy matching.

**Parameters:**
- `query` (str): Search query (airport name, city, country, or keywords)
- `language` (Language): Language for response (English or Chinese)
- `limit` (int): Maximum number of results to return

**Returns:**
- `List[Dict]`: List of matching airports

**Example:**
```python
# Search in English
results = airport_search_api.search_airports("beijing", Language.ENGLISH)

# Search in Chinese
results = airport_search_api.search_airports("北京", Language.CHINESE)

# Search by keywords
results = airport_search_api.search_airports("heathrow", Language.ENGLISH)
```

#### `get_airport_by_code(code, language=Language.ENGLISH)`

Get airport information by exact airport code.

**Parameters:**
- `code` (str): Airport IATA code (e.g., 'LHR', 'PEK')
- `language` (Language): Language for response

**Returns:**
- `Optional[Dict]`: Airport information or None if not found

**Example:**
```python
# Get airport in English
airport = airport_search_api.get_airport_by_code("LHR", Language.ENGLISH)

# Get airport in Chinese
airport = airport_search_api.get_airport_by_code("LHR", Language.CHINESE)
```

#### `search_by_city(city, language=Language.ENGLISH)`

Search airports by city name.

**Parameters:**
- `city` (str): City name in English or Chinese
- `language` (Language): Language for response

**Returns:**
- `List[Dict]`: List of airports in the specified city

**Example:**
```python
# Search by English city name
results = airport_search_api.search_by_city("London", Language.ENGLISH)

# Search by Chinese city name
results = airport_search_api.search_by_city("北京", Language.CHINESE)
```

#### `search_by_country(country, language=Language.ENGLISH, limit=20)`

Search airports by country name.

**Parameters:**
- `country` (str): Country name in English or Chinese
- `language` (Language): Language for response
- `limit` (int): Maximum number of results

**Returns:**
- `List[Dict]`: List of airports in the specified country

**Example:**
```python
# Search by English country name
results = airport_search_api.search_by_country("China", Language.ENGLISH)

# Search by Chinese country name
results = airport_search_api.search_by_country("中国", Language.CHINESE)
```

#### `get_all_airports(language=Language.ENGLISH, limit=None)`

Get all available airports.

**Parameters:**
- `language` (Language): Response language
- `limit` (Optional[int]): Maximum number of results (None for all)

**Returns:**
- `List[Dict]`: List of all airports

## Response Format

All API methods return airport information in the following format:

```python
{
    'code': 'LHR',                           # IATA airport code
    'name': 'London Heathrow Airport',       # Airport name (localized)
    'city': 'London',                        # City name (localized)
    'country': 'United Kingdom',             # Country name (localized)
    'region': 'Europe',                      # Geographic region
    'name_en': 'London Heathrow Airport',    # English name
    'name_cn': '伦敦希思罗机场'               # Chinese name (if available)
}
```

## Language Support

The API supports two languages:

- **English** (`Language.ENGLISH`): Default language
- **Chinese** (`Language.CHINESE`): Simplified Chinese

When using Chinese language:
- All localized fields (`name`, `city`, `country`) return Chinese text
- English versions are still available in `name_en` field
- Search queries can be in Chinese characters

## Search Capabilities

### 1. Exact Code Search
```python
# Search by exact IATA code
airport = airport_search_api.get_airport_by_code("LHR")
```

### 2. Fuzzy Name Search
```python
# Search by partial airport name
results = airport_search_api.search_airports("heathrow")
```

### 3. City Search
```python
# Search by city name
results = airport_search_api.search_airports("london")
results = airport_search_api.search_by_city("London")
```

### 4. Country Search
```python
# Search by country
results = airport_search_api.search_airports("china")
results = airport_search_api.search_by_country("China")
```

### 5. Keyword Search
```python
# Search by keywords
results = airport_search_api.search_airports("capital")  # Finds Beijing Capital
```

### 6. Multi-language Search
```python
# Chinese search
results = airport_search_api.search_airports("北京", Language.CHINESE)
results = airport_search_api.search_airports("希思罗", Language.CHINESE)
```

## Integration Examples

### Flight Booking System
```python
def find_departure_airports(user_input: str, language: str = "en"):
    """Find airports for flight booking departure selection"""
    lang = Language.CHINESE if language == "zh" else Language.ENGLISH
    
    # Try exact code first
    if len(user_input) == 3:
        exact = airport_search_api.get_airport_by_code(user_input, lang)
        if exact:
            return [exact]
    
    # Fuzzy search
    return airport_search_api.search_airports(user_input, lang, limit=5)
```

### Travel Planning App
```python
def get_airports_in_destination(country: str, language: str = "en"):
    """Get major airports for travel planning"""
    lang = Language.CHINESE if language == "zh" else Language.ENGLISH
    return airport_search_api.search_by_country(country, lang, limit=10)
```

### Auto-complete Widget
```python
def airport_autocomplete(query: str, max_results: int = 5):
    """Provide airport suggestions for autocomplete"""
    if len(query) < 2:
        return []
    
    return airport_search_api.search_airports(query, Language.ENGLISH, max_results)
```

## Performance Notes

- The API uses pre-built search indexes for fast queries
- Search operations are typically sub-millisecond
- All data is loaded into memory for optimal performance
- Supports concurrent access from multiple threads

## Error Handling

```python
try:
    results = airport_search_api.search_airports("invalid")
    if not results:
        print("No airports found")
except Exception as e:
    print(f"Search error: {e}")
```

## Data Coverage

The API currently includes enhanced data for major international airports with:
- Full English and Chinese names
- City and country information
- Geographic regions
- Search keywords

For airports not in the enhanced dataset, basic information from the IATA airport codes is provided.
