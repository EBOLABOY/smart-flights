#!/usr/bin/env python3
"""
测试机场API的语言响应功能
"""

from fli.api.airport_search import airport_search_api
from fli.models.google_flights.base import Language
import json

def test_language_response():
    """测试不同语言设置下的响应"""
    
    print('=== 测试语言响应功能 ===')
    print()

    # 测试1: 中文搜索，中文响应
    print('1. 中文搜索 "北京"，中文响应:')
    results = airport_search_api.search_airports('北京', Language.CHINESE, limit=2)
    for result in results:
        print(f'   {result["code"]}: {result["name"]} - {result["city"]}, {result["country"]}')
    print()

    # 测试2: 中文搜索，英文响应
    print('2. 中文搜索 "北京"，英文响应:')
    results = airport_search_api.search_airports('北京', Language.ENGLISH, limit=2)
    for result in results:
        print(f'   {result["code"]}: {result["name"]} - {result["city"]}, {result["country"]}')
    print()

    # 测试3: 英文搜索，英文响应
    print('3. 英文搜索 "beijing"，英文响应:')
    results = airport_search_api.search_airports('beijing', Language.ENGLISH, limit=2)
    for result in results:
        print(f'   {result["code"]}: {result["name"]} - {result["city"]}, {result["country"]}')
    print()

    # 测试4: 英文搜索，中文响应
    print('4. 英文搜索 "beijing"，中文响应:')
    results = airport_search_api.search_airports('beijing', Language.CHINESE, limit=2)
    for result in results:
        print(f'   {result["code"]}: {result["name"]} - {result["city"]}, {result["country"]}')
    print()

    # 测试5: 详细对比
    print('5. 详细对比同一机场的中英文信息:')
    airport_en = airport_search_api.get_airport_by_code('PEK', Language.ENGLISH)
    airport_cn = airport_search_api.get_airport_by_code('PEK', Language.CHINESE)
    
    print('英文响应:')
    print(json.dumps(airport_en, ensure_ascii=False, indent=2))
    print()
    print('中文响应:')
    print(json.dumps(airport_cn, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    test_language_response()
