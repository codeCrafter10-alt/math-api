import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()
project_id = os.getenv("FIREBASE_PROJECT_ID")

cred = credentials.Certificate("firebase_project_cred.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {'projectId': project_id})

db = firestore.client()

questions = {
    1: {
        "id": 1,
        "question": "What is 5 + 3?",
        "answer": "8"
    },
    2: {
        "id": 2,
        "question": "What is 9 - 4?",
        "answer": "5"
    },
    3: {
        "id": 3,
        "question": "What is 6 × 7?",
        "answer": "42"
    },
    4: {
        "id": 4,
        "question": "What is 20 ÷ 4?",
        "answer": "5"
    },
    5: {
        "id": 5,
        "question": "What is 12 + 15?",
        "answer": "27"
    },
    6: {
        "id": 6,
        "question": "What is 30 - 12?",
        "answer": "18"
    },
    7: {
        "id": 7,
        "question": "What is 8 × 5?",
        "answer": "40"
    },
    8: {
        "id": 8,
        "question": "What is 36 ÷ 6?",
        "answer": "6"
    },
    9: {
        "id": 9,
        "question": "What is 14 + 18?",
        "answer": "32"
    },
    10: {
        "id": 10,
        "question": "What is 50 - 23?",
        "answer": "27"
    },
    11: {
        "id": 11,
        "question": "What is 9 × 9?",
        "answer": "81"
    },
    12: {
        "id": 12,
        "question": "What is 72 ÷ 8?",
        "answer": "9"
    },
    13: {
        "id": 13,
        "question": "What is 25 + 17?",
        "answer": "42"
    },
    14: {
        "id": 14,
        "question": "What is 60 - 35?",
        "answer": "25"
    },
    15: {
        "id": 15,
        "question": "What is 7 × 8?",
        "answer": "56"
    },
    16: {
        "id": 16,
        "question": "What is 81 ÷ 9?",
        "answer": "9"
    },
    17: {
        "id": 17,
        "question": "What is 33 + 22?",
        "answer": "55"
    },
    18: {
        "id": 18,
        "question": "What is 90 - 45?",
        "answer": "45"
    },
    19: {
        "id": 19,
        "question": "What is 11 × 6?",
        "answer": "66"
    },
    20: {
        "id": 20,
        "question": "What is 100 ÷ 10?",
        "answer": "10"
    },
    21: {
        "id": 21,
        "question": "What is 45 + 28?",
        "answer": "73"
    },
    22: {
        "id": 22,
        "question": "What is 75 - 38?",
        "answer": "37"
    },
    23: {
        "id": 23,
        "question": "What is 12 × 12?",
        "answer": "144"
    },
    24: {
        "id": 24,
        "question": "What is 144 ÷ 12?",
        "answer": "12"
    },
    25: {
        "id": 25,
        "question": "What is 56 + 19?",
        "answer": "75"
    },
    26: {
        "id": 26,
        "question": "What is 120 - 55?",
        "answer": "65"
    },
    27: {
        "id": 27,
        "question": "What is 15 × 4?",
        "answer": "60"
    },
    28: {
        "id": 28,
        "question": "What is 96 ÷ 8?",
        "answer": "12"
    },
    29: {
        "id": 29,
        "question": "What is 67 + 24?",
        "answer": "91"
    },
    30: {
        "id": 30,
        "question": "What is 150 - 75?",
        "answer": "75"
    },
    31: {
        "id": 31,
        "question": "What is 13 × 7?",
        "answer": "91"
    },
    32: {
        "id": 32,
        "question": "What is 200 ÷ 10?",
        "answer": "20"
    },
    33: {
        "id": 33,
        "question": "What is 88 + 32?",
        "answer": "120"
    },
    34: {
        "id": 34,
        "question": "What is 140 - 60?",
        "answer": "80"
    },
    35: {
        "id": 35,
        "question": "What is 14 × 8?",
        "answer": "112"
    },
    36: {
        "id": 36,
        "question": "What is 225 ÷ 15?",
        "answer": "15"
    },
    37: {
        "id": 37,
        "question": "What is 99 + 45?",
        "answer": "144"
    },
    38: {
        "id": 38,
        "question": "What is 180 - 90?",
        "answer": "90"
    },
    39: {
        "id": 39,
        "question": "What is 16 × 6?",
        "answer": "96"
    },
    40: {
        "id": 40,
        "question": "What is 300 ÷ 15?",
        "answer": "20"
    }
}

for i in range(1, 41):
    question_data = questions[i]
    question_ref = db.collection('questions').document(str(question_data['id']))
    question_ref.set(question_data)