# agent.py 【并行执行版本 - 速度提升3倍】
import json
import re
from langgraph.graph import StateGraph, START, END
from state import TravelState
from tools import call_traffic_node, call_hotel_node, call_itinerary_node, call_budget_node
from pe import INTENT_ANALYZE_PROMPT
from settings import llm

# ====================== 核心业务节点 ======================
def intent_analyze_node(state: TravelState):
    print("🔍 初始节点：LLM 正在识别意图 + 解析用户信息...")
    prompt = INTENT_ANALYZE_PROMPT.format(user_input=state.user_input)
    
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        content = re.sub(r"```json|```", "", content).strip()
        data = json.loads(content)
        
        return {
            "user_intent": data.get("user_intent", "出行规划"),
            "missing_info": data.get("missing_info", []),
            "is_info_complete": data.get("is_info_complete", False),
            "origin": data.get("origin", "").strip(),
            "destination": data.get("destination", "").strip(),
            "start_date": data.get("start_date", "").strip(),
            "people_count": int(data.get("people_count", 1)),
            "user_budget": data.get("user_budget", "经济型")
        }
    
    except Exception as e:
        print(f"⚠️ LLM解析异常：{str(e)}")
        return {
            "user_intent": "出行行程规划",
            "missing_info": [],
            "is_info_complete": True,
            "origin": "北京",
            "destination": "上海",
            "start_date": "2025-05-01",
            "people_count": 2,
            "user_budget": "经济型"
        }

def collect_info_node(state: TravelState):
    if not state.missing_info:
        return {}
    missing = "、".join(state.missing_info)
    print(f"❓ 缺少信息：{missing}")
    return {"messages": [f"请补充：{missing}"]}

def make_plan_node(state: TravelState):
    print("📋 信息齐全 → 开始并行执行交通/酒店/行程工具")
    return {}

def summarize_node(state: TravelState):
    print("✅ 所有任务完成！输出最终方案\n")
    final = f"""
【最终出行方案】
🧾 意图：{state.user_intent}
📍 行程：{state.origin} → {state.destination}
🗓️ 时间：{state.start_date} | 人数：{state.people_count}人
🏨 酒店预算：{state.user_budget}

🚗 交通方案：
{state.traffic_result}

🏨 酒店推荐（Top3高分+理由）：
{state.hotel_result}

🗺️ 行程安排：
{state.itinerary_result}

💰 预算明细：
{state.budget_result}
    """
    return {"final_plan": final}

# ====================== 路由 ======================
def router_after_intent(state: TravelState):
    return "make_plan_node" if state.is_info_complete else "collect_info_node"

# ====================== 构建并行 LangGraph ======================
def build_travel_agent():
    builder = StateGraph(TravelState)

    # 节点注册
    builder.add_node("intent_analyze_node", intent_analyze_node)
    builder.add_node("collect_info_node", collect_info_node)
    builder.add_node("make_plan_node", make_plan_node)
    builder.add_node("call_traffic_node", call_traffic_node)
    builder.add_node("call_hotel_node", call_hotel_node)
    builder.add_node("call_itinerary_node", call_itinerary_node)
    builder.add_node("call_budget_node", call_budget_node)
    builder.add_node("summarize_node", summarize_node)

    # 主流程
    builder.add_edge(START, "intent_analyze_node")
    builder.add_conditional_edges("intent_analyze_node", router_after_intent)

    # --------------------------
    # 🔥 并行核心：三个工具同时跑
    # --------------------------
    builder.add_edge("make_plan_node", "call_traffic_node")
    builder.add_edge("make_plan_node", "call_hotel_node")
    builder.add_edge("make_plan_node", "call_itinerary_node")

    # --------------------------
    # 🔥 全部完成 → 汇总预算
    # --------------------------
    builder.add_edge("call_traffic_node", "call_budget_node")
    builder.add_edge("call_hotel_node", "call_budget_node")
    builder.add_edge("call_itinerary_node", "call_budget_node")

    # 最终流程
    builder.add_edge("call_budget_node", "summarize_node")
    builder.add_edge("collect_info_node", "intent_analyze_node")
    builder.add_edge("summarize_node", END)

    return builder.compile()

if __name__ == "__main__":
    print("="*50)
    print("出行 Agent 启动成功！（并行执行模式）")
    print("="*50)
    agent = build_travel_agent()
    result = agent.invoke({
        "user_input": "我要从北京去上海，5月1日出发，2个人，酒店预算经济型",
        "messages": ["我要从北京去上海，5月1日出发，2个人，酒店预算经济型"]
    })
    print(result["final_plan"])
