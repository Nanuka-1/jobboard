def login(client, email, password):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def test_route_jobs_ok(client):
    resp = client.get("/jobs")
    assert resp.status_code == 200


def test_login_success(client, users):
    u1, _ = users
    resp = login(client, u1["email"], "password123")
    assert resp.status_code == 200
    assert b"Add Job" in resp.data  # появляется только после логина


def test_permissions_cannot_edit_or_delete_others_job(client, users, sample_job):
    _, u2 = users
    login(client, u2["email"], "password123")

    resp = client.get(f"/jobs/{sample_job}/edit")
    assert resp.status_code == 403

    resp = client.post(f"/jobs/{sample_job}/delete", data={}, follow_redirects=False)
    assert resp.status_code == 403
