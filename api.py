from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from research_crew import run_research_crew
import uvicorn
import markdown

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"result": None}
    )

@app.post("/research", response_class=HTMLResponse)
async def start_research(request: Request, topic: str = Form(...)):
    # 调用 CrewAI 进行研究
    raw_result = run_research_crew(topic)
    
    # 将 Markdown 转换为 HTML 以便展示
    html_result = markdown.markdown(raw_result, extensions=['extra', 'codehilite', 'toc'])
    
    return templates.TemplateResponse(
        request=request, name="index.html", context={"topic": topic, "result": html_result}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)
