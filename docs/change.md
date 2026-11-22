## Change summary

Add a client-facing search box on the list page (`/`) that filters the displayed books by title or author. Filtering is performed server-side via an optional query parameter so it works without JavaScript and stays within the existing FastAPI + Jinja2 + Firestore stack. No new collections, endpoints, or external calls.

## Changes

1. **Add optional search query parameter to the list route**
   - Extend `GET /` to accept an optional query parameter `q` (string, default empty/absent).
   - When `q` is non-empty, filter the fetched books to those whose `title` or `author` contains `q` (case-insensitive, trimmed substring match). Filtering happens in the handler after fetching and sorting by `month`.
   - When `q` is empty or absent, behavior is unchanged (all books shown, sorted by `month`).
   - *Acceptance:* `GET /?q=orwell` returns only books whose title or author contains "orwell" (case-insensitive); `GET /` with no `q` returns all books sorted by `month` as before.

2. **Add a search box to `list.html`**
   - Add a small search form at the top of the list, above the book list, as a `GET` form targeting `/` with a single text input named `q`.
   - Preserve the current search term in the input's value after submission so the box reflects the active filter.
   - Keep the POC banner and base layout intact (template extends base as before).
   - *Acceptance:* The list page renders a search input; submitting a term reloads `/` with the `q` parameter and shows only matching books while the input retains the entered term.

3. **Handle the empty-result case gracefully**
   - When a search yields no matching books, show a short "No books match your search." message instead of an empty list. This message must not replace the existing empty-state behavior when there are simply no books at all.
   - *Acceptance:* Searching a term that matches nothing displays the no-match message; an app with zero books total still shows its existing empty state.

## Tests to add or update

- Add: `GET /?q=<term>` returns only books whose `title` contains the term (case-insensitive); non-matching books are excluded.
- Add: `GET /?q=<term>` matches on `author` as well as `title`.
- Add: `GET /` with no `q` (and with empty `q`) returns all books, still sorted by `month` (existing ordering assertion preserved).
- Add: `GET /?q=<no-match>` renders the "No books match your search." message.
- Update: existing list-page rendering test to confirm the search input is present and the POC banner still renders.

## Out of scope

- Filtering by month, status, rating, suggested_by, or any field other than title/author.
- Fuzzy/ranked search, pagination, or sorting changes.
- New endpoints, collections, or schema fields.
- Any client-side-only JavaScript framework; the search uses a plain server-rendered GET form.
