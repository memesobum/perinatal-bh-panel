#!/usr/bin/env python3
"""Deposit files on Zenodo (or its sandbox) with metadata, and optionally publish for a DOI.

Reads ZENODO_TOKEN (or ZENODO_SANDBOX_TOKEN with --sandbox) from the environment.
Token scopes: deposit:write and deposit:actions.

Always run with --sandbox first. The sandbox mints fake DOIs and shows exactly
what the public record will look like. Only publish for real after the author
has looked at the sandbox record and the publish gate has passed.

metadata.json example:
{
  "upload_type": "dataset",
  "title": "The Example Atlas v0.1.0",
  "creators": [{"name": "Surname, Given", "orcid": "0000-0000-0000-0000"}],
  "description": "<p>What it is, sources, vintage, limitations link.</p>",
  "license": "cc-by-4.0",
  "keywords": ["open data", "access"],
  "version": "0.1.0",
  "related_identifiers": [{"identifier": "https://github.com/user/repo", "relation": "isSupplementTo", "scheme": "url"}],
  "access_right": "open"
}

Usage:
  python zenodo_deposit.py --files release.zip README.md --metadata metadata.json [--sandbox]
                           [--publish] [--new-version-of <record_id>]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

import requests


def run_gate(files, metadata_path):
    """Run publish_gate.py over everything being uploaded (zip contents included) and the metadata.

    Scripts under any code/ or tools/ folder may mention the draft switch, so draft words are
    tolerated there only; every data file, document, and the metadata itself must be clean.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    tmp = tempfile.mkdtemp(prefix="zenodo_gate_")
    try:
        allow = set()
        for f in files:
            if f.lower().endswith(".zip"):
                with zipfile.ZipFile(f) as z:
                    z.extractall(tmp)
                    for n in z.namelist():
                        parts = n.split("/")
                        for i, p in enumerate(parts[:-1]):
                            if p in ("code", "tools"):
                                allow.add("/".join(parts[: i + 1]))
            else:
                shutil.copy2(f, tmp)
        shutil.copy2(metadata_path, os.path.join(tmp, "zenodo_metadata.json"))
        for req in ("README.md", "LICENSE"):  # gate requires these at its root; take them from the zip if present
            if not os.path.exists(os.path.join(tmp, req)):
                found = [os.path.join(dp, req) for dp, _, fns in os.walk(tmp) if req in fns]
                if found:
                    shutil.copy2(found[0], os.path.join(tmp, req))
        cmd = [sys.executable, os.path.join(here, "publish_gate.py"), tmp]
        if allow:
            cmd += ["--allow-draft-in", *sorted(allow)]
        if subprocess.run(cmd).returncode != 0:
            sys.exit("gate failed; not uploading")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--files", nargs="+", required=True)
    ap.add_argument("--metadata", required=True, help="path to metadata.json")
    ap.add_argument("--sandbox", action="store_true")
    ap.add_argument("--publish", action="store_true", help="publish (mints the DOI); omit to leave as draft")
    ap.add_argument("--new-version-of", help="existing record id to version instead of creating a new record")
    ap.add_argument("--skip-gate", action="store_true",
                    help="sandbox tests only; refused together with --publish on production")
    ap.add_argument("--authors", default="AUTHORS.json",
                    help="author block to build creators from when metadata has none (default: AUTHORS.json)")
    a = ap.parse_args()

    if a.skip_gate and a.publish and not a.sandbox:
        sys.exit("refusing: --skip-gate cannot be used to publish on production Zenodo")
    if not a.skip_gate:
        run_gate(a.files, a.metadata)

    base = "https://sandbox.zenodo.org/api" if a.sandbox else "https://zenodo.org/api"
    env = "ZENODO_SANDBOX_TOKEN" if a.sandbox else "ZENODO_TOKEN"
    token = os.environ.get(env)
    if not token:
        sys.exit(f"{env} is not set. Export it in the shell (never write it to a file).")
    params = {"access_token": token}
    hdr = {"Content-Type": "application/json"}

    for f in a.files:
        if not os.path.isfile(f):
            sys.exit(f"missing file: {f}")
    with open(a.metadata) as fh:
        metadata = json.load(fh)
    # creators from AUTHORS.json when the metadata does not name them, so the record
    # carries exactly the author block used everywhere else in the project
    if not metadata.get("creators") and a.authors and os.path.isfile(a.authors):
        block = json.load(open(a.authors))
        people = block.get("authors", []) + block.get("collaborators", [])
        creators = []
        for p in people:
            if not p.get("name"):
                continue
            c = {"name": f"{p.get('family', '')}, {p.get('given', '')}".strip(", ") or p["name"]}
            if p.get("orcid"):
                c["orcid"] = p["orcid"]
            if p.get("affiliation"):
                c["affiliation"] = p["affiliation"]
            creators.append(c)
        metadata["creators"] = creators
    for k in ("upload_type", "title", "creators", "description"):
        if not metadata.get(k):
            sys.exit(f"metadata missing required field: {k}")

    if a.new_version_of:
        r = requests.post(f"{base}/deposit/depositions/{a.new_version_of}/actions/newversion",
                          params=params, timeout=60)
        r.raise_for_status()
        dep_url = r.json()["links"]["latest_draft"]
        dep = requests.get(dep_url, params=params, timeout=60).json()
        # remove files carried over from the previous version
        for old in dep.get("files", []):
            requests.delete(old["links"]["self"], params=params, timeout=60)
    else:
        r = requests.post(f"{base}/deposit/depositions", params=params, json={}, headers=hdr, timeout=60)
        r.raise_for_status()
        dep = r.json()
    dep_id = dep["id"]
    bucket = dep["links"]["bucket"]
    print(f"deposition {dep_id} ({'sandbox' if a.sandbox else 'production'})")

    for f in a.files:
        name = os.path.basename(f)
        with open(f, "rb") as fh:
            up = requests.put(f"{bucket}/{name}", data=fh, params=params, timeout=600)
        up.raise_for_status()
        print(f"  uploaded {name} ({os.path.getsize(f)} bytes)")

    r = requests.put(f"{base}/deposit/depositions/{dep_id}", params=params, headers=hdr,
                     data=json.dumps({"metadata": metadata}), timeout=60)
    if r.status_code >= 400:
        sys.exit(f"metadata rejected: {r.status_code} {r.text[:500]}")
    print("  metadata set")

    if a.publish:
        r = requests.post(f"{base}/deposit/depositions/{dep_id}/actions/publish", params=params, timeout=60)
        if r.status_code >= 400:
            sys.exit(f"publish failed: {r.status_code} {r.text[:500]}")
        rec = r.json()
        print(f"PUBLISHED  DOI: {rec.get('doi')}  concept DOI: {rec.get('conceptdoi')}")
        print(f"           {rec['links'].get('html') or rec['links'].get('record_html')}")
        print("Log this DOI in the evidence log now.")
    else:
        print(f"left as draft; review at {dep['links'].get('html')} then re-run with --publish")


if __name__ == "__main__":
    main()
