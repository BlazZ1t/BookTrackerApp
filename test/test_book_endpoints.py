def test_status_derived_through_all_three_transitions(client):
    """Create a book at page 0 → reading → completed → back to not_started"""
    client.post(
        "/auth/register",
        json={"login": "alice", "password": "pass"},
    )
    token = client.post(
        "/auth/login",
        json={"login": "alice", "password": "pass"},
    ).json()["jwt_token"]
    h = {"Authorization": f"Bearer {token}"}

    # Create book: not_started
    book = client.post(
        "/books/",
        json={
            "title": "Book",
            "author": "Author",
            "status": "not_started",
            "total_pages": 100,
            "current_page": 0,
        },
        headers=h,
    ).json()
    assert book["status"] == "not_started"
    assert book["progress_percent"] == 0.0
    bid = book["id"]

    # Update current_page=50 → reading
    r = client.put(
        f"/books/{bid}",
        json={"current_page": 50},
        headers=h,
    )
    assert r.json()["status"] == "reading"
    assert r.json()["progress_percent"] == 50.0

    # Update current_page=100 → completed
    r = client.put(
        f"/books/{bid}",
        json={"current_page": 100},
        headers=h,
    )
    assert r.json()["status"] == "completed"
    assert r.json()["progress_percent"] == 100.0

    # Update current_page=0 → not_started
    r = client.put(
        f"/books/{bid}",
        json={"current_page": 0},
        headers=h,
    )
    assert r.json()["status"] == "not_started"
    assert r.json()["progress_percent"] == 0.0
