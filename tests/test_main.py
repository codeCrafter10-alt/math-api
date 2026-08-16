from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
import main
import pytest
from unittest.mock import MagicMock

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
@pytest.mark.parametrize("id", [1, 2, 3])
def test_test(id: int):
    response = client.get(f"/test/{id}")
    assert response.status_code == 200



# test get_question endpoint
def test_get_question_success(monkeypatch):
    mock_db = MagicMock()

    mock_doc = MagicMock()
    mock_doc.get.return_value.to_dict.return_value = mockQuestion()

    mock_db.collection.return_value.document.return_value = mock_doc

    monkeypatch.setattr(main, "db", mock_db)

    response = client.get("/questions/1")

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "question": "How many whole numbers are greater than 150 and less than 500?",
        "level": "Level 3",
        "topic": "Prealgebra",
    }

    mock_db.collection.assert_called_with("questions")
    mock_db.collection.return_value.document.assert_called_with("1")

def test_get_question_not_found(monkeypatch):
    mock_db = MagicMock()

    mock_doc = MagicMock()
    mock_doc.get.return_value.to_dict.return_value = None

    mock_db.collection.return_value.document.return_value = mock_doc

    monkeypatch.setattr(main, "db", mock_db)

    response = client.get("/questions/5")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Question not found"
    }


def test_get_question_invalid_id():
    response = client.get("/questions/not-an-integer")

    assert response.status_code == 422


# test check_answer post endpoint
def answer_response():
    return {
        "answer": "349",
        "question_id": 1,
        "user_id": "user_123",
        "time_to_answer_seconds": 10,
        "hint_used": False,
        "solution_viewed": False,
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

    user_document = MagicMock()
    user_document.collection.return_value = data_collection

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

    user_document = MagicMock()
    user_document.collection.return_value = data_collection

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

    docs = [
        MagicMock(to_dict=lambda: {"answered_correctly": True}),
        MagicMock(to_dict=lambda: {"answered_correctly": True}),
        MagicMock(to_dict=lambda: {"answered_correctly": False}),
        MagicMock(to_dict=lambda: {"answered_correctly": False}),
    ]

    data_collection = MagicMock()
    data_collection.stream.return_value = docs

    user_document = MagicMock()
    user_document.collection.return_value = data_collection

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
        "accuracy_percentage": 50.0,
    }


def test_get_user_statistics_no_answers(monkeypatch):
    mock_db = MagicMock()

    data_collection = MagicMock()
    data_collection.stream.return_value = []

    user_document = MagicMock()
    user_document.collection.return_value = data_collection

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
    }