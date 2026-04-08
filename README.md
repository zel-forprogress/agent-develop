# ReAct Agent Project

这是一个基于 Python 的智能体（Agent）示例合集，围绕 ReAct 思维链条构建，涵盖「手动实现的 ReAct 循环」「JSON 结构化工具调用」「与 LangChain Agent 的对比」以及「CrewAI 多智能体协作」。项目同时演示了如何在保证安全的前提下使用外部工具与 API。

## 功能亮点

- **手动 ReAct 实现**：在 [react_manual.py](file:///d:/code/agent-week1/react_manual.py) 中完整复现 Thought → Action → Observation 的循环。
- **多工具协作**：接入 DuckDuckGo 搜索与 AST 安全计算器，根据任务自动选择工具。
- **JSON 工具协议**：在 [react_json_tool.py](file:///d:/code/agent-week1/react_json_tool.py) 中引导 LLM 以结构化 JSON 触发工具，便于可靠解析与扩展。
- **LangChain 对比**：在 [compare_with_langchain_agent.py](file:///d:/code/agent-week1/compare_with_langchain_agent.py) 中用官方 `create_agent` 构建同类任务，直观看到不同抽象层的差异。
- **CrewAI 团队协作**：在 [research_crew.py](file:///d:/code/agent-week1/research_crew.py) 中构建“研究员 + 写作者”两角色流水线，输出报告到 `output/report.md`。
- **安全与工程实践**：通过 `.env` 隔离密钥，`.gitignore` 忽略本地环境与缓存；计算器基于 AST 执行只读安全计算。

## 项目结构

- react_manual.py：手动 ReAct 循环（支持 search 与 calculator 两工具）。
- react_json_tool.py：JSON 驱动的工具调用示例（含模拟天气接口与安全计算器）。
- compare_with_langchain_agent.py：LangChain 官方 Agent 对比示例（仅打印最终答复）。
- research_crew.py：CrewAI 多智能体研究流水线，输出到 [output/report.md](file:///d:/code/agent-week1/output/report.md)。
- requirements.txt：依赖清单。
- .env.example：环境变量模板。

## 快速开始

- 准备虚拟环境并安装依赖

```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

- 配置密钥

```bash
cp .env.example .env
```
编辑 `.env`：
- DEEPSEEK_API_KEY：DeepSeek API Key（必须）。
- LANGCHAIN_API_KEY：可选，用于 LangChain 追踪或服务。

## 如何运行

- 手动 ReAct：
```bash
python react_manual.py
```

- JSON 工具调用：
```bash
python react_json_tool.py
```

- LangChain Agent 对比：
```bash
python compare_with_langchain_agent.py
```
默认仅输出最终回答；如需查看完整状态对象，可打印 `result`。

- CrewAI 多智能体研究流水线：
```bash
python research_crew.py
```
默认主题为“2026年AI Agent开发最新趋势”，结果写入 [output/report.md](file:///d:/code/agent-week1/output/report.md)。

## 常见问题

- 运行 CrewAI 报 “OPENAI_API_KEY is required”：
  - 本项目在 [research_crew.py](file:///d:/code/agent-week1/research_crew.py) 中已显式配置 DeepSeek（`LLM(model=\"deepseek/deepseek-chat\", base_url=\"https://api.deepseek.com\")`）。请确保 `.env` 中存在 `DEEPSEEK_API_KEY` 并已激活虚拟环境。
- 终端输出过多：
  - 将 Agent/Crew 的 `verbose` 设为 `False`，或仅打印最终结果。
- 清屏：
  - Windows 使用 `cls`，大多数终端可用 `Ctrl + L`。
- Python AST 警告：
  - 代码已统一使用 `ast.Constant`，避免旧版 `ast.Num` 的弃用警告。

## 安全与规范

- `.env` 内含私密 Key，请勿提交到仓库或分享给他人。
- 计算器工具仅支持受限的算术表达式，严禁执行任意代码。

## 许可证

MIT License
