#!/usr/bin/env python3
"""
详细测试北京机场API功能
"""

from fli.api.airport_search import airport_search_api
from fli.models.google_flights.base import Language
import json

def test_beijing_detailed():
    """详细测试北京机场搜索功能"""
    
    print('=== 详细测试北京机场API ===')
    print()

    # 获取详细的机场信息
    result = airport_search_api.get_airport_by_code('PEK', Language.CHINESE)
    print('北京首都国际机场 (PEK) 详细信息:')
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print()
    print('=' * 50)
    print()

    # 搜索结果详细信息
    results = airport_search_api.search_airports('北京', Language.CHINESE, limit=2)
    print('搜索"北京"的详细结果:')
    for i, result in enumerate(results, 1):
        print(f'结果 {i}:')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()

    print('=' * 50)
    print()
    
    # 测试其他搜索方式
    print('通过城市搜索北京的机场:')
    city_results = airport_search_api.search_by_city('北京', Language.CHINESE)
    for i, result in enumerate(city_results, 1):
        print(f'城市搜索结果 {i}:')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print()

if __name__ == "__main__":
    test_beijing_detailed()
