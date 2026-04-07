# ReAct Agent Project

这是一个基于 Python 实现的 ReAct (Reasoning and Acting) 架构的智能代理项目。它利用 LangChain 和 DeepSeek API 来实现一个能够进行思考和搜索的 Agent。

## 功能特点

- **ReAct 架构**：实现标准的 "Thought -> Action -> Observation -> Thought" 循环。
- **搜索工具**：集成 DuckDuckGo 搜索功能，支持获取实时信息。
- **DeepSeek 支持**：使用 DeepSeek-chat 模型作为核心推理引擎。
- **环境隔离**：支持使用 `.env` 文件管理敏感配置（如 API 密钥）。

## 项目结构

- `react_mannual.py`: 项目核心代码，包含 Agent 的主循环逻辑。
- `requirements.txt`: 项目所需的 Python 依赖库。
- `.env.example`: 环境变量配置模板。
- `.gitignore`: Git 忽略规则文件，确保隐私安全。

## 快速开始

### 1. 克隆项目
```bash
git clone <your-repo-url>
cd agent-week1
```

### 2. 安装依赖
建议在虚拟环境中运行：
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 配置环境变量
将 `.env.example` 复制为 `.env` 并填入您的 API 密钥：
```bash
cp .env.example .env
```
编辑 `.env` 文件：
- `DEEPSEEK_API_KEY`: 您的 DeepSeek API Key。
- `LANGCHAIN_API_KEY`: (可选) 您的 LangChain API Key。

### 4. 运行项目
```bash
python react_mannual.py
```

## 贡献指南
欢迎提交 Issue 或 Pull Request 来改进本项目。

## 许可证
MIT License
