#!/usr/bin/env python3
"""
全面测试 Kiwi API 隐藏城市航班搜索
测试组合：中文/人民币 + 单程/往返 + 经济舱/商务舱
路线：LHR (伦敦希思罗) -> PVG (上海浦东)
日期：2025年6月30日
"""

from datetime import datetime
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


def create_search_filters(trip_type: TripType, seat_type: SeatType):
    """创建搜索过滤器
    
    Args:
        trip_type: 行程类型（单程/往返）
        seat_type: 舱位类型（经济舱/商务舱）
    """
    # 乘客信息
    passengers = PassengerInfo(
        adults=1,
        children=0,
        infants_on_lap=0,
        infants_in_seat=0
    )
    
    # 出发日期
    departure_date = "2025-06-30"
    
    # 出发航段
    outbound_segment = FlightSegment(
        departure_airport=[[Airport.LHR, 0]],  # 伦敦希思罗
        arrival_airport=[[Airport.PVG, 0]],    # 上海浦东
        travel_date=departure_date
    )
    
    flight_segments = [outbound_segment]
    
    # 如果是往返，添加返程航段
    if trip_type == TripType.ROUND_TRIP:
        return_date = "2025-07-07"  # 返程日期
        inbound_segment = FlightSegment(
            departure_airport=[[Airport.PVG, 0]],  # 上海浦东
            arrival_airport=[[Airport.LHR, 0]],    # 伦敦希思罗
            travel_date=return_date
        )
        flight_segments.append(inbound_segment)
    
    # 创建搜索过滤器
    filters = FlightSearchFilters(
        trip_type=trip_type,
        passenger_info=passengers,
        flight_segments=flight_segments,
        seat_type=seat_type
    )
    
    return filters


def format_flight_info(flight, index, trip_type):
    """格式化航班信息显示"""
    info = []
    info.append(f"航班 {index}:")
    info.append(f"  💰 价格: ¥{flight.price:.0f}")
    info.append(f"  ⏱️ 时长: {flight.duration // 60}小时{flight.duration % 60}分钟")
    info.append(f"  🔄 中转: {flight.stops}次")
    
    # 航班段信息
    for j, leg in enumerate(flight.legs, 1):
        info.append(f"  ✈️ 航段 {j}: {leg.departure_airport.name} -> {leg.arrival_airport.name}")
        info.append(f"    🏢 航空公司: {leg.airline.name}")
        info.append(f"    🔢 航班号: {leg.flight_number}")
        info.append(f"    🛫 出发: {leg.departure_datetime.strftime('%Y-%m-%d %H:%M')}")
        info.append(f"    🛬 到达: {leg.arrival_datetime.strftime('%Y-%m-%d %H:%M')}")
    
    # 隐藏城市信息
    if flight.hidden_city_info:
        hc_info = flight.hidden_city_info
        if hc_info.get("is_hidden_city"):
            info.append(f"  🎯 隐藏城市: {hc_info.get('hidden_destination_name', '')}")
            info.append(f"  🎯 隐藏代码: {hc_info.get('hidden_destination_code', '')}")
            if hc_info.get("is_throwaway"):
                info.append(f"  🎫 甩尾票: 是")
        else:
            info.append(f"  ❌ 非隐藏城市航班")
    
    return "\n".join(info)


def format_roundtrip_info(outbound, inbound, index):
    """格式化往返航班信息显示"""
    total_price = outbound.price + inbound.price
    info = []
    info.append(f"往返航班 {index}:")
    info.append(f"  💰 总价格: ¥{total_price:.0f}")
    
    # 去程信息
    info.append(f"  🛫 去程: {outbound.legs[0].departure_airport.name} -> {outbound.legs[0].arrival_airport.name}")
    info.append(f"    💰 价格: ¥{outbound.price:.0f}")
    info.append(f"    ⏱️ 时长: {outbound.duration // 60}小时{outbound.duration % 60}分钟")
    info.append(f"    🏢 航空公司: {outbound.legs[0].airline.name}")
    info.append(f"    🔢 航班号: {outbound.legs[0].flight_number}")
    info.append(f"    🕐 出发: {outbound.legs[0].departure_datetime.strftime('%Y-%m-%d %H:%M')}")
    
    if outbound.hidden_city_info and outbound.hidden_city_info.get("is_hidden_city"):
        info.append(f"    🎯 隐藏目的地: {outbound.hidden_city_info.get('hidden_destination_name', '')}")
    
    # 返程信息
    info.append(f"  🛬 返程: {inbound.legs[0].departure_airport.name} -> {inbound.legs[0].arrival_airport.name}")
    info.append(f"    💰 价格: ¥{inbound.price:.0f}")
    info.append(f"    ⏱️ 时长: {inbound.duration // 60}小时{inbound.duration % 60}分钟")
    info.append(f"    🏢 航空公司: {inbound.legs[0].airline.name}")
    info.append(f"    🔢 航班号: {inbound.legs[0].flight_number}")
    info.append(f"    🕐 出发: {inbound.legs[0].departure_datetime.strftime('%Y-%m-%d %H:%M')}")
    
    if inbound.hidden_city_info and inbound.hidden_city_info.get("is_hidden_city"):
        info.append(f"    🎯 隐藏目的地: {inbound.hidden_city_info.get('hidden_destination_name', '')}")
    
    return "\n".join(info)


