import os
import time
import logging
from sqlalchemy.orm import joinedload

from logging.handlers import RotatingFileHandler
from datetime import date

import requests
from dotenv import load_dotenv
from sqlalchemy import or_

from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from uuid import uuid4

from db import db
from models import User, Job, Category
from forms import RegisterForm, LoginForm, JobForm, DeleteForm, ProfileForm


load_dotenv()

app = Flask(__name__)


secret = os.getenv("SECRET_KEY")
if not secret:
    raise RuntimeError("SECRET_KEY is missing")
app.config["SECRET_KEY"] = secret


db_url = os.getenv("DATABASE_URL")
if db_url and db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url or (
    "sqlite:///" + os.path.join(app.instance_path, "jobboard.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["UPLOADS_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

app.config["TBC_API_KEY"] = os.getenv("TBC_API_KEY")
app.config["TBC_BASE_URL"] = os.getenv("TBC_BASE_URL", "https://test-api.tbcbank.ge")

os.makedirs(app.instance_path, exist_ok=True)
os.makedirs(app.config["UPLOADS_FOLDER"], exist_ok=True)



LOG_FILE = os.path.join(app.instance_path, "jobboard.log")

logger = logging.getLogger("jobboard")
logger.propagate = False

if not logger.handlers:
    logger.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(file_handler)



db.init_app(app)
logger.info("DB backend: %s", "postgres" if db_url else "sqlite")
csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"




with app.app_context():
    print("DB URL:", db.engine.url.render_as_string(hide_password=True))
    db.create_all()

    if Category.query.count() == 0:
        db.session.add_all([
            Category(name="IT"),
            Category(name="Design"),
            Category(name="Marketing"),
            Category(name="Sales"),
            Category(name="Other"),
        ])
        db.session.commit()



_RATES_CACHE = {"value": None, "expires_at": 0}
_RATES_TTL_SECONDS = 600


def tbc_get_commercial_rates(currencies=("USD", "EUR", "GBP")):
    api_key = app.config.get("TBC_API_KEY")
    if not api_key:
        raise RuntimeError("TBC_API_KEY is missing. Put it into .env")

    base_url = app.config.get("TBC_BASE_URL", "https://test-api.tbcbank.ge").rstrip("/")
    url = f"{base_url}/v1/exchange-rates/commercial"

    headers = {"apikey": api_key}
    params = {"currency": ",".join(c.lower() for c in currencies)}

    resp = requests.get(url, headers=headers, params=params, timeout=5)
    resp.raise_for_status()
    return resp.json()


def get_rates_tbc():

    try:
        data = tbc_get_commercial_rates(("USD", "EUR", "GBP"))

        items = (
            data.get("commercialRatesList")
            or data.get("commercialRates")
            or data.get("rates")
            or []
        )

        mapping = {}

        if isinstance(items, dict):
            mapping = {k.upper(): float(v) for k, v in items.items()}

        elif isinstance(items, list):
            for it in items:
                if not isinstance(it, dict):
                    continue

                ccy = (it.get("currency") or it.get("ccy") or it.get("code") or "").upper()
                if not ccy:
                    continue

                rate = None
                for key in ("sell", "sellRate", "rate", "value", "buy", "buyRate"):
                    if it.get(key) is not None:
                        rate = float(it[key])
                        break

                if rate is not None:
                    mapping[ccy] = rate

        usd_gel = mapping.get("USD")
        eur_gel = mapping.get("EUR")
        gbp_gel = mapping.get("GBP")

        if usd_gel is None or eur_gel is None or gbp_gel is None:
            logger.warning(
                f"tbc_rates_parse_failed keys={list(data.keys())} mapping={mapping}"
            )
            return None

        usd_eur = usd_gel / eur_gel

        return {
            "usd_gel": usd_gel,
            "eur_gel": eur_gel,
            "gbp_gel": gbp_gel,
            "usd_eur": usd_eur,
            "date": data.get("date") or date.today().isoformat(),
        }

    except Exception:
        logger.exception("tbc_rates_fetch_failed")
        return None


def get_rates_tbc_cached(ttl_seconds=_RATES_TTL_SECONDS):
    now = time.time()
    cached = _RATES_CACHE["value"]


    if cached is not None and now < _RATES_CACHE["expires_at"]:
        return {**cached, "stale": False}

    rates = get_rates_tbc()


    if rates is not None:
        _RATES_CACHE["value"] = rates
        _RATES_CACHE["expires_at"] = now + ttl_seconds
        return {**rates, "stale": False}


    if cached is not None:
        return {**cached, "stale": True}

    return None



@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.context_processor
def inject_rates():

    if not app.config.get("TBC_API_KEY"):
        return {"rates": None, "rates_note": "Rates are not configured (no API key)."}


    rates = get_rates_tbc_cached()

    if rates is None:
        return {"rates": None, "rates_note": "Rates unavailable right now."}

    if rates.get("stale"):
        return {"rates": rates, "rates_note": "Rates may be outdated (API temporarily unavailable)."}

    return {"rates": rates, "rates_note": None}





@app.get("/about")
def about():
    return render_template("about.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        full_name = form.full_name.data.strip()

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("This email is already registered. Please log in.", "warning")
            return render_template("auth/register.html", form=form)

        user = User(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(form.password.data),
        )
        db.session.add(user)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("auth/register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("jobs"))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            logger.warning(f"login_failed email={email}")
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)

        login_user(user, remember=form.remember.data)
        logger.info(f"login_success user_id={user.id} email={user.email}")
        flash("You are logged in.", "success")

        next_url = request.args.get("next")
        return redirect(next_url or url_for("jobs"))

    return render_template("auth/login.html", form=form)



@app.get("/logout")
@login_required
def logout():
    logout_user()
    flash("You are logged out.", "info")
    return redirect(url_for("jobs"))




@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm()
    delete_form = DeleteForm()

    if request.method == "GET":
        form.full_name.data = current_user.full_name
        form.email.data = current_user.email

    if form.validate_on_submit():
        new_name = form.full_name.data.strip()
        new_email = form.email.data.strip().lower()

        if new_email != current_user.email and User.query.filter_by(email=new_email).first():
            flash("This email is already taken.", "danger")
            return render_template("profile/profile.html", form=form, delete_form=delete_form)

        current_user.full_name = new_name
        current_user.email = new_email

        file = form.photo.data
        if file and getattr(file, "filename", ""):
            original = secure_filename(file.filename)
            ext = original.rsplit(".", 1)[-1].lower()
            new_filename = f"user_{current_user.id}_{uuid4().hex}.{ext}"
            save_path = os.path.join(app.config["UPLOADS_FOLDER"], new_filename)
            file.save(save_path)
            current_user.image_filename = new_filename

        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile"))

    return render_template("profile/profile.html", form=form, delete_form=delete_form)


@app.post("/profile/delete")
@login_required
def delete_profile():
    form = DeleteForm()

    if not form.validate_on_submit():
        abort(400)

    user_id = current_user.id
    email = current_user.email


    logout_user()

    user = db.session.get(User, user_id)
    if user is None:
        abort(404)

    db.session.delete(user)
    db.session.commit()

    logger.info(f"user_deleted user_id={user_id} email={email}")
    flash("Your account has been deleted.", "info")
    return redirect(url_for("jobs"))





@app.route("/jobs/add", methods=["GET", "POST"])
@login_required
def add_job():
    form = JobForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]

    if form.validate_on_submit():
        job = Job(
            title=form.title.data.strip(),
            short_description=form.short_description.data.strip(),
            full_description=form.full_description.data.strip(),
            company_name=form.company_name.data.strip(),
            salary=form.salary.data.strip() if form.salary.data else None,
            location=form.location.data.strip(),
            category_id=form.category_id.data,
            author_id=current_user.id,
        )
        db.session.add(job)
        db.session.commit()
        logger.info(f"job_added job_id={job.id} user_id={current_user.id}")

        flash("Job added successfully.", "success")
        return redirect(url_for("jobs"))

    return render_template("jobs/add_job.html", form=form)


@app.get("/")
@app.get("/jobs")
def jobs():
    q = request.args.get("q", "", type=str).strip()
    author = request.args.get("author", "", type=str).strip()
    location = request.args.get("location", "", type=str).strip()
    category_id = request.args.get("category", type=int)
    sort = request.args.get("sort", "new", type=str)

    if sort not in {"new", "old"}:
        sort = "new"

    query = Job.query.options(joinedload(Job.author), joinedload(Job.category))

    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            Job.title.ilike(like),
            Job.company_name.ilike(like),
            Job.short_description.ilike(like),
            Job.full_description.ilike(like),
        ))

    if author:
        like = f"%{author}%"
        query = query.filter(
            Job.author.has(or_(
                User.full_name.ilike(like),
                User.email.ilike(like),
            ))
        )

    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))

    if category_id:
        query = query.filter(Job.category_id == category_id)

    order = Job.created_at.asc() if sort == "old" else Job.created_at.desc()
    jobs_list = query.order_by(order).all()

    categories = Category.query.order_by(Category.name).all()

    return render_template(
        "jobs/jobs.html",
        jobs=jobs_list,
        categories=categories,
        q=q,
        author=author,
        location=location,
        category_id=category_id,
        sort=sort,
    )



