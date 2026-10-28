"""Level 1: AI-powered report generation agent.

Generates a professional pentest report from scan results using the Groq LLM.
Falls back to the deterministic template report (workflow/reporting.py)
whenever the LLM is unavailable or fails, so scan completion is never
blocked by AI issues.
"""

import logging
from typing import Dict, Any

from agent.llm import generate_text, llm_available
from agent.context import build_scan_context

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior penetration testing consultant writing the final report \
of an automated security assessment. You will receive the raw results of a 9-phase \
pentest workflow (passive reconnaissance, footprinting, network scanning, web scanning, \
vulnerability assessment, exploitation analysis) as JSON.

Write a professional penetration testing report in markdown that includes, in this order:
1. "# Penetration Testing Report" title
2. "## Executive Summary" - written for management, mentioning the target, the overall risk \
rating (Critical/High/Medium/Low derived from CVSS scores) and the 3-5 most important findings
3. "## Technical Findings" - one subsection per significant vulnerability or exposure, with \
severity, evidence from the scan data, and business impact
4. "## Attack Surface Analysis" - open ports, exposed paths, missing security headers and how \
they combine into potential attack paths
5. "## Remediation Plan" - prioritized actions grouped as Critical (immediate), High (30 days), \
Medium (90 days), each with a concrete recommendation
6. "## Conclusion"

Rules:
- Base every statement STRICTLY on the provided scan data. Never invent vulnerabilities, CVEs, \
ports or technologies that are not in the data. If data for a phase is missing, do not \
fabricate it - simply omit that phase.
- Quote actual values from the data (server headers, CVSS scores, port numbers, paths).
- Use markdown formatting: ##, ###, **bold**, bullet lists.
- Be factual and concise; avoid filler and generic security advice that does not relate to \
the actual findings.
- The assessment is authorized; this is for a legitimate security testing platform.
"""


async def generate_ai_report(
    scan_results: Dict[str, Any],
    target: str = "",
    fallback_report: str = "",
) -> str:
    """Generate an AI-written pentest report, with template fallback.

    Returns the fallback report unchanged if the LLM is not configured,
    so a missing API key never breaks the workflow.
    """
    if not llm_available():
        return fallback_report

    try:
        context = build_scan_context(scan_results, target)
        prompt = f"{SYSTEM_PROMPT}\n\n<scan_results>\n{context}\n</scan_results>"
        report = await generate_text(prompt, max_output_tokens=8192, temperature=0.3)
        logger.info(f"AI report generated successfully ({len(report)} chars)")
        return report
    except Exception as e:
        logger.warning(f"AI report generation failed, using template fallback: {e}")
        return fallback_report
