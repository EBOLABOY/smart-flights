"""Kiwi Flights API Integration

Provides access to Kiwi.com's flight search API with focus on hidden city flights.
Supports both one-way and round-trip searches with multi-language and multi-currency support.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import httpx

from fli.models.google_flights.base import LocalizationConfig, Language, Currency

# Configure logging
logger = logging.getLogger(__name__)

# Kiwi API Configuration
KIWI_GRAPHQL_ENDPOINT = "https://api.skypicker.com/umbrella/v2/graphql"

# Headers for Kiwi API (from kiwi_api_test.py)
KIWI_HEADERS = {
    'content-type': 'application/json',
    'kw-skypicker-visitor-uniqid': 'b500f05c-8234-4a94-82a7-fb5dc02340a9',
    'kw-umbrella-token': '0d23674b463dadee841cc65da51e34fe47bbbe895ae13b69d42ece267c7a2f51',
    'kw-x-rand-id': '07d338ea',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0',
    'origin': 'https://www.kiwi.com',
    'referer': 'https://www.kiwi.com/cn/search/tiles/--/--/anytime/anytime'
}

# GraphQL Query for One-way Hidden City Flights (使用与 kiwi_api_test.py 相同的完整查询)
ONEWAY_HIDDEN_CITY_QUERY = """
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

# GraphQL Query for Round-trip Hidden City Flights
ROUNDTRIP_HIDDEN_CITY_QUERY = """
query SearchReturnHiddenCityQuery(
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
      metadata {
        itinerariesCount
        hasMorePending
      }
      itineraries {
        __typename
        ... on ItineraryReturn {
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
          outbound {
            duration
            sectorSegments {
              segment {
                source {
                  localTime
                  station {
                    name
                    code
                  }
                }
                destination {
                  localTime
                  station {
                    name
                    code
                  }
                }
                hiddenDestination {
                  code
                  name
                }
                duration
                carrier {
                  name
                  code
                }
                code
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
                  }
                }
                destination {
                  localTime
                  station {
                    name
                    code
                  }
                }
                hiddenDestination {
                  code
                  name
                }
                duration
                carrier {
                  name
                  code
                }
                code
              }
            }
          }
        }
      }
    }
  }
}
"""


