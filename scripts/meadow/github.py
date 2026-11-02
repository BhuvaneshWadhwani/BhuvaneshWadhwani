"""Contribution calendar retrieval via the GitHub GraphQL API."""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import date, datetime, timedelta, timezone

LEVEL_ENUM = {
    "NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4,
}


def fetch_calendar(username: str):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is not set.")

    end = date.today()
    start = end - timedelta(days=364)
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date contributionCount contributionLevel
              }
            }
          }
        }
      }
    }"""
    payload = {
        "query": query,
        "variables": {
            "login": username,
            "from": datetime.combine(start, datetime.min.time(), timezone.utc).isoformat(),
            "to": datetime.combine(end, datetime.max.time(), timezone.utc).isoformat(),
        },
    }
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "pixel-meadow",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.loads(response.read().decode())

    if result.get("errors"):
        raise RuntimeError(json.dumps(result["errors"], indent=2))
    user = result.get("data", {}).get("user")
    if not user:
        raise RuntimeError(f"GitHub user {username!r} was not found.")

    cal = user["contributionsCollection"]["contributionCalendar"]
    days = []
    for week in cal["weeks"]:
        for day in week["contributionDays"]:
            days.append({
                "date": day["date"],
                "count": int(day["contributionCount"]),
                "level": LEVEL_ENUM.get(day["contributionLevel"], 0),
            })
    return days, int(cal["totalContributions"])
