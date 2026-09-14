"""Read-only Render keep-alive probe used by the scheduled cron service."""

import json
import os
import sys
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def main() -> int:
    url = os.getenv("PANGEAWORLD_HEALTH_URL", "").strip()
    if urlparse(url).scheme != "https" or not url.endswith("/healthz"):
        print("PANGEAWORLD_HEALTH_URL must be an HTTPS /healthz URL", file=sys.stderr)
        return 2

    request = Request(url, headers={"User-Agent": "PangeaWorld-Render-Keepalive/1.0"})
    try:
        with urlopen(request, timeout=20) as response:  # noqa: S310 - URL is validated above
            payload = json.loads(response.read().decode("utf-8"))
            if response.status != 200 or payload.get("status") != "ok":
                raise RuntimeError(f"unhealthy response: HTTP {response.status}")
    except Exception as exc:
        print(f"PangeaWorld health check failed: {exc}", file=sys.stderr)
        return 1

    print("PangeaWorld health check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

