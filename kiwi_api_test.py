#!/usr/bin/env python3
"""
Kiwi API 测试文件
包含项目中与Kiwi.com API通讯的主要方法，用于独立测试
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import httpx

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Kiwi API 配置
KIWI_GRAPHQL_ENDPOINT = "https://api.skypicker.com/umbrella/v2/graphql"

# 固定的Kiwi Headers（从项目中提取）
KIWI_HEADERS = {
    'content-type': 'application/json',
    'kw-skypicker-visitor-uniqid': 'b500f05c-8234-4a94-82a7-fb5dc02340a9',
    'kw-umbrella-token': '0d23674b463dadee841cc65da51e34fe47bbbe895ae13b69d42ece267c7a2f51',
    'kw-x-rand-id': '07d338ea',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
    'origin': 'https://www.kiwi.com',
    'referer': 'https://www.kiwi.com/cn/search/tiles/--/--/anytime/anytime'
}

# 最佳实践的精简GraphQL查询
BEST_PRACTICE_QUERY = """
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

# GraphQL 查询模板（基于项目中成熟的实现）
ONEWAY_QUERY_TEMPLATE = """
query SearchOneWayItinerariesQuery(
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
      server {
        requestId
        packageVersion
        serverToken
      }
      metadata {
        itinerariesCount
        hasMorePending
      }
      itineraries {
        __typename
        ... on ItineraryOneWay {
          id
          shareId
          price {
            amount
            priceBeforeDiscount
          }
          priceEur {
            amount
          }
          provider {
            name
            code
            hasHighProbabilityOfPriceChange
          }
          bagsInfo {
            includedCheckedBags
            includedHandBags
            hasNoBaggageSupported
            hasNoCheckedBaggage
            includedPersonalItem
          }
          bookingOptions {
            edges {
              node {
                token
                bookingUrl
                price {
                  amount
                }
                priceEur {
                  amount
                }
                itineraryProvider {
                  code
                  name
                  hasHighProbabilityOfPriceChange
                }
              }
            }
          }
          travelHack {
            isTrueHiddenCity
            isVirtualInterlining
            isThrowawayTicket
          }
          duration
          pnrCount
          sector {
            id
            duration
            sectorSegments {
              guarantee
              segment {
                id
                source {
                  localTime
                  utcTimeIso
                  station {
                    name
                    code
                    type
                    city {
                      name
                    }
                    country {
                      code
                      name
                    }
                  }
                }
                destination {
                  localTime
                  utcTimeIso
                  station {
                    name
                    code
                    type
                    city {
                      name
                    }
                    country {
                      code
                      name
                    }
                  }
                }
                hiddenDestination {
                  code
                  name
                  city {
                    name
                  }
                  country {
                    code
                    name
                  }
                }
                duration
                type
                code
                carrier {
                  name
                  code
                }
                operatingCarrier {
                  name
                  code
                }
                cabinClass
              }
              layover {
                duration
                isBaggageRecheck
              }
            }
          }
          lastAvailable {
            seatsLeft
          }
        }
      }
    }
  }
}
"""

# 往返航班查询模板
RETURN_QUERY_TEMPLATE = """
query SearchReturnItinerariesQuery(
  $search: SearchReturnInput
  $filter: ItinerariesFilterInput
  $options: ItinerariesOptionsInput
) {
  returnItineraries(search: $search, filter: $filter, options: $options) {
    __typename
    ... on AppError {
      error: message
    }
    ... on Itineraries {
      server {
        requestId
        packageVersion
        serverToken
      }
      metadata {
        itinerariesCount
        hasMorePending
      }
      itineraries {
        __typename
        ... on ItineraryReturn {
          id
          shareId
          price {
            amount
            priceBeforeDiscount
          }
          priceEur {
            amount
          }
          provider {
            name
            code
          }
          duration
          pnrCount
          travelHack {
            isTrueHiddenCity
            isThrowawayTicket
          }
          outbound {
            duration
            sectorSegments {
              segment {
                source {
                  localTime
                  station {
                    name
                    code
                    city {
                      name
                    }
                  }
                }
                destination {
                  localTime
                  station {
                    name
                    code
                    city {
                      name
                    }
                  }
                }
                duration
                carrier {
                  name
                  code
                }
                operatingCarrier {
                  name
                  code
                }
                cabinClass
                code
              }
              layover {
                duration
                isBaggageRecheck
              }
            }
          }
          inbound {
            duration
            sectorSegments {
              segment {
                source {
                  localTime
                  station {
                    name
                    code
                    city {
                      name
                    }
                  }
                }
                destination {
                  localTime
                  station {
                    name
                    code
                    city {
                      name
                    }
                  }
                }
                duration
                carrier {
                  name
                  code
                }
                operatingCarrier {
                  name
                  code
                }
                cabinClass
                code
              }
              layover {
                duration
                isBaggageRecheck
              }
            }
          }
        }
      }
    }
  }
}
"""


