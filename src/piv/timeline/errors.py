"""Errors of the timeline contract (docs/contracts/timeline.md)."""


class TimelineError(ValueError):
    """Base: something about a timeline, recipe or variant spec is not acceptable."""


class FormatError(TimelineError):
    """The JSON is not a well-formed document of the kind asked for (missing field, wrong type)."""


class VersionError(TimelineError):
    """`format_version` is one this reader does not know; refused rather than guessed."""


class ValidationError(TimelineError):
    """The document is well formed but breaks a rule. `problems` lists every rule broken."""

    def __init__(self, problems: list[str]):
        self.problems = list(problems)
        super().__init__("; ".join(self.problems))


class Refused(TimelineError):
    """A build that cannot be made convincing (a layout that shrinks the product too far, a
    swap without a placement). `reason` says why, in a sentence a person can act on."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)
