from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import SystemMessage, HumanMessage
import re
import os
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
# 搜索工具
search_tool = DuckDuckGoSearchRun()

# 安全计算器：支持 + - * / % ** 和括号
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
        if isinstance(node, ast.Constant):  # Python 3.8+ 统一使用 Constant
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("只允许数字常量")
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
        return str(result)
    except Exception as e:
        return f"计算失败: {e}"

REACT_SYSTEM_PROMPT = """
你是一个精确、可靠的 ReAct 助手。

你只能输出下面两种格式之一，必须严格遵守：

格式 A：
Thought: <你对下一步的思考>
Action: search 或 calculator
Action Input: <工具输入>

格式 B：
Thought: <你对当前结论的思考>
Final Answer: <最终答案>

工具说明：
1. search
   - 用于查询外部信息
   - Action Input 应该是简洁的搜索关键词
2. calculator
   - 用于数学计算
   - Action Input 必须是纯数学表达式，例如：
     3 + 5
     (18 + 5) * 2
     25 / 4

规则：
1. 绝对不允许输出 Observation
2. Observation 只能由程序在工具执行后提供
3. 一轮最多只能有一个 Action
4. 不能同时出现 Action 和 Final Answer
5. 需要外部事实时，优先用 search
6. 需要数学运算时，必须用 calculator
7. 如果信息已经足够，直接给 Final Answer
8. Action Input 要简洁，不要加多余解释
9. calculator 的输入必须是可直接计算的表达式，不能写自然语言
"""

# 构建用户提示，包含问题和之前的思考过程
def build_user_prompt(question: str, scratchpad: str) -> str:
    return f"""Question: {question}

{scratchpad}"""

# 解析 Final Answer，支持多行内容
def parse_final_answer(response_text: str):
    match = re.search(r"(?im)^\s*Final Answer\s*:\s*(.*)$", response_text)
    if not match:
        return None

    first_line = match.group(1).strip()
    rest = response_text[match.end():].strip()

    if rest:
        return f"{first_line}\n{rest}".strip()
    return first_line
# 解析 Action 和 Action Input
def parse_action(response_text: str):
    action_match = re.search(r"(?im)^\s*Action\s*:\s*(.+?)\s*$", response_text)
    action_input_match = re.search(r"(?im)^\s*Action Input\s*:\s*(.+?)\s*$", response_text)

    if not action_match:
        return None

    if not action_input_match:
        raise ValueError("Found Action but missing Action Input.")

    action = action_match.group(1).strip().lower()
    action_input = action_input_match.group(1).strip().strip('"').strip("'")

    return action, action_input

# 校验模型输出是否符合规范，并且 Action 是否在允许的工具列表中
def validate_output(response_text: str, allowed_actions: set):
    text = response_text.strip()

    # 不允许模型输出 Observation
    if re.search(r"(?im)^\s*Observation\s*:", text):
        raise ValueError("模型不允许生成 Observation。")

    thought_matches = re.findall(r"(?im)^\s*Thought\s*:", text)
    action_matches = re.findall(r"(?im)^\s*Action\s*:\s*(.+?)\s*$", text)
    action_input_matches = re.findall(r"(?im)^\s*Action Input\s*:", text)
    final_matches = re.findall(r"(?im)^\s*Final Answer\s*:", text)

    # 可选：要求必须有 Thought
    if len(thought_matches) != 1:
        raise ValueError("每轮必须且只能有一个 Thought。")

    if len(final_matches) > 1:
        raise ValueError("Final Answer 不能出现多次。")

    if len(action_matches) > 1:
        raise ValueError("一轮不能有多个 Action。")

    if action_matches and final_matches:
        raise ValueError("不能同时出现 Action 和 Final Answer。")

    if action_matches:
        if len(action_input_matches) != 1:
            raise ValueError("有 Action 时，必须且只能有一个 Action Input。")

        action_name = action_matches[0].strip().lower()
        if action_name not in allowed_actions:
            raise ValueError(f"非法工具: {action_name}，允许的工具: {allowed_actions}")
    else:
        if action_input_matches:
            raise ValueError("不能只有 Action Input 没有 Action。")

    if not action_matches and not final_matches:
        raise ValueError("必须包含 Action 或 Final Answer 之一。")

# 主循环，执行 ReAct Agent
def run_react_agent(question: str, max_steps: int = 5):
    print(f"问题: {question}\n")
    scratchpad = ""
    allowed_actions = {"search", "calculator"}

    for step in range(1, max_steps + 1):
        user_prompt = build_user_prompt(question, scratchpad)

        try:
            response = llm.invoke([
                SystemMessage(content=REACT_SYSTEM_PROMPT),
                HumanMessage(content=user_prompt),
            ])
            output = response.content.strip()
        except Exception as e:
            print(f"LLM 调用失败: {e}")
            return None

        print(f"===== Step {step} Raw LLM Output =====")
        print(output)
        print("======================================\n")

        # 1. 先校验
        try:
            validate_output(output, allowed_actions)
        except Exception as e:
            print(f"❌ 模型输出违规: {e}")
            print("原始输出如下：")
            print(output)
            return None

        # 2. 再判断是否 Final Answer
        final_answer = parse_final_answer(output)
        if final_answer is not None:
            print(f"✅ 最终答案: {final_answer}")
            return final_answer

        # 3. 再解析 Action
        try:
            parsed = parse_action(output)
            if parsed is None:
                print("⚠️ 未解析到 Action")
                return None
            action, action_input = parsed
        except Exception as e:
            print(f"⚠️ Action 解析失败: {e}")
            return None

        print(f"执行工具 → {action} | 输入: {action_input}")

        try:
            if action == "search":
                observation = search_tool.run(action_input)
                if not observation or not observation.strip():
                    observation = "搜索结果为空，请尝试更精确的关键词。"

            elif action == "calculator":
                observation = safe_calculate(action_input)

            else:
                observation = f"未知工具: {action}"
        except Exception as e:
            observation = f"工具调用失败: {e}"

        print(f"Observation: {observation[:800]}...\n")

        # 关键修复：不要再外面包 Thought:
        scratchpad += f"\n{output}\nObservation: {observation}\n"

    print("达到最大步数")
    return None

if __name__ == "__main__":
    test_question = "Python 是哪一年发布的？然后用这个年份减去 10"
    run_react_agent(test_question)