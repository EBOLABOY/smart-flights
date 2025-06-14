#!/usr/bin/env python3
"""
Test script for Airport Search API
"""

from fli.api.airport_search import airport_search_api
from fli.models.google_flights.base import Language

def test_airport_search():
    """Test various airport search scenarios."""
    
    print("=== 测试机场搜索API ===\n")
    
    # Test 1: Search by airport code
    print("1. 通过机场代码搜索:")
    result = airport_search_api.get_airport_by_code("LHR", Language.CHINESE)
    if result:
        print(f"   {result['code']}: {result['name']}")
    else:
        print("   未找到")
    
    # Test 2: Search by city name (English)
    print("\n2. 通过城市名搜索 (英文):")
    results = airport_search_api.search_airports("london", Language.CHINESE, limit=3)
    for result in results:
        print(f"   {result['code']}: {result['name']} - {result['city']}")
    
    # Test 3: Search by city name (Chinese)
    print("\n3. 通过城市名搜索 (中文):")
    results = airport_search_api.search_airports("北京", Language.CHINESE, limit=3)
    for result in results:
        print(f"   {result['code']}: {result['name']} - {result['city']}")
    
    # Test 4: Search by country
    print("\n4. 通过国家搜索:")
    results = airport_search_api.search_by_country("中国", Language.CHINESE, limit=5)
    for result in results:
        print(f"   {result['code']}: {result['name']} - {result['city']}")
    
    # Test 5: Fuzzy search
    print("\n5. 模糊搜索:")
    results = airport_search_api.search_airports("angeles", Language.ENGLISH, limit=3)
    for result in results:
        print(f"   {result['code']}: {result['name']} - {result['city']}")
    
    # Test 6: Search by keywords
    print("\n6. 关键词搜索:")
    results = airport_search_api.search_airports("heathrow", Language.ENGLISH, limit=2)
    for result in results:
        print(f"   {result['code']}: {result['name']} - {result['city']}")

if __name__ == "__main__":
    test_airport_search()
