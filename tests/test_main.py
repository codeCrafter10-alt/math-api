from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
import main
import pytest
from unittest.mock import MagicMock
from firebase_admin import firestore

client = TestClient(main.app)

def mockQuestion(
    question_id=1,
    question="How many whole numbers are greater than 150 and less than 500?",
    answer="349",
    level="Level 3",
    topic="Prealgebra",
    solution="The numbers are 151 through 499. Subtracting 150 from 499 gives 349, so there are 349 numbers.",
):
    return {
        "id": question_id,
        "question": question,
        "answer": answer,
        "level": level,
        "topic": topic,
        "solution": solution,
    }

# test endpoint
def test_test():
    response = client.head("/test")
    assert response.status_code == 200



# test get_question endpoint
def test_get_question_success(monkeypatch):
    mock_db = MagicMock()

    state_doc = MagicMock()
    state_doc.get.return_value.to_dict.return_value = {"is_answered": False}

    question_doc = MagicMock()
    question_doc.get.return_value.to_dict.return_value = mockQuestion()

    state_collection = MagicMock()
    state_collection.document.return_value = state_doc

    questions_collection = MagicMock()
    questions_collection.document.return_value = question_doc

    user_document = MagicMock()
    user_document.collection.return_value = state_collection

    user_data_collection = MagicMock()
    user_data_collection.document.return_value = user_document

    mock_db.collection.side_effect = lambda name: {
        "userData": user_data_collection,
        "questions": questions_collection,
    }[name]

    monkeypatch.setattr(main, "db", mock_db)

    monkeypatch.setattr(main.random, "randint", lambda a, b: 1)
    response = client.get("/questions/user_123")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "question": "How many whole numbers are greater than 150 and less than 500?",
        "level": "Level 3",
        "topic": "Prealgebra",
    }

    questions_collection.document.assert_called_once_with("1")
    state_doc.set.assert_called_once_with({
        "question_id": 1,
        "is_answered": False,
    })


def test_get_question_with_missing_state_document(monkeypatch):
    mock_db = MagicMock()

    state_doc = MagicMock()
    state_doc.get.return_value.to_dict.return_value = None

    question_doc = MagicMock()
    question_doc.get.return_value.to_dict.return_value = mockQuestion()

    state_collection = MagicMock()
    state_collection.document.return_value = state_doc

    questions_collection = MagicMock()
    questions_collection.document.return_value = question_doc

    user_document = MagicMock()
    user_document.collection.return_value = state_collection

    user_data_collection = MagicMock()
    user_data_collection.document.return_value = user_document

    mock_db.collection.side_effect = lambda name: {
        "userData": user_data_collection,
        "questions": questions_collection,
    }[name]

    monkeypatch.setattr(main, "db", mock_db)
    monkeypatch.setattr(main.random, "randint", lambda a, b: 1)

    response = client.get("/questions/user_123")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    state_doc.set.assert_called_once_with({
        "question_id": 1,
        "is_answered": False,
    })


def test_get_question_not_found(monkeypatch):
    mock_db = MagicMock()

    state_doc = MagicMock()
    state_doc.get.return_value.to_dict.return_value = {"is_answered": False}

    question_doc = MagicMock()
    question_doc.get.return_value.to_dict.return_value = None

    state_collection = MagicMock()
    state_collection.document.return_value = state_doc

    questions_collection = MagicMock()
    questions_collection.document.return_value = question_doc

    user_document = MagicMock()
    user_document.collection.return_value = state_collection

    user_data_collection = MagicMock()
    user_data_collection.document.return_value = user_document

    def collection_side_effect(name):
        if name == "userData":
            return user_data_collection
        if name == "questions":
            return questions_collection
        return MagicMock()

    mock_db.collection.side_effect = collection_side_effect

    monkeypatch.setattr(main, "db", mock_db)

    monkeypatch.setattr(main.random, "randint", lambda a, b: 5)

    response = client.get("/questions/user_123")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Question not found"
    }

    questions_collection.document.assert_called_once_with("5")
    state_doc.set.assert_called_once_with({
        "question_id": 5,
        "is_answered": False,
    })


