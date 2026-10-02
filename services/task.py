from dataclasses import dataclass
from datetime import datetime
from models.task import Project, Task
from repositories.task import TaskRepository

@dataclass
class TaskView:
    id: int
    title: str
    description: str
    created_at: datetime
    completed: bool
    project_id: int
    project_name: str

@dataclass
class ProjectView:
    id: int
    name: str
    owner: str
    tasks: list[TaskView]

class TaskService:
    def __init__(self, session, user_id):
        self.repository = TaskRepository(session)
        self.user_id = user_id

    def view(self, task):
        return TaskView(task.id, task.title, task.description, task.created_at, task.completed, task.project_id, task.project.name)

    def project_view(self, project):
        return ProjectView(project.id, project.name, project.owner.username, [self.view(task) for task in project.tasks])

    def projects(self):
        return [self.project_view(p) for p in self.repository.projects(self.user_id)]

    def require_project(self, identifier):
        project = self.repository.project(identifier)
        if project is None or project.user_id != self.user_id:
            raise LookupError('해당 프로젝트를 찾을 수 없습니다')
        return project

    def get_project(self, identifier):
        return self.project_view(self.require_project(identifier))

    def create_project(self, name):
        if not name.strip() or len(name.strip()) > 100:
            raise ValueError('프로젝트 이름은 1~100자로 입력하세요')
        return self.project_view(self.repository.save(Project(name=name.strip(), user_id=self.user_id)))

    def delete_project(self, identifier):
        self.repository.delete(self.require_project(identifier))

    def list(self, query='', completed='', project_id=None):
        query = query.strip()
        if len(query) > 100 or completed not in ('', 'true', 'false'):
            raise ValueError('검색어는 100자 이내, 상태는 true 또는 false를 사용하세요')
        if project_id is not None:
            self.require_project(project_id)
        state = None if not completed else completed == 'true'
        return [self.view(t) for t in self.repository.all(self.user_id, query, state, project_id)]

    def require(self, identifier):
        task = self.repository.get(identifier)
        if task is None or task.project.user_id != self.user_id:
            raise LookupError('해당 할 일을 찾을 수 없습니다')
        return task

    def get(self, identifier):
        return self.view(self.require(identifier))

    def validate(self, title, description):
        title, description = title.strip(), description.strip()
        if not title or len(title) > 100 or not description or len(description) > 2000:
            raise ValueError('제목은 1~100자, 내용은 1~2000자로 입력하세요')
        return title, description

    def create(self, project_id, title, description):
        project = self.require_project(project_id)
        title, description = self.validate(title, description)
        return self.view(self.repository.save(Task(title=title, description=description, project=project)))

    def update(self, identifier, title, description):
        task = self.require(identifier)
        task.title, task.description = self.validate(title, description)
        return self.view(self.repository.save(task))

    def set_completed(self, identifier, completed):
        """완료 상태 변경은 CRUD 입력 수정과 구분해 처리합니다."""
        task = self.require(identifier)
        task.completed = completed
        return self.view(self.repository.save(task))

    def delete(self, identifier):
        self.repository.delete(self.require(identifier))
