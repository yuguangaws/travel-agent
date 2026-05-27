from typing import Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

# ====================== 1. 定义 State ======================
class TravelState(BaseModel):
    user_input: str = Field(default="", description="用户原始提问")
    origin: str = Field(default="", description="出发地")
    destination: str = Field(default="", description="目的地")
    start_date: str = Field(default="", description="出发日期")
    people_count: int = Field(default=1, description="出行人数")
    
    user_intent: str = Field(default="", description="LLM识别的用户意图")
    missing_info: List[str] = Field(default_factory=list)
    is_info_complete: bool = Field(default=False)
    
    # 4个MCP工具结果
    traffic_result: str = Field(default="")
    hotel_result: str = Field(default="")
    itinerary_result: str = Field(default="")
    budget_result: str = Field(default="")
    
    final_plan: str = Field(default="")
    messages: Annotated[List, add_messages] = Field(default_factory=list)

# ====================== 2. 核心节点（模拟LLM，无API！） ======================
def intent_analyze_node(state: TravelState):
    print("🔍 初始节点：LLM 意图识别 + 信息校验")
    
    # 模拟LLM解析结果（不联网、无API）
    user_input = state.user_input
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
    missing = "、".join(state.missing_info)
    print(f"❓ 缺少信息：{missing}，请补充")
    return {"messages": [f"请你补充：{missing}"]}

# 制定计划
def make_plan_node(state: TravelState):
    print("📋 信息齐全，开始执行4个MCP工具")
    return {}

# ---------------------- 4个 MCP 工具节点 ----------------------
def call_traffic_node(state: TravelState):
    print("🚗 调用MCP：获取交通方案")
    return {"traffic_result": f"{state.origin}→{state.destination}：推荐高铁 G101，时长4.5小时"}

def call_hotel_node(state: TravelState):
    print("🏨 调用MCP：获取酒店推荐")
    return {"hotel_result": f"{state.destination}：推荐南京路附近舒适型酒店，均价500/晚"}

def call_itinerary_node(state: TravelState):
    print("🗺️ 调用MCP：生成行程")
    return {"itinerary_result": f"{state.destination} 3日游：迪士尼→外滩→城隍庙"}

def call_budget_node(state: TravelState):
    print("💰 调用MCP：计算预算")
    return {"budget_result": f"2人总预算：约3000元（交通+住宿+门票）"}

# 汇总结果
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

# ====================== 3. 构建 Graph ======================
builder = StateGraph(TravelState)

# 添加节点
builder.add_node("intent_analyze_node", intent_analyze_node)
builder.add_node("collect_info_node", collect_info_node)
builder.add_node("make_plan_node", make_plan_node)
builder.add_node("call_traffic_node", call_traffic_node)
builder.add_node("call_hotel_node", call_hotel_node)
builder.add_node("call_itinerary_node", call_itinerary_node)
builder.add_node("call_budget_node", call_budget_node)
builder.add_node("summarize_node", summarize_node)

# 流程
builder.add_edge(START, "intent_analyze_node")

# 路由
def router_after_intent(state: TravelState):
    return "make_plan_node" if state.is_info_complete else "collect_info_node"

builder.add_conditional_edges("intent_analyze_node", router_after_intent)

# 工具执行链
builder.add_edge("make_plan_node", "call_traffic_node")
builder.add_edge("call_traffic_node", "call_hotel_node")
builder.add_edge("call_hotel_node", "call_itinerary_node")
builder.add_edge("call_itinerary_node", "call_budget_node")
builder.add_edge("call_budget_node", "summarize_node")
builder.add_edge("summarize_node", END)
builder.add_edge("collect_info_node", "intent_analyze_node")

# 编译
graph = builder.compile()

# ====================== 测试运行 ======================
if __name__ == "__main__":
    print("="*50)
    print("出行 Agent 启动成功！")
    print("="*50)
    
    # 运行
    result = graph.invoke({
        "user_input": "我要从北京去上海，5月1日出发，2个人",
        "messages": ["我要从北京去上海，5月1日出发，2个人"]
    })

    # 输出结果
    print(result["final_plan"])