"""Agentic AI layer for PENTESTLAB.

Provides:
- Level 1: AI-powered report generation (report_agent)
- Level 2: Post-scan analysis copilot + scan Q&A chat (copilot)

All AI features degrade gracefully: if GROQ_API_KEY is not configured or
the API call fails, deterministic fallbacks are used (template report,
LLMNotAvailableError raised to endpoints for clean HTTP 503 handling).
"""

from agent.llm import generate_text, llm_available, LLMNotAvailableError
from agent.report_agent import generate_ai_report
from agent.copilot import answer_scan_question, analyze_scan

__all__ = [
    "generate_text",
    "llm_available",
    "LLMNotAvailableError",
    "generate_ai_report",
    "answer_scan_question",
    "analyze_scan",
]
