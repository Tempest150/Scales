import json
from email.utils import parseaddr

import httpx

from logger import get_logger

log = get_logger("EmailClassifier")

# Senders that never carry a real application the user submitted, only postings/
# alerts/digests. Matched against the bare address, display name stripped.
KNOWN_NON_APPLICATION_SENDERS = {
    "jobalerts-noreply@linkedin.com",
    "notifications@github.com",   # listing repos (SimplifyJobs, PittCSC, ...) fire these
    "noreply@github.com",
}
class Duro:
    """
    Classifies an email as job-application-related (or not), and if so,
    extracts company, role, and status — via a local Ollama instance.
    """

    # status values the pipeline understands; anything else from the model -> null
    VALID_STATUS = {"applied", "oa", "interview", "rejected", "offer", "ghosted"}
    # categories that count as "the user applied for work"
    JOB_CATEGORIES = {"job", "internship", "co_op", "apprenticeship", "fellowship", "new_grad"}
    # below this the model isn't sure enough to file an application
    MIN_CONFIDENCE = 0.6

    def __init__(self, model: str = "qwen2.5:7b-instruct", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host

    def _build_prompt(self, text: str, from_email: str, subject: str) -> str:
        return f"""You classify one email. Decide whether it is a step in a JOB APPLICATION
that THIS USER personally submitted for paid work (a job, internship, co-op,
apprenticeship, fellowship, or new-grad role).

Respond with ONLY a JSON object, no other text, in this exact shape:
{{
  "is_application_related": true or false,
  "category": "job" | "internship" | "co_op" | "apprenticeship" | "fellowship" | "new_grad" | "other" | "none",
  "confidence": 0.0 to 1.0,
  "reason": "one short sentence",
  "company_name": "string or null",
  "role_title": "string or null",
  "status": "applied" | "oa" | "interview" | "rejected" | "offer" | "ghosted" | null
}}

Set is_application_related to true ONLY IF ALL of these hold:
  1. category is one of: job, internship, co_op, apprenticeship, fellowship, new_grad.
  2. The email is a direct step in the user's OWN application to an employer, with
     explicit evidence the user already applied or is in the pipeline:
     "we received your application", "thanks for applying", a recruiter writing to
     the user about a role they applied to, an online assessment (OA)/coding
     challenge to complete, an interview invite/scheduling, an interview follow-up,
     a rejection, or an offer.
  3. A specific hiring company is identifiable FROM THIS EMAIL.
  4. You can assign a non-null status. If nothing in the email indicates where the
     user is in the process, it is NOT an application step.

Set is_application_related to false (category "other" or "none") for anything else,
EVEN IF it contains the words "apply", "application", "candidate", or real company
and job names:
  - Notifications that a NEW JOB/INTERNSHIP HAS BEEN POSTED — GitHub issue/repo
    notifications (SimplifyJobs, Pitt CSC, "New Internship (Issue #...)", "New Grad"
    listing repos), Discord/Slack posting bots, "a role was just added". The user
    has NOT applied to these; they are announcements.
  - Job alerts / digests / "new jobs matching your search" / "jobs you may be interested in".
  - Job-board newsletters, recommended jobs, "complete your profile", "you appeared in N searches".
  - Credit card, loan, mortgage, financing, or insurance applications.
  - University / college admissions, course enrollment, scholarship-only notices.
  - Apartment / rental / housing applications.
  - Grant, visa, or membership applications.
  - Volunteer / unpaid / "join our talent community" invites with no specific role applied to.
  - Marketing, receipts, security alerts, newsletters, anything unrelated.

company_name and role_title MUST be copied verbatim from THIS email's text or
subject. NEVER take them from the examples below or invent them — if this email
does not name them, use null.
status meaning: applied = submission confirmed, oa = assessment requested,
interview = interview invited/scheduled/held, rejected = declined, offer = offer extended,
ghosted = the email explicitly says the process ended with no decision.

Examples (illustrative only — do NOT copy any name or title from here):
EMAIL: "Thanks for applying to the <ROLE> role at <COMPANY>. We've received your application."
-> {{"is_application_related": true, "category": "job", "confidence": 0.95, "reason": "Employer confirmed the user's application was received.", "company_name": "<COMPANY>", "role_title": "<ROLE>", "status": "applied"}}

EMAIL: from notifications@github.com, subject "[SomeOrg/Summer2027-Internships] New Internship (Issue #123)", body lists a company and a posting link.
-> {{"is_application_related": false, "category": "none", "confidence": 0.97, "reason": "GitHub notification that a new posting was added to a listing repo; the user has not applied.", "company_name": null, "role_title": null, "status": null}}

EMAIL: "5 new jobs matching 'backend engineer' - three companies are hiring. Apply now."
-> {{"is_application_related": false, "category": "none", "confidence": 0.97, "reason": "Job alert digest, not a submitted application.", "company_name": null, "role_title": null, "status": null}}

EMAIL: "You're pre-approved! Finish your credit card application in 5 minutes."
-> {{"is_application_related": false, "category": "other", "confidence": 0.98, "reason": "Credit card application, not a job.", "company_name": null, "role_title": null, "status": null}}

EMAIL: "Hi, we reviewed your application for the <ROLE> position and would like to schedule a phone screen."
-> {{"is_application_related": true, "category": "job", "confidence": 0.9, "reason": "Interview invite for a role the user applied to.", "company_name": null, "role_title": "<ROLE>", "status": "interview"}}

Email_Subject: {subject}
Received_From: {from_email}
Email:
\"\"\"
{text}
\"\"\"
"""

    async def _call_llm(self, prompt: str) -> str:
        timeout = httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=10.0)
        log.debug("calling ollama model=%s host=%s prompt_chars=%s", self.model, self.host, len(prompt))
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
            raw = response.json()["response"]
            log.info("llm raw response (%s chars): %s", len(raw), raw)
            return raw

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
            log.warning("could not parse LLM response as JSON: %.200r", cleaned)
            return self._not_related()

        category = str(data.get("category") or "none").lower()
        try:
            confidence = float(data.get("confidence"))
        except (TypeError, ValueError):
            confidence = 0.0

        status = data.get("status")
        if status not in self.VALID_STATUS:
            status = None

        # The model's own flag is necessary but not sufficient: it must also
        # land in a job-type category and be confident enough. This is what
        # keeps "apply for our credit card" style emails out.
        # A real application step always maps to a status. No status => it's an
        # announcement/alert, not something the user submitted.
        is_related = (
            bool(data.get("is_application_related", False))
            and category in self.JOB_CATEGORIES
            and confidence >= self.MIN_CONFIDENCE
            and status is not None
        )
        if not is_related:
            log.info("not application-related: flag=%s category=%s confidence=%.2f reason=%r",
                     data.get("is_application_related"), category, confidence, data.get("reason"))

        return {
            "is_application_related": is_related,
            "category": category,
            "confidence": confidence,
            "reason": data.get("reason"),
            "company_name": data.get("company_name"),
            "role_title": data.get("role_title"),
            "status": status,
        }

    def _not_related(self) -> dict:
        return {
            "is_application_related": False,
            "category": "none",
            "confidence": 0.0,
            "reason": None,
            "company_name": None,
            "role_title": None,
            "status": None,
        }
   
    async def classify(self, text: str, from_email: str, subject: str) -> dict:
        with log.section("classify", from_email=from_email, subject=subject):
            addr = parseaddr(from_email or "")[1].lower()
            if addr in KNOWN_NON_APPLICATION_SENDERS:
                log.info("from=%s (%s) is a known non-application sender; skipping LLM", from_email, addr)
                return self._not_related()
            prompt = self._build_prompt(text, from_email, subject)
            raw = await self._call_llm(prompt)
            parsed = self._parse_response(raw)
            log.info("parsed classification for from=%s -> %s", from_email, parsed)
            return parsed


# Usage in the endpoint, replacing the classify_email() stub:
#
# classifier = EmailClassifier()
# classification = await classifier.classify(text)