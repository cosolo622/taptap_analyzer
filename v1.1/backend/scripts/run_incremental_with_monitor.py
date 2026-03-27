# -*- coding: utf-8 -*-
import time
import requests

BASE = "http://127.0.0.1:8000/api"
PASSWORD = "admin123"


def main():
    login = requests.post(f"{BASE}/admin/login", json={"password": PASSWORD}, timeout=10)
    login.raise_for_status()
    token = login.json().get("token")
    headers = {"X-Admin-Token": token}

    start = requests.post(
        f"{BASE}/crawler/incremental",
        params={"product_id": 1, "start_date": "2026-01-07"},
        headers=headers,
        timeout=30
    )
    print("start:", start.status_code, start.text)

    last_crawled = -1
    stagnant_rounds = 0
    for i in range(80):
        time.sleep(30)
        status = requests.get(f"{BASE}/crawler/status", headers=headers, timeout=20).json()
        running = status.get("running")
        crawled = int(status.get("crawled", 0) or 0)
        logs = status.get("logs", [])
        last_log = logs[-1]["message"] if logs else "-"
        print(f"[{i+1}] running={running} crawled={crawled} last_log={last_log}")
        if crawled > last_crawled:
            last_crawled = crawled
            stagnant_rounds = 0
        else:
            stagnant_rounds += 1

        if not running:
            print("task_finished")
            return

        if stagnant_rounds >= 6:
            print("no_progress_too_long_stop")
            requests.post(f"{BASE}/crawler/stop", headers=headers, timeout=20)
            return

    print("max_monitor_round_reached_stop")
    requests.post(f"{BASE}/crawler/stop", headers=headers, timeout=20)


if __name__ == "__main__":
    main()
