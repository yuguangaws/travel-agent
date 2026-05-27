# tools.py - MCP 工具集（交通+酒店+行程+预算 高德API完整版）
import requests
from state import TravelState
from settings import GAODE_API_KEY, GAODE_GEOCODE_URL, GAODE_DRIVING_URL, GAODE_POI_URL
from hotel_agent import hotel_recommend_agent
from settings import llm
# ====================== 公共工具：地址转经纬度 ======================
def geocode_address(address: str) -> str:
    """地址转经纬度"""
    if not address:
        return ""
    address = address.strip().replace(" ", "")
    try:
        params = {
            "key": GAODE_API_KEY,
            "address": address,
            "output": "json"
        }
        response = requests.get(GAODE_GEOCODE_URL, params=params, timeout=10)
        data = response.json()
        if data.get("status") == "1" and int(data.get("count", 0)) > 0:
            return data["geocodes"][0]["location"]
        return ""
    except:
        return ""

# ====================== 工具1：交通方案（新增里程字段） ======================
def call_traffic_node(state: TravelState):
    print("🚗 调用高德API：生成交通方案")
    origin_addr = state.origin
    dest_addr = state.destination
    if not origin_addr or not dest_addr:
        return {
            "traffic_result": "无法规划：缺少出发地/目的地",
            "total_distance": 0.0
        }
    
    origin = geocode_address(origin_addr)
    destination = geocode_address(dest_addr)
    if not origin or not destination:
        return {
            "traffic_result": "地址解析失败，请输入完整城市地址",
            "total_distance": 0.0
        }

    try:
        params = {
            "key": GAODE_API_KEY,
            "origin": origin,
            "destination": destination,
            "extensions": "all",
            "output": "json"
        }
        response = requests.get(GAODE_DRIVING_URL, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "1":
            route = data["route"]["paths"][0]
            distance = float(route["distance"]) / 1000  # 米 → 公里
            duration = int(route["duration"]) / 60      # 秒 → 分钟
            traffic_text = (
                f"{origin_addr} → {dest_addr}\n"
                f"🚗 出行方式：自驾\n"
                f"📏 全程：{distance:.1f} 公里\n"
                f"⏱️ 预计：{duration:.0f} 分钟"
            )
            # 返回文本 + 结构化里程数据
            return {
                "traffic_result": traffic_text,
                "total_distance": round(distance, 1)
            }
        else:
            return {
                "traffic_result": f"API错误：{data.get('info')}",
                "total_distance": 0.0
            }
    except Exception as e:
        return {
            "traffic_result": f"调用失败：{str(e)}",
            "total_distance": 0.0
        }

# ====================== 工具2：酒店推荐（调用子Agent） ======================
def call_hotel_node(state: TravelState):
    print("🏨 启动酒店推荐子Agent，生成Top3高评分酒店")
    
    city = state.destination
    budget = state.user_budget
    
    # 调用子Agent
    hotel_result = hotel_recommend_agent(city, budget, llm)
    
    return {
        "hotel_result": hotel_result
    }

# ====================== 工具3：行程规划（统计景点数量） ======================
def call_itinerary_node(state: TravelState):
    print("🗺️ 调用高德API：生成景点与行程安排")
    city = state.destination
    if not city:
        return {
            "itinerary_result": "无法规划行程：缺少目的地城市",
            "travel_days": 3,
            "scenic_count": 0
        }

    try:
        params = {
            "key": GAODE_API_KEY,
            "keywords": "旅游景点",
            "city": city,
            "offset": 8,
            "output": "json",
            "extensions": "all"
        }
        response = requests.get(GAODE_POI_URL, params=params, timeout=10)
        data = response.json()

        scenic_num = 0
        if data.get("status") == "1" and len(data.get("pois", [])) > 0:
            poi_list = data["pois"]
            scenic_num = len(poi_list)
            itinerary = f"【{city} 精选3日游玩行程】\n"

            day1 = poi_list[0:3]
            day2 = poi_list[3:6]
            day3 = poi_list[6:8]

            itinerary += "\n📅 第一天：经典地标打卡\n"
            for spot in day1:
                name = spot.get("name", "")
                addr = spot.get("address", "暂无详细地址")
                score = spot.get("biz_ext", {}).get("rating", "暂无评分")
                itinerary += f"• {name} | ⭐{score}\n  地址：{addr}\n"

            itinerary += "\n📅 第二天：休闲风光游览\n"
            for spot in day2:
                name = spot.get("name", "")
                addr = spot.get("address", "暂无详细地址")
                score = spot.get("biz_ext", {}).get("rating", "暂无评分")
                itinerary += f"• {name} | ⭐{score}\n  地址：{addr}\n"

            itinerary += "\n📅 第三天：特色体验游玩\n"
            for spot in day3:
                name = spot.get("name", "")
                addr = spot.get("address", "暂无详细地址")
                score = spot.get("biz_ext", {}).get("rating", "暂无评分")
                itinerary += f"• {name} | ⭐{score}\n  地址：{addr}\n"
        else:
            itinerary = f"{city} 暂未查询到相关旅游景点，无法生成行程"

        return {
            "itinerary_result": itinerary,
            "travel_days": 3,
            "scenic_count": scenic_num
        }
    except Exception as e:
        return {
            "itinerary_result": f"行程规划失败：{str(e)}",
            "travel_days": 3,
            "scenic_count": 0
        }

# ====================== 工具4：预算计算（🔥 全新实现，分项核算） ======================
def call_budget_node(state: TravelState):
    print("💰 开始综合计算出行预算")
    # 读取状态中的结构化数据
    people = state.people_count
    days = state.travel_days
    scenic_num = state.scenic_count
    distance = state.total_distance
    price_list = state.hotel_price_list

    # ========== 1. 基础参数兜底（数据缺失时使用默认值） ==========
    # 住宿：3天行程住2晚，双人一间，取酒店均价；无价格则默认400元/晚
    stay_nights = days - 1
    if price_list:
        avg_hotel_price = sum(price_list) / len(price_list)
    else:
        avg_hotel_price = 400.0

    # 费用单价（可自行修改）
    unit_km_cost = 0.8       # 自驾：元/公里
    unit_ticket = 60.0       # 景点门票：元/人/个
    unit_food = 80.0         # 餐饮：元/人/天
    extra_rate = 0.05        # 杂项比例 5%

    # ========== 2. 分项计算 ==========
    # 交通费用
    traffic_cost = distance * unit_km_cost
    # 住宿费用（双人一间，只算房间费）
    hotel_cost = avg_hotel_price * stay_nights
    # 门票费用
    ticket_cost = people * scenic_num * unit_ticket
    # 餐饮费用
    food_cost = people * days * unit_food
    # 基础合计
    base_total = traffic_cost + hotel_cost + ticket_cost + food_cost
    # 杂项费用
    extra_cost = base_total * extra_rate
    # 最终总预算
    total_cost = base_total + extra_cost

    # ========== 3. 拼接预算明细文本 ==========
    budget_text = "【出行预算明细】\n"
    budget_text += f"👥 出行人数：{people} 人 | 📅 出行天数：{days} 天（住宿 {stay_nights} 晚）\n\n"
    budget_text += f"🚗 交通费用（自驾）：{traffic_cost:.2f} 元\n"
    budget_text += f"🏨 住宿费用（均价 {avg_hotel_price:.0f} 元/晚）：{hotel_cost:.2f} 元\n"
    budget_text += f"🎫 景点门票（共 {scenic_num} 个景点）：{ticket_cost:.2f} 元\n"
    budget_text += f"🍚 餐饮费用：{food_cost:.2f} 元\n"
    budget_text += f"🎁 杂项费用（小交通/纪念品）：{extra_cost:.2f} 元\n"
    budget_text += f"\n💴 本次出行合计总预算：{total_cost:.2f} 元"

    return {"budget_result": budget_text}