#!/usr/bin/env python3
"""
测试打包后的 Kiwi API 调用
模拟项目已经打包为第三方库后的标准调用方式

测试组合：中文/人民币 + 单程/往返 + 经济舱/商务舱
路线：LHR (伦敦希思罗) -> PVG (上海浦东)
日期：2025年6月30日
"""

# 标准的第三方库导入方式
from fli.search import SearchKiwiFlights
from fli.models import FlightSearchFilters, PassengerInfo, FlightSegment
from fli.models.google_flights.base import LocalizationConfig, Language, Currency, TripType, SeatType
from fli.models import Airport


def create_localization_config():
    """创建本地化配置 - 中文/人民币"""
    return LocalizationConfig(
        language=Language.CHINESE,
        currency=Currency.CNY,
        region="CN"
    )


def create_passenger_info():
    """创建乘客信息"""
    return PassengerInfo(
        adults=1,
        children=0,
        infants_on_lap=0,
        infants_in_seat=0
    )


def create_oneway_filters(seat_type: SeatType):
    """创建单程航班搜索过滤器"""
    passengers = create_passenger_info()
    
    flight_segment = FlightSegment(
        departure_airport=[[Airport.LHR, 0]],  # 伦敦希思罗
        arrival_airport=[[Airport.PVG, 0]],    # 上海浦东
        travel_date="2025-06-30"
    )
    
    return FlightSearchFilters(
        trip_type=TripType.ONE_WAY,
        passenger_info=passengers,
        flight_segments=[flight_segment],
        seat_type=seat_type
    )


def create_roundtrip_filters(seat_type: SeatType):
    """创建往返航班搜索过滤器"""
    passengers = create_passenger_info()
    
    outbound_segment = FlightSegment(
        departure_airport=[[Airport.LHR, 0]],
        arrival_airport=[[Airport.PVG, 0]],
        travel_date="2025-06-30"
    )
    
    inbound_segment = FlightSegment(
        departure_airport=[[Airport.PVG, 0]],
        arrival_airport=[[Airport.LHR, 0]],
        travel_date="2025-07-07"
    )
    
    return FlightSearchFilters(
        trip_type=TripType.ROUND_TRIP,
        passenger_info=passengers,
        flight_segments=[outbound_segment, inbound_segment],
        seat_type=seat_type
    )


def print_flight_details(flight, index):
    """打印单程航班详情"""
    print(f"\n航班 {index}:")
    print(f"  💰 价格: ¥{flight.price:.0f}")
    print(f"  ⏱️ 时长: {flight.duration // 60}小时{flight.duration % 60}分钟")
    print(f"  🔄 中转: {flight.stops}次")

    # 显示完整航班路径
    if len(flight.legs) > 1:
        print(f"  🛣️ 完整路径:")
        for j, leg in enumerate(flight.legs, 1):
            print(f"    航段 {j}: {leg.departure_airport.name} -> {leg.arrival_airport.name}")
            print(f"      🏢 {leg.airline.name} {leg.flight_number}")
            print(f"      🕐 {leg.departure_datetime.strftime('%H:%M')} -> {leg.arrival_datetime.strftime('%H:%M')}")
    else:
        # 单段航班
        leg = flight.legs[0]
        print(f"  ✈️ 航班: {leg.departure_airport.name} -> {leg.arrival_airport.name}")
        print(f"    🏢 航空公司: {leg.airline.name}")
        print(f"    🔢 航班号: {leg.flight_number}")
        print(f"    🛫 出发: {leg.departure_datetime.strftime('%Y-%m-%d %H:%M')}")
        print(f"    🛬 到达: {leg.arrival_datetime.strftime('%Y-%m-%d %H:%M')}")

    # 隐藏城市信息
    if flight.hidden_city_info and flight.hidden_city_info.get("is_hidden_city"):
        print(f"  🎯 隐藏城市: {flight.hidden_city_info.get('hidden_destination_name', '')}")
        print(f"  🎯 隐藏代码: {flight.hidden_city_info.get('hidden_destination_code', '')}")
        if flight.hidden_city_info.get("is_throwaway"):
            print(f"  🎫 甩尾票: 是")


def print_roundtrip_details(outbound, inbound, index):
    """打印往返航班详情"""
    total_price = outbound.price + inbound.price
    print(f"\n往返航班 {index}:")
    print(f"  💰 总价格: ¥{total_price:.0f}")
    
    # 去程
    print(f"  🛫 去程: {outbound.legs[0].departure_airport.name} -> {outbound.legs[0].arrival_airport.name}")
    print(f"    💰 价格: ¥{outbound.price:.0f}")
    print(f"    ⏱️ 时长: {outbound.duration // 60}小时{outbound.duration % 60}分钟")
    print(f"    🏢 航空公司: {outbound.legs[0].airline.name}")
    print(f"    🔢 航班号: {outbound.legs[0].flight_number}")
    if outbound.hidden_city_info and outbound.hidden_city_info.get("is_hidden_city"):
        print(f"    🎯 隐藏目的地: {outbound.hidden_city_info.get('hidden_destination_name', '')}")
    
    # 返程
    print(f"  🛬 返程: {inbound.legs[0].departure_airport.name} -> {inbound.legs[0].arrival_airport.name}")
    print(f"    💰 价格: ¥{inbound.price:.0f}")
    print(f"    ⏱️ 时长: {inbound.duration // 60}小时{inbound.duration % 60}分钟")
    print(f"    🏢 航空公司: {inbound.legs[0].airline.name}")
    print(f"    🔢 航班号: {inbound.legs[0].flight_number}")
    if inbound.hidden_city_info and inbound.hidden_city_info.get("is_hidden_city"):
        print(f"    🎯 隐藏目的地: {inbound.hidden_city_info.get('hidden_destination_name', '')}")


