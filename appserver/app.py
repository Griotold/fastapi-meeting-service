from fastapi import FastAPI
from appserver.apps.account.endpoints import router as account_router
from appserver.apps.calendar.endpoints import router as calendar_router

app = FastAPI()

def include_routers(_app: FastAPI):
    _app.include_router(account_router)
    _app.include_router(calendar_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}

include_routers(app)