import random

from fastapi import FastAPI, HTTPException, Response
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

class UserProfile(BaseModel):
    user_id: str = Field( ..., description="The ID of the user." ) 
    email: str = Field( ..., description="The email of the user." ) 
    name: str = Field( ..., description="The first name of the user." )

@app.get("/questions/{user_id}")
def get_question(user_id: str):
    state_ref = db.collection("userData").document(str(user_id)).collection("state").document(str(1))
    state = state_ref.get().to_dict() or {}
    if state.get("question_id") is not None and not state.get("is_answered", True):
        reference = db.collection("userData").document(str(user_id)).collection("data").document()
        reference.set({
            "answer": "",
            "question": db.collection("questions").document(str(state.get("question_id"))),
            "answered_correctly": False,
            "answered_at": datetime.now(timezone.utc),
            "time_to_answer_seconds": 0,
            "hint_used": False,
            "solution_viewed": False,
            "question_id": state.get("question_id"),
            "user_id": user_id,
            "skipped": True
        })

    question_id = random.randint(1, 5000)
    question = db.collection("questions").document(str(question_id)).get().to_dict()

    
    state_ref.set({
        "question_id": question_id,
        "is_answered": False
    })

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
        "answered_at": datetime.now(timezone.utc),
    })
    reference = db.collection("userData").document(str(request.user_id)).collection("data").document()
    reference.set(data)

    state_ref = db.collection("userData").document(str(request.user_id)).collection("state").document(str(1))
    if not state_ref.get().exists:
        state_ref.set({
            "question_id": request.question_id,
            "is_answered": True
        })
    state_ref.update({
        "is_answered": True
    })

    reference = db.collection("userData").document(str(request.user_id)).collection("summary").document("1")
    if not reference.get().exists:
        reference.set({
            "problems_attempted": 0,
            "problems_correct": 0,
            "streak": 0
        })
    reference.update({
        "problems_attempted": firestore.Increment(1),
        "problems_correct": (firestore.Increment(1) if correct else firestore.Increment(0)),
        "streak": (firestore.Increment(1) if correct else 0)
    })

    return {
        "correct": correct
    }

@app.get("/users/{user_id}/summary")
def get_user_statistics(user_id: str):
    reference = db.collection("userData").document(str(user_id)).collection("summary").document("1")
    summary = reference.get().to_dict() or {}

    total_questions = summary.get("problems_attempted", 0)
    correct_answers = summary.get("problems_correct", 0)

    return {
        "user_id": user_id,
        "total_questions_answered": total_questions,
        "correct_answers": correct_answers,
        "accuracy_percentage":round((correct_answers / total_questions * 100) if total_questions > 0 else 0, 2),
        "streak": summary.get("streak", 0)
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

@app.head("/test")
def test():
    return Response(status_code=200)

@app.post("/users/create")
def create_user(user: UserProfile):
    user_id = user.user_id

    reference = db.collection("userData").document(str(user_id)).collection("profile").document("1")

    if not reference.get().exists:
        reference.set({
            "email": user.email,
            "name": user.name,
            "user_id": user.user_id
        })
    else:
        reference.update({
            "email": user.email,
            "name": user.name,
            "user_id": user.user_id
        })

    return {"msg": "User profile added"}