#!/usr/bin/env python3
"""Validate plugins/*.json against their release tarballs and regenerate index.json.

Usage: validate.py [--write-index] [files...]
Without files, validates every plugins/*.json. Exits non-zero on the first problem.
"""
import hashlib, io, json, re, sys, tarfile, urllib.request, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$")
PERM_KEYS = {"commands": list, "events": list, "threadStatus": bool, "sessionEnv": bool,
             "secrets": bool, "threads": bool, "terminals": bool, "api": bool}

def norm_perms(p):
    out = {}
    for k, t in PERM_KEYS.items():
        v = p.get(k, [] if t is list else False)
        if not isinstance(v, t):
            raise SystemExit(f"permissions.{k} must be {t.__name__}")
        out[k] = sorted(v) if t is list else v
    return out

def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()

def check(path):
    e = json.loads(path.read_text())
    name = e["name"]
    if not NAME_RE.match(name): raise SystemExit(f"{path}: bad name {name!r}")
    if path.stem != name: raise SystemExit(f"{path}: file name must be {name}.json")
    if not SEMVER_RE.match(e["version"]): raise SystemExit(f"{path}: bad version")
    if e.get("protocol") != 1: raise SystemExit(f"{path}: protocol must be 1")
    if "/" not in e["repo"]: raise SystemExit(f"{path}: repo must be owner/name")
    arts = e["artifacts"]
    if "darwin/arm64" not in arts: raise SystemExit(f"{path}: darwin/arm64 artifact required")
    for plat, a in arts.items():
        data = fetch(a["url"])
        got = hashlib.sha256(data).hexdigest()
        if got != a["sha256"]: raise SystemExit(f"{path}: {plat} sha256 {got} != {a['sha256']}")
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
            names = {m.name.lstrip("./") for m in tf.getmembers()}
            if "plugin.json" not in names: raise SystemExit(f"{path}: {plat} tarball lacks plugin.json at root")
            m = json.load(tf.extractfile([x for x in tf.getmembers() if x.name.lstrip('./') == 'plugin.json'][0]))
        if m.get("name") != name: raise SystemExit(f"{path}: manifest name {m.get('name')!r} != {name!r}")
        if m.get("version") != e["version"]: raise SystemExit(f"{path}: manifest version {m.get('version')!r} != {e['version']!r}")
        if norm_perms(m.get("permissions", {})) != norm_perms(e.get("permissions", {})):
            raise SystemExit(f"{path}: permissions differ from the manifest")
        exe = m.get("exec", [None])[0]
        if exe and exe.lstrip("./") not in names: raise SystemExit(f"{path}: exec {exe!r} missing from tarball")
    print(f"ok {name} {e['version']}")
    return e

def main(argv):
    write = "--write-index" in argv
    files = [pathlib.Path(a) for a in argv if not a.startswith("--")] or sorted((ROOT / "plugins").glob("*.json"))
    entries = [check(p) for p in files]
    if write:
        allf = sorted((ROOT / "plugins").glob("*.json"))
        entries = [json.loads(p.read_text()) for p in allf]
        idx = {"schema": 1,
               "generatedAt": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "plugins": sorted(entries, key=lambda e: e["name"])}
        (ROOT / "index.json").write_text(json.dumps(idx, indent=2) + "\n")
        print("index.json written")

if __name__ == "__main__":
    main(sys.argv[1:])
