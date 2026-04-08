# ReAct Agent Project

这是一个基于 Python 实现的 **ReAct (Reasoning and Acting)** 架构的智能代理项目。它展示了如何手动实现一个具备思考、行动、观察循环的 AI Agent，并与 LangChain 的内置 Agent 进行对比。

## 功能特点

- **手动 ReAct 实现**：深入展示了 Agent 的底层循环逻辑（Thought -> Action -> Observation）。
- **多工具支持**：
  - **实时搜索**：集成 DuckDuckGo 搜索，获取互联网最新信息。
  - **安全计算器**：基于 AST（抽象语法树）实现的数学运算工具，确保执行安全。
  - **模拟天气 API**：用于演示工具调用的 JSON 数据交互。
- **JSON 工具调用**：展示了如何引导 LLM 输出结构化的 JSON 格式来精确调用工具。
- **LangChain 对比**：提供了与 LangChain 官方 `create_agent` 方法的对比实现。
- **环境安全**：使用 `.env` 管理 API 密钥，并通过 `.gitignore` 保护敏感信息。

## 项目结构

- `react_manual.py`: **核心演示**。手动实现的 ReAct 循环，支持搜索和安全计算器。
- `react_json_tool.py`: 展示如何通过 JSON 格式让 Agent 调用自定义工具（如模拟天气接口）。
- `compare_with_langchain_agent.py`: 对比脚本，展示使用 LangChain 官方框架快速构建 Agent 的方法。
- `requirements.txt`: 项目所需的 Python 依赖库。
- `.env.example`: 环境变量配置模板。

## 快速开始

### 1. 环境准备
建议在虚拟环境中运行：
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 2. 配置 API 密钥
将 `.env.example` 复制为 `.env` 并填入您的 DeepSeek API 密钥：
```bash
cp .env.example .env
```
编辑 `.env` 文件：
- `DEEPSEEK_API_KEY`: 您的 DeepSeek API Key。
- `LANGCHAIN_API_KEY`: (可选) 用于 LangChain 追踪。

### 3. 运行项目
您可以分别运行不同的演示脚本：
```bash
# 运行手动 ReAct 演示
python react_manual.py

# 运行 JSON 工具调用演示
python react_json_tool.py

# 运行 LangChain 对比演示
python compare_with_langchain_agent.py
```

## 许可证
MIT License
