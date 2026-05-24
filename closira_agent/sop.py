import json
from pathlib import Path
from typing import Any


DEFAULT_SOP_PATH = Path(__file__).resolve().parents[1] / "data" / "sop.json"


class SOP:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    @classmethod
    def load(cls, path: Path = DEFAULT_SOP_PATH) -> "SOP":
        return cls(json.loads(path.read_text(encoding="utf-8")))

    @property
    def business(self) -> str:
        return self.data["business"]

    def service_by_name(self, text: str) -> dict[str, str] | None:
        lowered = text.lower()
        for service in self.data["services"]:
            name = service["name"].lower()
            singular = name[:-1] if name.endswith("s") else name
            if name in lowered or singular in lowered:
                return service
        return None

    def booking_channels(self) -> str:
        channels = self.data["booking"]["channels"]
        return " or ".join(channels)

    def qualification_questions(self) -> list[dict[str, str]]:
        return list(self.data["lead_qualification_questions"])
