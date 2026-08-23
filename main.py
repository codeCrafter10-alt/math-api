import random

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import firebase_admin
from firebase_admin import credentials, firestore
import sys

cred = credentials.Certificate("firebase_project_cred.json")
app = firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnswerRequest(BaseModel):
    answer: str
    question_id: int = Field( ..., description="The ID of the question." ) 
    user_id: str = Field( ..., description="The ID of the user." ) 
    time_to_answer_seconds: int = Field( ..., ge=0, description="Time taken to answer the question in seconds." ) 
    hint_used: bool = Field( ..., description="Whether the user used a hint." ) 
    solution_viewed: bool = Field( ..., description="Whether the user viewed the solution." )
    email: str = Field( ..., description="The email of the user." )
    first_name: str = Field( ..., description="The first name of the user." )
    last_name: str = Field( ..., description="The last name of the user." )
    grade: int = Field( ..., ge=1, le=12, description="The grade of the user." )

@app.get("/questions/{user_id}")
def get_question(user_id: str):
    question_id = get_question_id(user_id)["question_id"]
    question = db.collection("questions").document(str(question_id)).get().to_dict()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    return {
        "id": question["id"],
        "question": question["question"],
        "level": question["level"],
        "topic": question["topic"]
    }


@app.post("/questions/check_answer")
def submit_answer(request: AnswerRequest):
    question = db.collection("questions").document(str(request.question_id)).get().to_dict()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    data = dict(request)
    correct = request.answer.strip().lower() == question["answer"].strip().lower()
    data.update({
        "question": db.collection("questions").document(str(request.question_id)),
        "answered_correctly": correct,
        "answered_at": datetime.now(timezone.utc)
    })
    reference = db.collection("userData").document(str(request.user_id)).collection("data").document()
    reference.set(data)

    reference = db.collection("userData").document(str(request.user_id)).collection("summary").document("1")
    if not reference.get().exists:
        reference.set({
            "email": request.email,
            "problems_attempted": 0,
            "problems_correct": 0,
            "streak": 0,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "grade": request.grade
        })
    else:
        reference.update({
            "email": request.email,
            "problems_attempted": firestore.Increment(1),
            "problems_correct": (firestore.Increment(1) if correct else firestore.Increment(0)),
            "streak": (firestore.Increment(1) if correct else 0),
            "first_name": request.first_name,
            "last_name": request.last_name,
            "grade": request.grade
        })

    return {
        "correct": correct
    }

@app.get("/users/{user_id}/summary")
def get_user_statistics(user_id: str):
    reference = db.collection("userData").document(str(user_id)).collection("data")
    user_data = reference.stream()

    total_questions = 0
    correct_answers = 0

    for doc in user_data:
        total_questions += 1
        if doc.to_dict().get("answered_correctly"):
            correct_answers += 1

    return {
        "user_id": user_id,
        "total_questions_answered": total_questions,
        "correct_answers": correct_answers,
        "accuracy_percentage": (correct_answers / total_questions * 100) if total_questions > 0 else 0
    }

@app.get("/questions/{question_id}/answer")
def get_answer(question_id: int):
    question = db.collection("questions").document(str(question_id)).get().to_dict()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    return {
        "answer": question["answer"],
        "solution": question["solution"],
    }

@app.get("/test/{id}")
def test(id: int):
    return {"id": id, "msg": "Test passed"}

@app.get("/get_question_id/{user_id}")
def get_question_id(user_id: str):
    # Model predicts question id based on user performance.

    question_id = random.randint(1, 5000) # Random question id model

    return {
        "question_id": question_id
    }