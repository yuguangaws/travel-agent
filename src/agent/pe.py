# pe.py - 所有Prompt模板存放
# 意图识别 + 信息校验 核心Prompt（LLM使用）
# pe.py 【替换为这个】
INTENT_ANALYZE_PROMPT = """
你的任务只有3个，严格执行，**只输出JSON，不输出任何文字、解释、标点、markdown格式**！

用户输入：{user_input}

任务1：识别用户意图，只能是：出行行程规划、查询交通、查询酒店、其他
任务2：从用户输入中提取：出发地、目的地、出发日期、出行人数
任务3：检查4个必填项是否齐全，返回缺失列表

【输出要求】
1. 只返回JSON字符串，无任何其他内容
2. 不要```json```，不要解释，不要换行
3. 字段严格如下：

{{
    "user_intent": "字符串",
    "missing_info": ["字符串数组"],
    "is_info_complete": 布尔值,
    "origin": "字符串",
    "destination": "字符串",
    "start_date": "字符串",
    "people_count": 数字
}}
"""