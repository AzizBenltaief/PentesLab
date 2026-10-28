"""Level 2: Post-scan analysis copilot.

Two capabilities:
- analyze_scan(): one-shot AI triage of a completed scan (key risks,
  attack paths, prioritized remediation, suggested next tests).
- answer_scan_question(): conversational Q&A grounded in a specific
  scan's results, with conversation history support.
"""

import logging
from typing import Dict, Any, List, Optional

from agent.llm import generate_text, llm_available, LLMNotAvailableError
from agent.context import build_scan_context

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """You are PENTESTLAB Copilot, a senior security analyst reviewing the \
results of an automated penetration test. You receive the raw scan results as JSON.

Produce a concise expert analysis in markdown with these sections:
1. "## Key Findings" - the most important issues, ranked by severity (reference actual CVSS \
scores, ports, paths and headers from the data)
2. "## Attack Paths" - realistic chains connecting findings (e.g. exposed service + missing \
hardening + credential exposure). Only describe chains supported by the actual data.
3. "## Prioritized Remediation" - numbered, concrete actions ordered by risk reduction
4. "## Suggested Next Tests" - what an analyst should manually verify next, based on what \
the automation found

Rules:
- Use ONLY the provided scan data. Never invent findings, CVEs or services not present in it.
- If the scan found nothing significant, say so plainly and focus on hardening advice.
- Keep it under ~600 words, factual, no filler.
- The assessment is authorized; this is a legitimate security testing platform.
"""

COPILOT_PROMPT = """You are PENTESTLAB Copilot, a senior security analyst assistant embedded in \
a penetration testing platform. You help the user understand and act on the results of a scan \
that was run against {target}.

You must answer based STRICTLY on the scan data provided below. If something is not in the \
data, say so instead of guessing. If the user asks something unrelated to this scan or to \
security, politely redirect them to scan-related topics.

Style: professional, concise, markdown-formatted (##, **bold**, - bullets). Reference actual \
values (CVSS scores, ports, paths, headers) from the data. The assessment is authorized.

{history_section}
<scan_results>
{context}
</scan_results>

User question: {question}

Answer:"""


def _format_history(history: Optional[List[Dict[str, str]]], max_turns: int = 6) -> str:
    if not history:
        return ""
    recent = [m for m in history if m.get("role") in ("user", "assistant")][-max_turns:]
    if not recent:
        return ""
    lines = ["Previous conversation:"]
    for m in recent:
        role = "User" if m["role"] == "user" else "Copilot"
        content = (m.get("content") or "")[:1500]
        lines.append(f"{role}: {content}")
    return "\n".join(lines) + "\n\n"


async def analyze_scan(
    scan_results: Dict[str, Any],
    target: str = "",
) -> str:
    """Generate a one-shot AI triage analysis of scan results.

    Raises LLMNotAvailableError if the LLM is not configured or fails.
    """
    if not llm_available():
        raise LLMNotAvailableError("Gemini API key not configured")

    context = build_scan_context(scan_results, target)
    prompt = f"{ANALYSIS_PROMPT}\n\n<scan_results>\n{context}\n</scan_results>"
    return await generate_text(prompt, max_output_tokens=4096, temperature=0.4)


async def answer_scan_question(
    question: str,
    scan_results: Dict[str, Any],
    target: str = "",
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """Answer a user question grounded in a specific scan's results.

    Raises LLMNotAvailableError if the LLM is not configured or fails.
    """
    if not llm_available():
        raise LLMNotAvailableError("Gemini API key not configured")

    context = build_scan_context(scan_results, target)
    history_section = _format_history(history)
    prompt = COPILOT_PROMPT.format(
        target=target or "the scanned target",
        history_section=history_section,
        context=context,
        question=question[:2000],
    )
    return await generate_text(prompt, max_output_tokens=2048, temperature=0.4)
