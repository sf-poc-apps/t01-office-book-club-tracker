# change.md

## Change summary
Display each book's average star rating on the list page (`GET /`) next to the book, shown as `★ 4.2` when ratings exist, or `No ratings yet` when there are none. This reuses the average-computation logic already specified for the book detail page and keeps the existing stack (FastAPI + Firestore + Jinja2) and guardrails unchanged.

## Changes

1. **Compute per-book averages in the list handler**
   - In `GET /`, after fetching and sorting books by `month`, compute each book's average `stars` from the `ratings` collection (round to 1 decimal), matching the rounding rule already used on the detail page.
   - Pass the averages (and a flag/sentinel for "no ratings") to `list.html` alongside the books.
   - **Acceptance criteria:**
     - Given a book has one or more ratings, When I open `/`, Then that book row shows `★` followed by the average rounded to 1 decimal (e.g. `★ 4.2`).
     - Given a book has no ratings, When I open `/`, Then that book row shows `No ratings yet`.
     - Given multiple books, When I open `/`, Then each book's displayed average reflects only its own ratings and the existing month sort order is unchanged.
     - The average value on `/` matches the average shown on the same book's detail page.

2. **Render the average in `list.html`**
   - Update `list.html` to display the average star rating next to each book, preserving the existing status badge and base layout (POC banner intact).
   - Keep formatting consistent with the detail page (single leading `★` glyph, one decimal).
   - **Acceptance criteria:**
     - The rendered list HTML includes the `★ X.X` text for rated books and `No ratings yet` for unrated books.
     - The POC banner and status badges still render on the list page.

## Tests to add or update
- Update the list-endpoint test: seed books with and without ratings, then assert the rendered `/` HTML contains `★ <average>` (correctly rounded) for rated books and `No ratings yet` for unrated books.
- Add an assertion that the average shown on `/` equals the average shown on the corresponding `/books/{id}` detail page for the same book.
- Keep the existing "list ordered by month" and "POC banner present" assertions passing.

## Out of scope
- No changes to rating creation/upsert logic, data model, or any other endpoints.
- No new sorting/filtering by rating.
- No changes to the POC banner, `/health`, Dockerfile, or CI config.
