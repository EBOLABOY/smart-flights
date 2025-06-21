#!/usr/bin/env python3
"""
调试 Kiwi API 数据结构
查看实际返回的数据格式，特别是隐藏城市信息的位置
"""

import asyncio
import json
from fli.api.kiwi_flights import KiwiFlightsAPI
from fli.models.google_flights.base import LocalizationConfig, Language, Currency


async def debug_oneway_data():
    """调试单程航班数据结构"""
    print("🔍 调试单程航班数据结构")
    print("=" * 50)
    
    # 创建API客户端
    config = LocalizationConfig(Language.CHINESE, Currency.CNY, "CN")
    api = KiwiFlightsAPI(config)
    
    try:
        # 搜索单程航班
        result = await api.search_oneway_hidden_city(
            origin="LHR",
            destination="PVG", 
            departure_date="2025-06-30",
            adults=1,
            limit=2,
            cabin_class="ECONOMY"
        )
        
        if result.get("success"):
            flights = result.get("flights", [])
            print(f"找到 {len(flights)} 个航班")
            
            for i, flight in enumerate(flights, 1):
                print(f"\n航班 {i} 数据结构:")
                print(f"  ID: {flight.get('id', 'N/A')}")
                print(f"  价格: {flight.get('price', 'N/A')}")
                print(f"  是否隐藏城市: {flight.get('is_hidden_city', 'N/A')}")
                print(f"  隐藏目的地代码: '{flight.get('hidden_destination_code', '')}'")
                print(f"  隐藏目的地名称: '{flight.get('hidden_destination_name', '')}'")
                print(f"  航段数量: {flight.get('segment_count', 'N/A')}")
                print(f"  出发机场: {flight.get('departure_airport', 'N/A')}")
                print(f"  到达机场: {flight.get('arrival_airport', 'N/A')}")
                
                # 如果是隐藏城市但信息为空，说明提取有问题
                if flight.get('is_hidden_city') and not flight.get('hidden_destination_code'):
                    print("  ⚠️ 警告：隐藏城市航班但隐藏目的地信息为空！")
        else:
            print(f"搜索失败: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"调试失败: {e}")


async def debug_roundtrip_data():
    """调试往返航班数据结构"""
    print("\n🔍 调试往返航班数据结构")
    print("=" * 50)
    
    # 创建API客户端
    config = LocalizationConfig(Language.CHINESE, Currency.CNY, "CN")
    api = KiwiFlightsAPI(config)
    
    try:
        # 搜索往返航班
        result = await api.search_roundtrip_hidden_city(
            origin="LHR",
            destination="PVG",
            departure_date="2025-06-30",
            return_date="2025-07-07",
            adults=1,
            limit=2,
            cabin_class="BUSINESS"
        )
        
        if result.get("success"):
            flights = result.get("flights", [])
            print(f"找到 {len(flights)} 个往返航班")
            
            for i, flight in enumerate(flights, 1):
                print(f"\n往返航班 {i} 数据结构:")
                print(f"  ID: {flight.get('id', 'N/A')}")
                print(f"  总价格: {flight.get('price', 'N/A')}")
                print(f"  是否隐藏城市: {flight.get('is_hidden_city', 'N/A')}")
                
                # 检查去程信息
                outbound = flight.get('outbound', {})
                if outbound:
                    print(f"  去程:")
                    print(f"    出发: {outbound.get('departure_airport', 'N/A')}")
                    print(f"    到达: {outbound.get('arrival_airport', 'N/A')}")
                    print(f"    隐藏目的地: '{outbound.get('hidden_destination_name', '')}'")
                else:
                    print("  ⚠️ 警告：去程信息缺失！")
                
                # 检查返程信息
                inbound = flight.get('inbound', {})
                if inbound:
                    print(f"  返程:")
                    print(f"    出发: {inbound.get('departure_airport', 'N/A')}")
                    print(f"    到达: {inbound.get('arrival_airport', 'N/A')}")
                    print(f"    隐藏目的地: '{inbound.get('hidden_destination_name', '')}'")
                else:
                    print("  ⚠️ 警告：返程信息缺失！")
        else:
            print(f"搜索失败: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"调试失败: {e}")


async def debug_raw_api_response():
    """调试原始API响应"""
    print("\n🔍 调试原始API响应数据")
    print("=" * 50)
    
    # 创建API客户端
    config = LocalizationConfig(Language.CHINESE, Currency.CNY, "CN")
    api = KiwiFlightsAPI(config)
    
    try:
        # 构建请求变量
        variables = api._build_search_variables(
            origin="LHR",
            destination="PVG",
            departure_date="2025-06-30",
            adults=1,
            cabin_class="BUSINESS"
        )
        
        # 发送请求并保存原始响应
        import httpx
        from fli.api.kiwi_flights import KIWI_GRAPHQL_ENDPOINT, ONEWAY_HIDDEN_CITY_QUERY
        
        payload = {
            "query": ONEWAY_HIDDEN_CITY_QUERY,
            "variables": variables
        }
        
        api_url = f"{KIWI_GRAPHQL_ENDPOINT}?featureName=SearchOneWayItinerariesQuery"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_url, headers=api.headers, json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                
                # 保存原始响应到文件
                with open('debug_kiwi_raw_response.json', 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, ensure_ascii=False, indent=2)
                print("✅ 原始响应已保存到 debug_kiwi_raw_response.json")
                
                # 分析数据结构
                if 'data' in response_data:
                    oneway_data = response_data['data'].get('onewayItineraries')
                    if oneway_data and oneway_data.get('__typename') == 'Itineraries':
                        itineraries = oneway_data.get('itineraries', [])
                        print(f"找到 {len(itineraries)} 个航班")
                        
                        # 分析第一个航班的数据结构
                        if itineraries:
                            first_flight = itineraries[0]
                            print(f"\n第一个航班的数据结构:")
                            print(f"  travelHack: {first_flight.get('travelHack', {})}")
                            
                            sector = first_flight.get('sector', {})
                            segments = sector.get('sectorSegments', [])
                            print(f"  航段数量: {len(segments)}")
                            
                            for j, seg in enumerate(segments):
                                segment = seg.get('segment', {})
                                hidden_dest = segment.get('hiddenDestination')
                                print(f"  航段 {j+1}:")
                                print(f"    出发: {segment.get('source', {}).get('station', {}).get('code', 'N/A')}")
                                print(f"    到达: {segment.get('destination', {}).get('station', {}).get('code', 'N/A')}")
                                print(f"    隐藏目的地: {hidden_dest}")
                
            else:
                print(f"API请求失败: {response.status_code}")
                print(f"响应: {response.text}")
                
    except Exception as e:
        print(f"调试失败: {e}")
        import traceback
        print(traceback.format_exc())


async def main():
    """主调试函数"""
    print("🚀 Kiwi API 数据结构调试")
    print("目标：找出隐藏城市信息提取问题")
    
    await debug_oneway_data()
    await debug_roundtrip_data()
    await debug_raw_api_response()
    
    print("\n" + "=" * 50)
    print("🎯 调试完成！请检查:")
    print("1. 控制台输出的数据结构信息")
    print("2. debug_kiwi_raw_response.json 文件")
    print("3. 找出隐藏城市信息在哪个字段中")


if __name__ == "__main__":
    asyncio.run(main())