def test_search_combination(trip_type: TripType, seat_type: SeatType):
    """测试特定组合的搜索"""
    
    # 确定测试标题
    trip_name = "单程" if trip_type == TripType.ONE_WAY else "往返"
    seat_name = "经济舱" if seat_type == SeatType.ECONOMY else "商务舱"
    
    print(f"\n{'='*60}")
    print(f"🧪 测试：{trip_name} + {seat_name} (中文/人民币)")
    print(f"📍 路线: LHR (伦敦希思罗) -> PVG (上海浦东)")
    print(f"📅 日期: 2025-06-30" + (" (去程), 2025-07-07 (返程)" if trip_type == TripType.ROUND_TRIP else ""))
    print(f"{'='*60}")
    
    try:
        # 配置中文和人民币
        config = LocalizationConfig(
            language=Language.CHINESE,
            currency=Currency.CNY,
            region="CN"
        )
        
        # 创建搜索客户端
        search_client = SearchKiwiFlights(localization_config=config)
        
        # 创建搜索过滤器
        filters = create_search_filters(trip_type, seat_type)
        
        # 执行搜索
        print("🔍 正在搜索...")
        results = search_client.search(filters, top_n=5)
        
        if results:
            print(f"✅ 找到 {len(results)} 个隐藏城市航班")
            
            if trip_type == TripType.ONE_WAY:
                # 单程航班结果
                for i, flight in enumerate(results, 1):
                    print(f"\n{format_flight_info(flight, i, trip_type)}")
            else:
                # 往返航班结果
                for i, (outbound, inbound) in enumerate(results, 1):
                    print(f"\n{format_roundtrip_info(outbound, inbound, i)}")
        else:
            print("❌ 未找到隐藏城市航班")
            print("💡 这可能意味着该路线/舱位/日期组合没有隐藏城市机会")
            
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")


def main():
    """主测试函数"""
    print("🚀 Kiwi API 隐藏城市航班全面测试")
    print("🎯 测试所有组合：单程/往返 × 经济舱/商务舱")
    print("🌍 语言: 中文, 货币: 人民币")
    print("📍 路线: LHR (伦敦希思罗) ⇄ PVG (上海浦东)")
    print("📅 日期: 2025-06-30")
    
    # 测试组合列表
    test_combinations = [
        (TripType.ONE_WAY, SeatType.ECONOMY),    # 单程 + 经济舱
        (TripType.ONE_WAY, SeatType.BUSINESS),   # 单程 + 商务舱
        (TripType.ROUND_TRIP, SeatType.ECONOMY), # 往返 + 经济舱
        (TripType.ROUND_TRIP, SeatType.BUSINESS) # 往返 + 商务舱
    ]
    
    # 执行所有测试
    for trip_type, seat_type in test_combinations:
        test_search_combination(trip_type, seat_type)
    
    # 总结
    print(f"\n{'='*60}")
    print("🎉 所有测试完成！")
    print("📊 测试总结:")
    print("  ✅ 单程 + 经济舱")
    print("  ✅ 单程 + 商务舱") 
    print("  ✅ 往返 + 经济舱")
    print("  ✅ 往返 + 商务舱")
    print(f"{'='*60}")
    print("💡 提示：")
    print("  - 隐藏城市航班的可用性取决于具体的路线、日期和舱位")
    print("  - 商务舱的隐藏城市机会通常比经济舱少")
    print("  - 往返航班的隐藏城市机会通常比单程少")
    print("  - 不同日期可能有不同的结果")


if __name__ == "__main__":
    main()
