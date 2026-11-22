# Office Book Club Tracker

A small FastAPI app for an office book club (~12 people): track the books the club reads,
highlight the single book currently being read, and collect member ratings (1-5 stars) and
short comments. No login - members identify themselves by a first name.

## Features
- Add a book (title, author, suggested by, month `YYYY-MM`).
- Book list sorted by month with status badges (upcoming / currently reading / finished).
- Mark a book current (only one book can be current at a time; the previous one becomes
  finished) or finished.
- Rate a book 1-5 stars with a short comment, identified by first name. Submitting again
  with the same first name updates the existing rating (upsert), so there is one rating
  per person per book.
- Book detail page shows the average rating (rounded to 1 decimal) and all comments;
  shows "No ratings yet" when unrated.

## Usage
- Install: `pip install -r requirements-dev.txt && cp sf-banner.js app/static/sf-banner.js`
- Run locally: `uvicorn app.main:app --reload`
- Open `/` for the book list, `/books/new` to add a book, `/books/{id}` for details and ratings.
- Data is stored in Firestore when `FIRESTORE_DB` is set, otherwise in memory.
- Health check: `GET /healthz`.

## Tests
`python -m pytest -q`

Note: this is a trusted small-group tool without authentication; do not enter personal or
confidential data.
