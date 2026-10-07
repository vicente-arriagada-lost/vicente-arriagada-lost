import json
import os
from pathlib import Path

import requests


USERNAME = "vicente-arriagada-lost"

API_URL = "https://api.github.com/graphql"

OUTPUT = Path("data/contributions.json")


QUERY = """
query($username: String!) {
    user(login: $username) {
        contributionsCollection {
            contributionCalendar {
                totalContributions
                weeks {
                    contributionDays {
                        date
                        contributionCount
                        color
                    }
                }
            }
        }
    }
}
"""


def main():
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN no está definido.\n\n"
            "Este script está pensado para ejecutarse "
            "principalmente desde GitHub Actions."
        )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    payload = {
        "query": QUERY,
        "variables": {
            "username": USERNAME,
        },
    }

    response = requests.post(
        API_URL,
        json=payload,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    result = response.json()

    if "errors" in result:
        raise RuntimeError(
            "GitHub GraphQL devolvió un error:\n"
            + json.dumps(
                result["errors"],
                indent=2,
                ensure_ascii=False,
            )
        )

    user = result.get("data", {}).get("user")

    if not user:
        raise RuntimeError(
            f"No se encontró el usuario: {USERNAME}"
        )

    calendar = (
        user["contributionsCollection"]
        ["contributionCalendar"]
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "username": USERNAME,
        "totalContributions": calendar["totalContributions"],
        "weeks": calendar["weeks"],
    }

    OUTPUT.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"✓ Contribuciones obtenidas: "
        f"{calendar['totalContributions']}"
    )

    print(f"✓ Archivo generado: {OUTPUT}")


if __name__ == "__main__":
    main()
