import os

import mlflow
import mlflow.pyfunc

from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import cache
from database import Base, engine, get_db
from models import TaskModel

app = FastAPI(title="Tasks API", description="Bootcamp demo app — Week 1/2/8")

mlflow.set_tracking_uri(
    os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")
)

MODEL_URI = "models:/task-priority-classifier/3"

model = mlflow.pyfunc.load_model(MODEL_URI)

Base.metadata.create_all(bind=engine)


class Task(BaseModel):
    title: str
    description: Optional[str] = None
    done: bool = False
    priority: Optional[str] = None  # "low" | "medium" | "high" — set manually or by the priority-classifier model


class TaskOut(Task):
    id: int

    model_config = {"from_attributes": True}


@app.get("/health")
def health():
    return {"status": "ok", "service": "tasks-api"}


@app.get("/tasks", response_model=List[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    cached = cache.get_cached_tasks()
    if cached is not None:
        return cached
    result = [TaskOut.model_validate(t).model_dump() for t in db.query(TaskModel).order_by(TaskModel.id).all()]
    cache.set_cached_tasks(result)
    return result


@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(task: Task, db: Session = Depends(get_db)):
    db_task = TaskModel(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    cache.invalidate_task_cache(db_task.id)
    return db_task


@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    cached = cache.get_cached_task(task_id)
    if cached is not None:
        return cached
    db_task = db.get(TaskModel, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    result = TaskOut.model_validate(db_task).model_dump()
    cache.set_cached_task(task_id, result)
    return result


@app.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, task: Task, db: Session = Depends(get_db)):
    db_task = db.get(TaskModel, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in task.model_dump().items():
        setattr(db_task, field, value)
    db.commit()
    db.refresh(db_task)
    cache.invalidate_task_cache(task_id)
    return db_task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.get(TaskModel, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    cache.invalidate_task_cache(task_id)


class PredictRequest(BaseModel):
    title: str
    description: Optional[str] = None


@app.post("/predict")
def predict_priority(request: PredictRequest):
    text = request.title + " " + (request.description or "")

    prediction = model.predict([text])

    return {
        "title": request.title,
        "predicted_priority": str(prediction[0])
    }
