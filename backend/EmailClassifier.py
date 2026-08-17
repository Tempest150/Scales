import json
import httpx

KNOWN_NON_APPLICATION_SENDERS = {
        "jobalerts-noreply@linkedin.com"
    }
class Duro:
    """
    Classifies an email as job-application-related (or not), and if so,
    extracts company, role, and status — via a local Ollama instance.
    """

    def __init__(self, model: str = "qwen2.5:7b-instruct", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host

    def _build_prompt(self, text: str, from_email: str, subject: str) -> str:
        return f"""You are classifying an email to determine if it relates to a job application
                    the user has personally submitted — not general job-market content.
                    You will receive the email text, subject, and sender's email address.

                    Respond with ONLY a JSON object, no other text, in this exact shape:
                    {{
                    "is_application_related": true or false,
                    "company_name": "string or null",
                    "role_title": "string or null",
                    "status": "one of: applied, oa, interview, rejected, offer, ghosted, or null"
                    }}

                    Rules:
                    - Mark is_application_related as true ONLY if this email is about an
                    application the user has already submitted: a confirmation the
                    application was received, an interview invite, an assessment/OA
                    request, a rejection, or an offer.
                    - Mark is_application_related as false for:
                    - Job alert digests or "new jobs matching your search" emails
                        (e.g. LinkedIn Job Alerts, Indeed Job Alerts) — these list jobs
                        the user has NOT applied to, even though they mention real
                        company names and job titles.
                    - Job board newsletters, recommended jobs, or "jobs you may be
                        interested in" emails.
                    - General marketing, newsletters, or anything unrelated to a
                        specific application the user submitted.
                    - The presence of company names or job titles alone does NOT make
                    an email application-related — it must reference something the
                    user personally applied to.
                    - Only extract company_name/role_title/status if you're confident — use null
                    rather than guessing.

                    Email:
                    \"\"\"
                    {text}
                    \"\"\"
                    Email_Subject: {subject}
                    Received_From: {from_email}
            """

    async def _call_llm(self, prompt: str) -> str:
        timeout = httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            return response.json()["response"]

    def _parse_response(self, raw: str) -> dict:
        cleaned = raw.strip()
        # deepseek-r1 emits <think>...</think> reasoning before the actual answer —
        # strip it out before trying to parse JSON.
        if "</think>" in cleaned:
            cleaned = cleaned.split("</think>", 1)[1].strip()
        cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "is_application_related": False,
                "company_name": None,
                "role_title": None,
                "status": None,
            }

        return {
            "is_application_related": bool(data.get("is_application_related", False)),
            "company_name": data.get("company_name"),
            "role_title": data.get("role_title"),
            "status": data.get("status"),
        }
   
    async def classify(self, text: str, from_email: str, subject: str) -> dict:
        if from_email.lower() in KNOWN_NON_APPLICATION_SENDERS:
            return {
                "is_application_related": False,
                "company_name": None,
                "role_title": None,
                "status": None,
            }
        prompt = self._build_prompt(text, from_email, subject)
        raw = await self._call_llm(prompt)
        return self._parse_response(raw)


# Usage in the endpoint, replacing the classify_email() stub:
#
# classifier = EmailClassifier()
# classification = await classifier.classify(text)