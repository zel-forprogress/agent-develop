from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import os
import json
import re
import ast
import operator

load_dotenv()

llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0,
    max_tokens=1500,
)

# =========================
# 1) 自定义 Tool：假的天气 API
# =========================
def fake_weather_api(city: str) -> str:
    city = city.strip()

    fake_db = {
        "北京": {
            "city": "北京",
            "today_weather": "晴",
            "today_temp": 21,
            "tomorrow_weather": "多云",
            "tomorrow_temp": 23,
        },
        "上海": {
            "city": "上海",
            "today_weather": "小雨",
            "today_temp": 19,
            "tomorrow_weather": "阴",
            "tomorrow_temp": 20,
        },
        "深圳": {
            "city": "深圳",
            "today_weather": "阵雨",
            "today_temp": 27,
            "tomorrow_weather": "多云",
            "tomorrow_temp": 29,
        },
    }

    if city not in fake_db:
        return json.dumps(
            {"error": f"暂不支持城市: {city}"},
            ensure_ascii=False
        )

    return json.dumps(fake_db[city], ensure_ascii=False)


# =========================
# 2) 自定义 Tool：安全计算器
# =========================
_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def safe_calculate(expression: str) -> str:
    def _eval(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("只允许数字常量")
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _ALLOWED_OPERATORS:
                raise ValueError(f"不支持的运算符: {op_type.__name__}")
            left = _eval(node.left)
            right = _eval(node.right)
            return _ALLOWED_OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _ALLOWED_OPERATORS:
                raise ValueError(f"不支持的单目运算符: {op_type.__name__}")
            operand = _eval(node.operand)
            return _ALLOWED_OPERATORS[op_type](operand)
        else:
            raise ValueError(f"不支持的表达式类型: {type(node).__name__}")

    try:
        expression = expression.strip()
        tree = ast.parse(expression, mode="eval")
        result = _eval(tree.body)
        return json.dumps(
            {"expression": expression, "result": result},
            ensure_ascii=False
        )
    except Exception as e:
        return json.dumps(
            {"error": f"计算失败: {e}"},
            ensure_ascii=False
        )


# =========================
# 3) 严格 JSON 输出 Prompt
# =========================
REACT_SYSTEM_PROMPT = """
你是一个精确、可靠的 ReAct 助手。

你必须且只能输出一个 JSON 对象。
不要输出 Markdown，不要输出代码块，不要输出额外解释，不要输出 Observation。

你只能输出以下两种 JSON 之一：

格式 A（继续调用工具）：
{
  "thought": "你对下一步的思考",
  "action": "weather 或 calculator",
  "action_input": "工具输入"
}

格式 B（结束）：
{
  "thought": "你对最终结论的思考",
  "final_answer": "给用户的最终答案"
}

工具说明：
1. weather
   - 用于查询城市天气
   - action_input 只填城市名，例如：北京

2. calculator
   - 用于做数学计算
   - action_input 必须是纯数学表达式，例如：
     "23 + 5"
     "(18 + 5) * 2"
     "25 / 4"

规则：
1. 每次只能输出一个 JSON 对象
2. 不能同时出现 action 和 final_answer
3. 如果缺少外部天气信息，先用 weather
4. 如果需要做数值运算，必须用 calculator
5. calculator 的输入必须是纯表达式，不能写自然语言
6. 已经可以回答时，直接输出 final_answer
7. 你绝不能输出 Observation 字段
"""

def build_user_prompt(question: str, history: list) -> str:
    return f"""用户问题：
{question}

以下是之前的执行历史（由程序提供）：
{json.dumps(history, ensure_ascii=False, indent=2)}

现在请输出下一步唯一合法的 JSON 对象：
"""


# =========================
# 4) 解析 JSON
# =========================
def extract_json_object(text: str) -> dict:
    text = text.strip()

    # 去掉可能出现的 ```json ... ```
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # 优先尝试整体解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 兜底：提取第一个 {...}
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError("未解析到合法 JSON")


def validate_json_output(data: dict, allowed_actions: set):
    if not isinstance(data, dict):
        raise ValueError("输出必须是 JSON 对象")

    if "observation" in data:
        raise ValueError("模型不允许输出 observation")

    if "thought" not in data or not isinstance(data["thought"], str):
        raise ValueError("必须包含字符串字段 thought")

    has_action = "action" in data
    has_final = "final_answer" in data

    if has_action and has_final:
        raise ValueError("不能同时包含 action 和 final_answer")

    if not has_action and not has_final:
        raise ValueError("必须包含 action 或 final_answer 之一")

    if has_action:
        if "action_input" not in data:
            raise ValueError("有 action 时必须有 action_input")

        action = str(data["action"]).strip().lower()
        if action not in allowed_actions:
            raise ValueError(f"非法工具: {action}")

        if not isinstance(data["action_input"], str):
            raise ValueError("action_input 必须是字符串")

    if has_final:
        if not isinstance(data["final_answer"], str):
            raise ValueError("final_answer 必须是字符串")


# =========================
# 5) Tool 分发
# =========================
def run_tool(action: str, action_input: str) -> str:
    action = action.strip().lower()

    if action == "weather":
        return fake_weather_api(action_input)

    if action == "calculator":
        return safe_calculate(action_input)

    return json.dumps({"error": f"未知工具: {action}"}, ensure_ascii=False)


# =========================
# 6) 主循环
# =========================
def run_react_agent(question: str, max_steps: int = 5):
    print(f"问题: {question}\n")
    history = []
    allowed_actions = {"weather", "calculator"}

    for step in range(1, max_steps + 1):
        user_prompt = build_user_prompt(question, history)

        try:
            response = llm.invoke([
                SystemMessage(content=REACT_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ])
            raw_output = response.content.strip()
        except Exception as e:
            print(f"LLM 调用失败: {repr(e)}")
            return None

        print(f"===== Step {step} Raw LLM Output =====")
        print(raw_output)
        print("======================================\n")

        try:
            data = extract_json_object(raw_output)
            validate_json_output(data, allowed_actions)
        except Exception as e:
            print(f"❌ JSON 输出不合法: {e}")
            print("原始输出如下：")
            print(raw_output)
            return None

        # Final Answer
        if "final_answer" in data:
            print(f"✅ 最终答案: {data['final_answer']}")
            return data["final_answer"]

        # Tool Action
        action = data["action"].strip().lower()
        action_input = data["action_input"].strip()

        print(f"执行工具 → {action} | 输入: {action_input}")

        try:
            observation = run_tool(action, action_input)
        except Exception as e:
            observation = json.dumps(
                {"error": f"工具调用失败: {e}"},
                ensure_ascii=False
            )

        print(f"Observation: {observation}\n")

        history.append({
            "step": step,
            "assistant_output": data,
            "observation": observation
        })

    print("达到最大步数")
    return None


if __name__ == "__main__":
    test_question = "帮我查询北京天气并计算明天温度+5度后的结果"
    run_react_agent(test_question)