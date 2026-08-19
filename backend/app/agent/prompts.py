ANALYZE_PROMPT = """
You are analyzing project evidence for delivery risks.

Analyze ONLY the provided evidence.

Identify a meaningful delivery risk when the evidence indicates
things such as:
- delays
- blockers
- overdue work
- critical issues
- work being at risk

Do not invent facts that are not present in the evidence.

Return:
- whether this is a risk
- a concise finding title
- a clear description grounded in the evidence

Evidence:
{evidence}
"""