from pathlib import Path
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from auth.session import require_csrf, require_session
from database import get_db
from services.task import TaskService

router = APIRouter(prefix='/app')
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / 'templates'))

def render(request, name, context, **values):
    return templates.TemplateResponse(request=request, name=name, context=dict(auth=context, **values))

@router.get('/projects')
def projects(request: Request, auth=Depends(require_session), db=Depends(get_db)):
    return render(request, 'projects.html', auth, projects=TaskService(db, auth.user_id).projects())

@router.get('/projects/new')
def new_project(request: Request, auth=Depends(require_session)):
    return render(request, 'project-form.html', auth)

@router.post('/projects')
def create_project(name: str = Form(''), auth=Depends(require_csrf), db=Depends(get_db)):
    project = TaskService(db, auth.user_id).create_project(name)
    return RedirectResponse(f'/app/projects/{project.id}', status_code=303)

@router.get('/projects/{identifier}')
def project_detail(identifier: int, request: Request, auth=Depends(require_session), db=Depends(get_db)):
    return render(request, 'project.html', auth, project=TaskService(db, auth.user_id).get_project(identifier))

@router.post('/projects/{identifier}/delete')
def delete_project(identifier: int, auth=Depends(require_csrf), db=Depends(get_db)):
    TaskService(db, auth.user_id).delete_project(identifier)
    return RedirectResponse('/app/projects', status_code=303)

@router.get('/projects/{identifier}/tasks/new')
def new_task(identifier: int, request: Request, auth=Depends(require_session), db=Depends(get_db)):
    project = TaskService(db, auth.user_id).get_project(identifier)
    return render(request, 'form.html', auth, task=None, project=project)

@router.post('/projects/{identifier}/tasks')
def create_task(identifier: int, title: str = Form(''), description: str = Form(''), auth=Depends(require_csrf), db=Depends(get_db)):
    task = TaskService(db, auth.user_id).create(identifier, title, description)
    return RedirectResponse(f'/app/tasks/{task.id}', status_code=303)

@router.get('/tasks')
def listing(request: Request, auth=Depends(require_session), db=Depends(get_db)):
    return render(request, 'list.html', auth, tasks=TaskService(db, auth.user_id).list())

@router.get('/tasks/{identifier}')
def detail(identifier: int, request: Request, auth=Depends(require_session), db=Depends(get_db)):
    return render(request, 'detail.html', auth, task=TaskService(db, auth.user_id).get(identifier))

@router.get('/tasks/{identifier}/edit')
def edit(identifier: int, request: Request, auth=Depends(require_session), db=Depends(get_db)):
    return render(request, 'form.html', auth, task=TaskService(db, auth.user_id).get(identifier))

@router.post('/tasks/{identifier}/edit')
def update(identifier: int, title: str = Form(''), description: str = Form(''), auth=Depends(require_csrf), db=Depends(get_db)):
    task = TaskService(db, auth.user_id).update(identifier, title, description)
    return RedirectResponse(f'/app/tasks/{task.id}', status_code=303)

@router.post('/tasks/{identifier}/state')
def state(identifier: int, completed: str = Form(''), auth=Depends(require_csrf), db=Depends(get_db)):
    if completed not in ('true', 'false'):
        raise ValueError('상태는 true 또는 false를 사용하세요')
    task = TaskService(db, auth.user_id).set_completed(identifier, completed == 'true')
    return RedirectResponse(f'/app/tasks/{task.id}', status_code=303)

@router.post('/tasks/{identifier}/delete')
def delete(identifier: int, auth=Depends(require_csrf), db=Depends(get_db)):
    TaskService(db, auth.user_id).delete(identifier)
    return RedirectResponse('/app/tasks', status_code=303)
