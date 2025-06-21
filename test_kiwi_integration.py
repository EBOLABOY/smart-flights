#!/usr/bin/env python3
"""
测试 Kiwi API 集成功能
验证单程和往返隐藏城市航班搜索，以及中英文和货币切换功能
基于项目现有架构，测试新集成的 Kiwi API 功能
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta

# 导入项目中的本地化配置和新的 Kiwi API
from fli.models.google_flights.base import LocalizationConfig, Language, Currency
from fli.api.kiwi_oneway import KiwiOnewayAPI
from fli.api.kiwi_roundtrip import KiwiRoundtripAPI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_oneway_chinese_cny():
    """测试单程航班搜索 - 中文界面，人民币"""
    print("\n" + "="*60)
    print("测试 1: 单程隐藏城市航班搜索 (中文/人民币)")
    print("="*60)
    
    # 配置中文和人民币
    config = LocalizationConfig(
        language=Language.CHINESE,
        currency=Currency.CNY,
        region="CN"
    )
    
    # 创建API实例
    api = KiwiOnewayAPI(config)
    
    # 搜索参数
    origin = "LHR"  # 伦敦希思罗
    destination = "PVG"  # 北京
    departure_date = "2025-06-30"

    print(f"搜索路线: {origin} -> {destination}")
    print(f"出发日期: {departure_date}")
    print(f"语言: 中文, 货币: 人民币")
    
    try:
        result = await api.search_hidden_city_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            adults=1,
            limit=5
        )
        
        if result.get("success"):
            print(f"\n✅ 搜索成功!")
            print(f"总航班数: {result['results']['total_found']}")
            print(f"找到隐藏城市航班: {result['results']['hidden_city_count']} 个")
            print(f"返回的隐藏城市航班: {len(result['results']['flights'])} 个")

            if result['results']['flights']:
                for i, flight in enumerate(result['results']['flights'][:3], 1):
                    print(f"\n航班 {i}:")
                    print(f"  价格: {flight['currency_symbol']}{flight['price']}")
                    print(f"  时长: {flight['duration_hours']} 小时")
                    print(f"  航线: {flight['departure_airport_name']} -> {flight['arrival_airport_name']}")
                    print(f"  隐藏目的地: {flight['hidden_destination_name']}")
                    print(f"  航空公司: {flight['carrier_name']}")
                    print(f"  {flight['savings_info']}")
            else:
                print("  没有找到隐藏城市航班，但找到了常规航班")
        else:
            print(f"❌ 搜索失败: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")


async def test_oneway_english_usd():
    """测试单程航班搜索 - 英文界面，美元"""
    print("\n" + "="*60)
    print("测试 2: 单程隐藏城市航班搜索 (英文/美元)")
    print("="*60)
    
    # 配置英文和美元
    config = LocalizationConfig(
        language=Language.ENGLISH,
        currency=Currency.USD,
        region="US"
    )
    
    # 创建API实例
    api = KiwiOnewayAPI(config)
    
    # 搜索参数
    origin = "LHR"  # 伦敦希思罗
    destination = "PVG"  # 北京
    departure_date = "2025-06-30"

    print(f"Search route: {origin} -> {destination}")
    print(f"Departure date: {departure_date}")
    print(f"Language: English, Currency: USD")
    
    try:
        result = await api.search_hidden_city_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            adults=1,
            limit=5
        )
        
        if result.get("success"):
            print(f"\n✅ Search successful!")
            print(f"Total flights found: {result['results']['total_found']}")
            print(f"Hidden city flights found: {result['results']['hidden_city_count']}")
            print(f"Returned hidden city flights: {len(result['results']['flights'])}")

            if result['results']['flights']:
                for i, flight in enumerate(result['results']['flights'][:3], 1):
                    print(f"\nFlight {i}:")
                    print(f"  Price: {flight['currency_symbol']}{flight['price']}")
                    print(f"  Duration: {flight['duration_hours']} hours")
                    print(f"  Route: {flight['departure_airport_name']} -> {flight['arrival_airport_name']}")
                    print(f"  Hidden destination: {flight['hidden_destination_name']}")
                    print(f"  Carrier: {flight['carrier_name']}")
                    print(f"  {flight['savings_info']}")
            else:
                print("  No hidden city flights found, but regular flights were found")
        else:
            print(f"❌ Search failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Test exception: {e}")


async def test_roundtrip_chinese_cny():
    """测试往返航班搜索 - 中文界面，人民币"""
    print("\n" + "="*60)
    print("测试 3: 往返隐藏城市航班搜索 (中文/人民币)")
    print("="*60)
    
    # 配置中文和人民币
    config = LocalizationConfig(
        language=Language.CHINESE,
        currency=Currency.CNY,
        region="CN"
    )
    
    # 创建API实例
    api = KiwiRoundtripAPI(config)
    
    # 搜索参数
    origin = "LHR"  # 伦敦希思罗
    destination = "PVG"  # 北京
    departure_date = "2025-06-30"
    return_date = "2025-07-07"

    print(f"搜索路线: {origin} ⇄ {destination}")
    print(f"出发日期: {departure_date}")
    print(f"返回日期: {return_date}")
    print(f"语言: 中文, 货币: 人民币")
    
    try:
        result = await api.search_hidden_city_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=1,
            limit=3
        )
        
        if result.get("success"):
            print(f"\n✅ 搜索成功!")
            print(f"找到隐藏城市往返航班: {result['results']['hidden_city_count']} 个")
            
            for i, flight in enumerate(result['results']['flights'][:2], 1):
                print(f"\n往返航班 {i}:")
                print(f"  总价格: {flight['currency_symbol']}{flight['total_price']}")
                print(f"  总时长: {flight['total_duration_hours']} 小时")
                
                print(f"  去程: {flight['outbound']['departure_airport']} -> {flight['outbound']['arrival_airport']}")
                print(f"    隐藏目的地: {flight['outbound']['hidden_destination_name']}")
                print(f"    航空公司: {flight['outbound']['carrier_name']}")
                
                print(f"  返程: {flight['inbound']['departure_airport']} -> {flight['inbound']['arrival_airport']}")
                print(f"    隐藏目的地: {flight['inbound']['hidden_destination_name']}")
                print(f"    航空公司: {flight['inbound']['carrier_name']}")
                
                print(f"  {flight['savings_info']}")
        else:
            print(f"❌ 搜索失败: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")


async def test_validation():
    """测试参数验证功能"""
    print("\n" + "="*60)
    print("测试 4: 参数验证功能")
    print("="*60)
    
    api = KiwiOnewayAPI()
    
    # 测试无效的机场代码
    print("测试无效机场代码...")
    result = await api.search_hidden_city_flights("XX", "YYY", "2025-12-01")
    print(f"结果: {result.get('error', '未知错误')}")

    # 测试过去的日期
    print("\n测试过去的日期...")
    past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    result = await api.search_hidden_city_flights("LHR", "PEK", past_date)
    print(f"结果: {result.get('error', '未知错误')}")

    # 测试相同的出发和到达机场
    print("\n测试相同的出发和到达机场...")
    result = await api.search_hidden_city_flights("LHR", "LHR", "2025-06-30")
    print(f"结果: {result.get('error', '未知错误')}")


def save_test_results(results: dict, filename: str):
    """保存测试结果到文件"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n📁 测试结果已保存到: {filename}")
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")


async def main():
    """主测试函数"""
    print("🚀 开始测试 Kiwi API 集成功能")
    print("测试包括: 单程/往返航班搜索, 中英文切换, 货币转换, 参数验证")
    
    # 运行所有测试
    await test_oneway_chinese_cny()
    await test_oneway_english_usd()
    await test_roundtrip_chinese_cny()
    await test_validation()
    
    print("\n" + "="*60)
    print("🎉 所有测试完成!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
