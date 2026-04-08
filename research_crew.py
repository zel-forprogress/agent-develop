# research_crew.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, Process, LLM
from langchain_community.tools import DuckDuckGoSearchRun
from crewai.tools import tool # 导入 tool 装饰器

load_dotenv()

# 配置 DeepSeek LLM
deepseek_llm = LLM(
    model="deepseek/deepseek-chat",
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
    temperature=0.7
)

def build_research_crew(topic: str):
    # 将 LangChain 工具包装成 CrewAI 兼容的函数工具
    search_tool_lc = DuckDuckGoSearchRun()
    
    @tool("duckduckgo_search")
    def search_tool(query: str):
        """用于在互联网上搜索关于特定主题的最新信息。"""
        return search_tool_lc.run(query)

    researcher = Agent(
        role="Senior Researcher",
        goal=f"搜索并收集关于『{topic}』的准确信息，优先找最新、可信、可总结的内容",
        backstory="你擅长做网络研究、提炼要点、记录来源，输出结构化研究笔记。",
        tools=[search_tool],
        llm=deepseek_llm,
        verbose=True,
        allow_delegation=False,
    )

    writer = Agent(
        role="Professional Writer",
        goal=f"把关于『{topic}』的研究结果写成一份清晰、结构化、可读性强的 Markdown 报告",
        backstory="你擅长把零散研究资料整理成清楚的说明文和总结报告。",
        llm=deepseek_llm,
        verbose=True,
        allow_delegation=False,
    )

    research_task = Task(
        description=(
            f"研究主题：{topic}\n"
            "1. 使用搜索工具搜集最新相关信息\n"
            "2. 重点关注趋势、代表性产品/框架、常见架构、开发范式\n"
            "3. 输出结构化研究笔记，给后续写作者使用\n"
        ),
        expected_output=(
            "一份结构化研究笔记，包含："
            "关键趋势、代表工具/公司/框架、常见技术方向、值得关注的问题。"
        ),
        agent=researcher,
    )

    writing_task = Task(
        description=(
            f"基于研究员提供的结果，写一份主题为『{topic}』的 Markdown 报告。\n"
            "要求：\n"
            "- 有标题、摘要、小节标题\n"
            "- 内容清晰，不要空话\n"
            "- 给出最后的总结\n"
        ),
        expected_output="一份完整的 Markdown 报告，适合直接保存为 report.md",
        agent=writer,
        output_file="output/report.md",
    )

    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, writing_task],
        process=Process.sequential,
        verbose=True,
    )

    return crew


def run_research_crew(topic: str) -> str:
    Path("output").mkdir(exist_ok=True)
    crew = build_research_crew(topic)
    result = crew.kickoff(inputs={"topic": topic})
    return getattr(result, "raw", str(result))


if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "2026年AI Agent开发最新趋势"
    report = run_research_crew(topic)
    print("\n===== FINAL REPORT =====\n")
    print(report)