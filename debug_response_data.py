#!/usr/bin/env python3
"""
调试 Kiwi API 响应数据
查看实际返回的航班数据结构，特别是隐藏城市信息
"""

import asyncio
import json
import logging
from datetime import datetime

from fli.api.kiwi_flights import KiwiFlightsAPI
from fli.models.google_flights.base import LocalizationConfig, Language, Currency

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def debug_response_structure():
    """调试响应数据结构"""
    print("🔍 调试 Kiwi API 响应数据结构")
    print("=" * 50)
    
    # 创建API实例
    config = LocalizationConfig(
        language=Language.CHINESE,
        currency=Currency.CNY,
        region="CN"
    )
    api = KiwiFlightsAPI(config)
    
    # 搜索参数
    origin = "LHR"
    destination = "PEK"
    departure_date = "2025-06-30"
    
    print(f"搜索路线: {origin} -> {destination}")
    print(f"出发日期: {departure_date}")
    print()
    
    try:
        # 执行搜索
        result = await api.search_oneway_hidden_city(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            adults=1,
            limit=10
        )
        
        if result.get("success"):
            print(f"✅ 搜索成功!")
            print(f"总航班数: {result.get('total_count', 0)}")
            print(f"返回航班数: {len(result.get('flights', []))}")
            print()
            
            # 检查每个航班的详细信息
            flights = result.get('flights', [])
            for i, flight in enumerate(flights, 1):
                print(f"航班 {i} 详细信息:")
                print(f"  ID: {flight.get('id', 'N/A')}")
                print(f"  价格: {flight.get('price', 0)}")
                print(f"  时长: {flight.get('duration_minutes', 0)} 分钟")
                print(f"  is_hidden_city: {flight.get('is_hidden_city', False)}")
                print(f"  is_throwaway: {flight.get('is_throwaway', False)}")
                print(f"  出发机场: {flight.get('departure_airport', '')} ({flight.get('departure_airport_name', '')})")
                print(f"  到达机场: {flight.get('arrival_airport', '')} ({flight.get('arrival_airport_name', '')})")
                print(f"  隐藏目的地代码: {flight.get('hidden_destination_code', '')}")
                print(f"  隐藏目的地名称: {flight.get('hidden_destination_name', '')}")
                print(f"  航空公司: {flight.get('carrier_code', '')} ({flight.get('carrier_name', '')})")
                print(f"  航班号: {flight.get('flight_number', '')}")
                print(f"  航段数: {flight.get('segment_count', 1)}")
                print()
            
            # 保存原始响应数据用于分析
            if hasattr(api, '_last_raw_response'):
                with open('debug_raw_response.json', 'w', encoding='utf-8') as f:
                    json.dump(api._last_raw_response, f, ensure_ascii=False, indent=2)
                print("📁 原始响应数据已保存到 debug_raw_response.json")
        else:
            print(f"❌ 搜索失败: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 调试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


async def debug_with_raw_api_call():
    """直接调用 API 并保存原始响应"""
    print("\n" + "=" * 50)
    print("🔍 直接 API 调用调试")
    print("=" * 50)
    
    import httpx
    from fli.api.kiwi_flights import KIWI_GRAPHQL_ENDPOINT, KIWI_HEADERS
    
    # 构建请求参数（复制自我们的实现）
    dep_date_obj = datetime.strptime("2025-06-30", "%Y-%m-%d")
    
    variables = {
        "search": {
            "itinerary": {
                "source": {"ids": ["Station:airport:LHR"]},
                "destination": {"ids": ["Station:airport:PEK"]},
                "outboundDepartureDate": {
                    "start": dep_date_obj.strftime("%Y-%m-%dT00:00:00"),
                    "end": dep_date_obj.strftime("%Y-%m-%dT23:59:59")
                }
            },
            "passengers": {
                "adults": 1,
                "children": 0,
                "infants": 0,
                "adultsHoldBags": [0],
                "adultsHandBags": [1]
            },
            "cabinClass": {
                "cabinClass": "ECONOMY",
                "applyMixedClasses": False
            }
        },
        "filter": {
            "maxStopsCount": 0,  # 只搜索直飞航班
            "enableTrueHiddenCity": True,  # Enable hidden city search
            "transportTypes": ["FLIGHT"]
        },
        "options": {
            "sortBy": "PRICE",
            "currency": "cny",
            "locale": "zh",
            "partner": "skypicker",
            "partnerMarket": "cn",
            "storeSearch": False,
            "serverToken": None
        }
    }
    
    # 使用最佳实践查询
    best_practice_query = """
query SearchItinerariesQuery(
  $search: SearchOnewayInput
  $filter: ItinerariesFilterInput
  $options: ItinerariesOptionsInput
) {
  onewayItineraries(search: $search, filter: $filter, options: $options) {
    __typename
    ... on AppError {
      error: message
    }
    ... on Itineraries {
      metadata {
        itinerariesCount
        hasMorePending
      }
      itineraries {
        __typename
        ... on ItineraryOneWay {
          id
          price {
            amount
          }
          priceEur {
            amount
          }
          duration
          travelHack {
            isTrueHiddenCity
            isThrowawayTicket
          }
          sector {
            sectorSegments {
              segment {
                source {
                  localTime
                  station {
                    code
                    name
                  }
                }
                destination {
                  localTime
                  station {
                    code
                    name
                  }
                }
                hiddenDestination {
                  code
                  name
                }
                carrier {
                  code
                  name
                }
                code
                duration
              }
            }
          }
        }
      }
    }
  }
}
"""
    
    payload = {
        "query": best_practice_query,
        "variables": variables
    }
    
    try:
        api_url = f"{KIWI_GRAPHQL_ENDPOINT}?featureName=SearchOneWayItinerariesQuery"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(api_url, headers=KIWI_HEADERS, json=payload)
            
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                # 保存完整的原始响应
                with open('debug_full_raw_response.json', 'w', encoding='utf-8') as f:
                    json.dump(response_data, f, ensure_ascii=False, indent=2)
                print("📁 完整原始响应已保存到 debug_full_raw_response.json")
                
                # 分析响应结构
                if 'data' in response_data:
                    oneway_data = response_data['data'].get('onewayItineraries')
                    if oneway_data and oneway_data.get('__typename') == 'Itineraries':
                        itineraries = oneway_data.get('itineraries', [])
                        print(f"\n找到 {len(itineraries)} 个航班")
                        
                        for i, itinerary in enumerate(itineraries, 1):
                            print(f"\n航班 {i} 原始数据分析:")
                            
                            # 基本信息
                            travel_hack = itinerary.get('travelHack', {})
                            print(f"  travelHack.isTrueHiddenCity: {travel_hack.get('isTrueHiddenCity', False)}")
                            print(f"  travelHack.isThrowawayTicket: {travel_hack.get('isThrowawayTicket', False)}")
                            
                            # 航段信息
                            sector = itinerary.get('sector', {})
                            segments = sector.get('sectorSegments', [])
                            print(f"  航段数量: {len(segments)}")
                            
                            for j, seg_wrapper in enumerate(segments, 1):
                                segment = seg_wrapper.get('segment', {})
                                source = segment.get('source', {})
                                destination = segment.get('destination', {})
                                hidden_destination = segment.get('hiddenDestination')
                                
                                print(f"    航段 {j}:")
                                print(f"      从: {source.get('station', {}).get('code', '')} ({source.get('station', {}).get('name', '')})")
                                print(f"      到: {destination.get('station', {}).get('code', '')} ({destination.get('station', {}).get('name', '')})")
                                print(f"      隐藏目的地: {hidden_destination}")
                                if hidden_destination:
                                    print(f"        隐藏目的地代码: {hidden_destination.get('code', '')}")
                                    print(f"        隐藏目的地名称: {hidden_destination.get('name', '')}")
                    else:
                        print("❌ 响应格式不正确或包含错误")
                        print(f"oneway_data: {oneway_data}")
                else:
                    print("❌ 响应中缺少 data 字段")
            else:
                print(f"❌ API 请求失败: {response.text}")
                
    except Exception as e:
        print(f"❌ 直接 API 调用失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    await debug_response_structure()
    await debug_with_raw_api_call()


if __name__ == "__main__":
    asyncio.run(main())
