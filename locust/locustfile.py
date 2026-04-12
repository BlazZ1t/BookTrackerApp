from locust import HttpUser, task, between
import uuid
import random


class APIUser(HttpUser):
    wait_time = between(0.5, 2)

    def on_start(self):
        self.login = f"user_{uuid.uuid4()}"
        self.password = "password123"
        self.token = None
        self.book_ids = []

        self.register()
        self.login_user()

    def auth_headers(self):
        return {
            "Authorization": f"Bearer {self.token}"
        }

    def random_book(self):
        return {
            "title": f"Book {uuid.uuid4()}",
            "author": random.choice(["Author A", "Author B", "Author C"]),
            "genre": random.choice(["fiction", "sci-fi", "fantasy", None]),
            "total_pages": random.randint(50, 500),
            "current_page": random.randint(0, 50),
            "status": random.choice(["not_started", "reading", "completed"]),
        }
    

    def register(self):
        self.client.post(
            "/auth/register",
            json={
                "login": self.login,
                "password": self.password
            }
        )


    def login_user(self):
        with self.client.post(
            "/auth/login",
            json={
                "login": self.login,
                "password": self.password
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                self.token = response.json()["jwt_token"]
            else:
                response.failure("Login failed")


    @task(5)
    def list_books(self):
        self.client.get(
            "/books/",
            headers=self.auth_headers()
        )


    @task(3)
    def create_book(self):
        with self.client.post(
            "/books/",
            name="/books/{book_id}",
            headers=self.auth_headers(),
            json=self.random_book(),
            catch_response=True
        ) as response:
            if response.status_code == 201:
                self.book_ids.append(response.json()["id"])
            else:
                response.failure("Create failed")


    @task(1)
    def update_book(self):
        if not self.book_ids:
            return

        book_id = random.choice(self.book_ids)

        self.client.put(
            f"/books/{book_id}",
            name="/books/{book_id}",
            headers=self.auth_headers(),
            json={
                "current_page": random.randint(1, 100)
            }
        )


    @task(1)
    def delete_book(self):
        if not self.book_ids:
            return

        book_id = self.book_ids.pop()

        self.client.delete(
            f"/books/{book_id}",
            name="/books/{book_id}",
            headers=self.auth_headers()
        )