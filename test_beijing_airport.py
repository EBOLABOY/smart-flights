#!/usr/bin/env python3
"""
测试北京机场搜索功能
"""

from fli.api.airport_search import airport_search_api
from fli.models.google_flights.base import Language

def test_beijing_search():
    """测试输入'北京'的机场搜索功能"""
    
    print('=== 测试输入"北京"的机场搜索 ===')
    print()

    # 测试中文搜索
    print('1. 中文搜索 "北京":')
    results = airport_search_api.search_airports('北京', Language.CHINESE, limit=5)
    for i, result in enumerate(results, 1):
        print(f'   {i}. {result["code"]}: {result["name"]} - {result["city"]}')

    print()

    # 测试英文搜索
    print('2. 英文搜索 "beijing":')
    results = airport_search_api.search_airports('beijing', Language.CHINESE, limit=5)
    for i, result in enumerate(results, 1):
        print(f'   {i}. {result["code"]}: {result["name"]} - {result["city"]}')

    print()

    # 测试通过机场代码搜索
    print('3. 通过机场代码搜索 "PEK":')
    result = airport_search_api.get_airport_by_code('PEK', Language.CHINESE)
    if result:
        print(f'   {result["code"]}: {result["name"]} - {result["city"]}')
    else:
        print('   未找到')

    print()

    # 测试通过机场代码搜索
    print('4. 通过机场代码搜索 "PKX":')
    result = airport_search_api.get_airport_by_code('PKX', Language.CHINESE)
    if result:
        print(f'   {result["code"]}: {result["name"]} - {result["city"]}')
    else:
        print('   未找到')

    print()
    
    # 测试英文输出
    print('5. 英文输出搜索 "北京":')
    results = airport_search_api.search_airports('北京', Language.ENGLISH, limit=5)
    for i, result in enumerate(results, 1):
        print(f'   {i}. {result["code"]}: {result["name"]} - {result["city"]}')

if __name__ == "__main__":
    test_beijing_search()
