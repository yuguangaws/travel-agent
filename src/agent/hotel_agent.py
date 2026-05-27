# hotel_agent.py 【全新文件】
import requests
from settings import GAODE_API_KEY, GAODE_POI_URL
import json
from settings import llm

def hotel_recommend_agent(city: str, budget: str, llm):
    """
    酒店推荐子Agent
    :param city: 目的地城市
    :param budget: 预算档次（经济型/舒适型/高档型/豪华型）
    :param llm: 主模型实例
    :return: top3酒店+推荐理由
    """
    if not city:
        return "❌ 无法推荐：未输入目的地城市"

    # ===================== 1. 根据预算匹配关键词 =====================
    budget_keyword_map = {
        "经济型": "快捷酒店 平价",
        "舒适型": "商务酒店 中档",
        "高档型": "四星级 高端",
        "豪华型": "五星级 奢华"
    }
    keyword = budget_keyword_map.get(budget, "经济型") + " 酒店"

    try:
        # ===================== 2. 调用高德API，拉取 30 个酒店 =====================
        params = {
            "key": GAODE_API_KEY,
            "keywords": keyword,
            "city": city,
            "offset": 30,        # 拉取30个
            "sort": "rating",    # 按评分排序
            "output": "json",
            "extensions": "all"
        }
        response = requests.get(GAODE_POI_URL, params=params, timeout=10)
        data = response.json()

        if data.get("status") != "1" or len(data.get("pois", [])) == 0:
            return f"❌ {city} 未找到符合 {budget} 预算的酒店"

        # ===================== 3. 清洗数据 + 取评分 Top3 =====================
        hotels = []
        for poi in data["pois"]:
            name = poi.get("name", "")
            address = poi.get("address", "")
            rating = poi.get("biz_ext", {}).get("rating", "0")
            price = poi.get("biz_ext", {}).get("price", "0")
            
            try:
                rating = float(rating)
                if rating >= 4.0 and name:  # 只保留高分有效酒店
                    hotels.append({
                        "name": name,
                        "address": address,
                        "rating": round(rating, 1),
                        "price": price
                    })
            except:
                continue

        if not hotels:
            return "❌ 未找到符合条件的高分酒店"

        top3_hotels = hotels[:3]  # 取Top3

        # ===================== 4. LLM生成专业推荐理由 =====================
        prompt = f"""
        你是专业旅行顾问，根据以下酒店信息，为每个酒店写1句精准、吸引人的推荐理由。
        城市：{city}
        预算：{budget}
        酒店列表：{json.dumps(top3_hotels, ensure_ascii=False)}

        输出格式（严格按格式，不要多余内容）：
        1. 【酒店名】| 评分：⭐X.X | 价格：XX | 理由：XXX
        2. 【酒店名】| 评分：⭐X.X | 价格：XX | 理由：XXX
        3. 【酒店名】| 评分：⭐X.X | 价格：XX | 理由：XXX
        """
        
        response = llm.invoke(prompt)
        return response.content.strip()

    except Exception as e:
        return f"❌ 酒店推荐子Agent异常：{str(e)}"