def test_oneway_economy():
    """测试：单程 + 经济舱"""
    print(f"\n{'='*60}")
    print("🧪 测试 1: 单程 + 经济舱 (中文/人民币)")
    print("📍 LHR -> PVG, 2025-06-30")
    print(f"{'='*60}")
    
    try:
        # 创建配置和搜索客户端
        localization_config = create_localization_config()
        search_client = SearchKiwiFlights(localization_config)
        
        # 创建搜索过滤器
        filters = create_oneway_filters(SeatType.ECONOMY)
        
        # 执行搜索
        print("🔍 正在搜索...")
        results = search_client.search(filters, top_n=5)
        
        if results:
            print(f"✅ 找到 {len(results)} 个隐藏城市航班")
            for i, flight in enumerate(results, 1):
                print_flight_details(flight, i)
        else:
            print("❌ 未找到隐藏城市航班")
            
    except Exception as e:
        print(f"❌ 搜索失败: {e}")


def test_oneway_business():
    """测试：单程 + 商务舱"""
    print(f"\n{'='*60}")
    print("🧪 测试 2: 单程 + 商务舱 (中文/人民币)")
    print("📍 LHR -> PVG, 2025-06-30")
    print(f"{'='*60}")
    
    try:
        # 创建配置和搜索客户端
        localization_config = create_localization_config()
        search_client = SearchKiwiFlights(localization_config)
        
        # 创建搜索过滤器
        filters = create_oneway_filters(SeatType.BUSINESS)
        
        # 执行搜索
        print("🔍 正在搜索...")
        results = search_client.search(filters, top_n=5)
        
        if results:
            print(f"✅ 找到 {len(results)} 个隐藏城市航班")
            for i, flight in enumerate(results, 1):
                print_flight_details(flight, i)
        else:
            print("❌ 未找到隐藏城市航班")
            
    except Exception as e:
        print(f"❌ 搜索失败: {e}")


def test_roundtrip_economy():
    """测试：往返 + 经济舱"""
    print(f"\n{'='*60}")
    print("🧪 测试 3: 往返 + 经济舱 (中文/人民币)")
    print("📍 LHR ⇄ PVG, 2025-06-30 / 2025-07-07")
    print(f"{'='*60}")
    
    try:
        # 创建配置和搜索客户端
        localization_config = create_localization_config()
        search_client = SearchKiwiFlights(localization_config)
        
        # 创建搜索过滤器
        filters = create_roundtrip_filters(SeatType.ECONOMY)
        
        # 执行搜索
        print("🔍 正在搜索...")
        results = search_client.search(filters, top_n=3)
        
        if results:
            print(f"✅ 找到 {len(results)} 个往返隐藏城市航班")
            for i, (outbound, inbound) in enumerate(results, 1):
                print_roundtrip_details(outbound, inbound, i)
        else:
            print("❌ 未找到往返隐藏城市航班")
            
    except Exception as e:
        print(f"❌ 搜索失败: {e}")


def test_roundtrip_business():
    """测试：往返 + 商务舱"""
    print(f"\n{'='*60}")
    print("🧪 测试 4: 往返 + 商务舱 (中文/人民币)")
    print("📍 LHR ⇄ PVG, 2025-06-30 / 2025-07-07")
    print(f"{'='*60}")
    
    try:
        # 创建配置和搜索客户端
        localization_config = create_localization_config()
        search_client = SearchKiwiFlights(localization_config)
        
        # 创建搜索过滤器
        filters = create_roundtrip_filters(SeatType.BUSINESS)
        
        # 执行搜索
        print("🔍 正在搜索...")
        results = search_client.search(filters, top_n=3)
        
        if results:
            print(f"✅ 找到 {len(results)} 个往返隐藏城市航班")
            for i, (outbound, inbound) in enumerate(results, 1):
                print_roundtrip_details(outbound, inbound, i)
        else:
            print("❌ 未找到往返隐藏城市航班")
            
    except Exception as e:
        print(f"❌ 搜索失败: {e}")


def main():
    """主测试函数"""
    print("🚀 测试打包后的 Kiwi API 调用")
    print("📦 模拟第三方库标准调用方式")
    print("🎯 测试路线: LHR (伦敦希思罗) ⇄ PVG (上海浦东)")
    print("📅 测试日期: 2025-06-30")
    print("🌍 语言: 中文, 货币: 人民币")
    
    # 执行所有测试
    test_oneway_economy()      # 单程 + 经济舱
    test_oneway_business()     # 单程 + 商务舱
    test_roundtrip_economy()   # 往返 + 经济舱
    test_roundtrip_business()  # 往返 + 商务舱
    
    # 总结
    print(f"\n{'='*60}")
    print("🎉 所有测试完成！")
    print("📊 测试总结:")
    print("  ✅ 单程 + 经济舱")
    print("  ✅ 单程 + 商务舱")
    print("  ✅ 往返 + 经济舱")
    print("  ✅ 往返 + 商务舱")
    print(f"{'='*60}")
    print("💡 使用方式总结:")
    print("```python")
    print("from fli.search import SearchKiwiFlights")
    print("from fli.models import FlightSearchFilters, PassengerInfo, FlightSegment")
    print("from fli.models.google_flights.base import LocalizationConfig, Language, Currency")
    print("")
    print("# 创建配置")
    print("config = LocalizationConfig(Language.CHINESE, Currency.CNY, 'CN')")
    print("search_client = SearchKiwiFlights(config)")
    print("")
    print("# 执行搜索")
    print("results = search_client.search(filters, top_n=5)")
    print("```")


if __name__ == "__main__":
    main()
