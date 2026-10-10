from dataclasses import dataclass, field
from hashlib import sha256
from typing import Final

from .briefing import BriefResult, get_brief


SESSION_LIMIT: Final = 5


class BriefLimitReached(RuntimeError):
    pass


@dataclass(slots=True)  # noqa: MUTABLE_OK
class BriefSession:
    """Mutable session ledger: reserve each uncached attempt before external I/O."""
    attempts: int = 0
    results: dict[str, BriefResult] = field(default_factory=dict)

    def lookup(self, context: str) -> BriefResult | None:
        return self.results.get(sha256(context.encode()).hexdigest())

    def request(self, context: str) -> BriefResult:
        key = sha256(context.encode()).hexdigest()
        if key in self.results:
            return self.results[key]
        if self.attempts >= SESSION_LIMIT:
            raise BriefLimitReached
        self.attempts += 1
        result = get_brief(context)
        self.results[key] = result
        return result
