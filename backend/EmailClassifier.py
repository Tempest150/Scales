import json
import httpx


class Duro:
    """
    Classifies an email as job-application-related (or not), and if so,
    extracts company, role, and status — via a local Ollama instance.
    """

    def __init__(self, model: str = "qwen2.5:7b-instruct", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host

    def _build_prompt(self, text: str,from_email: str,subject: str) -> str:
        return f"""You are classifying an email to determine if it relates to a job application.
                    You will receive the email text, subject, and sender's email address. 
                    The email text is the main content of the email, the subject is the email's subject line, and the sender's email address is the email address of the person who sent the email.
  

                    Respond with ONLY a JSON object, no other text, in this exact shape:
                    {{
                    "is_application_related": true or false,
                    "company_name": "string or null",
                    "role_title": "string or null",
                    "status": "one of: applied, oa, interview, rejected, offer, ghosted, or null"
                    }}

                    Rules:
                    - If the email is a job-application confirmation, interview invite, assessment
                    request, rejection, or offer, mark is_application_related as true.
                    - If it's a marketing email, newsletter, or anything unrelated to a job
                    application, mark is_application_related as false and leave the other
                    fields null.
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
        async with httpx.AsyncClient(timeout=60.0) as client:
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
        prompt = self._build_prompt(text, from_email, subject)
        raw = await self._call_llm(prompt)
        return self._parse_response(raw)


# Usage in the endpoint, replacing the classify_email() stub:
#
# classifier = EmailClassifier()
# classification = await classifier.classify(text)