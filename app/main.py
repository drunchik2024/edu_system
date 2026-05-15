from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.routers import auth, programs, disciplines, reports, rop

app = FastAPI(title="ИС Управления ОП — ВГТУ", docs_url="/api/docs")

# Статика: загружаемые файлы отчётов и CSS/JS-ресурсы
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
# rop.router зарегистрирован ДО programs.router: статический /programs/new
# матчится раньше динамического /programs/{id}
app.include_router(rop.router)
app.include_router(rop.api_router)
app.include_router(programs.router)
app.include_router(disciplines.router)
app.include_router(reports.router)


@app.get("/")
async def root():
    return RedirectResponse(url="/programs")


# 401 без токена → редирект на страницу входа вместо JSON-ошибки
@app.exception_handler(401)
async def unauthorized_handler(request: Request, exc):
    return RedirectResponse(url="/auth/login")
