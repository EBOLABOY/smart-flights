"""Flight search implementation.

This module provides the core flight search functionality, interfacing with
Google Flights' API and Kiwi.com API to find available flights and their details.
"""

import json
import asyncio
from copy import deepcopy
from datetime import datetime

from fli.models import (
    Airline,
    Airport,
    FlightLeg,
    FlightResult,
    FlightSearchFilters,
)
from fli.models.google_flights.flights import SortBy
from fli.models.google_flights.base import LocalizationConfig, TripType
from fli.search.client import get_client
from fli.api.kiwi_flights import KiwiFlightsAPI


class SearchFlights:
    """Flight search implementation using Google Flights' API.

    This class handles searching for specific flights with detailed filters,
    parsing the results into structured data models.
    """

    BASE_URL = "https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights.FlightsFrontendService/GetShoppingResults"
    DEFAULT_HEADERS = {
        "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
    }

    def __init__(self, localization_config: LocalizationConfig = None):
        """Initialize the search client for flight searches.

        Args:
            localization_config: Configuration for language and currency settings

        """
        self.client = get_client()
        self.localization_config = localization_config or LocalizationConfig()

    def _get_at_param(self) -> str:
        """获取API请求所需的at参数."""
        return "AN8qZjZ4uOkhU80kMUKHA8tjPGXO:1751175953243"

    def search(
        self, filters: FlightSearchFilters, top_n: int = 5, enhanced_search: bool = False
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """Search for flights using the given FlightSearchFilters.

        Args:
            filters: Full flight search object including airports, dates, and preferences
            top_n: Number of flights to limit the return flight search to
            enhanced_search: If True, use extended search mode (135+ flights)
                           If False, use basic search mode (12 flights)

        Returns:
            List of FlightResult objects containing flight details, or None if no results

        Raises:
            Exception: If the search fails or returns invalid data
        """
        return self._search_internal(filters, top_n, enhanced_search)

    def search_extended(
        self, filters: FlightSearchFilters, top_n: int = 50
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """Search for flights using extended search mode for maximum results.

        This method automatically uses the extended search mode that returns 135+ flights
        instead of the basic 12 flights. It's equivalent to calling search() with
        enhanced_search=True but provides a cleaner API for users who always want
        maximum results.

        Args:
            filters: Full flight search object including airports, dates, and preferences
            top_n: Number of flights to limit the return flight search to (default: 50)
                  For round-trip flights, this limits the number of outbound flights
                  to consider for pairing with return flights.

        Returns:
            List of FlightResult objects containing flight details, or None if no results

        Raises:
            Exception: If the search fails or returns invalid data

        Note:
            For round-trip flights, the total number of combinations will be:
            min(outbound_flights, top_n) × return_flights_per_outbound
            To get more combinations, increase the top_n parameter.
        """
        return self._search_internal(filters, top_n, enhanced_search=True)

    def search_extended_max_combinations(
        self, filters: FlightSearchFilters, max_outbound: int = 100, max_return_per_outbound: int = 50
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """Search for flights with maximum combinations for round-trip flights.

        This method is optimized for round-trip searches where you want to maximize
        the number of flight combinations while controlling the search scope.

        Args:
            filters: Full flight search object including airports, dates, and preferences
            max_outbound: Maximum number of outbound flights to consider (default: 100)
            max_return_per_outbound: Maximum return flights per outbound flight (default: 50)

        Returns:
            List of FlightResult objects or flight pairs, or None if no results

        Raises:
            Exception: If the search fails or returns invalid data

        Note:
            This method can generate up to max_outbound × max_return_per_outbound combinations
            for round-trip flights, but will take longer to execute.
        """
        if filters.trip_type == TripType.ROUND_TRIP:
            return self._search_internal(filters, max_outbound, enhanced_search=True)
        else:
            # For one-way flights, use the standard extended search
            return self._search_internal(filters, max_outbound, enhanced_search=True)

    def _search_internal(
        self, filters: FlightSearchFilters, top_n: int = 5, enhanced_search: bool = False
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """Search for flights using the given FlightSearchFilters.

        Args:
            filters: Full flight search object including airports, dates, and preferences
            top_n: Number of flights to limit the return flight search to

        Returns:
            List of FlightResult objects containing flight details, or None if no results

        Raises:
            Exception: If the search fails or returns invalid data

        """
        # 优先使用简单的单次API调用方法（参考punitarani/fli）
        # 只有在简单方法失败时才使用复杂的状态令牌方法
        if filters.sort_by.value != 0 and filters.sort_by.value != 1:  # 不是NONE或TOP_FLIGHTS
            print(f"🔍 使用简单排序方法: {filters.sort_by.name}")
            # 先尝试简单方法
            try:
                simple_result = self._search_simple_sorting(filters, top_n, enhanced_search)
                if simple_result and len(simple_result) > 0:
                    return simple_result
            except Exception as e:
                print(f"⚠️ 简单排序方法失败: {e}")

            # 简单方法失败，回退到状态令牌方法
            print(f"🔄 回退到状态令牌方法")
            return self._search_with_sorting(filters, top_n, enhanced_search)

        # 默认搜索（最佳或无排序）
        encoded_filters = filters.encode(enhanced_search=enhanced_search)

        # Build URL with complete browser parameters to match real browser requests
        # These parameters are essential for getting third-party prices
        browser_params = {
            'f.sid': '-6262809356685208499',
            'bl': 'boq_travel-frontend-flights-ui_20250624.05_p0',
            'hl': self.localization_config.api_language_code,
            'gl': 'US',  # Force US region like browser for third-party prices
            'curr': self.localization_config.api_currency_code,  # Add currency parameter
            'soc-app': '162',
            'soc-platform': '1',
            'soc-device': '1',
            '_reqid': '949557',  # Updated request ID from browser
            'rt': 'c'
        }

        # Build complete URL with all browser parameters
        param_string = '&'.join([f"{k}={v}" for k, v in browser_params.items()])
        url_with_params = f"{self.BASE_URL}?{param_string}"

        try:
            # Add the 'at' authentication parameter found in browser requests
            # This may be the key to getting third-party prices
            at_param = "AN8qZjZ4uOkhU80kMUKHA8tjPGXO:1751175953243"

            # Add critical browser headers for complete API access
            enhanced_headers = {
                **self.DEFAULT_HEADERS,
                'x-goog-ext-259736195-jspb': f'["{self.localization_config.api_language_code}-CN","US","{self.localization_config.api_currency_code}",2,null,[-480],null,null,7,[]]',
                'x-same-domain': '1',
                'origin': 'https://www.google.com',
                'referer': 'https://www.google.com/travel/flights/',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
            }

            response = self.client.post(
                url=url_with_params,
                data=f"f.req={encoded_filters}&at={at_param}",
                headers=enhanced_headers,
                impersonate="chrome",
                allow_redirects=True,
            )
            response.raise_for_status()

            # Save raw response for debugging when using browser parameters
            raw_response = response.text

            # Try different JSON parsing approaches for browser parameter responses
            try:
                parsed = json.loads(raw_response.lstrip(")]}'"))[0][2]
            except (json.JSONDecodeError, IndexError, KeyError) as e:
                # Save raw response for analysis
                with open("raw_response_debug.txt", "w", encoding="utf-8") as f:
                    f.write(f"Raw response length: {len(raw_response)}\n")
                    f.write(f"First 500 chars: {raw_response[:500]}\n")
                    f.write(f"Last 500 chars: {raw_response[-500:]}\n")
                    f.write(f"Full response:\n{raw_response}")

                # Try alternative parsing methods
                try:
                    # Method 1: Try without lstrip
                    parsed = json.loads(raw_response)[0][2]
                except:
                    try:
                        # Method 2: Try different lstrip patterns
                        cleaned = raw_response.lstrip(")]}'").lstrip()
                        parsed = json.loads(cleaned)[0][2]
                    except:
                        # Method 3: Handle multi-line response format from browser parameters
                        lines = raw_response.strip().split('\n')
                        for line in lines:
                            if line.startswith('[["wrb.fr"'):
                                # Extract JSON from wrb.fr response
                                start_idx = line.find('"[[')
                                if start_idx > 0:
                                    json_str = line[start_idx+1:-3]  # Remove quotes and trailing ]]
                                    json_str = json_str.replace('\\"', '"').replace('\\\\', '\\')
                                    parsed = json.loads(json_str)
                                    break
                        else:
                            raise Exception(f"Failed to parse response. Raw response saved to raw_response_debug.txt. Original error: {e}")

            if not parsed:
                return None

            # Handle different response formats
            if isinstance(parsed, str):
                encoded_filters = json.loads(parsed)
            else:
                # Already parsed data from browser parameter response
                encoded_filters = parsed
            flights_data = [
                item
                for i in [2, 3]
                if isinstance(encoded_filters[i], list)
                for item in encoded_filters[i][0]
            ]
            flights = [self._parse_flights_data(flight) for flight in flights_data]

            if (
                filters.trip_type == TripType.ONE_WAY
                or filters.flight_segments[0].selected_flight is not None
            ):
                return flights

            # Get the return flights if round-trip
            flight_pairs = []
            # Call the search again with the return flight data
            for selected_flight in flights[:top_n]:
                selected_flight_filters = deepcopy(filters)
                selected_flight_filters.flight_segments[0].selected_flight = selected_flight
                return_flights = self._search_internal(selected_flight_filters, top_n=top_n, enhanced_search=enhanced_search)
                if return_flights is not None:
                    flight_pairs.extend(
                        (selected_flight, return_flight) for return_flight in return_flights
                    )

            return flight_pairs

        except Exception as e:
            raise Exception(f"Search failed: {str(e)}") from e

    def _search_with_sorting(
        self, filters: FlightSearchFilters, top_n: int = 5, enhanced_search: bool = False
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """执行带有复杂排序的搜索（需要两步走流程）.

        Args:
            filters: 航班搜索过滤器
            top_n: 返回航班数量限制
            enhanced_search: 是否使用扩展搜索

        Returns:
            航班结果列表或None

        """
        try:
            # 步骤1: 先执行默认搜索获取状态令牌
            print(f"🔍 步骤1: 执行初始搜索获取状态令牌...")

            # 创建默认排序的过滤器副本
            initial_filters = filters.model_copy()
            initial_filters.sort_by = SortBy.TOP_FLIGHTS  # 使用最佳排序获取初始数据

            encoded_filters = initial_filters.encode(enhanced_search=enhanced_search)

            # 构建URL参数
            browser_params = {
                'f.sid': '-6262809356685208499',
                'bl': 'boq_travel-frontend-flights-ui_20250624.05_p0',
                'hl': self.localization_config.api_language_code,
                'gl': 'US',
                'curr': self.localization_config.api_currency_code,
                'soc-app': '162',
                'soc-platform': '1',
                'soc-device': '1',
                '_reqid': '949557',
                'rt': 'c'
            }

            param_string = '&'.join([f"{k}={v}" for k, v in browser_params.items()])
            url_with_params = f"{self.BASE_URL}?{param_string}"

            # 发送初始请求
            at_param = "AN8qZjZ4uOkhU80kMUKHA8tjPGXO:1751175953243"
            enhanced_headers = {
                **self.DEFAULT_HEADERS,
                'x-goog-ext-259736195-jspb': f'["{self.localization_config.api_language_code}-CN","US","{self.localization_config.api_currency_code}",2,null,[-480],null,null,7,[]]',
                'x-same-domain': '1',
                'origin': 'https://www.google.com',
                'referer': 'https://www.google.com/travel/flights/',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
            }

            response = self.client.post(
                url=url_with_params,
                data=f"f.req={encoded_filters}&at={at_param}",
                headers=enhanced_headers,
                impersonate="chrome",
                allow_redirects=True,
            )
            response.raise_for_status()

            # 步骤2: 解析响应提取状态令牌
            print(f"🔍 步骤2: 解析响应提取状态令牌...")
            raw_response = response.text

            # 解析初始响应
            try:
                parsed = json.loads(raw_response.lstrip(")]}'"))[0][2]
            except (json.JSONDecodeError, IndexError, KeyError):
                # 尝试其他解析方法
                lines = raw_response.strip().split('\n')
                for line in lines:
                    if line.startswith('[["wrb.fr"'):
                        start_idx = line.find('"[[')
                        if start_idx > 0:
                            json_str = line[start_idx+1:-3]
                            json_str = json_str.replace('\\"', '"').replace('\\\\', '\\')
                            parsed = json.loads(json_str)
                            break
                else:
                    raise Exception("无法解析初始响应")

            if not parsed:
                return None

            # 提取状态令牌和价格锚点
            state_token, price_anchor = self._extract_sorting_tokens(parsed, filters.sort_by)

            if not state_token:
                print(f"⚠️ 未找到排序状态令牌，返回默认结果")
                # 如果没有找到状态令牌，返回默认搜索结果
                return self._parse_search_results(parsed, filters, top_n)

            # 步骤3: 使用状态令牌执行排序搜索
            print(f"🔍 步骤3: 使用状态令牌执行排序搜索...")
            print(f"   价格锚点: {price_anchor}")
            print(f"   状态令牌: {state_token[:50]}...")

            # 构造带有状态令牌的新请求
            sorted_encoded = filters.encode_with_state_token(
                enhanced_search=enhanced_search,
                price_anchor=price_anchor,
                state_token=state_token
            )

            # 发送排序请求
            sorted_response = self.client.post(
                url=url_with_params,
                data=f"f.req={sorted_encoded}&at={at_param}",
                headers=enhanced_headers,
                impersonate="chrome",
                allow_redirects=True,
            )
            sorted_response.raise_for_status()

            # 解析排序后的响应
            sorted_raw = sorted_response.text
            try:
                sorted_parsed = json.loads(sorted_raw.lstrip(")]}'"))[0][2]
            except (json.JSONDecodeError, IndexError, KeyError):
                lines = sorted_raw.strip().split('\n')
                for line in lines:
                    if line.startswith('[["wrb.fr"'):
                        start_idx = line.find('"[[')
                        if start_idx > 0:
                            json_str = line[start_idx+1:-3]
                            json_str = json_str.replace('\\"', '"').replace('\\\\', '\\')
                            sorted_parsed = json.loads(json_str)
                            break
                else:
                    raise Exception("无法解析排序响应")

            if not sorted_parsed:
                return None

            # 解析排序后的结果
            results = self._parse_search_results(sorted_parsed, filters, top_n)

            # 应用客户端排序（如果需要）
            if results and filters.sort_by != SortBy.NONE:
                results = self._apply_client_side_sorting(results, filters.sort_by)

            return results

        except Exception as e:
            print(f"❌ 排序搜索失败: {e}")
            # 如果排序搜索失败，回退到默认搜索
            return self._search_internal_fallback(filters, top_n, enhanced_search)

    def _search_internal_fallback(
        self, filters: FlightSearchFilters, top_n: int = 5, enhanced_search: bool = False
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """回退到默认搜索方法."""
        print(f"🔄 回退到默认搜索...")
        fallback_filters = filters.model_copy()
        fallback_filters.sort_by = SortBy.TOP_FLIGHTS
        encoded_filters = fallback_filters.encode(enhanced_search=enhanced_search)

        # 执行默认搜索的完整流程
        browser_params = {
            'f.sid': '-6262809356685208499',
            'bl': 'boq_travel-frontend-flights-ui_20250624.05_p0',
            'hl': self.localization_config.api_language_code,
            'gl': 'US',
            'curr': self.localization_config.api_currency_code,
            'soc-app': '162',
            'soc-platform': '1',
            'soc-device': '1',
            '_reqid': '949557',
            'rt': 'c'
        }

        param_string = '&'.join([f"{k}={v}" for k, v in browser_params.items()])
        url_with_params = f"{self.BASE_URL}?{param_string}"

        at_param = "AN8qZjZ4uOkhU80kMUKHA8tjPGXO:1751175953243"
        enhanced_headers = {
            **self.DEFAULT_HEADERS,
            'x-goog-ext-259736195-jspb': f'["{self.localization_config.api_language_code}-CN","US","{self.localization_config.api_currency_code}",2,null,[-480],null,null,7,[]]',
            'x-same-domain': '1',
            'origin': 'https://www.google.com',
            'referer': 'https://www.google.com/travel/flights/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
        }

        response = self.client.post(
            url=url_with_params,
            data=f"f.req={encoded_filters}&at={at_param}",
            headers=enhanced_headers,
            impersonate="chrome",
            allow_redirects=True,
        )
        response.raise_for_status()

        raw_response = response.text
        try:
            parsed = json.loads(raw_response.lstrip(")]}'"))[0][2]
        except (json.JSONDecodeError, IndexError, KeyError):
            lines = raw_response.strip().split('\n')
            for line in lines:
                if line.startswith('[["wrb.fr"'):
                    start_idx = line.find('"[[')
                    if start_idx > 0:
                        json_str = line[start_idx+1:-3]
                        json_str = json_str.replace('\\"', '"').replace('\\\\', '\\')
                        parsed = json.loads(json_str)
                        break
            else:
                return None

        if not parsed:
            return None

        return self._parse_search_results(parsed, filters, top_n)

    def _search_direct_cheapest(
        self,
        filters: FlightSearchFilters,
        top_n: int = 50,
        enhanced_search: bool = True
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """
        直接使用最低价格排序搜索，不使用状态令牌

        Args:
            filters: 搜索过滤器
            top_n: 返回航班数量限制
            enhanced_search: 是否使用增强搜索

        Returns:
            航班结果列表或None
        """
        try:
            print(f"🔍 直接最低价格搜索 (无状态令牌)")

            # 确保使用最低价格排序
            direct_filters = filters.model_copy()
            direct_filters.sort_by = SortBy.CHEAPEST

            # 直接编码为最低价格排序请求
            encoded_filters = direct_filters.encode(enhanced_search=enhanced_search)

            # 构建URL参数
            browser_params = {
                'f.sid': '-6262809356685208499',
                'bl': 'boq_travel-frontend-flights-ui_20250624.05_p0',
                'hl': self.localization_config.api_language_code,
                'gl': 'US',
                'curr': self.localization_config.api_currency_code,
                'soc-app': '162',
                'soc-platform': '1',
                'soc-device': '1',
                '_reqid': '949557',
                'rt': 'c'
            }

            param_string = '&'.join([f"{k}={v}" for k, v in browser_params.items()])
            url_with_params = f"{self.BASE_URL}?{param_string}"

            at_param = "AN8qZjZ4uOkhU80kMUKHA8tjPGXO:1751175953243"
            enhanced_headers = {
                **self.DEFAULT_HEADERS,
                'x-goog-ext-259736195-jspb': f'["{self.localization_config.api_language_code}-CN","US","{self.localization_config.api_currency_code}",2,null,[-480],null,null,7,[]]',
                'x-same-domain': '1',
                'origin': 'https://www.google.com',
                'referer': 'https://www.google.com/travel/flights/',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
            }

            print(f"   发送直接排序请求...")
            response = self.client.post(
                url=url_with_params,
                data=f"f.req={encoded_filters}&at={at_param}",
                headers=enhanced_headers,
                impersonate="chrome",
                allow_redirects=True,
            )
            response.raise_for_status()

            # 解析响应
            raw_response = response.text
            print(f"   响应长度: {len(raw_response):,} 字符")

            try:
                parsed = json.loads(raw_response.lstrip(")]}'"))[0][2]
            except (json.JSONDecodeError, IndexError, KeyError):
                # 尝试其他解析方法
                lines = raw_response.strip().split('\n')
                for line in lines:
                    if line.startswith('[["wrb.fr"'):
                        start_idx = line.find('"[[')
                        if start_idx > 0:
                            json_str = line[start_idx+1:-3]
                            json_str = json_str.replace('\\"', '"').replace('\\\\', '\\')
                            parsed = json.loads(json_str)
                            break
                else:
                    raise Exception("无法解析响应")

            if not parsed:
                print(f"   ❌ 解析结果为空")
                return None

            # 解析搜索结果
            results = self._parse_search_results(parsed, filters, top_n)

            if results:
                print(f"   ✅ 找到 {len(results)} 个航班")
                # 分析价格情况
                prices = [f.price for f in results if f.price > 0]
                zero_count = sum(1 for f in results if f.price == 0)

                if prices:
                    currency_symbol = "¥" if self.localization_config.currency.value == "CNY" else "$"
                    print(f"   价格范围: {currency_symbol}{min(prices):.0f} - {currency_symbol}{max(prices):.0f}")
                    print(f"   有价格航班: {len(prices)} 个")
                    print(f"   零价格航班: {zero_count} 个")
            else:
                print(f"   ❌ 未找到航班结果")

            return results

        except Exception as e:
            print(f"   ❌ 直接搜索失败: {e}")
            # 如果直接搜索失败，回退到原有方法
            print(f"   🔄 回退到原有搜索方法...")
            return self._search_internal(filters, top_n, enhanced_search)

    def _search_simple_sorting(
        self, filters: FlightSearchFilters, top_n: int = 5, enhanced_search: bool = False
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """使用简单的单次API调用进行排序搜索（参考punitarani/fli方法）.

        Args:
            filters: 航班搜索过滤器
            top_n: 返回航班数量限制
            enhanced_search: 是否使用扩展搜索

        Returns:
            航班结果列表或None
        """
        try:
            print(f"🔍 执行简单排序搜索 (sort_by={filters.sort_by.name})")

            # 直接使用包含排序参数的过滤器进行搜索
            encoded_filters = filters.encode(enhanced_search=enhanced_search)

            # 构建URL参数
            browser_params = {
                'f.sid': '-6262809356685208499',
                'bl': 'boq_travel-frontend-flights-ui_20250624.05_p0',
                'hl': self.localization_config.api_language_code,
                'gl': 'US',
                'curr': self.localization_config.api_currency_code,
                'soc-app': '162',
                'soc-platform': '1',
                'soc-device': '1',
                '_reqid': '949557',
                'rt': 'c'
            }

            url_with_params = f"{self.BASE_URL}?" + "&".join([f"{k}={v}" for k, v in browser_params.items()])

            # 构建请求头
            enhanced_headers = {
                "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "accept": "*/*",
                "accept-language": f"{self.localization_config.api_language_code},en;q=0.9",
                "accept-encoding": "gzip, deflate, br",
                "origin": "https://www.google.com",
                "referer": "https://www.google.com/travel/flights",
            }

            # 发送请求
            response = self.client.post(
                url=url_with_params,
                data=f"f.req={encoded_filters}&at={self._get_at_param()}",
                headers=enhanced_headers,
                impersonate="chrome",
                allow_redirects=True,
            )
            response.raise_for_status()

            # 解析响应
            raw_response = response.text
            try:
                parsed = json.loads(raw_response.lstrip(")]}'"))[0][2]
            except (json.JSONDecodeError, IndexError, KeyError):
                lines = raw_response.strip().split('\n')
                for line in lines:
                    if line.startswith('[["wrb.fr"'):
                        start_idx = line.find('"[[')
                        if start_idx > 0:
                            json_str = line[start_idx+1:-3]
                            json_str = json_str.replace('\\"', '"').replace('\\\\', '\\')
                            parsed = json.loads(json_str)
                            break
                else:
                    raise Exception("无法解析简单排序响应")

            if not parsed:
                return None

            # 解析并返回结果
            results = self._parse_search_results(parsed, filters, top_n)

            if results:
                print(f"✅ 简单排序搜索成功，找到 {len(results)} 个航班")

            return results

        except Exception as e:
            print(f"❌ 简单排序搜索失败: {e}")
            raise e

    def _extract_sorting_tokens(self, parsed_data: list, sort_by: SortBy) -> tuple[str | None, int | None]:
        """从初始响应中提取排序所需的状态令牌和价格锚点.

        Args:
            parsed_data: 解析后的API响应数据
            sort_by: 目标排序方式

        Returns:
            (状态令牌, 价格锚点) 的元组，如果未找到则返回 (None, None)
        """
        try:
            # 在响应数据中查找排序相关的令牌
            # 这需要根据实际的Google Flights响应结构来实现
            # 目前返回模拟数据用于测试

            if sort_by == SortBy.CHEAPEST:
                # 使用最低价格排序的状态令牌
                # 根据Google Flights API分析，最低价格排序需要特定的状态令牌

                # 不使用价格锚点，让API自然排序
                price_anchor = None
                print(f"   使用最低价格排序 (无价格锚点)")

                # 最低价格排序的状态令牌
                # 这个令牌告诉API按价格从低到高排序
                state_token = "CjRIeHlPNktDSjdrUGtBR1dmUFFCRy0tLS0tLS0tLXBqYmtrMkFBQUFBR2hnNHRFTWVMM01BEhZjb21wcmVoZW5zaXZlbmVzc19sdXJlGgoI0yAQABoDQ05ZOBxwvscD"

                return state_token, price_anchor

            # 其他排序方式的令牌提取逻辑
            return None, None

        except Exception as e:
            print(f"⚠️ 提取排序令牌失败: {e}")
            return None, None

    def _apply_client_side_sorting(
        self, flights: list[FlightResult], sort_by: SortBy
    ) -> list[FlightResult]:
        """在客户端对航班结果进行排序.

        Args:
            flights: 航班结果列表
            sort_by: 排序方式

        Returns:
            排序后的航班结果列表
        """
        try:
            if sort_by == SortBy.PRICE or sort_by == SortBy.CHEAPEST:
                # 按价格排序：有价格的航班在前，按价格升序；无价格的航班在后
                priced_flights = [f for f in flights if f.price > 0]
                zero_price_flights = [f for f in flights if f.price == 0]
                priced_flights.sort(key=lambda x: x.price)
                return priced_flights + zero_price_flights

            elif sort_by == SortBy.DEPARTURE_TIME:
                # 按出发时间排序
                return sorted(flights, key=lambda x: x.legs[0].departure_datetime if x.legs else "")

            elif sort_by == SortBy.ARRIVAL_TIME:
                # 按到达时间排序
                return sorted(flights, key=lambda x: x.legs[-1].arrival_datetime if x.legs else "")

            elif sort_by == SortBy.DURATION:
                # 按飞行时长排序
                return sorted(flights, key=lambda x: x.duration)

            elif sort_by == SortBy.STOPS:
                # 按中转次数排序
                return sorted(flights, key=lambda x: x.stops)

            elif sort_by == SortBy.AIRLINE:
                # 按航空公司排序
                return sorted(flights, key=lambda x: x.legs[0].airline.name if x.legs else "")

            else:
                # 其他排序方式保持原顺序
                return flights

        except Exception as e:
            print(f"⚠️ 客户端排序失败: {e}")
            return flights

    def _parse_search_results(
        self, parsed_data: list, filters: FlightSearchFilters, top_n: int
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """解析搜索结果数据."""
        try:
            # 使用现有的解析逻辑（从_search_internal方法中复制）
            if isinstance(parsed_data, str):
                encoded_filters = json.loads(parsed_data)
            else:
                # Already parsed data from browser parameter response
                encoded_filters = parsed_data

            flights_data = [
                item
                for i in [2, 3]
                if isinstance(encoded_filters[i], list)
                for item in encoded_filters[i][0]
            ]
            flights = [self._parse_flights_data(flight) for flight in flights_data]

            if (
                filters.trip_type == TripType.ONE_WAY
                or filters.flight_segments[0].selected_flight is not None
            ):
                # 应用客户端排序（如果需要）
                if filters.sort_by != SortBy.NONE and filters.sort_by != SortBy.TOP_FLIGHTS:
                    flights = self._apply_client_side_sorting(flights, filters.sort_by)
                return flights

            # Get the return flights if round-trip
            flight_pairs = []
            # Call the search again with the return flight data
            for selected_flight in flights[:top_n]:
                selected_flight_filters = deepcopy(filters)
                selected_flight_filters.flight_segments[0].selected_flight = selected_flight
                return_flights = self._search_internal(selected_flight_filters, top_n=top_n, enhanced_search=True)
                if return_flights is not None:
                    flight_pairs.extend(
                        (selected_flight, return_flight) for return_flight in return_flights
                    )

            return flight_pairs

        except Exception as e:
            print(f"❌ 解析搜索结果失败: {e}")
            return None

    @staticmethod
    def _parse_flights_data(data: list) -> FlightResult:
        """Parse raw flight data into a structured FlightResult.

        Args:
            data: Raw flight data from the API response

        Returns:
            Structured FlightResult object with all flight details

        """
        try:
            # Enhanced price extraction based on analysis of raw API response
            # The price information is located in different positions depending on the airline
            price = SearchFlights._extract_price_enhanced(data)

            # Note: Previous attempts to extract CA flight prices from [0][22][7] and [0][2][0][31]
            # were incorrect - those fields contain flight IDs or other data, not prices.
            # CA flights genuinely have no price data in the API response and should show
            # price_unavailable=True to indicate users need to check the airline website.

            duration = SearchFlights._safe_get_nested(data, [0, 9], 0)

            # Determine if price is unavailable (airline doesn't provide direct pricing)
            price_unavailable = (price == 0)

            # Handle different flight leg structures
            flight_legs_data = SearchFlights._safe_get_nested(data, [0, 2], [])
            stops = max(0, len(flight_legs_data) - 1) if flight_legs_data else 0

            legs = []
            for fl in flight_legs_data:
                try:
                    leg = FlightLeg(
                        airline=SearchFlights._parse_airline_safe(fl),
                        flight_number=SearchFlights._safe_get_nested(fl, [22, 1], ""),
                        departure_airport=SearchFlights._parse_airport_safe(fl, 3),
                        arrival_airport=SearchFlights._parse_airport_safe(fl, 6),
                        departure_datetime=SearchFlights._parse_datetime_safe(fl, [20], [8]),
                        arrival_datetime=SearchFlights._parse_datetime_safe(fl, [21], [10]),
                        duration=SearchFlights._safe_get_nested(fl, [11], 0),
                    )
                    legs.append(leg)
                except Exception as e:
                    # Log the error but continue processing other legs
                    print(f"Warning: Failed to parse flight leg: {e}")
                    continue

            flight = FlightResult(
                price=price,
                duration=duration,
                stops=stops,
                legs=legs,
                price_unavailable=price_unavailable,
            )

            return flight

        except Exception as e:
            # Provide detailed error information for debugging
            raise Exception(
                f"Failed to parse flight data: {e}. Data structure: {type(data)} with length {len(data) if hasattr(data, '__len__') else 'unknown'}"
            ) from e

    @staticmethod
    def _extract_price_enhanced(data: list) -> float:
        """
        Enhanced price extraction with multiple strategies for different airlines.

        Based on analysis of raw API responses, different airlines may store
        price information in different data structure positions.

        Args:
            data: Raw flight data from the API response

        Returns:
            Price as float, or 0 if no price found
        """
        try:
            # Strategy 1: Standard price extraction (works for most airlines)
            standard_price = (
                SearchFlights._safe_get_nested(data, [1, 0, -1], 0) or
                SearchFlights._safe_get_nested(data, [1, 0, -2], 0) or
                SearchFlights._safe_get_nested(data, [1, 0, -3], 0) or
                0
            )

            if standard_price > 0:
                return standard_price

            # Strategy 2: Search in price arrays at the end of flight data
            # Based on user analysis: prices like 585000, 556000 found in arrays
            price_from_arrays = SearchFlights._extract_price_from_arrays(data)
            if price_from_arrays > 0:
                # 添加调试信息
                extracted_price = price_from_arrays / 100
                # print(f"DEBUG: 从数组中提取到价格 {price_from_arrays} -> ¥{extracted_price}")
                return extracted_price

            # Strategy 3: Deep search for price patterns
            price_from_deep_search = SearchFlights._extract_price_deep_search(data)
            if price_from_deep_search > 0:
                return price_from_deep_search

            # 如果所有策略都失败，可能需要更深入的分析
            # print(f"DEBUG: 所有价格提取策略都失败，数据结构: {type(data)}, 长度: {len(data) if hasattr(data, '__len__') else 'N/A'}")
            return 0

        except Exception as e:
            # print(f"DEBUG: 价格提取异常: {e}")
            return 0

    @staticmethod
    def _extract_price_from_arrays(data: list) -> float:
        """
        Extract price from arrays containing large integers (like 585000, 556000).

        Based on user analysis of CA flights in raw API response:
        - 航班数据块格式: [["CA","国航"], [...航班信息...], [...价格数组...], [1], [["CA","国航", ...]]]
        - 价格数组位置: 通常在航班数据块的倒数第二或第三个位置
        - 价格数组格式: [null,null,2,5,null,true,true,585000,556000,null,708000,1,false,null,null,2,false]
        - 提取585000, 556000等大整数，除以100得到实际价格
        """
        try:
            # 根据用户分析，重点查找航班数据块末尾的价格数组
            # 航班数据通常是一个大的列表，价格数组在其末尾部分

            if not isinstance(data, list) or len(data) < 3:
                return 0

            # 查找价格数组的策略：
            # 1. 从数据块的末尾开始查找
            # 2. 寻找包含多个大整数(100000-10000000)的数组
            # 3. 这些大整数就是价格信息

            def extract_prices_from_array(arr):
                """从单个数组中提取价格"""
                if not isinstance(arr, list):
                    return []

                prices = []
                for item in arr:
                    if isinstance(item, int) and 100000 <= item <= 10000000:
                        prices.append(item)

                return prices

            # 策略1: 查找数据块末尾的价格数组
            # 通常价格数组在倒数第2-4个位置
            for i in range(min(5, len(data))):  # 检查末尾5个元素
                idx = len(data) - 1 - i
                if idx >= 0:
                    element = data[idx]
                    if isinstance(element, list):
                        prices = extract_prices_from_array(element)
                        if len(prices) >= 2:  # 至少2个价格才认为是价格数组
                            # 返回最小价格（通常是基础票价）
                            min_price = min(prices)
                            if 200000 <= min_price <= 5000000:  # 合理价格范围
                                return min_price

            # 策略2: 递归搜索整个数据结构
            def recursive_price_search(obj, depth=0):
                if depth > 6:  # 限制递归深度
                    return []

                found_prices = []

                if isinstance(obj, list):
                    # 检查当前数组是否是价格数组
                    prices = extract_prices_from_array(obj)
                    if len(prices) >= 2:
                        found_prices.extend(prices)

                    # 递归搜索子元素
                    for item in obj:
                        found_prices.extend(recursive_price_search(item, depth + 1))

                return found_prices

            all_prices = recursive_price_search(data)

            if all_prices:
                # 过滤合理价格范围
                filtered_prices = [p for p in all_prices if 200000 <= p <= 5000000]
                if filtered_prices:
                    # 返回最小价格
                    return min(filtered_prices)

            return 0

        except Exception:
            return 0

    @staticmethod
    def _extract_price_deep_search(data: list) -> float:
        """
        Deep search for price information in various data structure positions.
        """
        try:
            # Search in different known positions where prices might be stored
            search_paths = [
                # Common price locations
                [1, 0, 0],
                [1, 1, 0],
                [1, 2, 0],
                # End of data arrays
                [-1, 0],
                [-1, 1],
                [-1, 2],
                # Nested price structures
                [0, -1, 0],
                [0, -1, 1],
                [0, -1, 2],
            ]

            for path in search_paths:
                price = SearchFlights._safe_get_nested(data, path, 0)
                if isinstance(price, (int, float)) and 1000 <= price <= 100000:
                    return price

            return 0

        except Exception:
            return 0

    @staticmethod
    def _safe_get_nested(data: any, path: list[int], default: any = None) -> any:
        """Safely access nested data structure with fallback.

        Args:
            data: The data structure to access
            path: List of indices/keys to traverse
            default: Default value if access fails

        Returns:
            The value at the specified path or default value

        """
        try:
            current = data
            for key in path:
                if hasattr(current, "__getitem__") and len(current) > key:
                    current = current[key]
                else:
                    return default
            return current
        except (IndexError, KeyError, TypeError):
            return default



    @staticmethod
    def _parse_airline_safe(flight_leg: list) -> Airline:
        """Safely parse airline from flight leg data.

        Args:
            flight_leg: Flight leg data from API

        Returns:
            Airline enum or default airline

        """
        try:
            # Try multiple possible locations for airline code
            airline_code = (
                SearchFlights._safe_get_nested(flight_leg, [22, 0])
                or SearchFlights._safe_get_nested(flight_leg, [0, 0])
                or SearchFlights._safe_get_nested(flight_leg, [1, 0])
                or "UNKNOWN"
            )
            return SearchFlights._parse_airline(airline_code)
        except Exception:
            # Return a default airline if parsing fails
            return Airline.UNKNOWN if hasattr(Airline, "UNKNOWN") else list(Airline)[0]

    @staticmethod
    def _parse_airport_safe(flight_leg: list, index: int) -> Airport:
        """Safely parse airport from flight leg data.

        Args:
            flight_leg: Flight leg data from API
            index: Index where airport code should be located

        Returns:
            Airport enum or default airport

        """
        try:
            airport_code = SearchFlights._safe_get_nested(flight_leg, [index])
            if airport_code:
                return SearchFlights._parse_airport(airport_code)
            # Try alternative locations
            for alt_index in [3, 4, 5, 6, 7]:
                airport_code = SearchFlights._safe_get_nested(flight_leg, [alt_index])
                if airport_code and isinstance(airport_code, str) and len(airport_code) == 3:
                    return SearchFlights._parse_airport(airport_code)
            # If all fails, return a default
            return list(Airport)[0]
        except Exception:
            return list(Airport)[0]

    @staticmethod
    def _parse_datetime_safe(
        flight_leg: list, date_path: list[int], time_path: list[int]
    ) -> datetime:
        """Safely parse datetime from flight leg data.

        Args:
            flight_leg: Flight leg data from API
            date_path: Path to date array
            time_path: Path to time array

        Returns:
            Parsed datetime or current datetime as fallback

        """
        try:
            date_arr = SearchFlights._safe_get_nested(flight_leg, date_path, [2025, 1, 1])
            time_arr = SearchFlights._safe_get_nested(flight_leg, time_path, [0, 0])

            if date_arr and time_arr:
                return SearchFlights._parse_datetime(date_arr, time_arr)
        except Exception:
            pass

        # Fallback to current datetime
        from datetime import datetime

        return datetime.now()

    @staticmethod
    def _parse_datetime(date_arr: list[int], time_arr: list[int]) -> datetime:
        """Convert date and time arrays to datetime.

        Args:
            date_arr: List of integers [year, month, day]
            time_arr: List of integers [hour, minute]

        Returns:
            Parsed datetime object

        Raises:
            ValueError: If arrays contain only None values

        """
        if not any(x is not None for x in date_arr) or not any(x is not None for x in time_arr):
            raise ValueError("Date and time arrays must contain at least one non-None value")

        return datetime(*(x or 0 for x in date_arr), *(x or 0 for x in time_arr))

    @staticmethod
    def _parse_airline(airline_code: str) -> Airline:
        """Convert airline code to Airline enum.

        Args:
            airline_code: Raw airline code from API

        Returns:
            Corresponding Airline enum value

        """
        if airline_code[0].isdigit():
            airline_code = f"_{airline_code}"
        return getattr(Airline, airline_code)

    @staticmethod
    def _parse_airport(airport_code: str) -> Airport:
        """Convert airport code to Airport enum.

        Args:
            airport_code: Raw airport code from API

        Returns:
            Corresponding Airport enum value

        """
        return getattr(Airport, airport_code)


class SearchKiwiFlights:
    """Kiwi hidden city flight search implementation with Google Flights compatible interface.

    This class provides the same interface as SearchFlights but searches for hidden city flights
    using Kiwi.com's API, making it easy to switch between Google Flights and Kiwi searches.
    """

    def __init__(self, localization_config: LocalizationConfig = None):
        """Initialize the Kiwi search client.

        Args:
            localization_config: Configuration for language and currency settings
        """
        self.localization_config = localization_config or LocalizationConfig()
        self.kiwi_client = KiwiFlightsAPI(localization_config)

    def search(
        self, filters: FlightSearchFilters, top_n: int = 5
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """Search for hidden city flights using the same interface as Google Flights.

        Args:
            filters: Flight search filters (same as Google Flights)
            top_n: Number of flights to return

        Returns:
            List of FlightResult objects or flight pairs for round-trip
        """
        # Run async search in sync context
        return asyncio.run(self._async_search(filters, top_n))

    async def _async_search(
        self, filters: FlightSearchFilters, top_n: int = 5
    ) -> list[FlightResult | tuple[FlightResult, FlightResult]] | None:
        """Async implementation of the search method."""
        try:
            # Extract search parameters from filters
            origin = filters.flight_segments[0].departure_airport[0][0].name
            destination = filters.flight_segments[0].arrival_airport[0][0].name
            departure_date = filters.flight_segments[0].travel_date
            adults = filters.passenger_info.adults

            # Convert seat type to cabin class
            cabin_class = self._convert_seat_type_to_cabin_class(filters.seat_type)

            if filters.trip_type == TripType.ONE_WAY:
                # Single trip search
                result = await self.kiwi_client.search_oneway_hidden_city(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    adults=adults,
                    limit=top_n,
                    cabin_class=cabin_class
                )

                if result.get("success"):
                    flights = []
                    for flight_data in result.get("flights", []):
                        # Return all flights, not just hidden city flights
                        # This allows users to see both regular and hidden city options
                        try:
                            flight_result = self._convert_kiwi_to_flight_result(flight_data)
                            flights.append(flight_result)
                        except Exception as e:
                            # Skip flights that can't be converted
                            continue
                    return flights[:top_n]

            elif filters.trip_type == TripType.ROUND_TRIP:
                # Round trip search
                if len(filters.flight_segments) < 2:
                    return None

                return_date = filters.flight_segments[1].travel_date
                result = await self.kiwi_client.search_roundtrip_hidden_city(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date,
                    adults=adults,
                    limit=top_n,
                    cabin_class=cabin_class
                )

                if result.get("success"):
                    flight_pairs = []
                    for flight_data in result.get("flights", []):
                        # Return all flights, not just hidden city flights
                        # This allows users to see both regular and hidden city options
                        try:
                            outbound = self._convert_kiwi_roundtrip_to_flight_result(
                                flight_data, "outbound"
                            )
                            inbound = self._convert_kiwi_roundtrip_to_flight_result(
                                flight_data, "inbound"
                            )
                            flight_pairs.append((outbound, inbound))
                        except Exception as e:
                            # Skip flights that can't be converted
                            continue
                    return flight_pairs[:top_n]

            return None

        except Exception as e:
            raise Exception(f"Kiwi search failed: {str(e)}") from e

    def _convert_kiwi_to_flight_result(self, kiwi_flight: dict) -> FlightResult:
        """Convert Kiwi flight data to FlightResult format with complete route information.

        Args:
            kiwi_flight: Flight data from Kiwi API

        Returns:
            FlightResult object compatible with Google Flights format
        """
        try:
            # Create flight legs for all segments
            legs = []
            route_segments = kiwi_flight.get("route_segments", [])

            if route_segments:
                # Multi-segment flight - create leg for each segment
                for segment in route_segments:
                    leg = FlightLeg(
                        airline=self._parse_airline_from_code(segment.get("carrier", "")),
                        flight_number=segment.get("flight_number", ""),
                        departure_airport=self._parse_airport_from_code(segment.get("from", "")),
                        arrival_airport=self._parse_airport_from_code(segment.get("to", "")),
                        departure_datetime=self._parse_kiwi_datetime(segment.get("departure_time", "")),
                        arrival_datetime=self._parse_kiwi_datetime(segment.get("arrival_time", "")),
                        duration=segment.get("duration", 0) // 60,  # Convert to minutes
                    )
                    legs.append(leg)
            else:
                # Single segment flight - fallback to original logic
                leg = FlightLeg(
                    airline=self._parse_airline_from_code(kiwi_flight.get("carrier_code", "")),
                    flight_number=kiwi_flight.get("flight_number", ""),
                    departure_airport=self._parse_airport_from_code(kiwi_flight.get("departure_airport", "")),
                    arrival_airport=self._parse_airport_from_code(kiwi_flight.get("arrival_airport", "")),
                    departure_datetime=self._parse_kiwi_datetime(kiwi_flight.get("departure_time", "")),
                    arrival_datetime=self._parse_kiwi_datetime(kiwi_flight.get("arrival_time", "")),
                    duration=kiwi_flight.get("duration_minutes", 0),
                )
                legs.append(leg)

            # Extract and convert price safely
            price_value = kiwi_flight.get("price", 0)
            if isinstance(price_value, str):
                try:
                    price_value = float(price_value)
                except (ValueError, TypeError):
                    price_value = 0
            elif price_value is None:
                price_value = 0

            # Create flight result
            flight_result = FlightResult(
                price=price_value,
                duration=kiwi_flight.get("duration_minutes", 0),
                stops=max(0, kiwi_flight.get("segment_count", 1) - 1),
                legs=legs,
                # Add hidden city information as metadata
                hidden_city_info={
                    "is_hidden_city": kiwi_flight.get("is_hidden_city", False),
                    "hidden_destination_code": kiwi_flight.get("hidden_destination_code", ""),
                    "hidden_destination_name": kiwi_flight.get("hidden_destination_name", ""),
                    "is_throwaway": kiwi_flight.get("is_throwaway", False),
                    "route_segments": route_segments,  # Include complete route info
                }
            )

            return flight_result

        except Exception as e:
            raise Exception(f"Failed to convert Kiwi flight data: {e}") from e

    def _convert_kiwi_roundtrip_to_flight_result(self, kiwi_flight: dict, direction: str) -> FlightResult:
        """Convert Kiwi round-trip flight data to FlightResult format.

        Args:
            kiwi_flight: Round-trip flight data from Kiwi API
            direction: "outbound" or "inbound"

        Returns:
            FlightResult object for the specified direction
        """
        try:
            leg_data = kiwi_flight.get(direction, {})

            # Create flight leg
            leg = FlightLeg(
                airline=self._parse_airline_from_code(leg_data.get("carrier_code", "")),
                flight_number=leg_data.get("flight_number", ""),
                departure_airport=self._parse_airport_from_code(leg_data.get("departure_airport", "")),
                arrival_airport=self._parse_airport_from_code(leg_data.get("arrival_airport", "")),
                departure_datetime=self._parse_kiwi_datetime(leg_data.get("departure_time", "")),
                arrival_datetime=self._parse_kiwi_datetime(leg_data.get("arrival_time", "")),
                duration=leg_data.get("duration", 0),
            )

            # Extract and convert price safely for round-trip
            total_price = kiwi_flight.get("total_price", 0)
            if total_price == 0:
                # Fallback to main price field
                total_price = kiwi_flight.get("price", 0)

            if isinstance(total_price, str):
                try:
                    total_price = float(total_price)
                except (ValueError, TypeError):
                    total_price = 0
            elif total_price is None:
                total_price = 0

            # Split price for each direction (outbound/inbound)
            direction_price = total_price / 2 if total_price > 0 else 0

            # Create flight result
            flight_result = FlightResult(
                price=direction_price,
                duration=leg_data.get("duration", 0),
                stops=0,  # Assuming direct flights for now
                legs=[leg],
                # Add hidden city information
                hidden_city_info={
                    "is_hidden_city": leg_data.get("is_hidden", False),
                    "hidden_destination_code": leg_data.get("hidden_destination_code", ""),
                    "hidden_destination_name": leg_data.get("hidden_destination_name", ""),
                    "direction": direction,
                    "total_price": total_price,  # Store total price for reference
                }
            )

            return flight_result

        except Exception as e:
            raise Exception(f"Failed to convert Kiwi round-trip flight data: {e}") from e

    def _parse_airline_from_code(self, airline_code: str) -> Airline:
        """Convert airline code to Airline enum.

        Args:
            airline_code: Airline code (e.g., "CA", "BA")

        Returns:
            Airline enum value or default
        """
        try:
            if not airline_code:
                return list(Airline)[0]  # Default airline

            # Handle numeric codes
            if airline_code[0].isdigit():
                airline_code = f"_{airline_code}"

            # Try to get the airline enum
            if hasattr(Airline, airline_code):
                return getattr(Airline, airline_code)
            else:
                # Return default if not found
                return list(Airline)[0]

        except Exception:
            return list(Airline)[0]

    def _parse_airport_from_code(self, airport_code: str) -> Airport:
        """Convert airport code to Airport enum.

        Args:
            airport_code: Airport code (e.g., "LHR", "PEK")

        Returns:
            Airport enum value or default
        """
        try:
            if not airport_code:
                return list(Airport)[0]  # Default airport

            # Try to get the airport enum
            if hasattr(Airport, airport_code):
                return getattr(Airport, airport_code)
            else:
                # Return default if not found
                return list(Airport)[0]

        except Exception:
            return list(Airport)[0]

    def _parse_kiwi_datetime(self, datetime_str: str) -> datetime:
        """Parse Kiwi datetime string to datetime object.

        Args:
            datetime_str: Datetime string from Kiwi API

        Returns:
            Parsed datetime object or current time as fallback
        """
        try:
            if not datetime_str:
                return datetime.now()

            # Try different datetime formats that Kiwi might use
            formats = [
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%SZ",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(datetime_str, fmt)
                except ValueError:
                    continue

            # If all formats fail, return current time
            return datetime.now()

        except Exception:
            return datetime.now()

    def _convert_seat_type_to_cabin_class(self, seat_type) -> str:
        """Convert SeatType enum to Kiwi API cabin class string.

        Args:
            seat_type: SeatType enum value

        Returns:
            Cabin class string for Kiwi API
        """
        # Import here to avoid circular imports
        from fli.models.google_flights.base import SeatType

        if seat_type == SeatType.BUSINESS:
            return "BUSINESS"
        elif seat_type == SeatType.FIRST:
            return "FIRST"
        else:
            return "ECONOMY"  # Default to economy
