#!/usr/bin/env python3
"""
Airport Search API Usage Examples

This file demonstrates how to use the Fli Airport Search API
for various airport search scenarios.
"""

from fli.api.airport_search import airport_search_api
from fli.models.google_flights.base import Language


def example_1_exact_code_search():
    """Example 1: Search by exact airport code"""
    print("=== Example 1: Search by Airport Code ===")
    
    # Search for specific airports
    airports = ["LHR", "PEK", "LAX", "NRT", "ICN"]
    
    for code in airports:
        # Get English info
        result_en = airport_search_api.get_airport_by_code(code, Language.ENGLISH)
        # Get Chinese info
        result_cn = airport_search_api.get_airport_by_code(code, Language.CHINESE)
        
        if result_en and result_cn:
            print(f"{code}:")
            print(f"  English: {result_en['name']} - {result_en['city']}, {result_en['country']}")
            print(f"  Chinese: {result_cn['name']} - {result_cn['city']}, {result_cn['country']}")
        else:
            print(f"{code}: Not found")
    print()


def example_2_fuzzy_search():
    """Example 2: Fuzzy search by various terms"""
    print("=== Example 2: Fuzzy Search ===")
    
    search_terms = [
        ("london", "Search for London airports"),
        ("北京", "Search for Beijing airports"),
        ("angeles", "Search for Los Angeles"),
        ("heathrow", "Search by airport name"),
        ("成田", "Search for Narita"),
    ]
    
    for term, description in search_terms:
        print(f"{description}: '{term}'")
        results = airport_search_api.search_airports(term, Language.CHINESE, limit=3)
        
        for result in results:
            print(f"  {result['code']}: {result['name']} - {result['city']}")
        print()


def example_3_city_search():
    """Example 3: Search airports by city"""
    print("=== Example 3: Search by City ===")
    
    cities = ["London", "北京", "Tokyo", "上海", "New York"]
    
    for city in cities:
        print(f"Airports in {city}:")
        results = airport_search_api.search_by_city(city, Language.CHINESE)
        
        if results:
            for result in results:
                print(f"  {result['code']}: {result['name']}")
        else:
            print("  No airports found")
        print()


def example_4_country_search():
    """Example 4: Search airports by country"""
    print("=== Example 4: Search by Country ===")
    
    countries = ["China", "中国", "United Kingdom", "Japan", "美国"]
    
    for country in countries:
        print(f"Major airports in {country}:")
        results = airport_search_api.search_by_country(country, Language.CHINESE, limit=5)
        
        if results:
            for result in results:
                print(f"  {result['code']}: {result['name']} - {result['city']}")
        else:
            print("  No airports found")
        print()


def example_5_api_integration():
    """Example 5: API integration for flight booking system"""
    print("=== Example 5: Flight Booking System Integration ===")
    
    def find_airports_for_user_input(user_input: str, language: str = "en"):
        """Simulate a flight booking system's airport search"""
        lang = Language.CHINESE if language.lower() in ["zh", "zh-cn"] else Language.ENGLISH
        
        # Try exact code first
        if len(user_input) == 3:
            exact_match = airport_search_api.get_airport_by_code(user_input, lang)
            if exact_match:
                return [exact_match]
        
        # Fuzzy search
        results = airport_search_api.search_airports(user_input, lang, limit=5)
        return results
    
    # Simulate user inputs
    user_inputs = [
        ("LHR", "en", "User types exact code"),
        ("london", "en", "User types city name"),
        ("北京", "zh-cn", "Chinese user types city"),
        ("heathrow", "en", "User types airport name"),
        ("洛杉矶", "zh-cn", "Chinese user types LA"),
    ]
    
    for user_input, lang, description in user_inputs:
        print(f"{description}: '{user_input}' (language: {lang})")
        results = find_airports_for_user_input(user_input, lang)
        
        if results:
            print("  Suggestions:")
            for result in results:
                print(f"    {result['code']}: {result['name']} - {result['city']}")
        else:
            print("  No suggestions found")
        print()


def example_6_multilingual_support():
    """Example 6: Demonstrate multilingual support"""
    print("=== Example 6: Multilingual Support ===")
    
    airport_codes = ["LHR", "PEK", "LAX", "NRT"]
    
    for code in airport_codes:
        print(f"Airport {code}:")
        
        # Get in English
        result_en = airport_search_api.get_airport_by_code(code, Language.ENGLISH)
        if result_en:
            print(f"  EN: {result_en['name']} in {result_en['city']}, {result_en['country']}")
        
        # Get in Chinese
        result_cn = airport_search_api.get_airport_by_code(code, Language.CHINESE)
        if result_cn:
            print(f"  CN: {result_cn['name']} 位于 {result_cn['city']}, {result_cn['country']}")
        
        print()


def main():
    """Run all examples"""
    print("🛩️  Fli Airport Search API Examples\n")
    
    example_1_exact_code_search()
    example_2_fuzzy_search()
    example_3_city_search()
    example_4_country_search()
    example_5_api_integration()
    example_6_multilingual_support()
    
    print("✅ All examples completed!")


if __name__ == "__main__":
    main()
