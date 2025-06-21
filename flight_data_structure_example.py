#!/usr/bin/env python3
"""
航班搜索API返回数据结构说明和示例
"""

from fli.models import FlightResult, FlightLeg, Airport, Airline
from datetime import datetime
import json

def show_flight_data_structure():
    """展示航班API返回的数据结构"""
    
    print('=== 航班搜索API返回数据结构 ===')
    print()
    
    print('1. 主要数据模型:')
    print('   - FlightResult: 完整的航班搜索结果')
    print('   - FlightLeg: 单个航班段信息')
    print('   - Airport: 机场枚举')
    print('   - Airline: 航空公司枚举')
    print()
    
    print('2. FlightResult 结构:')
    print('''
    class FlightResult(BaseModel):
        legs: list[FlightLeg]        # 航班段列表
        price: NonNegativeFloat      # 价格（指定货币）
        duration: PositiveInt        # 总飞行时长（分钟）
        stops: NonNegativeInt        # 中转次数
    ''')
    
    print('3. FlightLeg 结构:')
    print('''
    class FlightLeg(BaseModel):
        airline: Airline             # 航空公司（枚举）
        flight_number: str           # 航班号
        departure_airport: Airport   # 出发机场（枚举）
        arrival_airport: Airport     # 到达机场（枚举）
        departure_datetime: datetime # 出发时间
        arrival_datetime: datetime   # 到达时间
        duration: PositiveInt        # 航段飞行时长（分钟）
    ''')
    
    print('4. 示例数据结构（模拟）:')
    
    # 创建示例数据
    example_leg1 = {
        "airline": "CA",  # 中国国际航空
        "airline_name": "中国国际航空",
        "flight_number": "CA987",
        "departure_airport": "PEK",
        "departure_airport_name": "北京首都国际机场",
        "arrival_airport": "LAX", 
        "arrival_airport_name": "洛杉矶国际机场",
        "departure_datetime": "2025-07-15T14:30:00",
        "arrival_datetime": "2025-07-15T10:45:00",  # 跨时区
        "duration": 780  # 13小时
    }
    
    example_flight = {
        "price": 8500.0,  # CNY
        "duration": 780,  # 总时长13小时
        "stops": 0,       # 直飞
        "legs": [example_leg1]
    }
    
    print('单程直飞示例:')
    print(json.dumps(example_flight, ensure_ascii=False, indent=2))
    print()
    
    # 中转航班示例
    example_leg2_1 = {
        "airline": "CA",
        "airline_name": "中国国际航空", 
        "flight_number": "CA123",
        "departure_airport": "PEK",
        "departure_airport_name": "北京首都国际机场",
        "arrival_airport": "NRT",
        "arrival_airport_name": "东京成田国际机场", 
        "departure_datetime": "2025-07-15T08:30:00",
        "arrival_datetime": "2025-07-15T12:45:00",
        "duration": 195  # 3小时15分
    }
    
    example_leg2_2 = {
        "airline": "AA",
        "airline_name": "美国航空",
        "flight_number": "AA456", 
        "departure_airport": "NRT",
        "departure_airport_name": "东京成田国际机场",
        "arrival_airport": "LAX",
        "arrival_airport_name": "洛杉矶国际机场",
        "departure_datetime": "2025-07-15T16:20:00", 
        "arrival_datetime": "2025-07-15T09:35:00",  # 跨日期线
        "duration": 615  # 10小时15分
    }
    
    example_connecting_flight = {
        "price": 6800.0,  # CNY
        "duration": 1290, # 总时长21.5小时（包含中转时间）
        "stops": 1,       # 1次中转
        "legs": [example_leg2_1, example_leg2_2]
    }
    
    print('中转航班示例:')
    print(json.dumps(example_connecting_flight, ensure_ascii=False, indent=2))
    print()
    
    print('5. 往返航班结构:')
    print('   往返航班搜索会返回 List[Tuple[FlightResult, FlightResult]]')
    print('   - 第一个FlightResult: 去程航班')
    print('   - 第二个FlightResult: 返程航班')
    print()
    
    print('6. 数据访问示例:')
    print('''
    # 访问航班信息
    for flight in results:
        print(f"价格: ¥{flight.price}")
        print(f"总时长: {flight.duration // 60}小时{flight.duration % 60}分钟")
        print(f"中转次数: {flight.stops}")
        
        for i, leg in enumerate(flight.legs):
            print(f"航段{i+1}: {leg.airline.value} {leg.flight_number}")
            print(f"  {leg.departure_airport.value} -> {leg.arrival_airport.value}")
            print(f"  {leg.departure_datetime} -> {leg.arrival_datetime}")
    ''')
    
    print('7. 本地化支持:')
    print('   - 价格货币: 根据LocalizationConfig设置（USD/CNY）')
    print('   - 航空公司名称: 支持中英文显示')
    print('   - 机场名称: 通过机场搜索API获取本地化名称')
    print('   - 时间格式: 标准ISO格式，可根据需要格式化')

if __name__ == "__main__":
    show_flight_data_structure()
