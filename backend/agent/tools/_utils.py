import json
import re


def _parse_json(text: str) -> dict:
    text = re.sub(r"```json\s*|\s*```", "", text).strip()
    return json.loads(text)
