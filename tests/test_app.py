from fastapi.testclient import TestClient

from app.main import app, store

client = TestClient(app)


def _cleanup():
    for r in store.list("ratings"):
        store.delete("ratings", r["id"])
    for b in store.list("books"):
        store.delete("books", b["id"])


def _add_book(title="Book", author="Author", suggested_by="Sam", month="2026-01", status="upcoming"):
    return store.create("books", {"title": title, "author": author, "suggested_by": suggested_by,
                                  "month": month, "status": status})


def test_health():
    assert client.get("/healthz").text == "ok"


def test_banner_on_all_pages():
    _cleanup()
    book = _add_book()
    for path in ("/", "/books/new", f"/books/{book['id']}"):
        r = client.get(path)
        assert r.status_code == 200
        assert "sf-banner.js" in r.text


def test_create_book_valid():
    _cleanup()
    r = client.post("/books", data={"title": "Dune", "author": "F. Herbert",
                                    "suggested_by": "Sam", "month": "2026-03"},
                    follow_redirects=False)
    assert r.status_code == 303
    body = client.get("/").text
    assert "Dune" in body
    assert "2026-03" in body


def test_create_book_missing_field():
    _cleanup()
    r = client.post("/books", data={"title": "", "author": "X", "suggested_by": "Sam",
                                     "month": "2026-03"}, follow_redirects=False)
    assert r.status_code in (303, 422)
    assert store.list("books") == []


def test_create_book_bad_month():
    _cleanup()
    r = client.post("/books", data={"title": "Dune", "author": "X", "suggested_by": "Sam",
                                    "month": "March"}, follow_redirects=False)
    assert r.status_code in (303, 422)
    assert store.list("books") == []


def test_list_sorted_by_month():
    _cleanup()
    _add_book(title="May book", month="2026-05")
    _add_book(title="Jan book", month="2026-01")
    _add_book(title="Mar book", month="2026-03")
    body = client.get("/").text
    assert body.index("Jan book") < body.index("Mar book") < body.index("May book")


def test_list_shows_current_status():
    _cleanup()
    _add_book(title="Hot book", status="current")
    body = client.get("/").text
    assert "Currently reading" in body


def test_single_current_book():
    _cleanup()
    a = _add_book(title="A", month="2026-01")
    b = _add_book(title="B", month="2026-02")
    r = client.post(f"/books/{a['id']}/status", data={"status": "current"}, follow_redirects=False)
    assert r.status_code == 303
    assert store.get("books", a["id"])["status"] == "current"
    r = client.post(f"/books/{b['id']}/status", data={"status": "current"}, follow_redirects=False)
    assert r.status_code == 303
    assert store.get("books", a["id"])["status"] == "finished"
    assert store.get("books", b["id"])["status"] == "current"
    currents = [x for x in store.list("books") if x["status"] == "current"]
    assert len(currents) == 1 and currents[0]["id"] == b["id"]


def test_mark_finished():
    _cleanup()
    a = _add_book(title="A", status="current")
    r = client.post(f"/books/{a['id']}/status", data={"status": "finished"}, follow_redirects=False)
    assert r.status_code == 303
    assert store.get("books", a["id"])["status"] == "finished"


def test_invalid_status_ignored():
    _cleanup()
    a = _add_book(title="A")
    client.post(f"/books/{a['id']}/status", data={"status": "bogus"}, follow_redirects=False)
    assert store.get("books", a["id"])["status"] == "upcoming"


def test_rating_create_and_upsert():
    _cleanup()
    book = _add_book()
    r = client.post(f"/books/{book['id']}/ratings",
                    data={"first_name": "Sam", "stars": "4", "comment": "Great"},
                    follow_redirects=False)
    assert r.status_code == 303
    ratings = store.list("ratings", book_id=book["id"])
    assert len(ratings) == 1
    assert ratings[0]["stars"] == 4 and ratings[0]["comment"] == "Great"
    client.post(f"/books/{book['id']}/ratings",
                data={"first_name": "Sam", "stars": "2", "comment": "Slower on reread"},
                follow_redirects=False)
    ratings = store.list("ratings", book_id=book["id"])
    assert len(ratings) == 1
    assert ratings[0]["stars"] == 2
    assert ratings[0]["comment"] == "Slower on reread"


def test_rating_upsert_normalizes_name():
    _cleanup()
    book = _add_book()
    client.post(f"/books/{book['id']}/ratings",
                data={"first_name": "Sam", "stars": "4", "comment": "a"}, follow_redirects=False)
    client.post(f"/books/{book['id']}/ratings",
                data={"first_name": " sam ", "stars": "5", "comment": "b"}, follow_redirects=False)
    assert len(store.list("ratings", book_id=book["id"])) == 1


def test_rating_invalid_stars_rejected():
    _cleanup()
    book = _add_book()
    for stars in ("0", "6"):
        r = client.post(f"/books/{book['id']}/ratings",
                        data={"first_name": "Sam", "stars": stars, "comment": ""},
                        follow_redirects=False)
        assert r.status_code in (303, 422)
    assert store.list("ratings", book_id=book["id"]) == []


def test_detail_average_and_comments():
    _cleanup()
    book = _add_book()
    client.post(f"/books/{book['id']}/ratings",
                data={"first_name": "Sam", "stars": "4", "comment": "Solid"}, follow_redirects=False)
    client.post(f"/books/{book['id']}/ratings",
                data={"first_name": "Jo", "stars": "5", "comment": "Loved it"}, follow_redirects=False)
    body = client.get(f"/books/{book['id']}").text
    assert "4.5" in body
    assert "Sam" in body and "Jo" in body
    assert "Solid" in body and "Loved it" in body


def test_detail_no_ratings():
    _cleanup()
    book = _add_book()
    body = client.get(f"/books/{book['id']}").text
    assert "No ratings yet" in body


def test_detail_unknown_book_redirects():
    _cleanup()
    r = client.get("/books/nope", follow_redirects=False)
    assert r.status_code == 303