@app.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)

    if job.author_id != current_user.id:
        abort(403)

    form = JobForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name).all()]

    if request.method == "GET":
        form.title.data = job.title
        form.short_description.data = job.short_description
        form.full_description.data = job.full_description
        form.company_name.data = job.company_name
        form.salary.data = job.salary or ""
        form.location.data = job.location
        form.category_id.data = job.category_id

    if form.validate_on_submit():
        job.title = form.title.data.strip()
        job.short_description = form.short_description.data.strip()
        job.full_description = form.full_description.data.strip()
        job.company_name = form.company_name.data.strip()
        job.salary = form.salary.data.strip() if form.salary.data else None
        job.location = form.location.data.strip()
        job.category_id = form.category_id.data

        db.session.commit()
        logger.info(f"job_edited job_id={job.id} user_id={current_user.id}")

        flash("Job updated successfully.", "success")
        return redirect(url_for("job_detail", job_id=job.id))

    return render_template("jobs/edit_job.html", form=form, job=job)


@app.post("/jobs/<int:job_id>/delete")
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)

    if job.author_id != current_user.id:
        abort(403)

    form = DeleteForm()
    if form.validate_on_submit():
        db.session.delete(job)
        db.session.commit()
        logger.info(f"job_deleted job_id={job_id} user_id={current_user.id}")

        flash("Job deleted successfully.", "info")
        return redirect(url_for("jobs"))

    abort(400)

@app.get("/jobs/<int:job_id>")
def job_detail(job_id):
    job = (
        Job.query
        .options(joinedload(Job.author), joinedload(Job.category))
        .get_or_404(job_id)
    )

    delete_form = DeleteForm()
    return render_template("jobs/job_detail.html", job=job, delete_form=delete_form)



@app.get("/users/<int:user_id>")
def user_jobs(user_id):
    user = User.query.get_or_404(user_id)
    jobs_list = (
        Job.query
        .options(joinedload(Job.category), joinedload(Job.author))
        .filter_by(author_id=user.id)
        .order_by(Job.created_at.desc())
        .all()
    )
    return render_template("jobs/user_jobs.html", user=user, jobs=jobs_list)


@app.errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    logger.exception("server_error")
    return render_template("errors/500.html"), 500



if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)


