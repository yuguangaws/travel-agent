import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatZhipuAI
from langchain_community.embeddings import ZhipuAIEmbeddings

# 加载环境变量
load_dotenv()

# ===================== LLM 配置 =====================
ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY")
ZHIPUAI_MODEL = os.getenv("ZHIPUAI_DEFAULT_MODEL", "glm-3-turbo")

# 生成用LLM
llm = ChatZhipuAI(
    model=ZHIPUAI_MODEL,
    temperature=0,
    api_key=ZHIPUAI_API_KEY
)
# 校验用LLM
llm_validate = ChatZhipuAI(
    model=ZHIPUAI_MODEL,
    temperature=0,
    api_key=ZHIPUAI_API_KEY
)

# =====================  Embedding 配置 =====================
embedding = ZhipuAIEmbeddings(
    api_key=ZHIPUAI_API_KEY,
    model="embedding-2"
)

GAODE_API_KEY = os.getenv("GAODE_API_KEY")
GAODE_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"  # 地理编码API
GAODE_DRIVING_URL = "https://restapi.amap.com/v3/direction/driving"  # 驾车路线API
GAODE_POI_URL = "https://restapi.amap.com/v3/place/text"         # 🔥 新增：POI搜索（酒店/景点）
