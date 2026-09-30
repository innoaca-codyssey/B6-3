from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from database import Base, engine
from routers.task import router, templates


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    yield
    engine.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(router)


@app.exception_handler(LookupError)
async def missing(request: Request, error: LookupError):
    return templates.TemplateResponse(request=request, name='error.html', context={'message': str(error)}, status_code=404)


@app.exception_handler(ValueError)
async def invalid(request: Request, error: ValueError):
    return templates.TemplateResponse(request=request, name='error.html', context={'message': str(error)}, status_code=400)
