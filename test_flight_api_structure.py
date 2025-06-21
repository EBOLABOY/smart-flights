#!/usr/bin/env python3
"""
测试航班搜索API返回的数据结构
"""

from fli.search import SearchFlights
from fli.models import (
    FlightSearchFilters, FlightSegment, Airport,
    SeatType, TripType, PassengerInfo
)
from fli.models.google_flights.base import LocalizationConfig, Language, Currency
import json
from datetime import datetime, timedelta

def test_flight_api_structure():
    """测试航班API返回的数据结构"""
    
    print('=== 航班搜索API数据结构测试 ===')
    print()

    # 创建本地化配置
    localization_config = LocalizationConfig(
        language=Language.CHINESE,
        currency=Currency.CNY,
        region="CN"
    )

    # 创建航班段 - 北京到洛杉矶
    future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    flight_segments = [
        FlightSegment(
            departure_airport=[[Airport.PEK, 0]],  # 北京首都国际机场
            arrival_airport=[[Airport.LAX, 0]],    # 洛杉矶国际机场
            travel_date=future_date
        )
    ]

    # 创建搜索过滤器
    filters = FlightSearchFilters(
        trip_type=TripType.ONE_WAY,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=flight_segments,
        seat_type=SeatType.ECONOMY
    )

    print(f'搜索条件:')
    print(f'  出发: {Airport.PEK.value} (北京首都国际机场)')
    print(f'  到达: {Airport.LAX.value} (洛杉矶国际机场)')
    print(f'  日期: {future_date}')
    print(f'  乘客: 1名成人')
    print(f'  舱位: 经济舱')
    print()

    try:
        # 初始化搜索客户端
        search = SearchFlights(localization_config=localization_config)
        
        print('正在搜索航班...')
        results = search.search(filters, top_n=2)  # 只获取前2个结果用于演示
        
        if results:
            print(f'✅ 找到 {len(results)} 个航班结果')
            print()
            
            for i, flight in enumerate(results, 1):
                print(f'=== 航班结果 {i} ===')
                print(f'FlightResult 对象结构:')
                print(f'  price: {flight.price} (价格)')
                print(f'  duration: {flight.duration} 分钟 (总飞行时长)')
                print(f'  stops: {flight.stops} (中转次数)')
                print(f'  legs: {len(flight.legs)} 个航班段')
                print()
                
                print(f'航班段详情:')
                for j, leg in enumerate(flight.legs, 1):
                    print(f'  === 航班段 {j} (FlightLeg) ===')
                    print(f'    airline: {leg.airline} (航空公司枚举)')
                    print(f'    flight_number: "{leg.flight_number}" (航班号)')
                    print(f'    departure_airport: {leg.departure_airport} (出发机场枚举)')
                    print(f'    arrival_airport: {leg.arrival_airport} (到达机场枚举)')
                    print(f'    departure_datetime: {leg.departure_datetime} (出发时间)')
                    print(f'    arrival_datetime: {leg.arrival_datetime} (到达时间)')
                    print(f'    duration: {leg.duration} 分钟 (航段飞行时长)')
                    print()
                
                # 显示JSON格式的数据结构
                print(f'JSON格式数据结构:')
                flight_dict = {
                    "price": flight.price,
                    "duration": flight.duration,
                    "stops": flight.stops,
                    "legs": [
                        {
                            "airline": leg.airline.name,
                            "airline_value": leg.airline.value,
                            "flight_number": leg.flight_number,
                            "departure_airport": leg.departure_airport.name,
                            "departure_airport_value": leg.departure_airport.value,
                            "arrival_airport": leg.arrival_airport.name,
                            "arrival_airport_value": leg.arrival_airport.value,
                            "departure_datetime": leg.departure_datetime.isoformat(),
                            "arrival_datetime": leg.arrival_datetime.isoformat(),
                            "duration": leg.duration
                        }
                        for leg in flight.legs
                    ]
                }
                print(json.dumps(flight_dict, ensure_ascii=False, indent=2))
                print('-' * 50)
                
        else:
            print('❌ 没有找到航班结果')
            
    except Exception as e:
        print(f'❌ 搜索失败: {e}')
        print('这可能是因为:')
        print('1. 网络连接问题')
        print('2. Google Flights API限制')
        print('3. 搜索参数问题')

if __name__ == "__main__":
    test_flight_api_structure()
