"""Light load test — 30-50 concurrent, find breaking point."""
import random
import string

from locust import HttpUser, between, task


TRIPS = [
    "Mumbai to Goa 4 vegetarian adults budget 60000",
    "Bangalore to Ooty weekend 3 people",
    "Delhi to Rishikesh road trip family of 5",
    "Chennai to Pondicherry beach getaway",
    "Pune to Lonavala short break 2 adults",
]


def sid() -> str:
    return "load" + "".join(random.choices(string.ascii_lowercase + string.digits, k=10))


class TravelKeetUser(HttpUser):
    wait_time = between(2, 5)

    @task(4)
    def chat_turn(self):
        s = sid()
        with self.client.post(
            "/v1/chat",
            json={"session_id": s, "message": random.choice(TRIPS)},
            catch_response=True,
            name="/v1/chat",
        ) as r:
            if r.status_code != 200:
                r.failure(f"Status {r.status_code}")

    @task(2)
    def stream_turn(self):
        s = sid()
        with self.client.post(
            "/v1/chat/stream",
            json={"session_id": s, "message": random.choice(TRIPS)},
            catch_response=True,
            name="/v1/chat/stream",
            stream=True,
        ) as r:
            if r.status_code != 200:
                r.failure(f"Status {r.status_code}")
                return
            n = 0
            for _ in r.iter_lines():
                n += 1
                if n > 100:
                    break

    @task(1)
    def health(self):
        self.client.get("/v1/health", name="/v1/health")