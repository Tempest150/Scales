# Ingest flow — Gmail → n8n → email-cleaner → Quart → Ollama

Current, as of the n8n workflow export reviewed for this doc. Slated to change —
see the note at the bottom and [[Desktop-Migration]].

```mermaid
flowchart TD
    Gmail[Gmail inbox] -->|"polled every minute"| Trigger["n8n: Gmail Trigger"]
    Trigger --> Parse["n8n: Code in JavaScript<br/>builds {from, subject, text, html, user}<br/>user = to.value[0].address"]

    Parse -->|"POST /clean {html}"| Cleaner["email-cleaner service<br/>(http://email-cleaner:3000,<br/>sibling container, not in this repo)"]
    Parse --> Meta["n8n: Code in JavaScript1<br/>strips to {from, subject, user}"]

    Cleaner -->|"{text: cleaned plain text}"| Merge["n8n: Code in JavaScript2<br/>merges into {from, subject, user, text}"]
    Meta --> Merge

    Merge -->|"POST /emails<br/>{from, subject, text, user}"| API["Quart backend<br/>backend/app.py"]
    API -->|"data.get('text', '')<br/>from/subject/user read but unused"| Duro["EmailClassifier.Duro"]
    Duro -->|"POST /api/generate<br/>model: deepseek-r1:8b"| Ollama["Ollama<br/>co-located with the backend"]
    Ollama -->|"raw completion,<br/>may include &lt;think&gt;...&lt;/think&gt;"| Duro
    Duro -->|"{is_application_related,<br/>company_name, role_title, status}"| API
    API -->|"200 JSON classification"| N8NResp["back to n8n"]

    N8NResp -.->|"no downstream node consumes this —<br/>response is dropped"| Dropped(( ))

    DB[("Postgres<br/>shared with Libra")]
    Rimiru["db.py: Rimiru"]
    API -.->|"imported, never called<br/>from /emails"| Rimiru
    Rimiru -.->|"not wired up"| DB

    style Dropped fill:none,stroke:none
    style DB stroke-dasharray: 5 5
    style Rimiru stroke-dasharray: 5 5
    style N8NResp stroke-dasharray: 5 5
```

## Notes / things worth knowing

- **`email-cleaner` is not in this repo.** It's a sibling service reached at
  `http://email-cleaner:3000/clean` (n8n-internal hostname, so it's on the
  same Docker network as n8n) that turns an email's raw HTML into plain
  text. Its source isn't part of the Scales codebase.
- **The final n8n HTTP Request node's JSON body has a malformed key**:
  `"jsonBody"` contains `\"user\"\":\"{{ $json.user }}\"` — an extra `"`
  after `user`. Worth checking in the n8n editor whether this actually
  serializes correctly today; it reads as broken JSON.
- **`from`, `subject`, and `user` are sent but never read.** `backend/app.py`'s
  `/emails` route only pulls `data.get("text", "")` out of the request body —
  the email's sender, subject, and destination user are currently discarded
  server-side.
- **No database write happens in this flow** (dashed edges above). `backend/db.py`
  (`Rimiru`) is imported in `app.py` but never called from the `/emails` route —
  the classification result is computed and returned in the HTTP response, not
  persisted anywhere.
- **Planned change**: per the project owner, this synchronous
  n8n → Quart → Ollama call is going away in favor of n8n writing incoming
  emails to a Postgres queue table, which the (future Tauri) desktop app
  will pull from on load to classify client-side and write results back.
  See [[Desktop-Migration]] and `to-do.md` in the repo root.
