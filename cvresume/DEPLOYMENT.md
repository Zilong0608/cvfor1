# Resume parsing and search configuration

The backend is started from `cvresume` with:

```sh
pip install -r requirements.txt
uvicorn api_server:app --host 0.0.0.0 --port $PORT
```

Set the Render health check path to `/api/health`.

The frontend build remains `npm ci && npm run build` from `cvresume/frontend`;
publish `build`. For a separately hosted backend, set `VITE_API_BASE_URL` to
`https://YOUR-BACKEND.onrender.com/api` **before building the frontend**.
The Vite `/api` proxy applies only to local development.

## AI extraction

Set `OPENAI_API_KEY` in the backend environment. Existing `OPENAI_MODEL` and
`OPENAI_BASE_URL` settings are reused. `RESUME_PARSE_MODEL` optionally overrides
the extraction model (must support strict JSON Schema); the existing default
is `gpt-4o-mini`. `RESUME_AI_PARSE=0` disables AI extraction.

Resume text is sent to the configured AI provider for extraction. It is not
stored in the public job search cache. Missing keys, refused/incomplete output,
and API failures fall back to basic extraction with a visible review warning.
Scanned PDFs without selectable text need OCR before upload; no OCR is included.
Files are limited to 10 MB and extracted text to 40,000 characters.

## Search behavior

The initial search uses the exact title, up to 20 jobs per platform and a
35-second response budget (after the backend has started). Expand Search
replaces the result set with a broader search: up to three title variants,
40 jobs per platform, and a 60-second response budget. It includes additional
platforms supported in the selected country. Jobs appear as each platform
finishes. A stalled platform cannot prevent returning the other results.

Completed searches without failures are cached for five minutes, at most 64
queries per backend process. The cache is for public jobs only, and resets on
restart. External sites may throttle or block requests; results are not guaranteed.
Timed-out worker threads cannot be force-killed, so a shared worker/queue limit
prevents accumulating unlimited work; running calls retain their slot until done.

The default resume generation batch is 10; users can still change it. ZIPs and
their download IDs still use temporary files and in-process state, so they do not
survive backend restarts and are not shared across multiple workers. Use one
backend worker until persistent task/file storage is added. Supabase is not
required or automatically connected by this change.

Editing or replacing a resume invalidates previous generation progress and ZIP
references, while retaining the public job results for a new generation run.
The preview and regenerated files therefore use the newly confirmed profile.

Render's free backend can still sleep and incur a cold start. Code changes do
not remove that hosting behavior. Parsing and streaming requests allow extra
time for startup, and interrupted streams now report an error rather than a
false success. Opening the upload screen starts a health request to wake the
backend while the user selects a file.
