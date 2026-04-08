from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
import os

load_dotenv()

def get_weather(city: str) -> str:
    """获取指定城市的实时天气信息。输入参数 city 是城市名称（如：北京）。"""
    fake_db = {
        "北京": "北京明天多云，23度",
        "上海": "上海明天阴，20度"
    }
    return fake_db.get(city, f"暂不支持城市: {city}")

def calculator(expression: str) -> str:
    """执行数学运算。输入参数 expression 是一个数学表达式字符串（如：23 + 5）。"""
    return str(eval(expression))

model = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0,
)

agent = create_agent(
    model=model,
    tools=[get_weather, calculator],
    system_prompt="你是一个会使用工具的助手。需要天气时调用 get_weather，需要计算时调用 calculator。"
)

result = agent.invoke({
    "messages": [
        {"role": "user", "content": "帮我查询北京天气并计算明天温度+5度后的结果"}
    ]
})

# print(result)
print(result["messages"][-1].content)