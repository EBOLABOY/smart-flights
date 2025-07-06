# Smart Flights 🛫

一个强大的 Python 库，提供对 Google Flights 数据的编程访问，配备优雅的命令行界面。轻松搜索航班、寻找最优惠价格并筛选结果。

> 🚀 **Smart Flights 的特别之处**
> 与其他依赖网页抓取的航班搜索库不同，Smart Flights 通过逆向工程直接与 Google Flights API 交互。
> 这意味着：
> - **快速**：直接 API 访问意味着更快、更可靠的结果
> - **零抓取**：无需 HTML 解析，无需浏览器自动化，纯 API 交互
> - **可靠**：不易因 UI 变化而中断
> - **模块化**：可扩展架构，便于自定义和集成
> - **智能增强**：在原有功能基础上增加了中英文双语支持、机场搜索等智能功能

## 📜 致谢与来源

本项目基于优秀的开发源项目 [**Fli**](https://github.com/punitarani/fli) 进行改编和增强。

**原始项目**：
- **项目名称**：Fli
- **原作者**：[punitarani](https://github.com/punitarani)
- **原始仓库**：https://github.com/punitarani/fli
- **许可证证**：MIT License

**Smart Flights 的增强功能**：
- 🌍 **中英文双语支持** - 完整的本地化界面和数据
- 🏢 **机场搜索 API** - 智能机场查询和搜索功能
- 🎯 **隐藏城市航班段搜索** - 集成 Kiwi.com API，发现隐藏城市机票优惠
- 📚 **完整文档** - 详细的 API 参考考和使用指南
- 🎯 **优化体验** - 更好的 CLI 界面和错误处理
- 📦 **包名优化** - 更直观的 `smart-flights` 包名

我们感谢原作者 punitarani 的杰出工作，为航班段搜索领域提供了如此优秀的基础框架。本项目在遵循 MIT 许可证证的前提下，致力于为中文用户和国际用户提供更好的使用体验。

![CLI 演示](https://github.com/punitarani/fli/blob/main/data/cli-demo.png)

## 📖 目录

- [🚀 快速开始发始](#快速开始发始)
- [🎯 功能特性性](#功能特性性)
- [🖥️ CLI 使用方法：](#cli-使用方法：)
- [🖥️ 完整 CLI 命令参考考考](#完整-cli-命令参考考
- [🎯 隐藏城市航班段搜索](#隐藏城市航班段搜索)
- [🐍 Python API 详细使用方法：](#python-api-详细使用方法：)
- [📚 完整 API 参考考](#-完整-api-参考考
- [✈️ 支持的机场和航空公司](#支持的机场和航空公司)
- [🛠️ 开发发发](#开发

## 🚀 快速开始发

```bash
pip install smart-flights
```

```bash
# 使用 pipx 安装（推荐用CLI
pipx install smart-flights

# 开发始使CLI
fli --help
```

## 功能特性

- 🔍 **强大搜索**
    - 单程航班段搜索
    - 往返航班段搜索
    - **基础搜索模式** (12个航班段班，快速响
    - **扩展搜索模式** (135+个航班段班，1025%提升) 🚀
    - 灵活的出发时
    - 多航空公司支
    - 舱位等级选择
    - 中转偏好设置
    - 自定义结果排
    - **隐藏城市航班段搜索** 🎯

- 💺 **舱位等级**
    - 经济
    - 超级经济
    - 商务
    - 头等

- 🎯 **智能排序**
    - 价格
    - 飞行时长
    - 出发时间
    - 到达时间

- 🛡**内置保护**
    - 速率限制
    - 自动重试
    - 全面错误处理
    - 输入验证

- 🌍 **多语言支持**
    - 中英文双语界
    - 机场名称本地
    - 航空公司名称翻译
    - 支持中文和英文搜

## CLI 使用方法：

### 搜索特定航班段

```bash
# 基础搜索
fli search JFK LHR 2025-10-25

# 高级搜索（带筛选条件）
fli search JFK LHR 2025-10-25 \
    -t 6-20 \              # 时间范围（上午6点 - 晚上8点）
    -a BA KL \             # 航空公司（英国航空、荷兰皇家航空）
    -s BUSINESS \          # 舱位类型
    -x NON_STOP \          # 仅直飞航班段
    -o DURATION            # 按飞行时长排序

# 中文搜索示例值
fli search PEK LAX 2025-10-25 \
    --language zh-cn \     # 中文界面
    --currency CNY         # 人民币价
```

### 查找最便宜日期

```bash
# 基础最便宜日期搜索
fli cheap JFK LHR

# 高级搜索（指定日期范围）
fli cheap JFK LHR \
    --from 2025-01-01 \
    --to 2025-02-01 \
    --monday --friday      # 仅周一和周
```

### 机场搜索

```bash
# 搜索机场
fli airport-search "北京"
fli airport-search "london" --language zh-cn
fli airport-search "PEK"

# 按国家搜索
fli airport-search "中国" --country --language zh-cn
```

## 🖥️ 完整 CLI 命令参考考

### `fli search` - 航班段搜索命令

**基本语法：*
```bash
fli search <出发机场> <到达机场> <出发日期> [选项]
```

**必需参考数*
- `<出发机场>` - 出发机场IATA代码 (如: JFK, PEK)
- `<到达机场>` - 到达机场IATA代码 (如: LHR, LAX)
- `<出发日期>` - 出发日期，格式: YYYY-MM-DD

**可选参考数：**

| 选项 | 长选项 | 描述 | 示例值| 默认值|
|------|--------|------|--------|--------|
| `-r` | `--return` | 返程日期 (往返票) | `2025-06-15` | 无 (单程) |
| `-t` | `--time` | 时间范围 (24小时制) | `6-20`, `8-18` | 无限制|
| `-a` | `--airlines` | 指定航空公司 | `BA KL CA`, `AA UA` | 所有航空公司|
| `-c` | `--class` | 舱位类型 | `ECONOMY`, `BUSINESS`, `FIRST` | `ECONOMY` |
| `-s` | `--stops` | 最大中转次数| `ANY`, `0`, `1`, `2` | `ANY` |
| `-o` | `--sort` | 排序方式 | `CHEAPEST`, `DURATION`, `DEPARTURE_TIME` | `CHEAPEST` |
| `-l` | `--language` | 界面语言 | `en`, `zh-cn` | `en` |
| `-cur` | `--currency` | 价格货币 | `USD`, `CNY` | `USD` |

**示例值*
```bash
# 基础搜索
fli search JFK LHR 2025-06-01

# 往返票搜索
fli search PEK LAX 2025-06-01 --return 2025-06-15

# 高级搜索
fli search JFK LHR 2025-06-01 \
    --time 8-20 \
    --airlines BA AA \
    --class BUSINESS \
    --stops 0 \
    --sort DURATION \
    --language zh-cn \
    --currency CNY
```

### `fli cheap` - 最便宜日期搜索

**基本语法：*
```bash
fli cheap <出发机场> <到达机场> [选项]
```

**必需参考数*
- `<出发机场>` - 出发机场IATA代码
- `<到达机场>` - 到达机场IATA代码

**可选参考数：**

| 选项 | 长选项 | 描述 | 示例值| 默认值|
|------|--------|------|--------|--------|
| | `--from` | 搜索开发始日| `2025-06-01` | 明天 |
| | `--to` | 搜索结束日期 | `2025-06-30` | 60天后 |
| `-d` | `--duration` | 行程天数 | `3`, `7`, `14` | `3` |
| `-a` | `--airlines` | 指定航空公司 | `BA KL CA` | 所有航空公司|
| `-R` | `--round` | 往返票搜索 | 无(标志) | 单程 |
| `-s` | `--stops` | 最大中转次数| `ANY`, `0`, `1`, `2` | `ANY` |
| `-c` | `--class` | 舱位类型 | `ECONOMY`, `BUSINESS` | `ECONOMY` |
| | `--sort` | 按价格排| 无(标志) | 按日期排|
| `-l` | `--language` | 界面语言 | `en`, `zh-cn` | `en` |
| `-cur` | `--currency` | 价格货币 | `USD`, `CNY` | `USD` |

**日期筛选选项*
| 选项 | 长选项 | 描述 |
|------|--------|------|
| `-mon` | `--monday` | 仅包含周一 |
| `-tue` | `--tuesday` | 仅包含周|
| `-wed` | `--wednesday` | 仅包含周|
| `-thu` | `--thursday` | 仅包含周|
| `-fri` | `--friday` | 仅包含周|
| `-sat` | `--saturday` | 仅包含周|
| `-sun` | `--sunday` | 仅包含周|

**示例值*
```bash
# 基础最便宜日期搜索
fli cheap JFK LHR

# 指定日期范围
fli cheap PEK LAX --from 2025-06-01 --to 2025-06-30

# 往返票 + 工作日筛
fli cheap JFK LHR --round --monday --tuesday --wednesday --thursday --friday

# 高级搜索
fli cheap PEK LAX \
    --from 2025-06-01 \
    --to 2025-06-30 \
    --duration 7 \
    --class BUSINESS \
    --stops 0 \
    --friday --saturday \
    --language zh-cn \
    --currency CNY
```

### `fli airport-search` - 机场搜索命令

**基本语法：*
```bash
fli airport-search <搜索查询> [选项]
```

**必需参考数*
- `<搜索查询>` - 机场名称、城市、国家或机场代码

**可选参考数：**

| 选项 | 长选项 | 描述 | 示例值| 默认值|
|------|--------|------|--------|--------|
| `-l` | `--language` | 结果语言 | `en`, `zh-cn` | `en` |
| `-n` | `--limit` | 最大结果数 | `5`, `20` | `10` |
| | `--city` | 按城市搜索| 无(标志) | 综合搜索 |
| | `--country` | 按国家搜索| 无(标志) | 综合搜索 |

**示例值*
```bash
# 基础搜索
fli airport-search "london"
fli airport-search "北京"
fli airport-search "LHR"

# 按城市搜索
fli airport-search "tokyo" --city --language zh-cn

# 按国家搜索
fli airport-search "china" --country --language zh-cn --limit 20

# 中文搜索
fli airport-search "上海" --language zh-cn
```

### `fli airport-info` - 机场详细信息

**基本语法：*
```bash
fli airport-info <机场代码> [选项]
```

**必需参考数*
- `<机场代码>` - 三字母IATA机场代码

**可选参考数：**

| 选项 | 长选项 | 描述 | 示例值| 默认值|
|------|--------|------|--------|--------|
| `-l` | `--language` | 信息语言 | `en`, `zh-cn` | `en` |

**示例值*
```bash
# 获取机场详细信息
fli airport-info LHR
fli airport-info PEK --language zh-cn
fli airport-info JFK --language en
```

### 🎯 常用命令组合示例值

#### 商务舱出行搜索
```bash
# 北京到纽约，商务舱，直飞
fli search PEK JFK 2025-06-01 \
    --class BUSINESS \
    --stops 0 \
    --sort DEPARTURE_TIME \
    --language zh-cn \
    --currency CNY
```

#### 度假出行规划
```bash
# 寻找最便宜的周末出行日
fli cheap LAX NRT \
    --from 2025-06-01 \
    --to 2025-08-31 \
    --round \
    --duration 7 \
    --friday --saturday \
    --class ECONOMY
```

#### 多航空公司比
```bash
# 比较多个航空公司价格
fli search JFK LHR 2025-06-01 \
    --airlines BA AA UA \
    --sort CHEAPEST \
    --time 8-20
```

#### 灵活时间搜索
```bash
# 寻找一周内最便宜的日
fli cheap SFO NRT \
    --from 2025-06-01 \
    --to 2025-06-07 \
    --class PREMIUM_ECONOMY \
    --sort
```

### CLI 选项

#### 搜索命令 (`fli search`)

| 选项             | 描述                    | 示例值                   |
|------------------|-------------------------|------------------------|
| `-t, --time`     | 时间范围4小时制）    | `6-20`                 |
| `-a, --airlines` | 航空公司代码            | `BA KL`                |
| `-s, --seat`     | 舱位等级                | `ECONOMY`, `BUSINESS`  |
| `-x, --stops`    | 最大中转次数           | `NON_STOP`, `ONE_STOP` |
| `-o, --sort`     | 结果排序方式            | `CHEAPEST`, `DURATION` |
| `-l, --language` | 界面语言                | `en`, `zh-cn`          |
| `--currency`     | 价格货币                | `USD`, `CNY`           |

#### 便宜航班段命令 (`fli cheap`)

| 选项          | 描述         | 示例值                   |
|---------------|--------------|------------------------|
| `--from`      | 开发始日    | `2025-01-01`           |
| `--to`        | 结束日期     | `2025-02-01`           |
| `-s, --seat`  | 舱位等级     | `ECONOMY`, `BUSINESS`  |
| `-x, --stops` | 最大中转次数| `NON_STOP`, `ONE_STOP` |
| `--[day]`     | 日期筛    | `--monday`, `--friday` |

#### 机场搜索命令 (`fli airport-search`)

| 选项             | 描述                    | 示例值                   |
|------------------|-------------------------|------------------------|
| `-l, --language` | 搜索结果语言            | `en`, `zh-cn`          |
| `-n, --limit`    | 最大结果数           | `10`                   |
| `--city`         | 按城市搜索             | `--city`               |
| `--country`      | 按国家搜索             | `--country`            |

## 🎯 KiwiFlightsAPI - 强大的航班搜索引擎

Smart Flights 集成了 Kiwi.com API，提供强大的航班搜索功能，支持普通航班和隐藏城市航班搜索。KiwiFlightsAPI 是最底层、最灵活的搜索接口，支持不同舱位、多乘客搜索。

### 🛫 KiwiFlightsAPI 核心功能

✅ **舱位支持**：ECONOMY、BUSINESS、FIRST_CLASS
✅ **乘客数支持**：1-9位成人（自动配置行李）
✅ **价格计算**：API自动计算多乘客总价
✅ **航班类型**：普通航班 + 隐藏城市航班混合搜索
✅ **搜索模式**：单程和往返航班搜索

### 🚀 基础使用方法

#### 1. 单程航班搜索

```python
import asyncio
from fli.api.kiwi_flights import KiwiFlightsAPI
from fli.models.google_flights.base import LocalizationConfig, Language, Currency

# 创建本地化配置置
localization_config = LocalizationConfig(
    language=Language.CHINESE,
    currency=Currency.CNY
)

# 创建API客户端
api = KiwiFlightsAPI(localization_config)

async def search_flights():
    # 单程航班段搜索
    result = await api.search_oneway_hidden_city(
        origin="LHR",                    # 伦敦希思罗
        destination="PEK",               # 北京首都
        departure_date="2025-07-31",     # 出发日期
        adults=1,                        # 成人乘客
        cabin_class="ECONOMY",           # 舱位等级
        hidden_city_only=False,          # False=所有航班段，True=隐藏城市优先
        limit=10                         # 返回航班段数量
    )

    if result.get("success"):
        flights = result.get("flights", [])
        print(f"✅ 找到 {len(flights)} 个航班")

        for i, flight in enumerate(flights[:3], 1):
            price = float(flight.get("price", 0))
            currency = flight.get("currency_symbol", "¥")
            carrier = flight.get("carrier_name", "未知")
            is_hidden = flight.get("is_hidden_city", False)

            print(f"\n航班 {i}: {carrier}")
            print(f"  💰 价格: {currency}{price:.0f}")
            print(f"  🏙️ 隐藏城市: {'是' if is_hidden else '否'}")
            print(f"  ✈️  {flight.get('departure_airport')} → {flight.get('arrival_airport')}")

# 运行搜索
asyncio.run(search_flights())
```

#### 2. 往返航班段搜索

```python
async def search_roundtrip():
    # 往返航班段搜索
    result = await api.search_roundtrip_hidden_city(
        origin="JFK",                    # 纽约肯尼
        destination="CDG",               # 巴黎戴高
        departure_date="2025-07-31",     # 出发日期
        return_date="2025-08-07",        # 返回日期
        adults=2,                        # 2位成人
        cabin_class="BUSINESS",          # 商务舱
        hidden_city_only=False           # 搜索所有类型型航
    )

    if result.get("success"):
        flights = result.get("flights", [])
        print(f"找到 {len(flights)} 个往返航)

        for i, flight in enumerate(flights[:2], 1):
            price = float(flight.get("price", 0))
            currency = flight.get("currency_symbol", "$")

            print(f"\n往返航班段 {i}:")
            print(f"  💰 总价: {currency}{price:.0f} (2人)")
            print(f"  🛫 去程: {flight.get('outbound', {}).get('departure_airport')} → {flight.get('outbound', {}).get('arrival_airport')}")
            print(f"  🛬 返程: {flight.get('inbound', {}).get('departure_airport')} → {flight.get('inbound', {}).get('arrival_airport')}")

asyncio.run(search_roundtrip())
```

### 🎯 不同舱位搜索

```python
async def search_different_cabins():
    """测试不同舱位的搜""

    cabins = [
        ("ECONOMY", "经济),
        ("BUSINESS", "商务),
        ("FIRST_CLASS", "头等)  # 注意：是FIRST_CLASS不是FIRST
    ]

    for cabin_code, cabin_name in cabins:
        print(f"\n🛫 搜索{cabin_name} ({cabin_code})")

        result = await api.search_oneway_hidden_city(
            origin="LHR",
            destination="PEK",
            departure_date="2025-07-31",
            adults=1,
            cabin_class=cabin_code,
            limit=3
        )

        if result.get("success"):
            flights = result.get("flights", [])
            if flights:
                price = float(flights[0].get("price", 0))
                currency = flights[0].get("currency_symbol", "¥")
                print(f"  找到 {len(flights)} 个航班段，起价: {currency}{price:.0f}")
            else:
                print(f"  没有找到{cabin_name}航班段")

asyncio.run(search_different_cabins())
```

### 👥 多乘客搜索

```python
async def search_multiple_passengers():
    """测试不同乘客数量的搜""

    passenger_counts = [1, 2, 3, 4]

    for adults in passenger_counts:
        print(f"\n👥 搜索 {adults}位成)

        result = await api.search_oneway_hidden_city(
            origin="JFK",
            destination="LAX",
            departure_date="2025-07-31",
            adults=adults,
            cabin_class="ECONOMY",
            limit=2
        )

        if result.get("success"):
            flights = result.get("flights", [])
            if flights:
                # API返回的是总价格（已包含所有乘客）
                total_price = float(flights[0].get("price", 0))
                currency = flights[0].get("currency_symbol", "$")
                single_price = total_price / adults

                print(f"  找到 {len(flights)} 个航)
                print(f"  💰 单人价格: {currency}{single_price:.0f}")
                print(f"  💰 {adults}人总价: {currency}{total_price:.0f}")

asyncio.run(search_multiple_passengers())
```

### 🔧 高级搜索选项

```python
async def advanced_search():
    """高级搜索示例值"""

    result = await api.search_oneway_hidden_city(
        origin="SIN",                    # 新加
        destination="SYD",               # 悉尼
        departure_date="2025-07-31",
        adults=2,                        # 2位成人
        cabin_class="BUSINESS",          # 商务舱
        limit=20,                        # 更多结果
        enable_pagination=True,          # 启用分页
        max_pages=3,                     # 最多3页
        hidden_city_only=False           # 搜索所有类型
    )

    if result.get("success"):
        flights = result.get("flights", [])
        hidden_count = sum(1 for f in flights if f.get("is_hidden_city", False))
        regular_count = len(flights) - hidden_count

        print(f"✅ 高级搜索结果:")
        print(f"  📊 总航班段数: {len(flights)}")
        print(f"  🏙️ 隐藏城市航班段: {hidden_count}")
        print(f"  ✈️  普通航班段: {regular_count}")
        print(f"  📄 分页信息: {result.get('total_count', 0)} 总数")

asyncio.run(advanced_search())
```

### 💡 最佳实

#### 1. 获取所有类型航班段（推荐
```python
# 推荐设置：返回普通航隐藏城市航班段
result = await api.search_oneway_hidden_city(
    origin="LHR", destination="PEK", departure_date="2025-07-31",
    hidden_city_only=False  # 🔑 关键参考数
)
```

#### 2. 优先获取隐藏城市航班段
```python
# 特殊需求：优先显示隐藏城市航班段
result = await api.search_oneway_hidden_city(
    origin="LHR", destination="PEK", departure_date="2025-07-31",
    hidden_city_only=True
)
```

#### 3. 价格处理
```python
# 价格是字符串，需要转换为数字
if result.get("success"):
    flights = result.get("flights", [])
    for flight in flights:
        price_str = flight.get("price")
        price_num = float(price_str)  # 转换为数
        currency = flight.get("currency_symbol", "$")
        print(f"价格: {currency}{price_num:.0f}")
```

### ⚠️ 重要说明

1. **异步调用**：所有KiwiFlightsAPI方法：都是异步的，需要使用`await`
2. **价格类型**：API返回的价格是字符串，需要转换为数字进行计算
3. **舱位名称**：头等舱使用`FIRST_CLASS`而不是`FIRST`
4. **多乘客价*：API自动计算总价，无需手动乘以乘客
5. **行李配置**：系统自动为每位成人配置行李，无需手动设置

## Python API 详细使用方法：

### 1. 航班段搜索 API

#### 1.1 基础搜索 vs 扩展搜索 🚀

Smart Flights 提供两种搜索模式，满足不同的使用需求：

**基础搜索模式** (默认值):
- 🚀 **快速响*: 平均1.1
- 📊 **12个航班段*: 主要航空公司和热门路线
- 💡 **适用场景**: 快速浏览、用户首次搜索

**扩展搜索模式** (推荐):
- 🎯 **更多选择**: 135+个航班段(1025%提升!)
- **⚡ **更快速度****: 平均0.6(比基础模式更快!)
- 🌍 **全面覆盖**: 更多航空公司、联程航班段、替代路线
- 💡 **适用场景**: 价格比较、寻找最优选择

```python
from fli.search import SearchFlights
from fli.models import FlightSearchFilters, FlightSegment, Airport, PassengerInfo, SeatType, TripType
from fli.models.google_flights.base import LocalizationConfig, Language, Currency

# 创建本地化配置
localization_config = LocalizationConfig(
    language=Language.CHINESE,
    currency=Currency.CNY
)

# 创建搜索过滤
filters = FlightSearchFilters(
    trip_type=TripType.ONE_WAY,
    passenger_info=PassengerInfo(adults=1),
    flight_segments=[
        FlightSegment(
            departure_airport=[[Airport.PEK, 0]],
            arrival_airport=[[Airport.LAX, 0]],
            travel_date="2025-06-01"
        )
    ],
    seat_type=SeatType.ECONOMY
)

# 初始化搜索客户端
search = SearchFlights(localization_config=localization_config)

# 方法：1: 基础搜索 (12个航班段
basic_results = search.search(filters, top_n=10)
print(f"基础搜索: {len(basic_results)} 个航)

# 方法：2: 扩展搜索 (135+个航班段 - 推荐
extended_results = search.search(filters, top_n=50, enhanced_search=True)
print(f"扩展搜索: {len(extended_results)} 个航)

# 方法：3: 专用扩展搜索API (135+个航班段 - 最简洁！
extended_results_v2 = search.search_extended(filters, top_n=50)
print(f"扩展API: {len(extended_results_v2)} 个航)
```

**性能对比测试结果:**

| 搜索模式 | 航班段数量 | 响应时间 | 提升幅度 | 推荐场景 |
|----------|----------|----------|----------|----------|
| 基础搜索 | 12| 1.14| - | 快速浏|
| 扩展搜索 | 135| 0.61| +1025% | 价格比较、完整选择 |

**不同路线的扩展搜索效**

| 路线 | 基础模式 | 扩展模式 | 提升幅度 |
|------|----------|----------|----------|
| 北京→洛杉矶 | 12| 135| +1025% |
| 北京→纽| 12| 112| +833% |
| 上海→旧金山 | 10| 143| +1330% |
| 广州→洛杉矶 | 12| 139| +1058% |

#### 1.2 基础单程航班段搜索

```python
from datetime import datetime, timedelta
from fli.search import SearchFlights
from fli.models import (
    FlightSearchFilters, FlightSegment, Airport,
    PassengerInfo, SeatType, MaxStops, SortBy, TripType
)
from fli.models.google_flights.base import LocalizationConfig, Language, Currency

# 创建本地化配置置（支持中英文切换）
localization_config = LocalizationConfig(
    language=Language.CHINESE,  # 或 Language.ENGLISH
    currency=Currency.CNY       # 或 Currency.USD
)

# 创建航班段段
flight_segments = [
    FlightSegment(
        departure_airport=[[Airport.PEK, 0]],  # 北京首都国际机场
        arrival_airport=[[Airport.LAX, 0]],    # 洛杉矶国际机
        travel_date="2025-06-01"               # 出发日期 (YYYY-MM-DD)
    )
]

# 创建搜索筛选条
filters = FlightSearchFilters(
    trip_type=TripType.ONE_WAY,                # 单程
    passenger_info=PassengerInfo(
        adults=1,                              # 成人数量
        children=0,                            # 儿童数量
        infants_in_seat=0,                     # 占座婴儿
        infants_on_lap=0                       # 膝上婴儿
    ),
    flight_segments=flight_segments,
    seat_type=SeatType.ECONOMY,                # 舱位等级
    stops=MaxStops.NON_STOP,                   # 中转限制
    sort_by=SortBy.CHEAPEST                    # 排序方式
)

# 执行搜索
search = SearchFlights(localization_config=localization_config)
flights = search.search(filters, top_n=10)

# 处理结果
if flights:
    for i, flight in enumerate(flights, 1):
        print(f"\n=== 航班段选项 {i} ===")
        print(f"💰 价格: {localization_config.currency_symbol}{flight.price}")
        print(f"⏱️ 总时 {flight.duration} 分钟")
        print(f"✈️ 中转次数: {flight.stops}")

        for j, leg in enumerate(flight.legs, 1):
            # 获取本地化的航空公司名称
            airline_name = localization_config.get_airline_name(
                leg.airline.name, leg.airline.value
            )
            print(f"\n  航段 {j}: {airline_name} {leg.flight_number}")
            print(f"  📍 {leg.departure_airport.value} → {leg.arrival_airport.value}")
            print(f"  {leg.departure_datetime} → {leg.arrival_datetime}")
else:
    print("未找到符合条件的航班段")
```

#### 1.2 往返航班段搜索

```python
# 创建往返航班段段
flight_segments = [
    # 去程
    FlightSegment(
        departure_airport=[[Airport.PEK, 0]],
        arrival_airport=[[Airport.LAX, 0]],
        travel_date="2025-06-01"
    ),
    # 返程
    FlightSegment(
        departure_airport=[[Airport.LAX, 0]],
        arrival_airport=[[Airport.PEK, 0]],
        travel_date="2025-06-15"
    )
]

filters = FlightSearchFilters(
    trip_type=TripType.ROUND_TRIP,             # 往
    passenger_info=PassengerInfo(adults=2),   # 2位成人
    flight_segments=flight_segments,
    seat_type=SeatType.BUSINESS,               # 商务舱
    stops=MaxStops.ONE_STOP,                   # 最多3页多一次中
    sort_by=SortBy.DURATION                    # 按时长排
)

search = SearchFlights(localization_config=localization_config)
flights = search.search(filters)

# 往返航班段结果处
if flights:
    for i, flight_pair in enumerate(flights, 1):
        if isinstance(flight_pair, tuple):
            outbound, return_flight = flight_pair
            print(f"\n=== 往返选项 {i} ===")
            print(f"💰 总价 {localization_config.currency_symbol}{outbound.price + return_flight.price}")
            print(f"🛫 去程: {outbound.duration}分钟, {outbound.stops}次中)
            print(f"🛬 🛬 返程: {return_flight.duration}分钟, {return_flight.stops}次中)
```

#### 1.3 指定中转机场搜索

```python
from fli.models import LayoverRestrictions

# 指定中转机场筛- 只允许在东京成田或首尔仁川中
layover_restrictions = LayoverRestrictions(
    airports=[Airport.NRT, Airport.ICN],  # 东京成田、首尔仁
    max_duration=360  # 最多3页长中转时小时
)

filters = FlightSearchFilters(
    trip_type=TripType.ONE_WAY,
    passenger_info=PassengerInfo(adults=1),
    flight_segments=[flight_segment],
    seat_type=SeatType.ECONOMY,
    stops=MaxStops.ANY,  # 允许中转
    layover_restrictions=layover_restrictions  # 中转机场筛
)

search = SearchFlights(localization_config=localization_config)
results = search.search(filters, top_n=5)

if results:
    for i, flight in enumerate(results, 1):
        print(f"\n=== 航班段选项 {i} ===")
        print(f"💰 价格: {localization_config.currency_symbol}{flight.price}")
        print(f"⏱️ 总时长: {flight.duration}分钟")
        print(f"🔄 中转次数: {flight.stops}")

        for j, leg in enumerate(flight.legs, 1):
            print(f"  航段 {j}: {leg.departure_airport.value} → {leg.arrival_airport.value}")
```

#### 1.4 高级搜索选项

```python
from fli.models import TimeRestrictions, PriceLimit, LayoverRestrictions, Airline

# 时间限制
time_restrictions = TimeRestrictions(
    earliest_departure=6,    # 最多3页早出发时(6:00)
    latest_departure=20,     # 最多3页晚出发时(20:00)
    earliest_arrival=8,      # 最多3页早到达时(8:00)
    latest_arrival=22        # 最多3页晚到达时(22:00)
)

# 价格限制
price_limit = PriceLimit(
    max_price=5000,          # 最多3页高价
    currency=Currency.CNY    # 货币
)

# 中转限制 - 指定中转机场和时
layover_restrictions = LayoverRestrictions(
    airports=[Airport.NRT, Airport.ICN],  # 允许的中转机场（东京成田、首尔仁川）
    max_duration=480                      # 最多3页长中转时分钟小时)
)

# 指定航空公司
preferred_airlines = [
    Airline.CA,  # 中国国际航空
    Airline.MU,  # 中国东方航空
    Airline.CZ   # 中国南方航空
]

# 创建带时间限制的航班段
flight_segments = [
    FlightSegment(
        departure_airport=[[Airport.PEK, 0]],
        arrival_airport=[[Airport.LAX, 0]],
        travel_date="2025-06-01",
        time_restrictions=time_restrictions
    )
]

filters = FlightSearchFilters(
    trip_type=TripType.ONE_WAY,
    passenger_info=PassengerInfo(adults=1),
    flight_segments=flight_segments,
    seat_type=SeatType.PREMIUM_ECONOMY,       # 超级经济
    stops=MaxStops.ANY,                       # 任意中转
    price_limit=price_limit,                  # 价格限制
    airlines=preferred_airlines,              # 指定航空公司
    max_duration=1200,                        # 最多3页长飞行时分钟)
    layover_restrictions=layover_restrictions, # 中转限制
    sort_by=SortBy.DEPARTURE_TIME             # 按出发时间排
)
```

#### 1.4 中转机场筛选功🎯

**LayoverRestrictions** 允许您精确控制航班段的中转条件，包括指定允许的中转机场和最长中转时间

```python
from fli.models import LayoverRestrictions, Airport

# 基础中转机场筛
layover_restrictions = LayoverRestrictions(
    airports=[Airport.NRT, Airport.ICN, Airport.HND],  # 指定允许的中转机
    max_duration=360  # 最多3页长中转时间：6小时60分钟
)

# 常用中转机场组合示例值

# 亚洲主要中转枢纽
asia_hubs = LayoverRestrictions(
    airports=[
        Airport.NRT,  # 东京成田
        Airport.HND,  # 东京羽田
        Airport.ICN,  # 首尔仁川
        Airport.SIN,  # 新加坡樟
        Airport.HKG,  # 香港国际
        Airport.TPE   # 台北桃园
    ],
    max_duration=480  # 8小时内中
)

# 欧洲主要中转枢纽
europe_hubs = LayoverRestrictions(
    airports=[
        Airport.LHR,  # 伦敦希思罗
        Airport.CDG,  # 巴黎戴高
        Airport.FRA,  # 法兰克福
        Airport.AMS,  # 阿姆斯特
        Airport.MUC,  # 慕尼
        Airport.ZUR   # 苏黎
    ],
    max_duration=300  # 5小时内中
)

# 北美主要中转枢纽
america_hubs = LayoverRestrictions(
    airports=[
        Airport.JFK,  # 纽约肯尼
        Airport.LAX,  # 洛杉
        Airport.ORD,  # 芝加哥奥黑尔
        Airport.DFW,  # 达拉斯沃斯堡
        Airport.SFO,  # 旧金
        Airport.SEA   # 西雅
    ],
    max_duration=240  # 4小时内中
)

# 仅限制中转时间（不限制机场）
time_only_restriction = LayoverRestrictions(
    airports=None,        # 不限制中转机
    max_duration=180      # 但限制中转时间不超过3小时
)

# 仅限制中转机场（不限制时间）
airport_only_restriction = LayoverRestrictions(
    airports=[Airport.DXB, Airport.DOH],  # 仅允许迪拜、多哈中
    max_duration=None                      # 不限制中转时
)
```

**使用场景示例值*

```python
# 场景1：商务出- 快速中
business_travel = FlightSearchFilters(
    trip_type=TripType.ROUND_TRIP,
    passenger_info=PassengerInfo(adults=1),
    flight_segments=flight_segments,
    seat_type=SeatType.BUSINESS,
    layover_restrictions=LayoverRestrictions(
        airports=[Airport.NRT, Airport.ICN, Airport.SIN],  # 亚洲优质机场
        max_duration=180  # 3小时内快速中
    )
)

# 场景2：经济出- 灵活中转
economy_travel = FlightSearchFilters(
    trip_type=TripType.ONE_WAY,
    passenger_info=PassengerInfo(adults=2, children=1),
    flight_segments=flight_segments,
    seat_type=SeatType.ECONOMY,
    layover_restrictions=LayoverRestrictions(
        airports=[Airport.DOH, Airport.DXB, Airport.IST],  # 中东航空枢纽
        max_duration=720  # 12小时内中转（可休息）
    )
)

# 场景3：避开发特定机场
avoid_certain_airports = FlightSearchFilters(
    trip_type=TripType.ONE_WAY,
    passenger_info=PassengerInfo(adults=1),
    flight_segments=flight_segments,
    layover_restrictions=LayoverRestrictions(
        # 只允许在这些机场中转，避开发其他机场
        airports=[Airport.LHR, Airport.CDG, Airport.FRA, Airport.AMS],
        max_duration=360
    )
)
```

**中转机场筛选的优势：*

- 🎯 **精确控制**: 指定首选的中转机场
- ⏱️ **时间管理**: 控制中转等待时间
- 🛡️ **风险控制**: 避开发不熟悉或设施较差的机
- 💺 **舒适度**: 选择设施完善的大型枢纽机
- 🌍 **地理优化**: 根据航线选择最佳中转点

**完整调用示例：值*

```python
from fli.search import SearchFlights
from fli.models import (
    FlightSearchFilters, FlightSegment, PassengerInfo,
    LayoverRestrictions, Airport, TripType, SeatType, MaxStops
)
from fli.models.google_flights.base import LocalizationConfig, Language, Currency

# 1. 创建本地化配置
config = LocalizationConfig(
    language=Language.CHINESE,
    currency=Currency.CNY
)

# 2. 创建中转机场筛选条
layover_restrictions = LayoverRestrictions(
    airports=[Airport.NRT, Airport.ICN, Airport.SIN],  # 指定中转机场
    max_duration=360  # 最多3页长中转时小时
)

# 3. 创建航班段段
flight_segment = FlightSegment(
    departure_airport=[[Airport.PEK, 0]],  # 北京首都
    arrival_airport=[[Airport.LAX, 0]],    # 洛杉
    travel_date="2025-06-01"
)

# 4. 创建搜索过滤
filters = FlightSearchFilters(
    trip_type=TripType.ONE_WAY,
    passenger_info=PassengerInfo(adults=1),
    flight_segments=[flight_segment],
    seat_type=SeatType.ECONOMY,
    stops=MaxStops.ANY,  # 允许中转
    layover_restrictions=layover_restrictions  # 中转机场筛
)

# 5. 执行搜索
search = SearchFlights(localization_config=config)
results = search.search(filters, top_n=5)

# 6. 处理结果
if results:
    for i, flight in enumerate(results, 1):
        print(f"航班段 {i}: {flight.price} - {flight.duration}分钟")
        for leg in flight.legs:
            print(f"  {leg.departure_airport} -> {leg.arrival_airport}")
```

**注意事项*

- 中转机场筛选会影响搜索结果数量，过于严格的限制可能导致无结
- 建议根据实际需求平衡筛选条件的严格程度
- 不同航空公司在不同机场的服务质量可能有差
- 中转时间建议预留足够缓冲，考虑可能的延误情

## 📚 完整 API 参考

### 🔍 搜索(Search Classes)

#### SearchFlights - 航班段搜索
```python
from fli.search import SearchFlights
from fli.models.google_flights.base import LocalizationConfig, Language, Currency

# 创建本地化配置
localization_config = LocalizationConfig(
    language=Language.CHINESE,  # 或 Language.ENGLISH
    currency=Currency.CNY       # 或 Currency.USD
)

# 初始化搜索客户端
search = SearchFlights(localization_config=localization_config)

# 执行搜索
results = search.search(filters, top_n=10)
```

**方法：*
- `search(filters: FlightSearchFilters, top_n: int = 5, enhanced_search: bool = False)` - 搜索航班段
  - `enhanced_search=False`: 基础搜索模式 (12个航班段班，快
  - `enhanced_search=True`: 扩展搜索模式 (135+个航班段班，推荐)
- `search_extended(filters: FlightSearchFilters, top_n: int = 50)` - 扩展搜索专用API
  - 自动启用扩展搜索模式，返35+个航
  - 等同`search(filters, top_n, enhanced_search=True)`

**使用建议*
```python
# 快速搜(12个航班段
results = search.search(filters)

# 完整搜索 (135+个航班段 - 推荐
results = search.search_extended(filters)
# 或
results = search.search(filters, enhanced_search=True)
```

#### SearchKiwiFlights - 隐藏城市航班段搜索
```python
from fli.search import SearchKiwiFlights
from fli.models.google_flights.base import LocalizationConfig, Language, Currency

# 创建本地化配置
localization_config = LocalizationConfig(
    language=Language.CHINESE,  # 或 Language.ENGLISH
    currency=Currency.CNY       # 或 Currency.USD
)

# 初始化隐藏城市搜索客户端
search = SearchKiwiFlights(localization_config=localization_config)

# 执行搜索（与 Google Flights 完全相同的接口）
results = search.search(filters, top_n=5)
```

**方法：*
- `search(filters: FlightSearchFilters, top_n: int = 5)` - 搜索隐藏城市航班段

**特点：*
- 与 `SearchFlights` 完全相同的接口
- 专门搜索隐藏城市航班段
- 支持单程和往返搜索
- 支持所有舱位类型
- 返回包含隐藏城市信息的 `FlightResult` 对象

#### SearchDates - 日期价格搜索
```python
from fli.search import SearchDates

# 初始化日期搜索
search = SearchDates(localization_config=localization_config)

# 搜索最便宜日期
results = search.search(filters)
```

**方法：*
- `search(filters: DateSearchFilters)` - 搜索日期价格

### 🏢 机场搜索 API

#### AirportSearchAPI - 机场搜索服务
```python
from fli.api.airport_search import airport_search_api
from fli.models.google_flights.base import Language

# 全局实例，可直接使用
api = airport_search_api
```

**方法：*
- `search_airports(query: str, language: Language = Language.ENGLISH, limit: int = 10)` - 综合机场搜索
- `get_airport_by_code(code: str, language: Language = Language.ENGLISH)` - 按机场代码获取信
- `search_by_city(city: str, language: Language = Language.ENGLISH)` - 按城市搜索索机
- `search_by_country(country: str, language: Language = Language.ENGLISH, limit: int = 20)` - 按国家搜索索机
- `get_all_airports(language: Language = Language.ENGLISH, limit: Optional[int] = None)` - 获取所有机

### 📋 数据模型 (Data Models)

#### FlightSearchFilters - 航班段搜索过滤
```python
from fli.models import FlightSearchFilters, FlightSegment, PassengerInfo

filters = FlightSearchFilters(
    trip_type=TripType.ONE_WAY,           # 行程类型
    passenger_info=PassengerInfo(adults=1), # 乘客信息
    flight_segments=[flight_segment],      # 航班段
    seat_type=SeatType.ECONOMY,           # 舱位类型
    stops=MaxStops.NON_STOP,              # 中转限制
    sort_by=SortBy.CHEAPEST,              # 排序方式
    airlines=[Airline.CA, Airline.MU],   # 指定航空公司
    max_duration=1200,                    # 最多3页长飞行时分钟)
    price_limit=PriceLimit(max_price=5000, currency=Currency.CNY),  # 价格限制
    layover_restrictions=LayoverRestrictions(  # 中转机场筛
        airports=[Airport.NRT, Airport.ICN],   # 允许的中转机
        max_duration=360                       # 最多3页长中转时分钟)
    )
)
```

#### DateSearchFilters - 日期搜索过滤
```python
from fli.models import DateSearchFilters

filters = DateSearchFilters(
    departure_airport=Airport.PEK,        # 出发机场
    arrival_airport=Airport.LAX,          # 到达机场
    from_date="2025-06-01",              # 开发始日
    to_date="2025-06-30",                # 结束日期
    trip_type=TripType.ONE_WAY,          # 行程类型
    seat_type=SeatType.ECONOMY,          # 舱位类型
    stops=MaxStops.ANY,                  # 中转限制
    passenger_info=PassengerInfo(adults=1) # 乘客信息
)
```

#### FlightSegment - 航班段
```python
from fli.models import FlightSegment, TimeRestrictions

segment = FlightSegment(
    departure_airport=[[Airport.PEK, 0]], # 出发机场
    arrival_airport=[[Airport.LAX, 0]],   # 到达机场
    travel_date="2025-06-01",            # 出行日期
    time_restrictions=TimeRestrictions(   # 时间限制
        earliest_departure=6,             # 最多3页早出发时
        latest_departure=20,              # 最多3页晚出发时
        earliest_arrival=8,               # 最多3页早到达时
        latest_arrival=22                 # 最多3页晚到达时
    )
)
```

#### LayoverRestrictions - 中转机场筛
```python
from fli.models import LayoverRestrictions, Airport

# 完整配置
layover_restrictions = LayoverRestrictions(
    airports=[Airport.NRT, Airport.ICN, Airport.SIN],  # 允许的中转机场列
    max_duration=360                                    # 最多3页长中转时分钟)
)

# 仅限制机
airport_only = LayoverRestrictions(
    airports=[Airport.DXB, Airport.DOH],  # 仅允许迪拜、多哈中
    max_duration=None                      # 不限制中转时
)

# 仅限制时
time_only = LayoverRestrictions(
    airports=None,        # 不限制中转机
    max_duration=240      # 但限制中转时间不超过4小时
)
```

**属性说明：**
- `airports: list[Airport] | None` - 允许的中转机场列表，None表示不限
- `max_duration: int | None` - 最长中转时间（分钟），None表示不限

**常用中转机场组合*
```python
# 亚洲枢纽
ASIA_HUBS = [Airport.NRT, Airport.HND, Airport.ICN, Airport.SIN, Airport.HKG, Airport.TPE]

# 欧洲枢纽
EUROPE_HUBS = [Airport.LHR, Airport.CDG, Airport.FRA, Airport.AMS, Airport.MUC, Airport.ZUR]

# 北美枢纽
AMERICA_HUBS = [Airport.JFK, Airport.LAX, Airport.ORD, Airport.DFW, Airport.SFO, Airport.SEA]

# 中东枢纽
MIDDLE_EAST_HUBS = [Airport.DXB, Airport.DOH, Airport.AUH, Airport.KWI]
```

**第三方库调用示例值*
```python
# 在其他项目中使用中转机场筛选功
import fli

# 快速搜- 指定中转机场
from fli.search import SearchFlights
from fli.models import FlightSearchFilters, LayoverRestrictions, Airport

# 创建搜索过滤器，指定只能在东京成田或首尔仁川中转
filters = FlightSearchFilters(
    # ... 其他基本参考数
    layover_restrictions=LayoverRestrictions(
        airports=[Airport.NRT, Airport.ICN],  # 只允许这两个机场中转
        max_duration=300  # 中转时间不超小时
    )
)

# 执行搜索
search = SearchFlights()
results = search.search(filters)
```

#### TimeRestrictions - 时间限制
```python
from fli.models import TimeRestrictions

time_restrictions = TimeRestrictions(
    earliest_departure=6,     # 最多3页早出发时(6:00)
    latest_departure=20,      # 最多3页晚出发时(20:00)
    earliest_arrival=8,       # 最多3页早到达时(8:00)
    latest_arrival=22         # 最多3页晚到达时(22:00)
)
```

**属性说明：**
- `earliest_departure: int | None` - 最早出发时间（24小时制）
- `latest_departure: int | None` - 最晚出发时间（24小时制）
- `earliest_arrival: int | None` - 最早到达时间（24小时制）
- `latest_arrival: int | None` - 最晚到达时间（24小时制）

#### PriceLimit - 价格限制
```python
from fli.models import PriceLimit, Currency

price_limit = PriceLimit(
    max_price=5000,           # 最多3页高价
    currency=Currency.CNY     # 货币类型
)
```

**属性说明：**
- `max_price: int` - 最高价格
- `currency: Currency | None` - 货币类型，默认值为USD

### 🏷️ 枚举类型 (Enums)

#### SeatType - 舱位类型
```python
from fli.models import SeatType

SeatType.ECONOMY          # 经济
SeatType.PREMIUM_ECONOMY  # 超级经济
SeatType.BUSINESS         # 商务舱
SeatType.FIRST           # 头等
```

#### MaxStops - 中转限制
```python
from fli.models import MaxStops

MaxStops.ANY                    # 任意中转
MaxStops.NON_STOP              # 直飞
MaxStops.ONE_STOP_OR_FEWER     # 最多3页多一次中
MaxStops.TWO_OR_FEWER_STOPS    # 最多3页多两次中
```

#### SortBy - 排序方式
```python
from fli.models import SortBy

SortBy.NONE            # 不排
SortBy.TOP_FLIGHTS     # 推荐航班段
SortBy.CHEAPEST        # 最多3页便宜
SortBy.DEPARTURE_TIME  # 出发时间
SortBy.ARRIVAL_TIME    # 到达时间
SortBy.DURATION        # 飞行时长
```

#### TripType - 行程类型
```python
from fli.models import TripType

TripType.ONE_WAY      # 单程
TripType.ROUND_TRIP   # 往
```

#### Language - 语言设置
```python
from fli.models.google_flights.base import Language

Language.ENGLISH   # 英文 ("en")
Language.CHINESE   # 中文 ("zh-CN")
```

#### Currency - 货币设置
```python
from fli.models.google_flights.base import Currency

Currency.USD  # 美元
Currency.CNY  # 人民
```

### ✈️ 机场和航空公司枚

#### Airport - 机场代码 (255+ 个全球主要机
```python
from fli.models import Airport

# 中国主要机场
Airport.PEK   # 北京首都国际机场
Airport.PVG   # 上海浦东国际机场
Airport.CAN   # 广州白云国际机场
Airport.SZX   # 深圳宝安国际机场
Airport.CTU   # 成都双流国际机场

# 美国主要机场
Airport.JFK   # 纽约肯尼迪国际机
Airport.LAX   # 洛杉矶国际机
Airport.ORD   # 芝加哥奥黑尔国际机场
Airport.DFW   # 达拉斯沃斯堡国际机场
Airport.SFO   # 旧金山国际机

# 欧洲主要机场
Airport.LHR   # 伦敦希思罗机场
Airport.CDG   # 巴黎戴高乐机
Airport.FRA   # 法兰克福机场
Airport.AMS   # 阿姆斯特丹史基浦机场
Airport.FCO   # 罗马菲乌米奇诺机
```

#### Airline - 航空公司代码 (382+ 个航空公司
```python
from fli.models import Airline

# 中国航空公司
Airline.CA    # 中国国际航空
Airline.MU    # 中国东方航空
Airline.CZ    # 中国南方航空
Airline.HU    # 海南航空
Airline.FM    # 上海航空

# 国际航空公司
Airline.AA    # 美国航空
Airline.UA    # 美联
Airline.DL    # 达美航空
Airline.BA    # 英国航空
Airline.AF    # 法国航空
Airline.LH    # 汉莎航空
Airline.KL    # 荷兰皇家航空
Airline.SQ    # 新加坡航
Airline.CX    # 国泰航空
```

### 🌐 本地化配

#### LocalizationConfig - 本地化设
```python
from fli.models.google_flights.base import LocalizationConfig, Language, Currency

# 中文配置
chinese_config = LocalizationConfig(
    language=Language.CHINESE,
    currency=Currency.CNY
)

# 英文配置
english_config = LocalizationConfig(
    language=Language.ENGLISH,
    currency=Currency.USD
)
```

**属性：**
- `language: Language` - 界面语言
- `currency: Currency` - 价格货币
- `region: str` - 地区代码
- `api_language_code: str` - API语言代码 (只读)
- `api_currency_code: str` - API货币代码 (只读)
- `currency_symbol: str` - 货币符号 (只读)

### 📊 结果模型

#### FlightResult - 航班段搜索结果
```python
# 结果属
result.price          # 价格
result.duration       # 总飞行时分钟)
result.stops          # 中转次数
result.legs           # 航班段段列
result.departure_time # 出发时间
result.arrival_time   # 到达时间
```

#### FlightLeg - 航班段段信
```python
# 航班段段属
leg.airline           # 航空公司
leg.flight_number     # 航班段
leg.departure_airport # 出发机场
leg.arrival_airport   # 到达机场
leg.departure_datetime # 出发时间
leg.arrival_datetime  # 到达时间
leg.duration          # 飞行时长
```

#### DatePrice - 日期价格
```python
# 日期价格属
date_price.date       # 日期
date_price.price      # 价格
```

## 支持的机场和航空公司

### 机场覆盖
- **全球 255+ 个主要机*
- **中英文双语名*
- **覆盖所有大*
- **支持中英文搜*

### 航空公司支持
- **382+ 个航空公司*
- **完整中文翻译**
- **包含主要国际和地区航空公司*
- **根据 API 语言参考数自动切换显示语言**

## 🛠️ 开发发

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/punitarani/fli.git
cd fli

# 使用 Poetry 安装依赖
poetry install

# 运行测试
poetry run pytest

# 运行代码检
poetry run ruff check .
poetry run ruff format .

# 构建文档
poetry run mkdocs serve
```

### 构建和发

```bash
# 构建
poetry build

# 发布PyPI
poetry publish
```

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request

### 贡献指南

1. Fork 本仓
2. 创建您的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开发一Pull Request

## 🙏 特别致谢

### 原始项目致谢

本项目基[**Fli**](https://github.com/punitarani/fli) 项目进行开发发，特别感谢

- **[punitarani](https://github.com/punitarani)** - Fli 项目的原始创建者和主要贡献
- **Fli 社区** - 为原始项目提供支持和贡献的所有开发发

### 技术致

- **Google Flights** - 提供强大的航班段搜API
- **Python 社区** - 提供优秀的开发发工具和
- **Poetry** - 现代化的 Python 包管理工
- **Typer** - 优雅CLI 框架

### 数据来源

- 机场数据来源于公开发的航空数据库
- 航空公司信息基于 IATA 标准
- 中文翻译由社区贡献和维护

## 📄 许可证

本项目采MIT 许可证详情请参考[LICENSE](LICENSE) 文件

### 许可证证说

- ✅ 商业使用
- ✅ 修改
- ✅ 分发
- ✅ 私人使用
- ❌ 责任
- ❌ 保证

## 🔗 相关链接

- **原始项目**: [Fli](https://github.com/punitarani/fli)
- **PyPI 包*: [smart-flights](https://pypi.org/project/smart-flights/)
- **文档**: [项目文档](https://github.com/EBOLABOY/smart-flights)
- **问题反馈**: [Issues](https://github.com/EBOLABOY/smart-flights/issues)
- **功能请求**: [Discussions](https://github.com/EBOLABOY/smart-flights/discussions)

---

**Smart Flights** - 让航班段搜索更智能、更便捷✈️

---

## 📋 更新日志

### v0.5.6 (2025-06-29)

**🌐 简化LocalizationConfig配置**
- **移除region参考数**: 不再需要手动指定国地区，固定使用美US)以获得最佳API性能
- **简化外部调*: 用户只需选择语言(Language)和货Currency)两个参考数
- **向后兼容**: 现有代码自动适配，无需✅ 修改
- **API性能优化**: 统一使用美国地区设置，确保Google Flights API的最佳响应速度

**📝 新的使用方式**
```python
# 之前: 需要指个参考
config = LocalizationConfig(language=Language.CHINESE, currency=Currency.CNY, region="CN")

# 现在: 只需指定2个参考
config = LocalizationConfig(language=Language.CHINESE, currency=Currency.CNY)
```

**🧪 测试验证**
- 100%向后兼容性测试通过
- 3/3种语言货币组合测试成功
- Google Flights API兼容性验证完

### v0.5.5 (2025-06-28)

**🔧 完善所有Kiwi API接口的limit优化**
- **统一所有API接口**: KiwiOnewayAPI、KiwiRoundtripAPI、KiwiFlightsAPI全部使用limit=50
- **保持接口一致*: 所有Kiwi相关API现在都有相同的性能表现
- **完整的向后兼*: 用户无需✅ 修改任何现有代码即可享受性能提升
- **全面测试验证**: 100%成功率，所有API接口都正常工

**📊 性能统计**
- 总航班段数: 75(3个API × 25个航
- 总隐藏城市航 12
- 平均搜索时间: 4.45
- API成功 100% (3/3)

### v0.5.4 (2025-06-28)

**🚀 分页性能优化**
- **大幅提升航班段数据获取*: 默认值每页航班段数从10提升0 (+400%)
- **优化分页参考数**: 最大页数从5提升0，理论最大获取量0提升00个航
- **修复duration数据解析**: 正确处理API返回的时间数据格
- **性能提升**: 搜索效率提升277.9%，航班段数量提50%
- **向后兼容**: 外部调用接口无需✅ 修改，自动享受性能提升

**🧪 测试验证**
- 全面测试了分页优化效
- 验证了多航线的稳定性和数据质量
- 确认了生产环境就绪状

### v0.5.3 (2025-06-28)

**🔧 重要修复**
- **修复Kiwi API价格显示问题**: 解决了所有航班段价格显示为¥0.0的问
- **修复往返航班段价格分配逻辑**: 正确处理往返航班段的价格分配
- **改善航线覆盖范围**: 移除了只返回隐藏城市航班段的限制，现在返回所有可用航
- **增强数据转换稳定*: 添加了字符串到数字的安全转换逻辑
- **提升商务舱搜索成功率**: 商务舱搜索现在能返回完整结果

**📈 性能改进**
- 往返航班段搜索索结果数量提44%（从平均2.25个增加到10个）
- 价格显示正确率从0%提升00%
- 航线覆盖成功率从25%提升00%
- 商务舱可用性从0%提升00%

**🧪 测试验证**
- 全面测试了伦北京和纽洛杉矶航
- 验证了经济舱和商务舱的搜索功
- 确认了常规航班段和隐藏城市航班段的正确显

### v0.5.2 及更早版
- 基础功能实现
- Google Flights API集成
- Kiwi API隐藏城市航班支持
- 双语支持（中文/英文）
- 双货币支持（CNY/USD）

---

**Smart Flights** - 让航班搜索更智能、更便捷！ ✈️