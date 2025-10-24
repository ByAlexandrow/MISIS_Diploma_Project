from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from api import router as api_router


app = FastAPI()

app.include_router(api_router, prefix="/api")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Главная страница сайта.
    Возвращает: шаблон index.html с объектом запроса.
    """
    return templates.TemplateResponse("base.html", {"request": request})
