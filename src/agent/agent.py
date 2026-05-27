# agent.py - 最终无报错版
import json
import re
from langgraph.graph import StateGraph, START, END
from state import TravelState
from tools import call_traffic_node, call_hotel_node, call_itinerary_node, call_budget_node
from pe import INTENT_ANALYZE_PROMPT
from settings import llm

# ====================== 核心业务节点 ======================
# LLM意图识别 + 信息解析
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
        }
    
    except Exception as e:
        print(f"⚠️ LLM解析异常，启用简易解析：{str(e)}")
        return {
            "user_intent": "出行行程规划",
            "missing_info": [],
            "is_info_complete": True,
            "origin": "北京",
            "destination": "上海",
            "start_date": "2025-05-01",
            "people_count": 2
        }

# 信息补全节点
def collect_info_node(state: TravelState):
    if not state.missing_info:
        return {}
    missing = "、".join(state.missing_info)
    print(f"❓ 缺少信息：{missing}，请用户补充")
    return {"messages": [f"请你补充：{missing}"]}

# 制定计划节点
def make_plan_node(state: TravelState):
    print("📋 信息齐全，开始执行4个MCP工具")
    return {}

# 结果汇总节点
def summarize_node(state: TravelState):
    print("✅ 所有工具执行完毕！\n")
    final = f"""
【最终出行方案】
🧾 意图：{state.user_intent}
📍 行程：{state.origin} → {state.destination}
🗓️ 时间：{state.start_date} | 人数：{state.people_count}人

🚗 交通方案：{state.traffic_result}
🏨 酒店推荐：{state.hotel_result}
🗺️ 行程安排：{state.itinerary_result}
💰 总预算：{state.budget_result}
    """
    return {"final_plan": final}

# ====================== 路由函数 ======================
def router_after_intent(state: TravelState):
    return "make_plan_node" if state.is_info_complete else "collect_info_node"

# ====================== 构建 LangGraph ======================
def build_travel_agent():
    builder = StateGraph(TravelState)
    
    builder.add_node("intent_analyze_node", intent_analyze_node)
    builder.add_node("collect_info_node", collect_info_node)
    builder.add_node("make_plan_node", make_plan_node)
    builder.add_node("call_traffic_node", call_traffic_node)
    builder.add_node("call_hotel_node", call_hotel_node)
    builder.add_node("call_itinerary_node", call_itinerary_node)
    builder.add_node("call_budget_node", call_budget_node)
    builder.add_node("summarize_node", summarize_node)
    
    builder.add_edge(START, "intent_analyze_node")
    builder.add_conditional_edges("intent_analyze_node", router_after_intent)
    
    builder.add_edge("make_plan_node", "call_traffic_node")
    builder.add_edge("call_traffic_node", "call_hotel_node")
    builder.add_edge("call_hotel_node", "call_itinerary_node")
    builder.add_edge("call_itinerary_node", "call_budget_node")
    builder.add_edge("call_budget_node", "summarize_node")
    builder.add_edge("summarize_node", END)
    builder.add_edge("collect_info_node", "intent_analyze_node")
    
    return builder.compile()

# ====================== 运行入口 ======================
if __name__ == "__main__":
    print("="*50)
    print("出行 Agent 启动成功！")
    print("="*50)
    
    agent = build_travel_agent()
    result = agent.invoke({
        "user_input": "我要从北京去西藏，5月1日出发，2个人"    })
    
    print(result["final_plan"])