"""Model routing: Sonnet for live chat, Opus for heavy work."""
import re

from . import config

# Heavy work = anything that benefits from Opus-level reasoning.
_HEAVY = re.compile(
    r"\b(code|coding|debug|refactor|build|implement|program|script|"
    r"research|deep dive|analy[sz]e|investigat|plan|design|architect|"
    r"write (?:a|the|me)|draft (?:a|the)|fix|optimi[sz]e|think hard|"
    r"strateg|compare|evaluate)\b",
    re.I,
)


def choose_model(text: str) -> str:
    """Pick the model for this turn. Long or 'heavy' prompts go to Opus."""
    text = text or ""
    if _HEAVY.search(text) or len(text) > 600:
        return config.MODEL_HEAVY
    return config.MODEL_FAST
