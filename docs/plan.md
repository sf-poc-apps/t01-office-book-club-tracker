# Office Book Club Tracker

## Summary
A small office book club of about 12 people needs a simple shared place to track the books they read, highlight the one currently being read, and collect member ratings and comments. This FastAPI + Firestore app lets anyone add books, mark a single "current" book, and rate books 1–5 stars with a short comment. No login is required; members identify themselves by typing a first name.

## Similar initiatives
- **LP-014: Training session feedback (fastapi-crud)** — Reuses the pattern of collecting ratings (1–5) plus free-text comments and showing an average. Differs by attaching ratings to books rather than sessions and enforcing one rating per name per book (upsert).
- **LP-001: Meeting room booking (fastapi-crud)** — Reuses the server-rendered list/detail Jinja2 pattern and the "single exclusive state" idea (one booking per slot → here, one current book at a time). Differs by not using date/time grids.
- **LP-018: New joiner checklist (nextjs-crud)** — Different stack (Next.js), so not reused directly; only borrows the "no real login, identify by name" convention.

## Scope
1. **Add a book**
   - *Story:* As a club member, I want to add a book with its details so the club can track what we read.
   - Given I am on the add-book form, When I submit title, author, suggested_by and month, Then the book is saved and appears on the list page.
   - Given I submit with a missing required field, When the form validates, Then I see an error and no book is created.

2. **List books sorted by month**
   - *Story:* As a member, I want to see all books ordered by month so I can scan our reading history.
   - Given one or more books exist, When I open the list page, Then books are shown sorted by month.
   - Given a book is current, When I view the list, Then its status is clearly indicated.

3. **Mark a book current or finished (single current)**
   - *Story:* As a member, I want to set the current book so everyone knows what we're reading now.
   - Given a book is set to current, When another book was previously current, Then the previous one is changed to finished so at most one book is current.
   - Given a book, When I mark it finished, Then its status updates to finished.

4. **Rate a book by first name (upsert)**
   - *Story:* As a member, I want to rate a book 1–5 stars with a comment using my first name.
   - Given I submit a rating with stars (1–5), a comment and a first name, When I save, Then a rating is recorded for that book.
   - Given I already rated this book with the same first name, When I submit again, Then my existing rating is updated rather than duplicated.
   - Given stars are outside 1–5, When I submit, Then the rating is rejected with an error.

5. **Show average rating and comments**
   - *Story:* As a member, I want to see each book's average rating and all comments.
   - Given a book has ratings, When I view its detail page, Then I see the average star rating and the list of comments with first names.
   - Given a book has no ratings, When I view it, Then it shows "No ratings yet".

## Out of scope
- Login or user accounts (identify by first name only).
- Email or SMS notifications.
- External book lookups or third-party APIs.
- Role-based editing or deleting.
- Storing employer-confidential or sensitive personal data.

## Data model
Firestore collections:

**books**
- `id`: string (document id)
- `title`: string
- `author`: string
- `suggested_by`: string
- `month`: string (format `YYYY-MM`, used for sorting)
- `status`: string enum (`upcoming` | `current` | `finished`), default `upcoming`
- `created_at`: timestamp

**ratings**
- `id`: string (document id, e.g. `{book_id}_{normalized_first_name}` to enforce uniqueness)
- `book_id`: string (reference to books.id)
- `first_name`: string
- `stars`: integer (1–5)
- `comment`: string (short)
- `updated_at`: timestamp

## Pages and endpoints
| Path | Method | Purpose | Who uses it |
|------|--------|---------|-------------|
| `/` | GET | Book list page sorted by month, shows status | All members |
| `/books/new` | GET | Form to add a book | All members |
| `/books` | POST | Create a book | All members |
| `/books/{id}` | GET | Book detail: info, average rating, comments, rating form | All members |
| `/books/{id}/status` | POST | Set status current/finished (enforces single current) | All members |
| `/books/{id}/ratings` | POST | Submit/upsert a rating by first name | All members |
| `/health` | GET | Health check (unchanged from template) | Ops/CI |

## Test plan
**Automated (unit + HTTP-level, add to the template's test dir):**
- `POST /books` with valid data creates a book and redirects/renders the list containing it.
- `POST /books` with a missing field returns a validation error and creates nothing.
- List endpoint returns books ordered by `month`.
- `POST /books/{id}/status` to `current` sets target to current and flips any prior current book to `finished`; assert at most one `current` exists.
- `POST /books/{id}/ratings` with stars 1–5 creates a rating; same `first_name` + same book updates in place (count stays 1, values change).
- Rating with stars outside 1–5 is rejected.
- Book detail computes the correct average rating and lists comments.
- POC banner is present in rendered HTML.

**Manual UAT checklist (requester, on staging):**
1. Add three books with different months; confirm they appear sorted by month.
2. Mark book A as current, then mark book B as current; confirm A becomes finished and only B is current.
3. Rate book B as "Sam" 4 stars with a comment; confirm it shows on the detail page.
4. Re-rate book B as "Sam" with 2 stars; confirm no duplicate and the value updated.
5. Add a second rating as "Jo"; confirm the average updates correctly.
6. Confirm a book with no ratings shows "No ratings yet".
7. Confirm the POC banner is visible on every page.

## Risks and guardrails
- **No authentication (template rule):** Members are identified by a typed first name only; anyone can edit status or ratings. Acceptable for a trusted 12-person office club; document this on the UI.
- **Name collisions:** Two people sharing a first name would overwrite each other's rating. Mitigate by normalizing names and noting this limitation on the rating form.
- **Single-current race condition:** Flip of previous current → finished must happen in one request path; use a query-then-update within the same handler (Firestore transaction if available in template) to avoid two current books.
- **No outbound HTTP / external APIs (template rule):** Book data is entered manually; no external lookups.
- **No sensitive data (spec + template rule):** Comments are short and public to the club; add a note discouraging personal/confidential content.
- **Keep template banner, `/health` endpoint, Dockerfile and CI files unchanged.**

## Builder instructions
1. Start from the `fastapi-crud` template. Do **not** modify the POC banner, `/health` endpoint, `Dockerfile`, or CI workflow files.
2. In the Firestore access module, add helpers for two collections: `books` and `ratings` (create, get, list, update).
3. Define Pydantic models/schemas for `Book` (title, author, suggested_by, month, status) and `Rating` (book_id, first_name, stars, comment). Validate `stars` in range 1–5 and `status` in {`upcoming`,`current`,`finished`}.
4. Add routes in the app router:
   - `GET /` — fetch all books, sort by `month` ascending, render list template with status badges.
   - `GET /books/new` and `POST /books` — render form and create a book (default status `upcoming`).
   - `GET /books/{id}` — render detail: book fields, computed average of `stars`, list of comments, and a rating form.
   - `POST /books/{id}/status` — set the given book's status; if setting to `current`, query the existing `current` book and set it to `finished` first (prefer a Firestore transaction to keep it atomic).
   - `POST /books/{id}/ratings` — upsert using document id `{book_id}_{normalized_first_name}` (lowercase, trimmed); update stars/comment and `updated_at` on repeat submissions.
5. Add Jinja2 templates: `list.html`, `book_form.html`, `book_detail.html`, extending the template's base layout so the banner stays intact. Include the status toggle buttons and the rating form on the detail page.
6. Compute average rating in the route handler (round to 1 decimal) and pass it to `book_detail.html`; show "No ratings yet" when there are none.
7. Add the automated tests listed in the Test plan under the template's existing test directory; ensure they run in CI without changing CI config.
8. Run the test suite locally and confirm all pass before handing off for review.
