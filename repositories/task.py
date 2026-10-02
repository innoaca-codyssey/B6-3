from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.task import Project, Task

class TaskRepository:
    def __init__(self, session):
        self.session = session

    def projects(self, user_id):
        return self.session.scalars(select(Project).where(Project.user_id == user_id).options(selectinload(Project.tasks)).order_by(Project.id.desc())).all()

    def project(self, identifier):
        return self.session.get(Project, identifier)

    def get(self, identifier):
        return self.session.get(Task, identifier)

    def all(self, user_id, query='', completed=None, project_id=None):
        statement = select(Task).join(Task.project).where(Project.user_id == user_id)
        if query:
            statement = statement.where(Task.title.contains(query, autoescape=True))
        if completed is not None:
            statement = statement.where(Task.completed == completed)
        if project_id is not None:
            statement = statement.where(Task.project_id == project_id)
        return self.session.scalars(statement.order_by(Task.created_at.desc(), Task.id.desc())).all()

    def save(self, row):
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return row

    def delete(self, row):
        self.session.delete(row)
        self.session.commit()
