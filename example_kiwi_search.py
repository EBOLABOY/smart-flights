#!/usr/bin/env python3
"""
示例：使用与 Google Flights 相同的接口调用 Kiwi API 搜索隐藏城市航班

这个示例展示了如何使用 SearchKiwiFlights 类，它与 SearchFlights 有完全相同的接口，
但专门搜索隐藏城市航班。
"""

from datetime import datetime, timedelta

from fli.models import (
    Airport,
    FlightSearchFilters,
    FlightSegment,
    PassengerInfo,
    SeatType,
    TripType,
)
from fli.models.google_flights.base import LocalizationConfig, Language, Currency
from fli.search import SearchKiwiFlights


def create_oneway_search_filters():
    """创建单程航班搜索过滤器 - 与 Google Flights 完全相同的格式"""
    
    # 乘客信息
    passengers = PassengerInfo(
        adults=1,
        children=0,
        infants_on_lap=0,
        infants_in_seat=0
    )
    
    # 航班段
    departure_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    flight_segment = FlightSegment(
        departure_airport=[[Airport.LHR, 0]],  # 伦敦希思罗
        arrival_airport=[[Airport.PEK, 0]],    # 北京首都
        travel_date=departure_date
    )
    
    # 搜索过滤器
    filters = FlightSearchFilters(
        trip_type=TripType.ONE_WAY,
        passenger_info=passengers,
        flight_segments=[flight_segment],
        seat_type=SeatType.ECONOMY  # 或 SeatType.BUSINESS
    )
    
    return filters


def create_roundtrip_search_filters():
    """创建往返航班搜索过滤器 - 与 Google Flights 完全相同的格式"""
    
    # 乘客信息
    passengers = PassengerInfo(
        adults=1,
        children=0,
        infants_on_lap=0,
        infants_in_seat=0
    )
    
    # 航班段
    departure_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    return_date = (datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d")
    
    outbound_segment = FlightSegment(
        departure_airport=[[Airport.LHR, 0]],
        arrival_airport=[[Airport.PEK, 0]],
        travel_date=departure_date
    )
    
    inbound_segment = FlightSegment(
        departure_airport=[[Airport.PEK, 0]],
        arrival_airport=[[Airport.LHR, 0]],
        travel_date=return_date
    )
    
    # 搜索过滤器
    filters = FlightSearchFilters(
        trip_type=TripType.ROUND_TRIP,
        passenger_info=passengers,
        flight_segments=[outbound_segment, inbound_segment],
        seat_type=SeatType.ECONOMY
    )
    
    return filters


def main():
    """主函数 - 演示如何使用 Kiwi API 与 Google Flights 相同的接口"""
    
    print("🔍 Kiwi 隐藏城市航班搜索示例")
    print("使用与 Google Flights 完全相同的接口")
    print("=" * 60)
    
    # 配置中文和人民币
    config = LocalizationConfig(
        language=Language.CHINESE,
        currency=Currency.CNY,
        region="CN"
    )
    
    # 创建 Kiwi 搜索客户端 - 与 Google Flights 相同的接口
    kiwi_search = SearchKiwiFlights(localization_config=config)
    
    # 示例 1: 单程航班搜索
    print("\n1️⃣ 单程隐藏城市航班搜索")
    print("-" * 30)
    
    try:
        # 创建搜索过滤器 - 与 Google Flights 完全相同
        oneway_filters = create_oneway_search_filters()
        
        # 执行搜索 - 与 Google Flights 完全相同的方法调用
        oneway_results = kiwi_search.search(oneway_filters, top_n=5)
        
        if oneway_results:
            print(f"✅ 找到 {len(oneway_results)} 个隐藏城市航班")
            
            for i, flight in enumerate(oneway_results, 1):
                print(f"\n航班 {i}:")
                print(f"  价格: ¥{flight.price}")
                print(f"  时长: {flight.duration} 分钟")
                print(f"  中转: {flight.stops} 次")
                
                # 显示航班段信息
                for j, leg in enumerate(flight.legs, 1):
                    print(f"  航段 {j}: {leg.departure_airport.name} -> {leg.arrival_airport.name}")
                    print(f"    航空公司: {leg.airline.name}")
                    print(f"    航班号: {leg.flight_number}")
                    print(f"    出发: {leg.departure_datetime}")
                    print(f"    到达: {leg.arrival_datetime}")
                
                # 显示隐藏城市信息
                if flight.hidden_city_info:
                    hc_info = flight.hidden_city_info
                    if hc_info.get("is_hidden_city"):
                        print(f"  🎯 隐藏城市: {hc_info.get('hidden_destination_name', '')}")
                        print(f"  🎯 隐藏代码: {hc_info.get('hidden_destination_code', '')}")
        else:
            print("❌ 未找到隐藏城市航班")
            
    except Exception as e:
        print(f"❌ 单程搜索失败: {e}")
    
    # 示例 2: 往返航班搜索
    print("\n\n2️⃣ 往返隐藏城市航班搜索")
    print("-" * 30)
    
    try:
        # 创建往返搜索过滤器
        roundtrip_filters = create_roundtrip_search_filters()
        
        # 执行搜索 - 与 Google Flights 完全相同的方法调用
        roundtrip_results = kiwi_search.search(roundtrip_filters, top_n=3)
        
        if roundtrip_results:
            print(f"✅ 找到 {len(roundtrip_results)} 个往返隐藏城市航班")
            
            for i, (outbound, inbound) in enumerate(roundtrip_results, 1):
                total_price = outbound.price + inbound.price
                print(f"\n往返航班 {i}:")
                print(f"  总价格: ¥{total_price}")
                
                print(f"  去程: {outbound.legs[0].departure_airport.name} -> {outbound.legs[0].arrival_airport.name}")
                print(f"    价格: ¥{outbound.price}, 时长: {outbound.duration} 分钟")
                if outbound.hidden_city_info and outbound.hidden_city_info.get("is_hidden_city"):
                    print(f"    🎯 隐藏目的地: {outbound.hidden_city_info.get('hidden_destination_name', '')}")
                
                print(f"  返程: {inbound.legs[0].departure_airport.name} -> {inbound.legs[0].arrival_airport.name}")
                print(f"    价格: ¥{inbound.price}, 时长: {inbound.duration} 分钟")
                if inbound.hidden_city_info and inbound.hidden_city_info.get("is_hidden_city"):
                    print(f"    🎯 隐藏目的地: {inbound.hidden_city_info.get('hidden_destination_name', '')}")
        else:
            print("❌ 未找到往返隐藏城市航班")
            
    except Exception as e:
        print(f"❌ 往返搜索失败: {e}")
    
    print("\n" + "=" * 60)
    print("✨ 搜索完成！")
    print("💡 提示：您可以像使用 Google Flights 一样使用 SearchKiwiFlights")
    print("💡 只需将 SearchFlights 替换为 SearchKiwiFlights 即可搜索隐藏城市航班")


if __name__ == "__main__":
    main()
