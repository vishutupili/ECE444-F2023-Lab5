import pytest
from pathlib import Path
from project.app import app, db
import json

TEST_DB = "test.db"
# configuration
DATABASE = "flaskr.db"
USERNAME = "admin"
PASSWORD = "admin"
SECRET_KEY = "change_me"

@pytest.fixture
def client():
    BASE_DIR = Path(__file__).resolve().parent.parent
    app.config["TESTING"] = True
    app.config["DATABASE"] = BASE_DIR.joinpath(TEST_DB)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR.joinpath(TEST_DB)}"

    with app.app_context():
        db.create_all()
        yield app.test_client() 
        db.drop_all()  

def login(client, username, password):
    return client.post(
        "/login",
        data=dict(username=username, password=password),
        follow_redirects=True,
    )

def logout(client):
    return client.get("/logout", follow_redirects=True)

def test_index(client):
    response = client.get("/", content_type="html/text")
    assert response.status_code == 200

def test_database(client):
    tester = Path("test.db").is_file()
    assert tester

def test_empty_db(client):
    rv = client.get("/")
    assert b"No entries yet. Add some!" in rv.data

def test_login_logout(client):
    rv = login(client, app.config["USERNAME"], app.config["PASSWORD"])
    assert b"You were logged in" in rv.data
    rv = logout(client)
    assert b"You were logged out" in rv.data
    rv = login(client, app.config["USERNAME"] + "x", app.config["PASSWORD"])
    assert b"Invalid username" in rv.data
    rv = login(client, app.config["USERNAME"], app.config["PASSWORD"] + "x")
    assert b"Invalid password" in rv.data

def test_messages(client):
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    rv = client.post(
        "/add",
        data=dict(title="<Hello>", text="<strong>HTML</strong> allowed here"),
        follow_redirects=True,
    )
    assert b"No entries here so far" not in rv.data
    assert b"&lt;Hello&gt;" in rv.data
    assert b"<strong>HTML</strong> allowed here" in rv.data

def test_delete_message(client):
    rv = client.get("/delete/1")
    data = json.loads(rv.data)
    assert data["status"] == 0
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    rv = client.get("/delete/1")
    data = json.loads(rv.data)
    assert data["status"] == 1

def test_search_message(client):
    response = client.get('/search/?query=test')
    assert response.status_code == 200