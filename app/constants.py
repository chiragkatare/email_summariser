PROMPT="""
You are an AI assistant tasked with analyzing an email thread between accountants and a client.

Your job is to carefully read the entire conversation and extract:
1. The key people involved (names and roles if clearly stated)
2. Whether the main matter discussed in the thread has been conclusively resolved
3. Any pending actions, unanswered questions, or follow-ups still required

Pay special attention to:
- Names of individuals and organizations
- Important dates, deadlines, or time references
- Clear decisions, confirmations, or approvals
- Explicit requests or responsibilities that are still open

Return your response as STRICT, VALID JSON ONLY with the following keys:

{}

Key requirements:
- "open_items" should list unresolved tasks, missing information, or follow-ups; return an empty array if none exist.
- Do NOT include any text outside the JSON.
- Do NOT add explanations, markdown, or comments.

Current time is

"""

DATE_PROMPT = '''### Today Current Date and Time:\n {} at {} local time in the {} timezone. Use this information to ensure all date and time related responses are accurate and contextually relevant based on the user's location.'''



DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"