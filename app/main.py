import os
import pathlib

from fastapi import FastAPI, Form, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.store import make_store

BASE = pathlib.Path(__file__).parent
app = FastAPI(title="Office Book Club Tracker")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
templates.env.globals["sf"] = {"expires": os.environ.get("SF_EXPIRES", ""), "env": os.environ.get("SF_ENV", "local")}
store = make_store()

MAX_LEN = 200
MAX_COMMENT = 500
STATUSES = ("upcoming", "current", "finished")


def _valid_month(month: str) -> bool:
    parts = month.split("-")
    if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        return False
    return 1 <= int(parts[1]) <= 12


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"


@app.get("/")
def index(request: Request):
    books = store.list("books", order_by="month")
    ratings_by_book: dict[str, list] = {}
    for rating in store.list("ratings"):
        ratings_by_book.setdefault(rating.get("book_id"), []).append(rating)
    avgs = {}
    for book in books:
        ratings = ratings_by_book.get(book["id"], [])
        avgs[book["id"]] = round(sum(r["stars"] for r in ratings) / len(ratings), 1) if ratings else None
    return templates.TemplateResponse(request, "list.html", {"books": books, "avgs": avgs})


@app.get("/books/new")
def new_book(request: Request, error: str = ""):
    return templates.TemplateResponse(request, "book_form.html", {"error": error})


@app.post("/books")
def create_book(
    title: str = Form(..., max_length=MAX_LEN),
    author: str = Form(..., max_length=MAX_LEN),
    suggested_by: str = Form(..., max_length=MAX_LEN),
    month: str = Form(..., max_length=7),
):
    title = title.strip()
    author = author.strip()
    suggested_by = suggested_by.strip()
    month = month.strip()
    if not title or not author or not suggested_by or not _valid_month(month):
        return RedirectResponse("/books/new?error=" + "1", status_code=303)
    store.create("books", {"title": title, "author": author, "suggested_by": suggested_by,
                           "month": month, "status": "upcoming"})
    return RedirectResponse("/", status_code=303)


@app.get("/books/{book_id}")
def book_detail(request: Request, book_id: str, error: str = ""):
    book = store.get("books", book_id)
    if not book:
        return RedirectResponse("/", status_code=303)
    ratings = store.list("ratings", order_by="-updated_at", book_id=book_id)
    avg = round(sum(r["stars"] for r in ratings) / len(ratings), 1) if ratings else None
    return templates.TemplateResponse(request, "book_detail.html",
                                      {"book": book, "ratings": ratings, "avg": avg, "error": error})


@app.post("/books/{book_id}/status")
def set_status(book_id: str, status: str = Form(...)):
    status = status.strip()
    if status not in ("current", "finished"):
        return RedirectResponse(f"/books/{book_id}", status_code=303)
    book = store.get("books", book_id)
    if not book:
        return RedirectResponse("/", status_code=303)
    if status == "current":
        for other in store.list("books", status="current"):
            if other["id"] != book_id:
                store.update("books", other["id"], {"status": "finished"})
    store.update("books", book_id, {"status": status})
    return RedirectResponse("/", status_code=303)


@app.post("/books/{book_id}/ratings")
def submit_rating(
    book_id: str,
    first_name: str = Form(..., max_length=MAX_LEN),
    stars: int = Form(...),
    comment: str = Form("", max_length=MAX_COMMENT),
):
    book = store.get("books", book_id)
    if not book:
        return RedirectResponse("/", status_code=303)
    first_name = " ".join(first_name.strip().split())
    comment = comment.strip()
    if not first_name or not (1 <= stars <= 5) or len(comment) > MAX_COMMENT:
        return RedirectResponse(f"/books/{book_id}?error=" + "1", status_code=303)
    doc_id = f"{book_id}_{_normalize_name(first_name)}"
    store.upsert("ratings", doc_id, {"book_id": book_id, "first_name": first_name,
                                     "stars": stars, "comment": comment})
    return RedirectResponse(f"/books/{book_id}", status_code=303)
