# state.py - 出行Agent状态管理
from typing import Annotated, List
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

class TravelState(BaseModel):
    # 用户输入信息
    user_input: str = Field(default="", description="用户原始提问")
    origin: str = Field(default="", description="出发地")
    destination: str = Field(default="", description="目的地")
    start_date: str = Field(default="", description="出发日期")
    people_count: int = Field(default=1, description="出行人数")
    
    # 核心控制字段
    user_intent: str = Field(default="", description="LLM识别的用户意图")
    missing_info: List[str] = Field(default_factory=list, description="缺失的必填信息")
    is_info_complete: bool = Field(default=False, description="信息是否齐全")
    
    # MCP 工具执行结果
    traffic_result: str = Field(default="", description="交通方案")
    hotel_result: str = Field(default="", description="酒店推荐")
    itinerary_result: str = Field(default="", description="行程安排")
    budget_result: str = Field(default="", description="总预算预估")
    
    # ===================== 新增：预算计算用结构化数据 =====================
    total_distance: float = Field(default=0.0, description="自驾总里程(公里)")
    hotel_price_list: List[float] = Field(default_factory=list, description="推荐酒店单晚价格列表")
    travel_days: int = Field(default=3, description="出行总天数")
    scenic_count: int = Field(default=0, description="游玩景点总数")
    
    # 最终输出
    final_plan: str = Field(default="", description="完整出行方案")
    messages: Annotated[List, add_messages] = Field(default_factory=list)