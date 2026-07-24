from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
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
    user_id: int = Field( ..., description="The ID of the user." ) 
    time_to_answer_seconds: int = Field( ..., ge=0, description="Time taken to answer the question in seconds." ) 
    answered_at: datetime = Field( ..., description="The date and time the question was answered." ) 
    hint_used: bool = Field( ..., description="Whether the user used a hint." ) 
    answered_correctly: bool = Field( ..., description="Whether the user answered correctly." ) 
    solution_viewed: bool = Field( ..., description="Whether the user viewed the solution." )

@app.get("/questions/{question_id}")
def get_question(question_id: int):
    question = db.collection("questions").document(str(question_id)).get().to_dict()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    return {
        "id": question["id"],
        "question": question["question"],
        "answer": question["answer"]
    }


@app.post("/questions/answer")
def submit_answer(request: AnswerRequest):
    question = db.collection("questions").document(str(request.question_id)).get().to_dict()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    return {}