def test_get_question_records_skipped_question(monkeypatch):
    mock_db = MagicMock()

    state_doc = MagicMock()
    state_doc.get.return_value.to_dict.return_value = {
        "is_answered": False,
        "question_id": 7,
    }

    skipped_doc = MagicMock()
    question_doc = MagicMock()
    question_doc.get.return_value.to_dict.return_value = mockQuestion(question_id=8)

    state_collection = MagicMock()
    state_collection.document.return_value = state_doc

    data_collection = MagicMock()
    data_collection.document.return_value = skipped_doc

    user_document = MagicMock()
    user_document.collection.side_effect = lambda name: {
        "state": state_collection,
        "data": data_collection,
    }[name]

    user_data_collection = MagicMock()
    user_data_collection.document.return_value = user_document

    questions_collection = MagicMock()
    questions_collection.document.return_value = question_doc

    mock_db.collection.side_effect = lambda name: {
        "userData": user_data_collection,
        "questions": questions_collection,
    }[name]

    monkeypatch.setattr(main, "db", mock_db)
    monkeypatch.setattr(main.random, "randint", lambda a, b: 8)

    response = client.get("/questions/user_123")

    assert response.status_code == 200
    skipped_data = skipped_doc.set.call_args.args[0]
    assert skipped_data["question_id"] == 7
    assert skipped_data["user_id"] == "user_123"
    assert skipped_data["skipped"] is True
    assert skipped_data["answer"] == ""
    state_doc.set.assert_called_once_with({
        "question_id": 8,
        "is_answered": False,
    })



# test check_answer post endpoint
def answer_response():
    return {
        "answer": "349",
        "question_id": 1,
        "user_id": "user_123",
        "time_to_answer_seconds": 10,
        "hint_used": False,
        "solution_viewed": False
    }


