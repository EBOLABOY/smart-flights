#!/usr/bin/env python3
"""
测试机场API的高级搜索功能
"""

from fli.api.airport_search import airport_search_api
from fli.models.google_flights.base import Language

def test_advanced_search():
    """测试高级搜索功能"""
    
    print('=== 测试更多搜索功能 ===')
    print()

    # 测试模糊搜索
    print('1. 模糊搜索 "京"（只输入一个字）:')
    results = airport_search_api.search_airports('京', Language.CHINESE, limit=3)
    for result in results:
        print(f'   {result["code"]}: {result["name"]} - {result["city"]}')

    print()

    # 测试关键词搜索
    print('2. 关键词搜索 "首都"（北京首都机场的关键词）:')
    results = airport_search_api.search_airports('首都', Language.CHINESE, limit=3)
    for result in results:
        print(f'   {result["code"]}: {result["name"]} - {result["city"]}')

    print()

    # 测试国家搜索
    print('3. 按国家搜索 "中国"（前5个结果）:')
    results = airport_search_api.search_by_country('中国', Language.CHINESE, limit=5)
    for result in results:
        print(f'   {result["code"]}: {result["name"]} - {result["city"]}')

    print()

    # 测试英文输入搜索中文机场
    print('4. 英文输入 "capital" 搜索（应该找到首都机场）:')
    results = airport_search_api.search_airports('capital', Language.CHINESE, limit=3)
    for result in results:
        print(f'   {result["code"]}: {result["name"]} - {result["city"]}')

    print()

    # 测试拼音搜索
    print('5. 拼音搜索 "beijing"（应该找到北京机场）:')
    results = airport_search_api.search_airports('beijing', Language.CHINESE, limit=3)
    for result in results:
        print(f'   {result["code"]}: {result["name"]} - {result["city"]}')

if __name__ == "__main__":
    test_advanced_search()