class KiwiFlightsAPI:
    """Kiwi Flights API client for hidden city flight searches."""
    
    def __init__(self, localization_config: LocalizationConfig = None):
        """Initialize the Kiwi API client.
        
        Args:
            localization_config: Configuration for language and currency settings
        """
        self.localization_config = localization_config or LocalizationConfig()
        self.headers = KIWI_HEADERS.copy()
        self.timeout = 30.0
    
    def _build_search_variables(self, origin: str, destination: str,
                               departure_date: str, adults: int = 1, cabin_class: str = "ECONOMY") -> Dict[str, Any]:
        """Build search variables for Kiwi API request - 基于真实浏览器请求负载.

        Args:
            origin: Origin airport code (e.g., 'PEK')
            destination: Destination airport code (e.g., 'LAX')
            departure_date: Departure date in YYYY-MM-DD format
            adults: Number of adult passengers

        Returns:
            Dictionary containing search variables
        """
        dep_date_obj = datetime.strptime(departure_date, "%Y-%m-%d")

        # Map localization config to Kiwi API parameters
        currency_code = "cny" if self.localization_config.currency == Currency.CNY else "usd"
        locale_code = "cn" if self.localization_config.language == Language.CHINESE else "en"  # 使用 'cn' 而不是 'zh'
        partner_market = "cn" if self.localization_config.language == Language.CHINESE else "us"

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
                    "adultsHoldBags": [0],
                    "adultsHandBags": [0],  # 修正为 [0] 而不是 [1]
                    "childrenHoldBags": [],
                    "childrenHandBags": []
                },
                "cabinClass": {
                    "cabinClass": cabin_class,
                    "applyMixedClasses": False
                }
            },
            "filter": {
                "allowChangeInboundDestination": True,
                "allowChangeInboundSource": True,
                "allowDifferentStationConnection": True,
                "enableSelfTransfer": True,
                "enableThrowAwayTicketing": True,
                "enableTrueHiddenCity": True,  # 关键：启用隐藏城市
                "maxStopsCount": 1,  # 搜索直飞和1次中转航班
                "transportTypes": ["FLIGHT"],
                "contentProviders": ["KIWI"],  # 关键：内容提供商
                "flightsApiLimit": 25,  # 关键：API限制
                "limit": 10  # 关键：结果限制
            },
            "options": {
                "sortBy": "QUALITY",  # 修正为 QUALITY 而不是 PRICE
                "mergePriceDiffRule": "INCREASED",
                "currency": currency_code,
                "apiUrl": None,
                "locale": locale_code,
                "market": "us",
                "partner": "skypicker",
                "partnerMarket": partner_market,
                "affilID": "cj_5250933",  # 关键：联盟ID
                "storeSearch": False,
                "searchStrategy": "REDUCED",
                "abTestInput": {},  # 简化A/B测试参数，避免无效字段
                "serverToken": None,
                "searchSessionId": None
            }
        }

    def _build_roundtrip_variables(self, origin: str, destination: str,
                                  departure_date: str, return_date: str,
                                  adults: int = 1, cabin_class: str = "ECONOMY") -> Dict[str, Any]:
        """Build search variables for round-trip Kiwi API request - 基于成功的单程请求负载模式.

        Args:
            origin: Origin airport code
            destination: Destination airport code
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date in YYYY-MM-DD format
            adults: Number of adult passengers

        Returns:
            Dictionary containing search variables
        """
        # 复用单程的构建逻辑作为基础
        variables = self._build_search_variables(origin, destination, departure_date, adults, cabin_class)

        # 添加返程日期
        ret_date_obj = datetime.strptime(return_date, "%Y-%m-%d")
        variables["search"]["itinerary"]["inboundDepartureDate"] = {
            "start": ret_date_obj.strftime("%Y-%m-%dT00:00:00"),
            "end": ret_date_obj.strftime("%Y-%m-%dT23:59:59")
        }

        # 添加往返特有的过滤器参数
        variables["filter"]["allowReturnFromDifferentCity"] = True
        variables["filter"]["allowChangeInboundDestination"] = True
        variables["filter"]["allowChangeInboundSource"] = True

        return variables

    async def search_oneway_hidden_city(self, origin: str, destination: str,
                                       departure_date: str, adults: int = 1,
                                       limit: int = 10, cabin_class: str = "ECONOMY") -> Dict[str, Any]:
        """Search for one-way hidden city flights.

        Args:
            origin: Origin airport code (e.g., 'PEK')
            destination: Destination airport code (e.g., 'LAX')
            departure_date: Departure date in YYYY-MM-DD format
            adults: Number of adult passengers
            limit: Maximum number of results to return

        Returns:
            Dictionary containing search results and metadata
        """
        search_id = f"oneway_hidden_{int(time.time())}"
        logger.info(f"[{search_id}] Searching one-way hidden city flights: {origin} -> {destination}")

        try:
            # Build search variables
            variables = self._build_search_variables(origin, destination, departure_date, adults, cabin_class)

            # 使用最佳实践查询以获得更好的隐藏城市航班结果
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

            # Send request
            api_url = f"{KIWI_GRAPHQL_ENDPOINT}?featureName=SearchOneWayItinerariesQuery"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(api_url, headers=self.headers, json=payload)

                logger.info(f"[{search_id}] Response status: {response.status_code}")

                if response.status_code == 200:
                    response_data = response.json()
                    return self._parse_oneway_response(response_data, search_id, limit)
                else:
                    logger.error(f"[{search_id}] Request failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }

        except Exception as e:
            logger.error(f"[{search_id}] Search failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def search_roundtrip_hidden_city(self, origin: str, destination: str,
                                          departure_date: str, return_date: str,
                                          adults: int = 1, limit: int = 10, cabin_class: str = "ECONOMY") -> Dict[str, Any]:
        """Search for round-trip hidden city flights.

        Args:
            origin: Origin airport code
            destination: Destination airport code
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date in YYYY-MM-DD format
            adults: Number of adult passengers
            limit: Maximum number of results to return

        Returns:
            Dictionary containing search results and metadata
        """
        search_id = f"roundtrip_hidden_{int(time.time())}"
        logger.info(f"[{search_id}] Searching round-trip hidden city flights: {origin} ⇄ {destination}")

        try:
            # Build search variables
            variables = self._build_roundtrip_variables(origin, destination, departure_date, return_date, adults, cabin_class)

            payload = {
                "query": ROUNDTRIP_HIDDEN_CITY_QUERY,
                "variables": variables
            }

            # Send request
            api_url = f"{KIWI_GRAPHQL_ENDPOINT}?featureName=SearchReturnItinerariesQuery"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(api_url, headers=self.headers, json=payload)

                logger.info(f"[{search_id}] Response status: {response.status_code}")

                if response.status_code == 200:
                    response_data = response.json()
                    return self._parse_roundtrip_response(response_data, search_id, limit)
                else:
                    logger.error(f"[{search_id}] Request failed: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}",
                        "details": response.text
                    }

        except Exception as e:
            logger.error(f"[{search_id}] Search failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _parse_oneway_response(self, response_data: Dict[str, Any],
                              search_id: str, limit: int) -> Dict[str, Any]:
        """Parse one-way flight search response.

        Args:
            response_data: Raw response from Kiwi API
            search_id: Search identifier for logging
            limit: Maximum number of results to return

        Returns:
            Parsed response with flight information
        """
        try:
            if 'data' not in response_data:
                return {
                    "success": False,
                    "error": "Missing data field in response",
                    "raw_response": response_data
                }

            oneway_data = response_data['data'].get('onewayItineraries')
            if not oneway_data:
                return {
                    "success": False,
                    "error": "Missing onewayItineraries field in response",
                    "raw_response": response_data
                }

            # Check for API errors
            if oneway_data.get('__typename') == 'AppError':
                error_msg = oneway_data.get('error', 'Unknown API error')
                logger.error(f"[{search_id}] API returned error: {error_msg}")
                return {
                    "success": False,
                    "error": f"API Error: {error_msg}"
                }

            if oneway_data.get('__typename') != 'Itineraries':
                return {
                    "success": False,
                    "error": f"Unexpected response type: {oneway_data.get('__typename')}",
                    "raw_response": response_data
                }

            # Parse flight data
            itineraries = oneway_data.get('itineraries', [])
            metadata = oneway_data.get('metadata', {})

            logger.info(f"[{search_id}] Found {len(itineraries)} flights")

            # Parse all flights and count hidden city ones
            all_flights = []
            hidden_city_count = 0
            for itinerary in itineraries[:limit]:
                flight_info = self._extract_oneway_flight_info(itinerary)
                if flight_info:
                    all_flights.append(flight_info)
                    if flight_info.get('is_hidden_city'):
                        hidden_city_count += 1

            return {
                "success": True,
                "search_id": search_id,
                "trip_type": "oneway",
                "total_count": metadata.get('itinerariesCount', 0),
                "hidden_city_count": hidden_city_count,
                "has_more": metadata.get('hasMorePending', False),
                "flights": all_flights,
                "currency": self.localization_config.currency.value,
                "language": self.localization_config.language.value
            }

        except Exception as e:
            logger.error(f"[{search_id}] Failed to parse response: {e}")
            return {
                "success": False,
                "error": f"Parse failed: {str(e)}",
                "raw_response": response_data
            }

    def _parse_roundtrip_response(self, response_data: Dict[str, Any],
                                 search_id: str, limit: int) -> Dict[str, Any]:
        """Parse round-trip flight search response.

        Args:
            response_data: Raw response from Kiwi API
            search_id: Search identifier for logging
            limit: Maximum number of results to return

        Returns:
            Parsed response with flight information
        """
        try:
            if 'data' not in response_data:
                return {
                    "success": False,
                    "error": "Missing data field in response",
                    "raw_response": response_data
                }

            return_data = response_data['data'].get('returnItineraries')
            if not return_data:
                return {
                    "success": False,
                    "error": "Missing returnItineraries field in response",
                    "raw_response": response_data
                }

            # Check for API errors
            if return_data.get('__typename') == 'AppError':
                error_msg = return_data.get('error', 'Unknown API error')
                logger.error(f"[{search_id}] API returned error: {error_msg}")
                return {
                    "success": False,
                    "error": f"API Error: {error_msg}"
                }

            if return_data.get('__typename') != 'Itineraries':
                return {
                    "success": False,
                    "error": f"Unexpected response type: {return_data.get('__typename')}",
                    "raw_response": response_data
                }

            # Parse flight data
            itineraries = return_data.get('itineraries', [])
            metadata = return_data.get('metadata', {})

            logger.info(f"[{search_id}] Found {len(itineraries)} round-trip flights")

            # Parse all flights and count hidden city ones
            all_flights = []
            hidden_city_count = 0
            for itinerary in itineraries[:limit]:
                flight_info = self._extract_roundtrip_flight_info(itinerary)
                if flight_info:
                    all_flights.append(flight_info)
                    if flight_info.get('is_hidden_city'):
                        hidden_city_count += 1

            return {
                "success": True,
                "search_id": search_id,
                "trip_type": "roundtrip",
                "total_count": metadata.get('itinerariesCount', 0),
                "hidden_city_count": hidden_city_count,
                "has_more": metadata.get('hasMorePending', False),
                "flights": all_flights,
                "currency": self.localization_config.currency.value,
                "language": self.localization_config.language.value
            }

        except Exception as e:
            logger.error(f"[{search_id}] Failed to parse response: {e}")
            return {
                "success": False,
                "error": f"Parse failed: {str(e)}",
                "raw_response": response_data
            }

    def _extract_oneway_flight_info(self, itinerary: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract key information from one-way flight itinerary.

        Args:
            itinerary: Flight itinerary data from API

        Returns:
            Extracted flight information or None if extraction fails
        """
        try:
            # Basic information
            flight_id = itinerary.get('id', '')
            price_main = itinerary.get('price', {}).get('amount', 0)
            price_eur = itinerary.get('priceEur', {}).get('amount', 0)
            duration = itinerary.get('duration', 0)

            # Hidden city information
            travel_hack = itinerary.get('travelHack', {})
            is_hidden_city = travel_hack.get('isTrueHiddenCity', False)
            is_throwaway = travel_hack.get('isThrowawayTicket', False)

            # Flight segments information
            sector = itinerary.get('sector', {})
            segments = sector.get('sectorSegments', [])

            if not segments:
                return None

            # Extract first and last segments for complete route info
            first_segment = segments[0].get('segment', {})
            last_segment = segments[-1].get('segment', {})

            # Source from first segment, destination from last segment
            source = first_segment.get('source', {})
            destination = last_segment.get('destination', {})

            # Use adaptive hidden destination parsing
            hidden_destination = self._find_hidden_destination(segments)

            # Use first segment's carrier for main airline
            carrier = first_segment.get('carrier', {})

            # Get localized names
            airline_name = self.localization_config.get_airline_name(
                carrier.get('code', ''), carrier.get('name', '')
            )

            # Extract complete route information
            route_info = self._extract_complete_route_info(segments)

            return {
                "id": flight_id,
                "price": price_main,
                "price_eur": price_eur,
                "currency": self.localization_config.currency.value,
                "currency_symbol": self.localization_config.currency_symbol,
                "duration_minutes": duration // 60 if duration else 0,
                "is_hidden_city": is_hidden_city,
                "is_throwaway": is_throwaway,
                "departure_airport": source.get('station', {}).get('code', ''),
                "departure_airport_name": self.localization_config.get_airport_name(
                    source.get('station', {}).get('code', ''),
                    source.get('station', {}).get('name', '')
                ),
                "arrival_airport": destination.get('station', {}).get('code', ''),
                "arrival_airport_name": self.localization_config.get_airport_name(
                    destination.get('station', {}).get('code', ''),
                    destination.get('station', {}).get('name', '')
                ),
                "hidden_destination_code": hidden_destination.get('code', '') if hidden_destination else '',
                "hidden_destination_name": self.localization_config.get_airport_name(
                    hidden_destination.get('code', ''), hidden_destination.get('name', '')
                ) if hidden_destination else '',
                "carrier_code": carrier.get('code', ''),
                "carrier_name": airline_name,
                "flight_number": first_segment.get('code', ''),
                "departure_time": source.get('localTime', ''),
                "arrival_time": destination.get('localTime', ''),
                "segment_count": len(segments),
                "route_segments": route_info.get('segments', []),  # 完整航段信息
                "trip_type": "oneway"
            }

        except Exception as e:
            logger.error(f"Failed to extract one-way flight info: {e}")
            return None

    def _extract_roundtrip_flight_info(self, itinerary: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract key information from round-trip flight itinerary.

        Args:
            itinerary: Flight itinerary data from API

        Returns:
            Extracted flight information or None if extraction fails
        """
        try:
            # Basic information
            flight_id = itinerary.get('id', '')
            price_main = itinerary.get('price', {}).get('amount', 0)
            price_eur = itinerary.get('priceEur', {}).get('amount', 0)
            duration = itinerary.get('duration', 0)

            # Hidden city information
            travel_hack = itinerary.get('travelHack', {})
            is_hidden_city = travel_hack.get('isTrueHiddenCity', False)
            is_throwaway = travel_hack.get('isThrowawayTicket', False)

            # Parse outbound and inbound legs
            def parse_leg(leg_data: Dict[str, Any], leg_type: str) -> Optional[Dict[str, Any]]:
                segments = leg_data.get('sectorSegments', [])
                if not segments:
                    return None

                # For simplicity, take the first segment
                segment = segments[0].get('segment', {})
                source = segment.get('source', {})
                destination = segment.get('destination', {})
                hidden_destination = segment.get('hiddenDestination', {})
                carrier = segment.get('carrier', {})

                # Get localized names
                airline_name = self.localization_config.get_airline_name(
                    carrier.get('code', ''), carrier.get('name', '')
                )

                return {
                    "departure_airport": source.get('station', {}).get('code', ''),
                    "departure_airport_name": self.localization_config.get_airport_name(
                        source.get('station', {}).get('code', ''),
                        source.get('station', {}).get('name', '')
                    ),
                    "arrival_airport": destination.get('station', {}).get('code', ''),
                    "arrival_airport_name": self.localization_config.get_airport_name(
                        destination.get('station', {}).get('code', ''),
                        destination.get('station', {}).get('name', '')
                    ),
                    "hidden_destination_code": hidden_destination.get('code', '') if hidden_destination else '',
                    "hidden_destination_name": hidden_destination.get('name', '') if hidden_destination else '',
                    "carrier_code": carrier.get('code', ''),
                    "carrier_name": airline_name,
                    "flight_number": segment.get('code', ''),
                    "departure_time": source.get('localTime', ''),
                    "arrival_time": destination.get('localTime', ''),
                    "duration": segment.get('duration', 0),
                    "is_hidden": bool(hidden_destination),
                    "leg_type": leg_type
                }

            outbound_info = parse_leg(itinerary.get('outbound', {}), "outbound")
            inbound_info = parse_leg(itinerary.get('inbound', {}), "inbound")

            if not outbound_info or not inbound_info:
                return None

            return {
                "id": flight_id,
                "price": price_main,
                "price_eur": price_eur,
                "currency": self.localization_config.currency.value,
                "currency_symbol": self.localization_config.currency_symbol,
                "duration_minutes": duration // 60 if duration else 0,
                "is_hidden_city": is_hidden_city,
                "is_throwaway": is_throwaway,
                "outbound": outbound_info,
                "inbound": inbound_info,
                "trip_type": "roundtrip"
            }

        except Exception as e:
            logger.error(f"Failed to extract round-trip flight info: {e}")
            return None

    def _find_hidden_destination(self, segments: list) -> dict:
        """Adaptively find hidden destination information in flight segments.

        Different query types may have hidden destination in different locations:
        - Economy vs Business class
        - Direct vs connecting flights
        - Different routes

        Args:
            segments: List of flight segments

        Returns:
            Hidden destination information or empty dict if not found
        """
        if not segments:
            return {}

        # Strategy 1: Check all segments for hidden destination (most common)
        for seg in segments:
            segment_data = seg.get('segment', {})
            hidden_dest = segment_data.get('hiddenDestination')
            if hidden_dest:
                return hidden_dest

        # Strategy 2: Check if any segment has a different final destination
        # This handles cases where hidden city info might be implicit
        if len(segments) > 1:
            last_segment = segments[-1].get('segment', {})
            last_destination = last_segment.get('destination', {})

            # Check if the last segment's destination differs from expected
            # This is a fallback for cases where hiddenDestination field is missing
            for i, seg in enumerate(segments[:-1]):
                segment_data = seg.get('segment', {})
                dest = segment_data.get('destination', {})
                if dest and dest != last_destination:
                    # Potential hidden city scenario
                    return dest.get('station', {})

        return {}

    def _extract_complete_route_info(self, segments: list) -> dict:
        """Extract complete route information including all segments.

        Args:
            segments: List of flight segments

        Returns:
            Dictionary with complete route information
        """
        if not segments:
            return {}

        first_segment = segments[0].get('segment', {})
        last_segment = segments[-1].get('segment', {})

        # Build complete route
        route_segments = []
        for seg in segments:
            segment_data = seg.get('segment', {})
            source = segment_data.get('source', {})
            destination = segment_data.get('destination', {})

            route_segments.append({
                "from": source.get('station', {}).get('code', ''),
                "to": destination.get('station', {}).get('code', ''),
                "carrier": segment_data.get('carrier', {}).get('code', ''),
                "flight_number": segment_data.get('code', ''),
                "departure_time": source.get('localTime', ''),
                "arrival_time": destination.get('localTime', ''),
                "duration": segment_data.get('duration', 0)
            })

        return {
            "origin": first_segment.get('source', {}).get('station', {}).get('code', ''),
            "destination": last_segment.get('destination', {}).get('station', {}).get('code', ''),
            "segments": route_segments,
            "total_segments": len(segments)
        }

    def _detect_query_type(self, variables: dict) -> str:
        """Detect the type of query to apply appropriate parsing strategy.

        Args:
            variables: Query variables sent to API

        Returns:
            Query type string for parsing strategy selection
        """
        cabin_class = variables.get('search', {}).get('cabinClass', {}).get('cabinClass', 'ECONOMY')
        max_stops = variables.get('filter', {}).get('maxStopsCount', 0)
        has_return = 'inboundDepartureDate' in variables.get('search', {}).get('itinerary', {})

        query_type = f"{cabin_class.lower()}"
        if max_stops > 0:
            query_type += f"_stops{max_stops}"
        if has_return:
            query_type += "_roundtrip"
        else:
            query_type += "_oneway"

        return query_type


# Global instance for easy access
kiwi_flights_api = KiwiFlightsAPI()
