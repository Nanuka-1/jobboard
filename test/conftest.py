import os

import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture(scope="session")
def app_module(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "test_jobboard.db"

    os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"
    os.environ["SECRET_KEY"] = "test-secret"
    os.environ.pop("TBC_API_KEY", None)

    import app as app_module
    return app_module


@pytest.fixture()
def app(app_module):
    app = app_module.app
    db = app_module.db

    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

        if app_module.Category.query.count() == 0:
            db.session.add_all([
                app_module.Category(name="IT"),
                app_module.Category(name="Design"),
                app_module.Category(name="Marketing"),
                app_module.Category(name="Sales"),
                app_module.Category(name="Other"),
            ])
            db.session.commit()

        yield app

        db.session.remove()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def users(app_module, app):
    db = app_module.db

    with app.app_context():
        u1 = app_module.User(
            full_name="User One",
            email="u1@test.com",
            password_hash=generate_password_hash("password123"),
        )
        u2 = app_module.User(
            full_name="User Two",
            email="u2@test.com",
            password_hash=generate_password_hash("password123"),
        )

        db.session.add_all([u1, u2])
        db.session.commit()

        return (
            {"id": u1.id, "email": u1.email},
            {"id": u2.id, "email": u2.email},
        )


@pytest.fixture()
def sample_job(app_module, app, users):
    db = app_module.db
    u1, _ = users

    with app.app_context():
        cat = app_module.Category.query.filter_by(name="IT").first()

        job = app_module.Job(
            title="Test Job",
            short_description="Short description for test job",
            full_description="Full description for test job " * 3,
            company_name="Test Company",
            salary="1000",
            location="Tbilisi",
            category_id=cat.id,
            author_id=u1["id"],
        )
        db.session.add(job)
        db.session.commit()

        return job.id
