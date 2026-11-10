import os

import mlflow
import mlflow.pyfunc

import logging
import time

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import Response

from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

import cache
from database import Base, engine, get_db
from models import TaskModel

app = FastAPI(title="Tasks API", description="Bootcamp demo app — Week 1/2/8")

# Structured logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("taskly-api")

# Model version
MODEL_VERSION = "3"

# Prometheus metrics
PREDICTIONS_TOTAL = Counter(
    "taskly_predictions_total",
    "Total predictions",
    ["model_version", "priority"]
)

PREDICTION_ERRORS_TOTAL = Counter(
    "taskly_prediction_errors_total",
    "Total prediction errors",
    ["model_version"]
)

PREDICTION_LATENCY = Histogram(
    "taskly_prediction_latency_seconds",
    "Prediction latency in seconds",
    ["model_version"]
)

MODEL_VERSION_INFO = Gauge(
    "taskly_model_version_info",
    "Currently loaded model version",
    ["model_version"]
)

MODEL_VERSION_INFO.labels(model_version=MODEL_VERSION).set(1)

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

@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4"
    )


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

    start_time = time.perf_counter()

    try:
        prediction = model.predict([text])
        priority = str(prediction[0])

        PREDICTIONS_TOTAL.labels(
            model_version=MODEL_VERSION,
            priority=priority
        ).inc()

        logger.info(
            "Prediction successful",
            extra={
                "model_version": MODEL_VERSION,
                "predicted_priority": priority,
                "title": request.title,
            },
        )

        return {
            "title": request.title,
            "predicted_priority": priority,
        }

    except Exception:
        PREDICTION_ERRORS_TOTAL.labels(
            model_version=MODEL_VERSION
        ).inc()

        logger.exception(
            "Prediction failed",
            extra={"model_version": MODEL_VERSION},
        )

        raise HTTPException(
            status_code=500,
            detail="Prediction failed",
        )

    finally:
        PREDICTION_LATENCY.labels(
            model_version=MODEL_VERSION
        ).observe(time.perf_counter() - start_time)