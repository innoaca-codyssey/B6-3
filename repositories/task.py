from sqlalchemy import select
from models.task import Task


class TaskRepository:
    def __init__(self, session):
        self.session = session

    def all(self):
        return self.session.scalars(select(Task).order_by(Task.created_at.desc(), Task.id.desc())).all()

    def get(self, identifier):
        return self.session.get(Task, identifier)

    def save(self, task):
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def delete(self, task):
        self.session.delete(task)
        self.session.commit()
