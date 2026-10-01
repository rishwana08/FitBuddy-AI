import os

os.environ["DATABASE_URL"] = "sqlite:///./test_fitbuddy.db"

os.environ["DEMO_MODE"] = "true"

os.environ["GEMINI_API_KEY"] = ""


from fastapi.testclient import TestClient

from app.database import Base, engine

from app.main import app


Base.metadata.drop_all(
    bind=engine
)

Base.metadata.create_all(
    bind=engine
)


client = TestClient(app)


def test_home():

    response = client.get("/")

    assert response.status_code == 200

    assert "FitBuddy" in response.text


def test_health():

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json()["status"] == "ok"


def test_generate():

    payload = {

        "user_id": "TEST001",

        "name": "Test User",

        "age": 25,

        "weight": 65,

        "goal": "general wellness",

        "intensity": "medium",
    }


    response = client.post(
        "/api/generate",
        json=payload,
    )


    assert response.status_code == 200

    assert (
        response.json()["user"]["user_id"]
        == "TEST001"
    )


def test_feedback():

    response = client.post(
        "/api/feedback",

        json={
            "user_id": "TEST001",
            "feedback":
                "Add more rest days.",
        },
    )


    assert response.status_code == 200

    assert (
        response.json()["user_id"]
        == "TEST001"
    )


def test_get_user():

    response = client.get(
        "/api/users/TEST001"
    )


    assert response.status_code == 200

    assert (
        response.json()["user"]["name"]
        == "Test User"
    )