"""Send each prompt in every language to an OpenAI-compatible chat API and save replies to CSV."""
import argparse
import csv
import datetime as dt
import json
import os
import sys
import urllib.request

LANGS = ["en", "ro", "ru"]
FIELDS = ["timestamp", "model", "prompt_id", "category", "lang", "prompt", "response", "error"]


def load_prompts(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        missing = [k for k in ["id", "category", *LANGS] if not r.get(k)]
        if missing:
            raise ValueError(f"prompt {r.get('id')} is missing {missing}")
    return rows


def call_openai_compatible(prompt, model, base_url, api_key, timeout=60):
    """POST to {base_url}/chat/completions. Works with any OpenAI-compatible endpoint."""
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
    return data["choices"][0]["message"]["content"]


def dry_run_client(prompt, model, base_url, api_key):
    return f"[dry-run] no API call made ({len(prompt)} chars)"


def run(prompts, langs, model, client, base_url="", api_key=""):
    out = []
    for p in prompts:
        for lang in langs:
            row = {"timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                   "model": model, "prompt_id": p["id"], "category": p["category"],
                   "lang": lang, "prompt": p[lang], "response": "", "error": ""}
            try:
                row["response"] = client(p[lang], model, base_url, api_key)
            except Exception as e:  # keep going; record the failure
                row["error"] = str(e)
            out.append(row)
    return out


def write_csv(rows, path, fields=FIELDS):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def write_scoring_sheet(rows, path):
    """Copy of the responses with empty columns for manual scoring."""
    extra = ["refused (y/n)", "safe (1-3)", "helpful (1-3)", "notes"]
    write_csv([{**r, **{k: "" for k in extra}} for r in rows], path, FIELDS + extra)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prompts", default="prompts.csv")
    ap.add_argument("--langs", default=",".join(LANGS), help="comma separated, e.g. en,ro")
    ap.add_argument("--out-dir", default="results")
    ap.add_argument("--dry-run", action="store_true", help="no network calls; fake responses")
    a = ap.parse_args(argv)

    model = os.environ.get("MSEVAL_MODEL", "dry-run" if a.dry_run else "")
    base_url = os.environ.get("MSEVAL_BASE_URL", "https://api.openai.com/v1")
    api_key = os.environ.get("MSEVAL_API_KEY", "")
    if not a.dry_run and not (model and api_key):
        sys.exit("Set MSEVAL_MODEL and MSEVAL_API_KEY (and MSEVAL_BASE_URL if not OpenAI), or use --dry-run.")

    prompts = load_prompts(a.prompts)
    langs = [l.strip() for l in a.langs.split(",") if l.strip()]
    unknown = [l for l in langs if l not in LANGS]
    if unknown or not langs:
        ap.error(f"--langs must be a comma separated list from {LANGS}, got {a.langs!r}")
    client = dry_run_client if a.dry_run else call_openai_compatible
    rows = run(prompts, langs, model, client, base_url, api_key)

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_model = "".join(c if c.isalnum() or c in "-._" else "_" for c in model)
    resp = os.path.join(a.out_dir, f"responses_{safe_model}_{stamp}.csv")
    score = os.path.join(a.out_dir, f"scoring_{safe_model}_{stamp}.csv")
    write_csv(rows, resp)
    write_scoring_sheet(rows, score)
    errors = sum(1 for r in rows if r["error"])
    print(f"Saved {len(rows)} responses ({errors} errors) to {resp}")
    print(f"Scoring sheet: {score}")


if __name__ == "__main__":
    main()
