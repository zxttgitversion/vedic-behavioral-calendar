from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from app.api import upload
from app.api import profile  
from app.api import calendar

app = FastAPI()

# 告诉 FastAPI：HTML 模板放在哪
templates = Jinja2Templates(directory="app/templates")

# 注册 upload API
app.include_router(upload.router)
app.include_router(profile.router)
app.include_router(calendar.router)

# 首页：返回 HTML 页面
@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )
