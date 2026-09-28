#!/usr/bin/env python3
"""Update the uptime line inside assets/terminal-hero.svg."""

import base64
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta

SVG_PATH = "assets/terminal-hero.svg"
BIRTH = datetime(2006, 8, 3, 5, 53, 0, tzinfo=ZoneInfo("Asia/Kolkata"))
UPTIME_PATTERN = re.compile(r"\d+ years?, \d+ months?, \d+ days?, \d+ hours?")
B64_PATTERN = re.compile(r"data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)")


def compute_uptime() -> str:
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    d = relativedelta(now, BIRTH)
    def unit(n: int, word: str) -> str:
        return f"{n} {word}" if n == 1 else f"{n} {word}s"

    return ", ".join(unit(n, w) for n, w in
                     ((d.years, "year"), (d.months, "month"), (d.days, "day"), (d.hours, "hour")))


def main() -> int:
    with open(SVG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    new_uptime = compute_uptime()
    changed = False

    def replace_in_b64(match: re.Match) -> str:
        nonlocal changed
        try:
            decoded = base64.b64decode(match.group(1)).decode("utf-8")
        except Exception:
            return match.group(0)

        new_decoded, n = UPTIME_PATTERN.subn(new_uptime, decoded)
        if n == 0 or new_decoded == decoded:
            return match.group(0)

        changed = True
        new_b64 = base64.b64encode(new_decoded.encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{new_b64}"

    new_content = B64_PATTERN.sub(replace_in_b64, content)

    if changed and new_content != content:
        with open(SVG_PATH, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"updated uptime -> {new_uptime}")
        return 0

    print(f"no change (current: {new_uptime})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
