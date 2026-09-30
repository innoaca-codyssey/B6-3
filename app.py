from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from database import Base, SessionLocal, engine
from routers.task import router, templates
from routers.auth import router as public_router
from services.auth import AuthService, Forbidden, Unauthorized

@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        AuthService(db).seed()
    yield
    engine.dispose()

app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.include_router(public_router)
app.include_router(router)

async def error_page(request, error, status):
    with SessionLocal() as db:
        auth = AuthService(db).context(request.cookies.get('session'))
    return templates.TemplateResponse(request=request, name='error.html', context={'auth': auth, 'message': str(error)}, status_code=status)

@app.exception_handler(Unauthorized)
async def unauthenticated(request: Request, error: Unauthorized):
    return RedirectResponse('/login', status_code=303)

@app.exception_handler(Forbidden)
async def forbidden(request: Request, error: Forbidden):
    return await error_page(request, error, 403)

@app.exception_handler(LookupError)
async def missing(request: Request, error: LookupError):
    return await error_page(request, error, 404)

@app.exception_handler(ValueError)
async def invalid(request: Request, error: ValueError):
    return await error_page(request, error, 400)
