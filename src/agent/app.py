# app.py - Streamlit 交互式出行 Agent UI
import streamlit as st
import json
from state import TravelState
from agent import build_travel_agent

# ---------------------- 页面配置 ----------------------
st.set_page_config(
    page_title="智能出行规划助手",
    page_icon="✈️",
    layout="wide"
)

# ---------------------- UI 标题 ----------------------
st.title("✈️ 智能出行规划助手")
st.subheader("输入出行信息，一键生成完整旅行方案")
st.divider()

# ---------------------- 侧边栏：输入表单 ----------------------
with st.sidebar:
    st.header("📝 出行信息填写")
    origin = st.text_input("出发地", value="北京", placeholder="例如：北京市朝阳区")
    destination = st.text_input("目的地", value="上海", placeholder="例如：上海市浦东新区")
    start_date = st.text_input("出发日期", value="2025-05-01")
    people_count = st.number_input("出行人数", min_value=1, max_value=10, value=2)
    
    # 生成按钮
    generate_btn = st.button("🚀 生成出行方案", type="primary", use_container_width=True)

# ---------------------- 加载 Agent ----------------------
@st.cache_resource
def load_agent():
    return build_travel_agent()

agent = load_agent()

# ---------------------- 执行 Agent 并展示结果 ----------------------
if generate_btn:
    # 1. 组装用户输入
    user_input = f"我要从{origin}去{destination}，{start_date}出发，{people_count}个人"
    
    with st.spinner("🔍 LLM正在解析意图 + 调用高德API生成方案..."):
        try:
            # 2. 调用 Agent
            result = agent.invoke({
                "user_input": user_input,
                "origin": origin,
                "destination": destination,
                "start_date": start_date,
                "people_count": people_count,
                "messages": [user_input]
            })

            # 3. 分模块展示结果（清晰美观）
            st.success("✅ 方案生成完成！")
            st.divider()

            # 基础信息
            st.markdown(f"### 🧾 基础信息")
            st.write(f"**出发地**：{origin}")
            st.write(f"**目的地**：{destination}")
            st.write(f"**出发日期**：{start_date}")
            st.write(f"**出行人数**：{people_count}人")
            st.divider()

            # 交通方案
            st.markdown("### 🚗 交通方案")
            st.text(result["traffic_result"])
            st.divider()

            # 酒店推荐
            st.markdown("### 🏨 酒店推荐")
            st.text(result["hotel_result"])
            st.divider()

            # 行程安排
            st.markdown("### 🗺️ 行程安排")
            st.text(result["itinerary_result"])
            st.divider()

            # 预算明细
            st.markdown("### 💰 预算明细")
            st.text(result["budget_result"])

        except Exception as e:
            st.error(f"❌ 生成失败：{str(e)}")

# ---------------------- 底部说明 ----------------------
st.divider()
st.caption("✅ 基于 LangGraph + 高德API + Streamlit 构建的智能出行Agent")