def test_submit_answer_correct(monkeypatch):
    mock_db = MagicMock()

    question_doc = MagicMock()
    question_doc.get.return_value.to_dict.return_value = mockQuestion()

    questions_collection = MagicMock()
    questions_collection.document.return_value = question_doc

    new_data_doc = MagicMock()

    data_collection = MagicMock()
    data_collection.document.return_value = new_data_doc

    summary_doc = MagicMock()

    summary_collection = MagicMock()
    summary_collection.document.return_value = summary_doc

    state_doc = MagicMock()
    state_collection = MagicMock()
    state_collection.document.return_value = state_doc

    user_document = MagicMock()
    def user_collection_side_effect(name):
        if name == "data":
            return data_collection
        elif name == "summary":
            return summary_collection
        elif name == "state":
            return state_collection

        return MagicMock()
    user_document.collection.side_effect = user_collection_side_effect

    user_data_collection = MagicMock()
    user_data_collection.document.return_value = user_document

    def collection_side_effect(name):
        if name == "questions":
            return questions_collection
        elif name == "userData":
            return user_data_collection

        return MagicMock()

    mock_db.collection.side_effect = collection_side_effect

    monkeypatch.setattr(main, "db", mock_db)

    response = client.post(
        "/questions/check_answer",
        json=answer_response(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "correct": True
    }

    new_data_doc.set.assert_called_once()
    saved_data = new_data_doc.set.call_args[0][0]

    assert saved_data["answer"] == "349"
    assert saved_data["question_id"] == 1
    assert saved_data["user_id"] == "user_123"
    assert saved_data["time_to_answer_seconds"] == 10
    assert saved_data["hint_used"] is False
    assert saved_data["solution_viewed"] is False
    assert saved_data["answered_correctly"] is True
    assert isinstance(saved_data["answered_at"], datetime)

    summary_doc.update.assert_called_once()

    summary_data = summary_doc.update.call_args[0][0]


    assert summary_data["problems_attempted"] == firestore.Increment(1)
    assert summary_data["problems_correct"] == firestore.Increment(1)
    assert summary_data["streak"] == firestore.Increment(1)

    summary_doc.update.assert_called_once_with(
        summary_data
    )
    state_collection.document.assert_called_once_with("1")
    state_doc.update.assert_called_once_with({"is_answered": True})
    

def test_submit_answer_incorrect(monkeypatch):
    mock_db = MagicMock()

    question_doc = MagicMock()
    question_doc.get.return_value.to_dict.return_value = mockQuestion(
        answer="349"
    )

    questions_collection = MagicMock()
    questions_collection.document.return_value = question_doc

    new_data_doc = MagicMock()

    data_collection = MagicMock()
    data_collection.document.return_value = new_data_doc

    summary_doc = MagicMock()

    summary_collection = MagicMock()
    summary_collection.document.return_value = summary_doc

    user_document = MagicMock()
    def user_collection_side_effect(name):
        if name == "data":
            return data_collection
        elif name == "summary":
            return summary_collection

        return MagicMock()
    user_document.collection.side_effect = user_collection_side_effect

    user_data_collection = MagicMock()
    user_data_collection.document.return_value = user_document

    def collection_side_effect(name):
        if name == "questions":
            return questions_collection
        elif name == "userData":
            return user_data_collection

        return MagicMock()

    mock_db.collection.side_effect = collection_side_effect

    monkeypatch.setattr(main, "db", mock_db)

    payload = answer_response()
    payload["answer"] = "5"

    response = client.post(
        "/questions/check_answer",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json() == {
        "correct": False
    }

    new_data_doc.set.assert_called_once()

    saved_data = new_data_doc.set.call_args[0][0]

    assert saved_data["answered_correctly"] is False


def test_submit_answer_question_not_found(monkeypatch):
    mock_db = MagicMock()

    question_doc = MagicMock()
    question_doc.get.return_value.to_dict.return_value = None

    mock_db.collection.return_value.document.return_value = question_doc

    monkeypatch.setattr(main, "db", mock_db)

    response = client.post(
        "/questions/check_answer",
        json=answer_response(),
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Question not found"
    }


def test_answer_request_missing_fields():
    response = client.post(
        "/questions/check_answer",
        json={},
    )

    assert response.status_code == 422


def test_answer_request_negative_time():
    payload = answer_response()
    payload["time_to_answer_seconds"] = -1

    response = client.post(
        "/questions/check_answer",
        json=payload,
    )

    assert response.status_code == 422


def test_answer_request_invalid_question_id():
    payload = answer_response()
    payload["question_id"] = "abc"

    response = client.post(
        "/questions/check_answer",
        json=payload,
    )

    assert response.status_code == 422



def test_answer_request_invalid_hint_used():
    payload = answer_response()
    payload["hint_used"] = "not-a-bool"

    response = client.post(
        "/questions/check_answer",
        json=payload,
    )

    assert response.status_code == 422


def test_answer_request_invalid_solution_viewed():
    payload = answer_response()
    payload["solution_viewed"] = "not-a-bool"

    response = client.post(
        "/questions/check_answer",
        json=payload,
    )

    assert response.status_code == 422



# test get_answer endpoint
def test_get_answer_success(monkeypatch):
    mock_db = MagicMock()

    mock_doc = MagicMock()
    mock_doc.get.return_value.to_dict.return_value = mockQuestion()

    mock_db.collection.return_value.document.return_value = mock_doc

    monkeypatch.setattr(main, "db", mock_db)

    response = client.get("/questions/1/answer")

    assert response.status_code == 200
    assert response.json() == {
        "answer": "349",
        "solution": "The numbers are 151 through 499. Subtracting 150 from 499 gives 349, so there are 349 numbers.",
    }


def test_get_answer_not_found(monkeypatch):
    mock_db = MagicMock()

    mock_doc = MagicMock()
    mock_doc.get.return_value.to_dict.return_value = None

    mock_db.collection.return_value.document.return_value = mock_doc

    monkeypatch.setattr(main, "db", mock_db)

    response = client.get("/questions/999/answer")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Question not found"
    }


def test_get_answer_invalid_id():
    response = client.get("/questions/abc/answer")

    assert response.status_code == 422



# test get_user_statistics endpoint
def test_get_user_statistics_with_answers(monkeypatch):
    mock_db = MagicMock()

    summary_doc = MagicMock()
    summary_doc.get.return_value.to_dict.return_value = {
        "problems_attempted": 4,
        "problems_correct": 2,
        "streak": 2,
    }

    user_document = MagicMock()
    summary_collection = MagicMock()
    summary_collection.document.return_value = summary_doc
    user_document.collection.return_value = summary_collection

    user_collection = MagicMock()
    user_collection.document.return_value = user_document

    mock_db.collection.return_value = user_collection

    monkeypatch.setattr(main, "db", mock_db)

    response = client.get("/users/user_123/summary")

    assert response.status_code == 200
    assert response.json() == {
        "user_id": "user_123",
        "total_questions_answered": 4,
        "correct_answers": 2,
        "accuracy_percentage": 50.00,
        "streak": 2,
    }
    summary_collection.document.assert_called_once_with("1")


def test_get_user_statistics_no_answers(monkeypatch):
    mock_db = MagicMock()

    summary_doc = MagicMock()
    summary_doc.get.return_value.to_dict.return_value = {}

    user_document = MagicMock()
    summary_collection = MagicMock()
    summary_collection.document.return_value = summary_doc
    user_document.collection.return_value = summary_collection

    user_collection = MagicMock()
    user_collection.document.return_value = user_document

    mock_db.collection.return_value = user_collection

    monkeypatch.setattr(main, "db", mock_db)

    response = client.get("/users/user_123/summary")

    assert response.status_code == 200
    assert response.json() == {
        "user_id": "user_123",
        "total_questions_answered": 0,
        "correct_answers": 0,
        "accuracy_percentage": 0,
        "streak": 0,
    }


def test_get_user_statistics_with_missing_summary_document(monkeypatch):
    mock_db = MagicMock()

    summary_doc = MagicMock()
    summary_doc.get.return_value.to_dict.return_value = None

    user_document = MagicMock()
    summary_collection = MagicMock()
    summary_collection.document.return_value = summary_doc
    user_document.collection.return_value = summary_collection

    user_collection = MagicMock()
    user_collection.document.return_value = user_document

    mock_db.collection.return_value = user_collection

    monkeypatch.setattr(main, "db", mock_db)

    response = client.get("/users/user_123/summary")

    assert response.status_code == 200
    assert response.json() == {
        "user_id": "user_123",
        "total_questions_answered": 0,
        "correct_answers": 0,
        "accuracy_percentage": 0,
        "streak": 0,
    }


def test_create_user_profile(monkeypatch):
    mock_db = MagicMock()

    user_doc = MagicMock()
    user_doc.get.return_value.exists = False

    user_collection = MagicMock()
    user_collection.document.return_value = user_doc

    mock_db.collection.return_value = user_collection

    monkeypatch.setattr(main, "db", mock_db)

    payload = {
        "user_id": "user_123",
        "email": "bob@example.com",
        "name": "Bob"
    }

    response = client.post("/users/create", json=payload)

    assert response.status_code == 200
    assert response.json() == {"msg": "User profile added"}

def test_create_user_profile_update_existing(monkeypatch):
    mock_db = MagicMock()

    user_doc = MagicMock()
    user_doc.get.return_value.exists = True

    user_collection = MagicMock()
    user_collection.document.return_value = user_doc

    mock_db.collection.return_value = user_collection

    monkeypatch.setattr(main, "db", mock_db)

    payload = {
        "user_id": "user_123",
        "email": "bob@example.com",
        "name": "Bob"
    }

    response = client.post("/users/create", json=payload)

    assert response.status_code == 200
    assert response.json() == {"msg": "User profile added"}

def test_create_user_profile_missing_fields():
    payload = {
        "user_id": "user_123"
    }

    response = client.post("/users/create", json=payload)

    assert response.status_code == 422
