#!/usr/bin/env python3
"""
调试 Kiwi API 搜索
直接使用 kiwi_api_test.py 中的方法来测试 LHR -> PEK 路线
"""

import asyncio
import json
from datetime import datetime, timedelta
import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kiwi_api_test import KiwiAPITester


async def debug_search():
    """调试搜索功能"""
    print("🔍 调试 Kiwi API 搜索功能")
    print("=" * 50)
    
    # 创建测试器
    tester = KiwiAPITester()
    
    # 测试路线和日期
    origin = "LHR"
    destination = "PEK"
    departure_date = "2025-06-30"
    
    print(f"搜索路线: {origin} -> {destination}")
    print(f"出发日期: {departure_date}")
    print()
    
    # 1. 测试基础搜索
    print("1. 基础搜索（包含隐藏城市）")
    print("-" * 30)
    result1 = await tester.search_flights(origin, destination, departure_date)
    
    if result1.get("success"):
        print(f"✅ 找到 {len(result1.get('flights', []))} 个航班")
        
        # 统计隐藏城市航班
        hidden_count = 0
        for flight in result1.get('flights', []):
            if flight.get('is_hidden_city'):
                hidden_count += 1
        
        print(f"📊 其中隐藏城市航班: {hidden_count} 个")
        
        # 显示前3个航班的详细信息
        for i, flight in enumerate(result1.get('flights', [])[:3], 1):
            print(f"\n航班 {i}:")
            print(f"  ID: {flight.get('id', 'N/A')}")
            print(f"  价格: €{flight.get('price_eur', 0)}")
            print(f"  时长: {flight.get('duration_minutes', 0)} 分钟")
            print(f"  隐藏城市: {flight.get('is_hidden_city', False)}")
            print(f"  甩尾票: {flight.get('is_throwaway', False)}")
            print(f"  虚拟联程: {flight.get('is_virtual_interlining', False)}")
            
            segments = flight.get('segments', [])
            if segments:
                for j, seg in enumerate(segments, 1):
                    print(f"    航段 {j}: {seg.get('from', '')} -> {seg.get('to', '')}")
                    if seg.get('hidden_destination'):
                        print(f"      隐藏目的地: {seg.get('hidden_destination')}")
    else:
        print(f"❌ 搜索失败: {result1.get('error')}")
    
    print("\n" + "=" * 50)
    
    # 2. 测试专门的隐藏城市搜索
    print("2. 专门的隐藏城市搜索")
    print("-" * 30)
    result2 = await tester.search_with_hidden_city(origin, destination, departure_date)
    
    if result2.get("success"):
        print(f"✅ 找到 {len(result2.get('flights', []))} 个航班")
        
        # 统计隐藏城市航班
        hidden_count = 0
        for flight in result2.get('flights', []):
            if flight.get('is_hidden_city'):
                hidden_count += 1
        
        print(f"📊 其中隐藏城市航班: {hidden_count} 个")
        
        # 显示隐藏城市航班
        hidden_flights = [f for f in result2.get('flights', []) if f.get('is_hidden_city')]
        if hidden_flights:
            print(f"\n🎯 隐藏城市航班详情:")
            for i, flight in enumerate(hidden_flights[:3], 1):
                print(f"\n隐藏城市航班 {i}:")
                print(f"  ID: {flight.get('id', 'N/A')}")
                print(f"  价格: €{flight.get('price_eur', 0)}")
                print(f"  时长: {flight.get('duration_minutes', 0)} 分钟")
                
                segments = flight.get('segments', [])
                for j, seg in enumerate(segments, 1):
                    print(f"    航段 {j}: {seg.get('from', '')} -> {seg.get('to', '')}")
                    print(f"      出发: {seg.get('departure', '')}")
                    print(f"      到达: {seg.get('arrival', '')}")
                    print(f"      航空公司: {seg.get('carrier', '')}")
                    if seg.get('hidden_destination'):
                        print(f"      🎯 隐藏目的地: {seg.get('hidden_destination')}")
        else:
            print("  没有找到隐藏城市航班")
    else:
        print(f"❌ 搜索失败: {result2.get('error')}")
    
    print("\n" + "=" * 50)
    
    # 3. 测试最佳实践搜索
    print("3. 最佳实践搜索")
    print("-" * 30)
    result3 = await tester.search_best_practice(origin, destination, departure_date, 
                                               max_stops=2, enable_hidden_city=True)
    
    if result3.get("success"):
        flights = result3.get('parsed_flights', [])
        print(f"✅ 找到 {len(flights)} 个航班")
        
        # 统计隐藏城市航班
        hidden_count = sum(1 for f in flights if f.get('is_hidden_city'))
        print(f"📊 其中隐藏城市航班: {hidden_count} 个")
        
        # 显示隐藏城市航班
        hidden_flights = [f for f in flights if f.get('is_hidden_city')]
        if hidden_flights:
            print(f"\n🎯 最佳实践隐藏城市航班:")
            for i, flight in enumerate(hidden_flights[:3], 1):
                print(f"\n航班 {i}:")
                print(f"  ID: {flight.get('id', 'N/A')}")
                print(f"  价格: ¥{flight.get('price_cny', 0)}")
                print(f"  时长: {flight.get('duration_minutes', 0)} 分钟")
                print(f"  出发: {flight.get('departure_airport', '')} ({flight.get('departure_airport_name', '')})")
                print(f"  到达: {flight.get('arrival_airport', '')} ({flight.get('arrival_airport_name', '')})")
                print(f"  🎯 隐藏目的地: {flight.get('hidden_destination_code', '')} ({flight.get('hidden_destination_name', '')})")
                print(f"  航空公司: {flight.get('carrier_code', '')} ({flight.get('carrier_name', '')})")
                print(f"  航班号: {flight.get('flight_number', '')}")
        else:
            print("  没有找到隐藏城市航班")
    else:
        print(f"❌ 搜索失败: {result3.get('error')}")


async def main():
    """主函数"""
    try:
        await debug_search()
    except Exception as e:
        print(f"❌ 调试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
