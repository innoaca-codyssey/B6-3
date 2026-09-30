from dataclasses import dataclass
from datetime import datetime
from models.task import Task
from repositories.task import TaskRepository


@dataclass
class TaskView:
    id: int
    title: str
    description: str
    created_at: datetime


class TaskService:
    def __init__(self, session):
        self.repository = TaskRepository(session)

    def view(self, task):
        return TaskView(task.id, task.title, task.description, task.created_at)

    def list(self):
        return [self.view(task) for task in self.repository.all()]

    def require(self, identifier):
        task = self.repository.get(identifier)
        if task is None:
            raise LookupError('해당 할 일을 찾을 수 없습니다')
        return task

    def get(self, identifier):
        return self.view(self.require(identifier))

    def validate(self, title, description):
        title, description = title.strip(), description.strip()
        if not title or len(title) > 100:
            raise ValueError('제목은 1~100자로 입력하세요')
        if not description or len(description) > 2000:
            raise ValueError('내용은 1~2000자로 입력하세요')
        return title, description

    def create(self, title, description):
        title, description = self.validate(title, description)
        return self.view(self.repository.save(Task(title=title, description=description)))

    def update(self, identifier, title, description):
        task = self.require(identifier)
        task.title, task.description = self.validate(title, description)
        return self.view(self.repository.save(task))

    def delete(self, identifier):
        self.repository.delete(self.require(identifier))