class KiwiAPITester:
    """Kiwi API 测试类"""
    
    def __init__(self):
        self.headers = KIWI_HEADERS.copy()
        self.timeout = 30.0
    
    async def test_token_validation(self) -> bool:
        """测试Token是否有效"""
        logger.info("开始测试Kiwi API Token有效性...")
        
        try:
            test_payload = {
                "query": "query { __typename }",
                "variables": {}
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    KIWI_GRAPHQL_ENDPOINT,
                    headers=self.headers,
                    json=test_payload
                )
                
                logger.info(f"Token验证响应状态码: {response.status_code}")
                if response.status_code == 200:
                    logger.info("✅ Token验证成功")
                    return True
                else:
                    logger.error(f"❌ Token验证失败: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Token验证请求失败: {e}")
            return False
    
    def build_search_variables(self, origin: str, destination: str,
                             departure_date: str, adults: int = 1) -> Dict[str, Any]:
        """构建搜索变量 - 完全基于项目中的 _build_kiwi_variables 实现"""
        dep_date_obj = datetime.strptime(departure_date, "%Y-%m-%d")

        return {
            "search": {
                "itinerary": {
                    "source": {"ids": [f"Station:airport:{origin.upper()}"]},
                    "destination": {"ids": [f"Station:airport:{destination.upper()}"]},
                    "outboundDepartureDate": {
                        "start": dep_date_obj.strftime("%Y-%m-%dT00:00:00"),
                        "end": dep_date_obj.strftime("%Y-%m-%dT23:59:59")
                    }
                },
                "passengers": {
                    "adults": adults,
                    "children": 0,
                    "infants": 0,
                    "adultsHoldBags": [0],  # 项目中默认为 [0]
                    "adultsHandBags": [1]   # 项目中默认为 [1]
                },
                "cabinClass": {
                    "cabinClass": "ECONOMY",
                    "applyMixedClasses": False  # 项目中为 False
                }
            },
            "filter": {
                "allowDifferentStationConnection": True,
                "enableSelfTransfer": True,
                "enableThrowAwayTicketing": True,
                "enableTrueHiddenCity": True,
                "transportTypes": ["FLIGHT"],
                "contentProviders": ["KIWI"],  # 项目中只有 KIWI
                "limit": 30  # 项目中为 30
            },
            "options": {
                "sortBy": "PRICE",  # 项目中为 PRICE
                "currency": "cny",  # 改为人民币
                "locale": "zh",     # 改为中文
                "partner": "skypicker",
                "partnerMarket": "cn",  # 项目中默认为 cn
                "storeSearch": False,
                "serverToken": None
            }
        }
    
    async def search_flights(self, origin: str, destination: str, 
                           departure_date: str, max_stops: int = 3) -> Dict[str, Any]:
        """搜索航班"""
        search_id = f"test_{int(time.time())}"
        logger.info(f"[{search_id}] 开始搜索航班: {origin} -> {destination}, 日期: {departure_date}")
        
        try:
            # 构建搜索变量
            variables = self.build_search_variables(origin, destination, departure_date)
            variables["filter"]["maxStopsCount"] = max_stops
            
            payload = {
                "query": ONEWAY_QUERY_TEMPLATE,
                "variables": variables
            }
            
            # 发送请求
            api_url = f"{KIWI_GRAPHQL_ENDPOINT}?featureName=SearchOneWayItinerariesQuery"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(api_url, headers=self.headers, json=payload)
                
                logger.info(f"[{search_id}] 响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    response_data = response.json()
                    return self.parse_search_response(response_data, search_id)
                else:
                    logger.error(f"[{search_id}] 请求失败: {response.status_code} - {response.text}")
                    return {"error": f"HTTP {response.status_code}", "details": response.text}
                    
        except Exception as e:
            logger.error(f"[{search_id}] 搜索失败: {e}")
            return {"error": str(e)}
    
    def parse_search_response(self, response_data: Dict[str, Any], search_id: str) -> Dict[str, Any]:
        """解析搜索响应"""
        try:
            if 'data' not in response_data:
                return {"error": "响应中缺少data字段", "raw_response": response_data}
            
            oneway_data = response_data['data'].get('onewayItineraries')
            if not oneway_data:
                return {"error": "响应中缺少onewayItineraries字段", "raw_response": response_data}
            
            if oneway_data.get('__typename') == 'AppError':
                error_msg = oneway_data.get('error', 'Unknown API error')
                logger.error(f"[{search_id}] API返回错误: {error_msg}")
                return {"error": f"API Error: {error_msg}"}
            
            if oneway_data.get('__typename') != 'Itineraries':
                return {"error": f"意外的响应类型: {oneway_data.get('__typename')}", "raw_response": response_data}
            
            # 解析航班数据
            itineraries = oneway_data.get('itineraries', [])
            metadata = oneway_data.get('metadata', {})
            
            logger.info(f"[{search_id}] 找到 {len(itineraries)} 个航班")
            logger.info(f"[{search_id}] 总数量: {metadata.get('itinerariesCount', 0)}")
            logger.info(f"[{search_id}] 是否有更多: {metadata.get('hasMorePending', False)}")
            
            # 简化航班信息
            simplified_flights = []
            for i, itinerary in enumerate(itineraries[:5]):  # 只显示前5个
                flight_info = self.extract_flight_info(itinerary, i)
                simplified_flights.append(flight_info)
            
            return {
                "success": True,
                "search_id": search_id,
                "total_count": metadata.get('itinerariesCount', 0),
                "has_more": metadata.get('hasMorePending', False),
                "flights": simplified_flights,
                "raw_sample": itineraries[0] if itineraries else None
            }
            
        except Exception as e:
            logger.error(f"[{search_id}] 解析响应失败: {e}")
            return {"error": f"解析失败: {str(e)}", "raw_response": response_data}
    
    def extract_flight_info(self, itinerary: Dict[str, Any], index: int) -> Dict[str, Any]:
        """提取航班关键信息"""
        try:
            price = itinerary.get('priceEur', {}).get('amount', 0)
            duration = itinerary.get('duration', 0)
            pnr_count = itinerary.get('pnrCount', 1)

            # 提取航段信息
            sector = itinerary.get('sector', {})
            segments = sector.get('sectorSegments', [])

            flight_segments = []
            for seg in segments:
                segment_data = seg.get('segment', {})
                source = segment_data.get('source', {})
                destination = segment_data.get('destination', {})
                carrier = segment_data.get('carrier', {})
                hidden_dest = segment_data.get('hiddenDestination', {})

                flight_segments.append({
                    "from": source.get('station', {}).get('code', ''),
                    "to": destination.get('station', {}).get('code', ''),
                    "departure": source.get('localTime', ''),
                    "arrival": destination.get('localTime', ''),
                    "carrier": carrier.get('code', ''),
                    "flight_number": segment_data.get('code', ''),
                    "hidden_destination": hidden_dest.get('code', '') if hidden_dest else None
                })

            # 提取预订选项
            booking_options = itinerary.get('bookingOptions', {}).get('edges', [])
            booking_url = None
            if booking_options:
                booking_url = booking_options[0].get('node', {}).get('bookingUrl', '')

            return {
                "index": index + 1,
                "id": itinerary.get('id', ''),
                "price_eur": price,
                "duration_minutes": duration // 60 if duration else 0,
                "pnr_count": pnr_count,
                "segments": flight_segments,
                "is_hidden_city": itinerary.get('travelHack', {}).get('isTrueHiddenCity', False),
                "is_throwaway": itinerary.get('travelHack', {}).get('isThrowawayTicket', False),
                "is_virtual_interlining": itinerary.get('travelHack', {}).get('isVirtualInterlining', False),
                "booking_url": booking_url,
                "provider": itinerary.get('provider', {}).get('name', ''),
                "bags_info": {
                    "checked_bags": itinerary.get('bagsInfo', {}).get('includedCheckedBags', 0),
                    "hand_bags": itinerary.get('bagsInfo', {}).get('includedHandBags', 0)
                }
            }

        except Exception as e:
            logger.error(f"提取航班信息失败: {e}")
            return {"index": index + 1, "error": str(e)}

    async def search_direct_flights_only(self, origin: str, destination: str,
                                       departure_date: str) -> Dict[str, Any]:
        """搜索仅直飞航班"""
        logger.info(f"搜索直飞航班: {origin} -> {destination}")
        return await self.search_flights(origin, destination, departure_date, max_stops=0)

    async def search_with_hidden_city(self, origin: str, destination: str,
                                    departure_date: str) -> Dict[str, Any]:
        """搜索包含隐藏城市的航班"""
        search_id = f"hidden_{int(time.time())}"
        logger.info(f"[{search_id}] 搜索隐藏城市航班: {origin} -> {destination}")

        try:
            variables = self.build_search_variables(origin, destination, departure_date)
            # 启用隐藏城市搜索
            variables["filter"]["enableTrueHiddenCity"] = True
            variables["filter"]["enableSelfTransfer"] = True
            variables["filter"]["enableThrowAwayTicketing"] = True
            variables["filter"]["maxStopsCount"] = 2

            payload = {
                "query": ONEWAY_QUERY_TEMPLATE,
                "variables": variables
            }

            api_url = f"{KIWI_GRAPHQL_ENDPOINT}?featureName=SearchOneWayItinerariesQuery"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(api_url, headers=self.headers, json=payload)

                if response.status_code == 200:
                    response_data = response.json()
                    return self.parse_search_response(response_data, search_id)
                else:
                    return {"error": f"HTTP {response.status_code}", "details": response.text}

        except Exception as e:
            return {"error": str(e)}

    async def test_multiple_destinations(self, origin: str, destinations: List[str],
                                       departure_date: str) -> Dict[str, Any]:
        """测试多个目的地的搜索（甩尾票策略）"""
        logger.info(f"测试甩尾票策略: {origin} -> {destinations}")

        results = {}
        for dest in destinations:
            logger.info(f"搜索 {origin} -> {dest}")
            result = await self.search_flights(origin, dest, departure_date)
            results[dest] = result

            # 添加延迟避免请求过快
            await asyncio.sleep(1)

        return result

    def build_best_practice_variables(self, origin: str, destination: str,
                                    departure_date: str, max_stops: int = 0,
                                    enable_hidden_city: bool = True) -> Dict[str, Any]:
        """构建最佳实践的请求变量"""
        dep_date_obj = datetime.strptime(departure_date, "%Y-%m-%d")

        return {
            "search": {
                "itinerary": {
                    "source": {"ids": [f"Station:airport:{origin.upper()}"]},
                    "destination": {"ids": [f"Station:airport:{destination.upper()}"]},
                    "outboundDepartureDate": {
                        "start": dep_date_obj.strftime("%Y-%m-%dT00:00:00"),
                        "end": dep_date_obj.strftime("%Y-%m-%dT23:59:59")
                    }
                },
                "passengers": {
                    "adults": 1,
                    "children": 0,
                    "infants": 0
                },
                "cabinClass": {
                    "cabinClass": "ECONOMY",
                    "applyMixedClasses": False
                }
            },
            "filter": {
                "maxStopsCount": max_stops,
                "enableTrueHiddenCity": enable_hidden_city,
                "transportTypes": ["FLIGHT"]
            },
            "options": {
                "sortBy": "PRICE",
                "currency": "cny",  # 人民币
                "locale": "zh",     # 中文
                "partner": "skypicker",
                "partnerMarket": "cn",
                "storeSearch": False
            }
        }

    async def search_best_practice(self, origin: str, destination: str,
                                 departure_date: str, max_stops: int = 0,
                                 enable_hidden_city: bool = True) -> Dict[str, Any]:
        """使用最佳实践方法搜索航班"""
        search_id = f"bp_{int(time.time())}"
        logger.info(f"[{search_id}] 最佳实践搜索: {origin} -> {destination}, 最大中转: {max_stops}, 隐藏城市: {enable_hidden_city}")

        try:
            # 构建请求变量
            variables = self.build_best_practice_variables(
                origin, destination, departure_date, max_stops, enable_hidden_city
            )

            payload = {
                "query": BEST_PRACTICE_QUERY,
                "variables": variables
            }

            # 发送请求
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    KIWI_GRAPHQL_ENDPOINT,  # 使用全局定义的常量
                    headers=self.headers,
                    json=payload
                )

                logger.info(f"[{search_id}] 响应状态码: {response.status_code}")

                if response.status_code == 200:
                    response_data = response.json()
                    return {
                        "success": True,
                        "search_id": search_id,
                        "request": payload,
                        "response": response_data,
                        "parsed_flights": self.parse_best_practice_response(response_data, search_id)
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }

        except Exception as e:
            logger.error(f"[{search_id}] 搜索失败: {e}")
            return {"success": False, "error": str(e)}

    def parse_best_practice_response(self, response_data: Dict[str, Any], search_id: str) -> List[Dict[str, Any]]:
        """使用最佳实践方法解析响应"""
        try:
            if 'data' not in response_data:
                logger.error(f"[{search_id}] 响应中缺少data字段")
                return []

            oneway_data = response_data['data'].get('onewayItineraries')
            if not oneway_data:
                logger.error(f"[{search_id}] 响应中缺少onewayItineraries字段")
                return []

            # 检查API错误
            if oneway_data.get('__typename') == 'AppError':
                error_msg = oneway_data.get('error', 'Unknown API error')
                logger.error(f"[{search_id}] API返回错误: {error_msg}")
                return []

            # 解析航班数据
            itineraries = oneway_data.get('itineraries', [])
            metadata = oneway_data.get('metadata', {})

            logger.info(f"[{search_id}] 找到 {len(itineraries)} 个航班，总数: {metadata.get('itinerariesCount', 0)}")

            parsed_flights = []
            for flight in itineraries:
                parsed_flight = self.parse_single_best_practice_flight(flight)
                if parsed_flight:
                    parsed_flights.append(parsed_flight)

            return parsed_flights

        except Exception as e:
            logger.error(f"[{search_id}] 解析响应失败: {e}")
            return []

    def parse_single_best_practice_flight(self, flight: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析单个航班信息（最佳实践版本）"""
        try:
            # 基本信息
            flight_id = flight.get('id', '')
            price_cny = flight.get('price', {}).get('amount', 0)
            price_eur = flight.get('priceEur', {}).get('amount', 0)
            duration = flight.get('duration', 0)

            # 隐藏城市信息
            travel_hack = flight.get('travelHack', {})
            is_hidden_city = travel_hack.get('isTrueHiddenCity', False)
            is_throwaway = travel_hack.get('isThrowawayTicket', False)

            # 航段信息
            sector = flight.get('sector', {})
            segments = sector.get('sectorSegments', [])

            if not segments:
                return None

            # 解析第一个航段（主要航段）
            first_segment = segments[0].get('segment', {})
            source = first_segment.get('source', {})
            destination = first_segment.get('destination', {})
            hidden_destination = first_segment.get('hiddenDestination', {})
            carrier = first_segment.get('carrier', {})

            return {
                "id": flight_id,
                "price_cny": price_cny,
                "price_eur": price_eur,
                "duration_minutes": duration // 60 if duration else 0,
                "is_hidden_city": is_hidden_city,
                "is_throwaway": is_throwaway,
                "departure_airport": source.get('station', {}).get('code', ''),
                "departure_airport_name": source.get('station', {}).get('name', ''),
                "arrival_airport": destination.get('station', {}).get('code', ''),
                "arrival_airport_name": destination.get('station', {}).get('name', ''),
                "hidden_destination_code": hidden_destination.get('code', '') if hidden_destination else '',
                "hidden_destination_name": hidden_destination.get('name', '') if hidden_destination else '',
                "carrier_code": carrier.get('code', ''),
                "carrier_name": carrier.get('name', ''),
                "flight_number": first_segment.get('code', ''),
                "departure_time": source.get('localTime', ''),
                "arrival_time": destination.get('localTime', ''),
                "segment_count": len(segments)
            }

        except Exception as e:
            logger.error(f"解析单个航班失败: {e}")
            return None

    async def search_oneway_direct(self, origin: str, destination: str,
                                 departure_date: str, currency: str = "cny",
                                 locale: str = "zh") -> Dict[str, Any]:
        """搜索单程直飞航班"""
        search_id = f"oneway_{currency}_{int(time.time())}"
        logger.info(f"[{search_id}] 单程直飞搜索: {origin} -> {destination}, 货币: {currency}, 语言: {locale}")

        try:
            # 构建请求变量（使用指定货币和语言）
            variables = self.build_best_practice_variables(origin, destination, departure_date, max_stops=0)
            variables["options"]["currency"] = currency
            variables["options"]["locale"] = locale

            payload = {
                "query": BEST_PRACTICE_QUERY,
                "variables": variables
            }

            # 发送请求
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    KIWI_GRAPHQL_ENDPOINT,
                    headers=self.headers,
                    json=payload
                )

                logger.info(f"[{search_id}] 响应状态码: {response.status_code}")

                if response.status_code == 200:
                    response_data = response.json()
                    parsed_flights = self.parse_best_practice_response_with_currency(response_data, search_id, currency)

                    return {
                        "success": True,
                        "search_id": search_id,
                        "currency": currency,
                        "locale": locale,
                        "trip_type": "oneway",
                        "parsed_flights": parsed_flights
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }

        except Exception as e:
            logger.error(f"[{search_id}] 搜索失败: {e}")
            return {"success": False, "error": str(e)}

    async def search_roundtrip_direct(self, origin: str, destination: str,
                                    departure_date: str, return_date: str,
                                    currency: str = "cny", locale: str = "zh") -> Dict[str, Any]:
        """搜索往返直飞航班"""
        search_id = f"rt_{currency}_{int(time.time())}"
        logger.info(f"[{search_id}] 往返直飞搜索: {origin} ⇄ {destination}, 货币: {currency}, 语言: {locale}")

        try:
            # 构建往返请求变量
            variables = self.build_roundtrip_variables(origin, destination, departure_date, return_date)
            variables["options"]["currency"] = currency
            variables["options"]["locale"] = locale
            variables["filter"]["maxStopsCount"] = 0  # 只要直飞
            variables["filter"]["enableTrueHiddenCity"] = True  # 启用隐藏城市

            payload = {
                "query": RETURN_QUERY_TEMPLATE,
                "variables": variables
            }

            # 发送请求到往返航班端点（使用正确的featureName）
            api_url = f"{KIWI_GRAPHQL_ENDPOINT}?featureName=SearchReturnItinerariesQuery"
            logger.info(f"[{search_id}] 使用往返端点: {api_url}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    api_url,
                    headers=self.headers,
                    json=payload
                )

                logger.info(f"[{search_id}] 响应状态码: {response.status_code}")

                if response.status_code == 200:
                    response_data = response.json()
                    parsed_flights = self.parse_roundtrip_best_practice_response(response_data, search_id, currency)

                    return {
                        "success": True,
                        "search_id": search_id,
                        "currency": currency,
                        "locale": locale,
                        "trip_type": "roundtrip",
                        "parsed_flights": parsed_flights
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }

        except Exception as e:
            logger.error(f"[{search_id}] 往返搜索失败: {e}")
            return {"success": False, "error": str(e)}

    def parse_roundtrip_best_practice_response(self, response_data: Dict[str, Any],
                                             search_id: str, currency: str) -> List[Dict[str, Any]]:
        """解析往返航班的最佳实践响应"""
        try:
            if 'data' not in response_data:
                logger.error(f"[{search_id}] 响应中缺少data字段")
                return []

            return_data = response_data['data'].get('returnItineraries')
            if not return_data:
                logger.error(f"[{search_id}] 响应中缺少returnItineraries字段")
                return []

            # 检查API错误
            if return_data.get('__typename') == 'AppError':
                error_msg = return_data.get('error', 'Unknown API error')
                logger.error(f"[{search_id}] API返回错误: {error_msg}")
                return []

            # 解析航班数据
            itineraries = return_data.get('itineraries', [])
            metadata = return_data.get('metadata', {})

            logger.info(f"[{search_id}] 找到 {len(itineraries)} 个往返航班，总数: {metadata.get('itinerariesCount', 0)}")

            parsed_flights = []
            for itinerary in itineraries:
                parsed_flight = self.parse_single_roundtrip_flight(itinerary, currency)
                if parsed_flight:
                    parsed_flights.append(parsed_flight)

            return parsed_flights

        except Exception as e:
            logger.error(f"[{search_id}] 解析往返响应失败: {e}")
            return []

    def parse_single_roundtrip_flight(self, itinerary: Dict[str, Any], currency: str) -> Optional[Dict[str, Any]]:
        """解析单个往返航班信息"""
        try:
            # 基本信息
            flight_id = itinerary.get('id', '')
            price_main = itinerary.get('price', {}).get('amount', 0)
            is_overall_hidden_city = itinerary.get('travelHack', {}).get('isTrueHiddenCity', False)

            # 解析去程和返程
            def parse_leg(leg_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
                segments = leg_data.get('sectorSegments', [])
                if not segments:
                    return None

                # 对于直飞，应该只有一个segment
                if len(segments) == 1:
                    segment = segments[0].get('segment', {})
                    source = segment.get('source', {})
                    destination = segment.get('destination', {})
                    hidden_destination = segment.get('hiddenDestination', {})
                    carrier = segment.get('carrier', {})

                    is_hidden = bool(hidden_destination)

                    return {
                        "departure_airport": source.get('station', {}).get('code', ''),
                        "departure_airport_name": source.get('station', {}).get('name', ''),
                        "arrival_airport": destination.get('station', {}).get('code', ''),
                        "arrival_airport_name": destination.get('station', {}).get('name', ''),
                        "hidden_destination_code": hidden_destination.get('code', '') if hidden_destination else '',
                        "hidden_destination_name": hidden_destination.get('name', '') if hidden_destination else '',
                        "carrier_code": carrier.get('code', ''),
                        "carrier_name": carrier.get('name', ''),
                        "flight_number": segment.get('code', ''),
                        "is_hidden": is_hidden,
                        "route": f"{source.get('station', {}).get('code', '')} -> {destination.get('station', {}).get('code', '')}"
                    }
                return None

            outbound_info = parse_leg(itinerary.get('outbound', {}))
            inbound_info = parse_leg(itinerary.get('inbound', {}))

            if outbound_info and inbound_info:
                return {
                    "id": flight_id,
                    "price_main": price_main,
                    "currency": currency,
                    "is_overall_hidden_city": is_overall_hidden_city,
                    "outbound": outbound_info,
                    "inbound": inbound_info,
                    "trip_type": "roundtrip"
                }
            return None

        except Exception as e:
            logger.error(f"解析单个往返航班失败: {e}")
            return None

    async def search_best_practice_with_currency(self, origin: str, destination: str,
                                               departure_date: str, currency: str = "cny",
                                               locale: str = "zh") -> Dict[str, Any]:
        """使用指定货币和语言的最佳实践搜索"""
        search_id = f"bp_{currency}_{int(time.time())}"
        logger.info(f"[{search_id}] 最佳实践搜索: {origin} -> {destination}, 货币: {currency}, 语言: {locale}")

        try:
            # 构建请求变量（使用指定货币和语言）
            variables = self.build_best_practice_variables(origin, destination, departure_date)
            variables["options"]["currency"] = currency
            variables["options"]["locale"] = locale

            payload = {
                "query": BEST_PRACTICE_QUERY,
                "variables": variables
            }

            # 发送请求
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    KIWI_GRAPHQL_ENDPOINT,
                    headers=self.headers,
                    json=payload
                )

                logger.info(f"[{search_id}] 响应状态码: {response.status_code}")

                if response.status_code == 200:
                    response_data = response.json()
                    parsed_flights = self.parse_best_practice_response(response_data, search_id)
                    # 为每个航班添加货币信息
                    for flight in parsed_flights:
                        flight["currency"] = currency
                        flight["price_main"] = flight.get("price_cny", 0) if currency == "cny" else flight.get("price_eur", 0)

                    return {
                        "success": True,
                        "search_id": search_id,
                        "currency": currency,
                        "locale": locale,
                        "request": payload,
                        "response": response_data,
                        "parsed_flights": parsed_flights
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }

        except Exception as e:
            logger.error(f"[{search_id}] 搜索失败: {e}")
            return {"success": False, "error": str(e)}




    def parse_best_practice_response_with_currency(self, response_data: Dict[str, Any],
                                                 search_id: str, currency: str) -> List[Dict[str, Any]]:
        """解析指定货币的响应"""
        try:
            if 'data' not in response_data:
                logger.error(f"[{search_id}] 响应中缺少data字段")
                return []

            oneway_data = response_data['data'].get('onewayItineraries')
            if not oneway_data:
                logger.error(f"[{search_id}] 响应中缺少onewayItineraries字段")
                return []

            # 检查API错误
            if oneway_data.get('__typename') == 'AppError':
                error_msg = oneway_data.get('error', 'Unknown API error')
                logger.error(f"[{search_id}] API返回错误: {error_msg}")
                return []

            # 解析航班数据
            itineraries = oneway_data.get('itineraries', [])
            metadata = oneway_data.get('metadata', {})

            logger.info(f"[{search_id}] 找到 {len(itineraries)} 个航班，总数: {metadata.get('itinerariesCount', 0)}")

            parsed_flights = []
            for flight in itineraries:
                parsed_flight = self.parse_single_flight_with_currency(flight, currency)
                if parsed_flight:
                    parsed_flights.append(parsed_flight)

            return parsed_flights

        except Exception as e:
            logger.error(f"[{search_id}] 解析响应失败: {e}")
            return []

    def parse_single_flight_with_currency(self, flight: Dict[str, Any], currency: str) -> Optional[Dict[str, Any]]:
        """解析单个航班信息（支持不同货币）"""
        try:
            # 基本信息
            flight_id = flight.get('id', '')
            price_main = flight.get('price', {}).get('amount', 0)  # 主要货币价格
            price_eur = flight.get('priceEur', {}).get('amount', 0)  # 欧元价格
            duration = flight.get('duration', 0)

            # 隐藏城市信息
            travel_hack = flight.get('travelHack', {})
            is_hidden_city = travel_hack.get('isTrueHiddenCity', False)
            is_throwaway = travel_hack.get('isThrowawayTicket', False)

            # 航段信息
            sector = flight.get('sector', {})
            segments = sector.get('sectorSegments', [])

            if not segments:
                return None

            # 解析第一个航段（主要航段）
            first_segment = segments[0].get('segment', {})
            source = first_segment.get('source', {})
            destination = first_segment.get('destination', {})
            hidden_destination = first_segment.get('hiddenDestination', {})
            carrier = first_segment.get('carrier', {})

            return {
                "id": flight_id,
                "price_main": price_main,  # 请求货币的价格
                "price_eur": price_eur,    # 欧元价格（用于对比）
                "currency": currency,      # 主要货币类型
                "duration_minutes": duration // 60 if duration else 0,
                "is_hidden_city": is_hidden_city,
                "is_throwaway": is_throwaway,
                "departure_airport": source.get('station', {}).get('code', ''),
                "departure_airport_name": source.get('station', {}).get('name', ''),
                "arrival_airport": destination.get('station', {}).get('code', ''),
                "arrival_airport_name": destination.get('station', {}).get('name', ''),
                "hidden_destination_code": hidden_destination.get('code', '') if hidden_destination else '',
                "hidden_destination_name": hidden_destination.get('name', '') if hidden_destination else '',
                "carrier_code": carrier.get('code', ''),
                "carrier_name": carrier.get('name', ''),
                "flight_number": first_segment.get('code', ''),
                "departure_time": source.get('localTime', ''),
                "arrival_time": destination.get('localTime', ''),
                "segment_count": len(segments)
            }

        except Exception as e:
            logger.error(f"解析单个航班失败: {e}")
            return None

    def save_results_to_file(self, results: Dict[str, Any], filename: str):
        """保存结果到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"结果已保存到: {filename}")
        except Exception as e:
            logger.error(f"保存文件失败: {e}")



    async def search_roundtrip_hidden_city(self, origin: str, destination: str,
                                         departure_date: str, return_date: str) -> Dict[str, Any]:
        """搜索往返隐藏城市航班"""
        search_id = f"roundtrip_hidden_{int(time.time())}"
        logger.info(f"[{search_id}] 搜索往返隐藏城市航班: {origin} ⇄ {destination}")

        try:
            variables = self.build_roundtrip_variables(origin, destination, departure_date, return_date)
            # 启用隐藏城市搜索
            variables["filter"]["enableTrueHiddenCity"] = True
            variables["filter"]["enableSelfTransfer"] = True
            variables["filter"]["enableThrowAwayTicketing"] = True
            variables["filter"]["maxStopsCount"] = 2

            payload = {
                "query": RETURN_QUERY_TEMPLATE,
                "variables": variables
            }

            api_url = f"{KIWI_GRAPHQL_ENDPOINT}?featureName=SearchReturnItinerariesQuery"
            logger.info(f"[{search_id}] 使用往返隐藏城市端点: {api_url}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(api_url, headers=self.headers, json=payload)

                if response.status_code == 200:
                    response_data = response.json()
                    return self.parse_roundtrip_response(response_data, search_id)
                else:
                    return {"error": f"HTTP {response.status_code}", "details": response.text}

        except Exception as e:
            return {"error": str(e)}

    def build_roundtrip_variables(self, origin: str, destination: str,
                                departure_date: str, return_date: str) -> Dict[str, Any]:
        """构建往返搜索变量 - 基于项目中的实现"""
        dep_date_obj = datetime.strptime(departure_date, "%Y-%m-%d")
        ret_date_obj = datetime.strptime(return_date, "%Y-%m-%d")

        return {
            "search": {
                "itinerary": {
                    "source": {"ids": [f"Station:airport:{origin.upper()}"]},
                    "destination": {"ids": [f"Station:airport:{destination.upper()}"]},
                    "outboundDepartureDate": {
                        "start": dep_date_obj.strftime("%Y-%m-%dT00:00:00"),
                        "end": dep_date_obj.strftime("%Y-%m-%dT23:59:59")
                    },
                    "inboundDepartureDate": {
                        "start": ret_date_obj.strftime("%Y-%m-%dT00:00:00"),
                        "end": ret_date_obj.strftime("%Y-%m-%dT23:59:59")
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
                    "applyMixedClasses": False  # 项目中为 False
                }
            },
            "filter": {
                "allowDifferentStationConnection": True,
                "enableSelfTransfer": True,
                "enableThrowAwayTicketing": True,
                "enableTrueHiddenCity": True,
                "transportTypes": ["FLIGHT"],
                "contentProviders": ["KIWI"],  # 项目中只有 KIWI
                "limit": 30,  # 项目中为 30
                # 往返航班特有的过滤器
                "allowReturnFromDifferentCity": True,
                "allowChangeInboundDestination": True,
                "allowChangeInboundSource": True
            },
            "options": {
                "sortBy": "PRICE",  # 项目中为 PRICE
                "currency": "cny",  # 改为人民币
                "locale": "zh",     # 改为中文
                "partner": "skypicker",
                "partnerMarket": "cn",
                "storeSearch": False,
                "serverToken": None
            }
        }

    def parse_roundtrip_response(self, response_data: Dict[str, Any], search_id: str) -> Dict[str, Any]:
        """解析往返航班响应"""
        try:
            if 'data' not in response_data:
                return {"error": "响应中缺少data字段", "raw_response": response_data}

            return_data = response_data['data'].get('returnItineraries')
            if not return_data:
                return {"error": "响应中缺少returnItineraries字段", "raw_response": response_data}

            if return_data.get('__typename') == 'AppError':
                error_msg = return_data.get('error', 'Unknown API error')
                logger.error(f"[{search_id}] API返回错误: {error_msg}")
                return {"error": f"API Error: {error_msg}"}

            if return_data.get('__typename') != 'Itineraries':
                return {"error": f"意外的响应类型: {return_data.get('__typename')}", "raw_response": response_data}

            # 解析往返航班数据
            itineraries = return_data.get('itineraries', [])
            metadata = return_data.get('metadata', {})

            logger.info(f"[{search_id}] 找到 {len(itineraries)} 个往返航班")

            # 简化往返航班信息
            simplified_flights = []
            for i, itinerary in enumerate(itineraries[:5]):  # 只显示前5个
                flight_info = self.extract_roundtrip_flight_info(itinerary, i)
                simplified_flights.append(flight_info)

            return {
                "success": True,
                "search_id": search_id,
                "total_count": metadata.get('itinerariesCount', 0),
                "has_more": metadata.get('hasMorePending', False),
                "flights": simplified_flights,
                "raw_sample": itineraries[0] if itineraries else None
            }

        except Exception as e:
            logger.error(f"[{search_id}] 解析往返响应失败: {e}")
            return {"error": f"解析失败: {str(e)}", "raw_response": response_data}

    def extract_roundtrip_flight_info(self, itinerary: Dict[str, Any], index: int) -> Dict[str, Any]:
        """提取往返航班关键信息"""
        try:
            price = itinerary.get('priceEur', {}).get('amount', 0)
            duration = itinerary.get('duration', 0)
            pnr_count = itinerary.get('pnrCount', 1)

            # 提取出发航段信息
            outbound = itinerary.get('outbound', {})
            outbound_segments = outbound.get('sectorSegments', [])

            # 提取返程航段信息
            inbound = itinerary.get('inbound', {})
            inbound_segments = inbound.get('sectorSegments', [])

            outbound_flight_segments = []
            for seg in outbound_segments:
                segment_data = seg.get('segment', {})
                source = segment_data.get('source', {})
                destination = segment_data.get('destination', {})
                carrier = segment_data.get('carrier', {})

                outbound_flight_segments.append({
                    "from": source.get('station', {}).get('code', ''),
                    "to": destination.get('station', {}).get('code', ''),
                    "departure": source.get('localTime', ''),
                    "arrival": destination.get('localTime', ''),
                    "carrier": carrier.get('code', ''),
                    "flight_number": segment_data.get('code', '')
                })

            inbound_flight_segments = []
            for seg in inbound_segments:
                segment_data = seg.get('segment', {})
                source = segment_data.get('source', {})
                destination = segment_data.get('destination', {})
                carrier = segment_data.get('carrier', {})

                inbound_flight_segments.append({
                    "from": source.get('station', {}).get('code', ''),
                    "to": destination.get('station', {}).get('code', ''),
                    "departure": source.get('localTime', ''),
                    "arrival": destination.get('localTime', ''),
                    "carrier": carrier.get('code', ''),
                    "flight_number": segment_data.get('code', '')
                })

            return {
                "index": index + 1,
                "id": itinerary.get('id', ''),
                "price_eur": price,
                "duration_minutes": duration // 60 if duration else 0,
                "pnr_count": pnr_count,
                "outbound_segments": outbound_flight_segments,
                "inbound_segments": inbound_flight_segments,
                "is_hidden_city": itinerary.get('travelHack', {}).get('isTrueHiddenCity', False),
                "is_throwaway": itinerary.get('travelHack', {}).get('isThrowawayTicket', False),
                "provider": itinerary.get('provider', {}).get('name', '')
            }

        except Exception as e:
            logger.error(f"提取往返航班信息失败: {e}")
            return {"index": index + 1, "error": str(e)}

    async def display_flight_results(self, result: Dict[str, Any], category: str):
        """显示航班搜索结果"""
        if result.get("success"):
            count = result.get('total_count', 0)
            returned = len(result.get('flights', []))
            print(f"✅ 成功! API返回总数: {count}, 解析成功: {returned}")

            if returned > 0:
                flights = result.get('flights', [])

                # 分类统计
                direct_flights = []
                hidden_city_flights = []

                for flight in flights:
                    if 'error' in flight:
                        continue

                    if "往返" in category:
                        # 往返航班：检查出发和返程是否都是直飞
                        outbound_stops = len(flight.get('outbound_segments', [])) - 1
                        inbound_stops = len(flight.get('inbound_segments', [])) - 1
                        is_direct = outbound_stops == 0 and inbound_stops == 0
                    else:
                        # 单程航班：检查航段数
                        is_direct = len(flight.get('segments', [])) == 1

                    is_hidden = flight.get('is_hidden_city', False) or flight.get('is_throwaway', False)

                    if is_hidden:
                        hidden_city_flights.append(flight)
                    elif is_direct:
                        direct_flights.append(flight)

                # 显示直飞航班
                if direct_flights:
                    print(f"\n   🛫 直飞航班 ({len(direct_flights)}个):")
                    for flight in direct_flights[:3]:  # 显示前3个
                        self.print_flight_info(flight, category)

                # 显示隐藏城市航班
                if hidden_city_flights:
                    print(f"\n   🔸 隐藏城市航班 ({len(hidden_city_flights)}个):")
                    for flight in hidden_city_flights[:3]:  # 显示前3个
                        self.print_flight_info(flight, category)

                if not direct_flights and not hidden_city_flights:
                    print("   ⚠️  未找到符合条件的航班")
            else:
                print("⚠️  解析到0个航班")
        else:
            print(f"❌ 失败: {result.get('error')}")

    def print_flight_info(self, flight: Dict[str, Any], category: str):
        """打印单个航班信息"""
        if "往返" in category:
            # 往返航班
            outbound = flight.get('outbound_segments', [])
            inbound = flight.get('inbound_segments', [])
            if outbound and inbound:
                out_route = f"{outbound[0].get('from')} -> {outbound[-1].get('to')}"
                in_route = f"{inbound[0].get('from')} -> {inbound[-1].get('to')}"
                out_stops = len(outbound) - 1
                in_stops = len(inbound) - 1
                price = flight.get('price_eur', 0)
                duration = flight.get('duration_minutes', 0)

                hc_flag = "🔸" if flight.get('is_hidden_city') else ""
                ta_flag = "🎯" if flight.get('is_throwaway') else ""

                print(f"     去程: {out_route} ({out_stops}中转)")
                print(f"     返程: {in_route} ({in_stops}中转)")
                print(f"     价格: ¥{price}, 总时长: {duration}分钟 {hc_flag}{ta_flag}")
        else:
            # 单程航班
            segments = flight.get('segments', [])
            if segments:
                route = f"{segments[0].get('from')} -> {segments[-1].get('to')}"
                price = flight.get('price_eur', 0)
                duration = flight.get('duration_minutes', 0)
                stops = len(segments) - 1

                hc_flag = "🔸" if flight.get('is_hidden_city') else ""
                ta_flag = "🎯" if flight.get('is_throwaway') else ""

                print(f"     {route}: ¥{price}, {duration}分钟, {stops}中转 {hc_flag}{ta_flag}")


async def main():
    """主测试函数"""
    print("🛩️ Kiwi API 测试开始")
    print("=" * 50)
    
    tester = KiwiAPITester()
    
    # 1. 测试Token有效性
    print("\n1. 测试Token有效性...")
    token_valid = await tester.test_token_validation()
    if not token_valid:
        print("❌ Token无效，无法继续测试")
        return
    
    # 2. 测试航班搜索
    print("\n2. 测试航班搜索...")
    test_cases = [
        ("PEK", "LAX", "2025-03-15"),  # 北京到洛杉矶
        ("PVG", "NRT", "2025-03-20"),  # 上海到东京
        ("CAN", "SIN", "2025-03-25"),  # 广州到新加坡
    ]
    
    for origin, destination, date in test_cases:
        print(f"\n📍 测试路线: {origin} -> {destination}, 日期: {date}")
        result = await tester.search_flights(origin, destination, date)
        
        if result.get("success"):
            print(f"✅ 搜索成功!")
            print(f"   总航班数: {result.get('total_count', 0)}")
            print(f"   返回航班数: {len(result.get('flights', []))}")
            
            # 显示前3个航班的简要信息
            for flight in result.get('flights', [])[:3]:
                if 'error' not in flight:
                    print(f"   航班 {flight['index']}: ¥{flight['price_eur']}, "
                          f"{flight['duration_minutes']}分钟, "
                          f"{len(flight['segments'])}段")
        else:
            print(f"❌ 搜索失败: {result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 50)
    print("🎯 测试完成!")


async def test_comprehensive():
    """综合测试函数"""
    print("🚀 Kiwi API 综合测试")
    print("=" * 60)

    tester = KiwiAPITester()

    # 1. Token验证
    print("\n1️⃣ Token验证测试")
    if not await tester.test_token_validation():
        print("❌ Token无效，停止测试")
        return

    # 2. 直飞航班测试
    print("\n2️⃣ 直飞航班测试")
    direct_result = await tester.search_direct_flights_only("PEK", "LAX", "2025-06-30")
    if direct_result.get("success"):
        print(f"✅ 找到 {direct_result.get('total_count', 0)} 个直飞航班")
    else:
        print(f"❌ 直飞搜索失败: {direct_result.get('error')}")

    # 3. 隐藏城市航班测试
    print("\n3️⃣ 隐藏城市航班测试")
    hidden_result = await tester.search_with_hidden_city("PEK", "LAX", "2025-06-30")
    if hidden_result.get("success"):
        print(f"✅ 找到 {hidden_result.get('total_count', 0)} 个隐藏城市航班")
        # 统计隐藏城市航班数量
        hidden_count = sum(1 for f in hidden_result.get('flights', [])
                          if f.get('is_hidden_city') or f.get('is_throwaway'))
        print(f"   其中隐藏城市/甩尾航班: {hidden_count} 个")
    else:
        print(f"❌ 隐藏城市搜索失败: {hidden_result.get('error')}")

    # 4. 甩尾票策略测试
    print("\n4️⃣ 甩尾票策略测试")
    throwaway_destinations = ["LAX", "SFO", "SEA", "LAS"]  # 从北京到美国西海岸城市
    throwaway_results = await tester.test_multiple_destinations(
        "PEK", throwaway_destinations, "2025-06-30"
    )

    print("甩尾票搜索结果:")
    for dest, result in throwaway_results.items():
        if result.get("success"):
            count = result.get('total_count', 0)
            print(f"   PEK -> {dest}: {count} 个航班")
        else:
            print(f"   PEK -> {dest}: 失败 - {result.get('error', 'Unknown')}")

    # 5. 保存详细结果
    print("\n5️⃣ 保存测试结果")
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "direct_flights": direct_result,
        "hidden_city_flights": hidden_result,
        "throwaway_results": throwaway_results
    }
    tester.save_results_to_file(all_results, "kiwi_test_results.json")

    print("\n" + "=" * 60)
    print("🎯 综合测试完成!")


async def test_debug_fixed():
    """调试修正后的实现"""
    print("🔧 Kiwi API 修正版调试测试")
    print("=" * 50)

    tester = KiwiAPITester()

    # 1. Token验证
    print("\n1️⃣ Token验证")
    if not await tester.test_token_validation():
        print("❌ Token验证失败，停止测试")
        return

    # 2. 测试热门路线 - 使用2025年6月30日
    test_routes = [
        ("LHR", "JFK", "2025-06-30"),  # 伦敦到纽约 - 热门国际路线
        ("PEK", "PVG", "2025-06-30"),  # 北京到上海 - 国内路线
        ("PEK", "NRT", "2025-06-30"),  # 北京到东京 - 亚洲路线
        ("PEK", "LAX", "2025-06-30"),  # 北京到洛杉矶 - 原问题路线
    ]

    for i, (origin, destination, date) in enumerate(test_routes):
        print(f"\n{i+2}️⃣ 测试路线: {origin} -> {destination} ({date})")

        # 保存请求和响应用于调试
        variables = tester.build_search_variables(origin, destination, date)

        # 保存请求参数
        with open(f"debug_fixed_request_{origin}_{destination}.json", "w", encoding="utf-8") as f:
            json.dump({
                "query": ONEWAY_QUERY_TEMPLATE,
                "variables": variables
            }, f, indent=2, ensure_ascii=False)

        result = await tester.search_flights(origin, destination, date)

        # 保存结果
        with open(f"debug_fixed_result_{origin}_{destination}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

        if result.get("success"):
            count = result.get("total_count", 0)
            returned = len(result.get("flights", []))
            print(f"✅ 成功! API返回总数: {count}, 解析成功: {returned}")

            if returned > 0:
                print("   前3个航班:")
                for flight in result.get('flights', [])[:3]:
                    if 'error' not in flight:
                        segments = flight.get('segments', [])
                        if segments:
                            route = f"{segments[0].get('from')} -> {segments[-1].get('to')}"
                            price = flight.get('price_eur', 0)
                            duration = flight.get('duration_minutes', 0)
                            stops = len(segments) - 1
                            hc_flag = "🔸" if flight.get('is_hidden_city') else ""
                            ta_flag = "🎯" if flight.get('is_throwaway') else ""
                            print(f"     {route}: ¥{price}, {duration}分钟, {stops}中转 {hc_flag}{ta_flag}")




async def test_best_practice():
    """最佳实践测试：同时测试人民币和美元两种货币"""
    print("🚀 Kiwi API 最佳实践测试 - 双货币对比 - 2025年6月30日")
    print("=" * 70)

    tester = KiwiAPITester()

    # Token验证
    print("验证Token...")
    if not await tester.test_token_validation():
        return

    origin, destination, date = "LHR", "PEK", "2025-06-30"

    print(f"\n🎯 测试路线: {origin} -> {destination} ({date})")
    print(f"💰 货币对比: 人民币(CNY) vs 美元(USD)")

    # 测试配置
    currency_configs = [
        {"currency": "cny", "symbol": "¥", "name": "人民币", "locale": "zh"},
        {"currency": "usd", "symbol": "$", "name": "美元", "locale": "en"}
    ]

    all_results = {}

    for i, config in enumerate(currency_configs, 1):
        currency = config["currency"]
        symbol = config["symbol"]
        name = config["name"]
        locale = config["locale"]

        print(f"\n{i}️⃣ 最佳实践搜索 - {name} ({currency.upper()})")
        print("-" * 50)

        # 执行指定货币的搜索
        result = await tester.search_best_practice_with_currency(
            origin, destination, date, currency, locale
        )

        if result.get("success"):
            flights = result.get("parsed_flights", [])

            print(f"✈️ 查找到 {len(flights)} 个行程选项")
            print("=" * 40)

            # 统计信息
            direct_count = 0
            hidden_count = 0

            for j, flight in enumerate(flights, 1):
                price_main = flight.get('price_main', 0)
                price_eur = flight.get('price_eur', 0)
                is_hidden_city = flight.get('is_hidden_city', False)
                is_throwaway = flight.get('is_throwaway', False)

                departure_airport = flight.get('departure_airport', '')
                arrival_airport = flight.get('arrival_airport', '')
                hidden_dest = flight.get('hidden_destination_code', '')

                print(f"【行程 {j}】")
                print(f"  💰 价格: {symbol}{price_main} (€{price_eur})")
                print(f"  ⏱️ 时长: {flight.get('duration_minutes', 0)}分钟")
                print(f"  ✈️ 航班: {flight.get('carrier_code', '')} {flight.get('flight_number', '')}")

                # 核心逻辑：根据 isTrueHiddenCity 判断并展示不同信息
                if is_hidden_city or is_throwaway:
                    hidden_count += 1
                    print(f"  ⚠️ 类型: 隐藏城市航班 (Hidden City)")
                    print(f"     - 表面行程: {departure_airport} -> {arrival_airport}")
                    if hidden_dest:
                        print(f"     - 实际机票终点: {hidden_dest}")
                    print(f"     - 风险提示: 必须在 {arrival_airport} 放弃后续航段，通常不能托运行李。")
                    if is_throwaway:
                        print(f"     - 甩尾票: 是")
                else:
                    direct_count += 1
                    print(f"  ✅ 类型: 标准直飞 (Standard Direct)")
                    print(f"     - 行程: {departure_airport} -> {arrival_airport}")

                print(f"  🕐 时间: {flight.get('departure_time', '')} -> {flight.get('arrival_time', '')}")
                print("-" * 25)

            # 统计信息
            print(f"\n📊 {name}测试统计:")
            print(f"   总航班数: {len(flights)}")
            print(f"   标准直飞: {direct_count}")
            print(f"   隐藏城市: {hidden_count}")

            # 保存结果
            all_results[currency] = {
                "config": config,
                "result": result,
                "statistics": {
                    "total_flights": len(flights),
                    "direct_flights": direct_count,
                    "hidden_city_flights": hidden_count
                }
            }

        else:
            print(f"❌ {name}搜索失败: {result.get('error')}")
            all_results[currency] = {"error": result.get('error')}

        # 添加延迟避免请求过快
        if i < len(currency_configs):
            print(f"\n⏳ 等待3秒后进行下一个货币测试...")
            await asyncio.sleep(3)

    # 保存完整对比数据
    print(f"\n💾 保存对比数据")
    print("-" * 30)

    comparison_data = {
        "test_info": {
            "route": f"{origin} -> {destination}",
            "date": date,
            "timestamp": datetime.now().isoformat(),
            "description": "最佳实践双货币对比测试：直飞+隐藏城市搜索",
            "method": "maxStopsCount=0 + enableTrueHiddenCity=true",
            "currencies_tested": [config["currency"] for config in currency_configs]
        },
        "results": all_results
    }

    filename = f"kiwi_dual_currency_test_{origin}_{destination}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(comparison_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"✅ 双货币对比数据已保存到: {filename}")
    print(f"📊 文件包含:")
    print(f"   - 人民币 (CNY) 测试结果")
    print(f"   - 美元 (USD) 测试结果")
    print(f"   - 完整的请求和响应数据")
    print(f"   - 统计对比信息")

    print(f"\n🎯 双货币最佳实践测试完成!")


async def test_comprehensive_dual_currency():
    """综合双货币测试：单程 + 往返"""
    print("🚀 Kiwi API 综合双货币测试 - 单程 + 往返")
    print("=" * 60)

    tester = KiwiAPITester()

    # Token验证
    print("验证Token...")
    if not await tester.test_token_validation():
        return

    origin, destination = "LHR", "PEK"
    dep_date, ret_date = "2025-06-30", "2025-07-07"

    print(f"\n🎯 测试路线: {origin} ⇄ {destination}")
    print(f"📅 出发日期: {dep_date}")
    print(f"📅 返回日期: {ret_date}")
    print(f"💱 货币对比: 人民币(CNY) vs 美元(USD)")
    print(f"✈️ 测试类型: 单程直飞 + 往返直飞")

    # 测试配置
    currency_configs = [
        {"currency": "cny", "symbol": "¥", "name": "人民币", "locale": "zh"},
        {"currency": "usd", "symbol": "$", "name": "美元", "locale": "en"}
    ]

    all_results = {}

    for i, config in enumerate(currency_configs, 1):
        currency = config["currency"]
        symbol = config["symbol"]
        name = config["name"]
        locale = config["locale"]

        print(f"\n{'='*60}")
        print(f"{i}️⃣ {name} ({currency.upper()}) 测试")
        print(f"{'='*60}")

        # A. 单程测试
        print(f"\n🛫 单程直飞测试 - {name}")
        print("-" * 40)

        oneway_result = await tester.search_best_practice_with_currency(
            origin, destination, dep_date, currency, locale
        )

        if oneway_result.get("success"):
            oneway_flights = oneway_result.get("parsed_flights", [])
            print(f"✈️ 查找到 {len(oneway_flights)} 个单程选项")

            # 显示前3个单程航班
            for j, flight in enumerate(oneway_flights[:3], 1):
                price_main = flight.get('price_main', 0)
                price_eur = flight.get('price_eur', 0)
                is_hidden = flight.get('is_hidden_city', False) or flight.get('is_throwaway', False)

                departure_airport = flight.get('departure_airport', '')
                arrival_airport = flight.get('arrival_airport', '')

                print(f"  【单程 {j}】")
                print(f"    💰 价格: {symbol}{price_main} (€{price_eur})")
                print(f"    ✈️ 航班: {flight.get('carrier_code', '')} {flight.get('flight_number', '')}")
                print(f"    🛣️ 类型: {'⚠️隐藏城市' if is_hidden else '✅标准直飞'}")
                print(f"    📍 路线: {departure_airport} -> {arrival_airport}")
        else:
            print(f"❌ 单程搜索失败: {oneway_result.get('error')}")
            oneway_flights = []

        # B. 往返测试
        print(f"\n🔄 往返直飞测试 - {name}")
        print("-" * 40)

        roundtrip_result = await tester.search_roundtrip_direct(
            origin, destination, dep_date, ret_date, currency, locale
        )

        if roundtrip_result.get("success"):
            roundtrip_flights = roundtrip_result.get("parsed_flights", [])
            print(f"✈️ 查找到 {len(roundtrip_flights)} 个往返选项")

            # 显示前3个往返航班
            for j, flight in enumerate(roundtrip_flights[:3], 1):
                price_main = flight.get('price_main', 0)
                outbound = flight.get('outbound', {})
                inbound = flight.get('inbound', {})

                print(f"  【往返 {j}】")
                print(f"    💰 价格: {symbol}{price_main}")
                print(f"    🛫 去程: {outbound.get('route', '')} {'⚠️隐藏城市' if outbound.get('is_hidden') else '✅直飞'}")
                print(f"    🛬 返程: {inbound.get('route', '')} {'⚠️隐藏城市' if inbound.get('is_hidden') else '✅直飞'}")
        else:
            print(f"❌ 往返搜索失败: {roundtrip_result.get('error')}")
            roundtrip_flights = []

        # 统计信息
        oneway_direct = sum(1 for f in oneway_flights if not f.get('is_hidden_city') and not f.get('is_throwaway'))
        oneway_hidden = sum(1 for f in oneway_flights if f.get('is_hidden_city') or f.get('is_throwaway'))

        roundtrip_direct = sum(1 for f in roundtrip_flights
                             if not f.get('outbound', {}).get('is_hidden') and not f.get('inbound', {}).get('is_hidden'))
        roundtrip_hidden = sum(1 for f in roundtrip_flights
                             if f.get('outbound', {}).get('is_hidden') or f.get('inbound', {}).get('is_hidden'))

        print(f"\n📊 {name}测试统计:")
        print(f"   单程航班: {len(oneway_flights)} (直飞: {oneway_direct}, 隐藏城市: {oneway_hidden})")
        print(f"   往返航班: {len(roundtrip_flights)} (直飞: {roundtrip_direct}, 隐藏城市: {roundtrip_hidden})")

        # 保存结果
        all_results[currency] = {
            "config": config,
            "oneway": {
                "result": oneway_result,
                "statistics": {
                    "total_flights": len(oneway_flights),
                    "direct_flights": oneway_direct,
                    "hidden_city_flights": oneway_hidden
                }
            },
            "roundtrip": {
                "result": roundtrip_result,
                "statistics": {
                    "total_flights": len(roundtrip_flights),
                    "direct_flights": roundtrip_direct,
                    "hidden_city_flights": roundtrip_hidden
                }
            }
        }

        # 添加延迟避免请求过快
        if i < len(currency_configs):
            print(f"\n⏳ 等待3秒后进行下一个货币测试...")
            await asyncio.sleep(3)

    # 保存完整对比数据
    print(f"\n💾 保存综合对比数据")
    print("-" * 30)

    comprehensive_data = {
        "test_info": {
            "route": f"{origin} ⇄ {destination}",
            "departure_date": dep_date,
            "return_date": ret_date,
            "timestamp": datetime.now().isoformat(),
            "description": "综合双货币对比测试：单程+往返直飞+隐藏城市搜索",
            "method": "maxStopsCount=0 + enableTrueHiddenCity=true",
            "currencies_tested": [config["currency"] for config in currency_configs],
            "test_types": ["oneway", "roundtrip"]
        },
        "results": all_results
    }

    filename = f"kiwi_comprehensive_dual_currency_{origin}_{destination}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(comprehensive_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"✅ 综合双货币对比数据已保存到: {filename}")
    print(f"📊 文件包含:")
    print(f"   - 人民币 (CNY) 单程+往返测试结果")
    print(f"   - 美元 (USD) 单程+往返测试结果")
    print(f"   - 完整的请求和响应数据")
    print(f"   - 详细的统计对比信息")

    print(f"\n🎯 综合双货币测试完成!")


async def display_detailed_results(result: Dict[str, Any], category: str):
    """显示详细的搜索结果"""
    if result.get("success"):
        count = result.get('total_count', 0)
        returned = len(result.get('flights', []))
        print(f"✅ 成功! API返回总数: {count}, 解析成功: {returned}")

        if returned > 0:
            flights = result.get('flights', [])

            print(f"\n   📋 详细航班信息:")
            for i, flight in enumerate(flights[:5]):  # 显示前5个
                if 'error' in flight:
                    print(f"     航班 {i+1}: ❌ 解析错误 - {flight.get('error')}")
                    continue

                segments = flight.get('segments', [])
                if not segments:
                    print(f"     航班 {i+1}: ⚠️  无航段信息")
                    continue

                # 基本信息
                route = f"{segments[0].get('from')} -> {segments[-1].get('to')}"
                price = flight.get('price_eur', 0)
                duration = flight.get('duration_minutes', 0)
                stops = len(segments) - 1

                # 特殊标识
                is_hidden = flight.get('is_hidden_city', False)
                is_throwaway = flight.get('is_throwaway', False)
                is_virtual = flight.get('is_virtual_interlining', False)

                flags = []
                if is_hidden:
                    flags.append("🔸隐藏城市")
                if is_throwaway:
                    flags.append("🎯甩尾票")
                if is_virtual:
                    flags.append("🔗虚拟联程")

                flag_str = " ".join(flags) if flags else "🛫普通航班"

                print(f"     航班 {i+1}: {route}")
                print(f"           价格: ¥{price}, 时长: {duration}分钟, 中转: {stops}次")
                print(f"           类型: {flag_str}")
                print(f"           原始标识: hidden={is_hidden}, throwaway={is_throwaway}, virtual={is_virtual}")

                # 显示航段详情
                if len(segments) > 1:
                    print(f"           航段: ", end="")
                    for j, seg in enumerate(segments):
                        if j > 0:
                            print(" -> ", end="")
                        print(f"{seg.get('from')}-{seg.get('to')}", end="")
                    print()

                print()  # 空行分隔

            # 统计信息
            direct_count = sum(1 for f in flights if len(f.get('segments', [])) == 1)
            hidden_count = sum(1 for f in flights if f.get('is_hidden_city', False))
            throwaway_count = sum(1 for f in flights if f.get('is_throwaway', False))
            virtual_count = sum(1 for f in flights if f.get('is_virtual_interlining', False))

            print(f"   📊 {category}搜索统计:")
            print(f"     总解析: {returned}")
            print(f"     直飞: {direct_count}")
            print(f"     隐藏城市: {hidden_count}")
            print(f"     甩尾票: {throwaway_count}")
            print(f"     虚拟联程: {virtual_count}")

        else:
            print("⚠️  解析到0个航班")
    else:
        print(f"❌ 失败: {result.get('error')}")


async def test_direct_and_hidden_city():
    """专门测试直飞和隐藏城市航班 - 单程和往返"""
    print("✈️ 直飞 & 隐藏城市航班测试 - 2025年6月30日")
    print("=" * 55)

    tester = KiwiAPITester()

    # Token验证
    print("验证Token...")
    if not await tester.test_token_validation():
        return

    # 测试路线
    test_route = ("PEK", "LAX", "2025-06-30", "2025-07-07")  # 北京到洛杉矶，7月7日返回
    origin, destination, dep_date, ret_date = test_route

    print(f"\n🎯 测试路线: {origin} -> {destination}")
    print(f"   出发日期: {dep_date}")
    print(f"   返回日期: {ret_date}")

    # 1. 单程直飞航班测试
    print(f"\n1️⃣ 单程直飞航班 ({origin} -> {destination})")
    print("-" * 40)

    direct_oneway_result = await tester.search_direct_flights_only(origin, destination, dep_date)
    await tester.display_flight_results(direct_oneway_result, "单程直飞")

    # 2. 单程隐藏城市航班测试
    print(f"\n2️⃣ 单程隐藏城市航班 ({origin} -> {destination})")
    print("-" * 40)

    hidden_oneway_result = await tester.search_with_hidden_city(origin, destination, dep_date)
    await tester.display_flight_results(hidden_oneway_result, "单程隐藏城市")

    # 3. 往返直飞航班测试
    print(f"\n3️⃣ 往返直飞航班 ({origin} ⇄ {destination})")
    print("-" * 40)

    direct_roundtrip_result = await tester.search_roundtrip_direct(origin, destination, dep_date, ret_date)
    await tester.display_flight_results(direct_roundtrip_result, "往返直飞")

    # 4. 往返隐藏城市航班测试
    print(f"\n4️⃣ 往返隐藏城市航班 ({origin} ⇄ {destination})")
    print("-" * 40)

    hidden_roundtrip_result = await tester.search_roundtrip_hidden_city(origin, destination, dep_date, ret_date)
    await tester.display_flight_results(hidden_roundtrip_result, "往返隐藏城市")

    # 5. 汇总统计
    print(f"\n📊 搜索结果汇总")
    print("=" * 30)

    results = {
        "单程直飞": direct_oneway_result,
        "单程隐藏城市": hidden_oneway_result,
        "往返直飞": direct_roundtrip_result,
        "往返隐藏城市": hidden_roundtrip_result
    }

    for category, result in results.items():
        if result.get("success"):
            total = result.get('total_count', 0)
            parsed = len(result.get('flights', []))
            direct_count = sum(1 for f in result.get('flights', [])
                             if not f.get('is_hidden_city') and not f.get('is_throwaway') and len(f.get('segments', [])) == 1)
            hidden_count = sum(1 for f in result.get('flights', [])
                             if f.get('is_hidden_city') or f.get('is_throwaway'))
            print(f"   {category:12}: 总数 {total:3}, 解析 {parsed:2}, 直飞 {direct_count:2}, 隐藏城市 {hidden_count:2}")
        else:
            print(f"   {category:12}: ❌ 失败")

    print(f"\n🎯 直飞 & 隐藏城市航班测试完成!")


async def test_june_30():
    """测试2025年6月30日的航班"""
    print("📅 Kiwi API 测试 - 2025年6月30日")
    print("=" * 45)

    tester = KiwiAPITester()

    # Token验证
    print("验证Token...")
    if not await tester.test_token_validation():
        return

    # 测试你关心的路线
    test_routes = [
        ("PEK", "LAX", "2025-06-30"),  # 北京到洛杉矶
        ("PEK", "SFO", "2025-06-30"),  # 北京到旧金山
        ("PEK", "SEA", "2025-06-30"),  # 北京到西雅图
        ("PEK", "LAS", "2025-06-30"),  # 北京到拉斯维加斯
    ]

    for i, (origin, destination, date) in enumerate(test_routes):
        print(f"\n{i+1}️⃣ 搜索航班: {origin} -> {destination} ({date})")
        result = await tester.search_flights(origin, destination, date)

        if result.get("success"):
            count = result.get('total_count', 0)
            returned = len(result.get('flights', []))
            print(f"✅ 成功! API返回总数: {count}, 解析成功: {returned}")

            if returned > 0:
                print("   航班示例:")
                for flight in result.get('flights', [])[:2]:  # 显示前2个
                    if 'error' not in flight:
                        segments = flight.get('segments', [])
                        if segments:
                            route = f"{segments[0].get('from')} -> {segments[-1].get('to')}"
                            price = flight.get('price_eur', 0)
                            duration = flight.get('duration_minutes', 0)
                            stops = len(segments) - 1
                            hc_flag = "🔸" if flight.get('is_hidden_city') else ""
                            ta_flag = "🎯" if flight.get('is_throwaway') else ""
                            print(f"     {route}: ¥{price}, {duration}分钟, {stops}中转 {hc_flag}{ta_flag}")
            else:
                print("⚠️  解析到0个航班")
        else:
            print(f"❌ 失败: {result.get('error')}")

        # 添加延迟避免请求过快
        await asyncio.sleep(1)

    print(f"\n🎯 2025年6月30日航班测试完成!")


async def test_simple():
    """简单测试函数"""
    print("✈️ Kiwi API 简单测试")
    print("=" * 40)

    tester = KiwiAPITester()

    # Token验证
    print("验证Token...")
    if not await tester.test_token_validation():
        return

    # 简单搜索
    print("搜索航班: PEK -> NRT (2025-06-30)")
    result = await tester.search_flights("PEK", "NRT", "2025-06-30")

    if result.get("success"):
        print(f"✅ 成功! 找到 {result.get('total_count')} 个航班")
        for flight in result.get('flights', [])[:3]:
            if 'error' not in flight:
                segments = flight.get('segments', [])
                if segments:
                    first_seg = segments[0]
                    last_seg = segments[-1]
                    print(f"   {first_seg.get('from')} -> {last_seg.get('to')}: "
                          f"¥{flight.get('price_eur')}")
    else:
        print(f"❌ 失败: {result.get('error')}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "simple":
            asyncio.run(test_simple())
        elif sys.argv[1] == "debug":
            asyncio.run(test_debug_fixed())
        elif sys.argv[1] == "june30":
            asyncio.run(test_june_30())
        elif sys.argv[1] == "direct":
            asyncio.run(test_direct_and_hidden_city())
        elif sys.argv[1] == "lhr":
            asyncio.run(test_comprehensive_dual_currency())
        elif sys.argv[1] == "comprehensive":
            asyncio.run(test_comprehensive())
        else:
            print("用法: python kiwi_api_test.py [simple|debug|june30|direct|lhr|comprehensive]")
            print("  simple       - 简单测试")
            print("  debug        - 调试修正版测试")
            print("  june30       - 测试2025年6月30日航班")
            print("  direct       - 直飞&隐藏城市航班测试(单程+往返)")
            print("  lhr          - 综合双货币测试(单程+往返+双货币)")
            print("  comprehensive - 完整测试")
    else:
        # 默认运行综合双货币测试
        asyncio.run(test_comprehensive_dual_currency())


async def comprehensive_dual_currency_test():
    """综合双货币测试：单程 + 往返 (最终优化版)"""
    print("🚀 Kiwi API 综合双货币测试 (最终优化版)")
    print("=" * 60)

    tester = KiwiAPITester()

    # 1. Token验证
    if not await tester.test_token_validation():
        return

    # 2. 测试参数
    origin, destination = "LHR", "PEK"
    dep_date, ret_date = "2025-06-30", "2025-07-07"
    currency_configs = [
        {"code": "cny", "symbol": "¥", "locale": "zh"},
        {"code": "usd", "symbol": "$", "locale": "en"}
    ]

    for config in currency_configs:
        currency, symbol, locale = config["code"], config["symbol"], config["locale"]
        print(f"\n{'='*25} 测试货币: {currency.upper()} {'='*25}")

        # --- 单程测试 ---
        print("\n🛫 单程直飞测试...")
        oneway_result = await tester.search_oneway_direct(origin, destination, dep_date, currency, locale)
        if oneway_result.get("success") and oneway_result.get("parsed_flights"):
            flights = oneway_result["parsed_flights"]
            print(f"  共找到 {len(flights)} 个单程选项:")
            for flight in flights[:3]:
                price = flight.get('price_main', 'N/A')
                route = f"{flight.get('departure_airport', '')} -> {flight.get('arrival_airport', '')}"
                route_type = "⚠️隐藏城市" if flight.get('is_hidden_city') else "✅标准直飞"
                print(f"    - {route} | {symbol}{price} | {route_type}")
        else:
            print("  未找到单程航班。")

        await asyncio.sleep(2) # 礼貌性延迟

        # --- 往返测试 ---
        print("\n🔄 往返直飞测试...")
        roundtrip_result = await tester.search_roundtrip_direct(origin, destination, dep_date, ret_date, currency, locale)
        if roundtrip_result.get("success") and roundtrip_result.get("parsed_flights"):
            flights = roundtrip_result["parsed_flights"]
            print(f"  共找到 {len(flights)} 个往返选项:")
            for flight in flights[:3]:
                price = flight.get('price_main', 'N/A')
                out_route = flight.get('outbound', {}).get('route', '')
                in_route = flight.get('inbound', {}).get('route', '')
                out_type = "⚠️隐藏" if flight.get('outbound', {}).get('is_hidden') else "✅直飞"
                in_type = "⚠️隐藏" if flight.get('inbound', {}).get('is_hidden') else "✅直飞"
                print(f"    - 价格: {symbol}{price}")
                print(f"      去: {out_route} ({out_type}) | 返: {in_route} ({in_type})")
        else:
            print("  未找到往返航班。")

    print(f"\n{'='*60}")
    print("🎯 测试完成!")
