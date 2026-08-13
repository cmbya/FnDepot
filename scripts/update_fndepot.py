#!/usr/bin/env python3
import hashlib
import io
import json
import os
import tarfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "apps.json"
INDEX = ROOT / "fnpack.json"
ICONS = ROOT / "assets" / "icons"
ICONS.mkdir(parents=True, exist_ok=True)

TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()

def headers():
    h = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "fnOS-FnDepot-auto-indexer",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return h

def request_json(url):
    req = urllib.request.Request(url, headers=headers())
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def request_bytes(url):
    req = urllib.request.Request(
        url,
        headers={**headers(), "Accept": "application/octet-stream"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()

def parse_manifest(blob):
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tf:
        manifest_member = None
        icon_member = None

        for member in tf.getmembers():
            normalized = member.name.lstrip("./")
            if normalized == "manifest":
                manifest_member = member
            if normalized in ("ICON_256.PNG", "ICON.PNG") and icon_member is None:
                icon_member = member
            if normalized == "ICON_256.PNG":
                icon_member = member

        if manifest_member is None:
            raise RuntimeError("FPK 中找不到根目录 manifest")

        f = tf.extractfile(manifest_member)
        if f is None:
            raise RuntimeError("无法读取 FPK manifest")
        manifest_text = f.read().decode("utf-8", errors="replace")

        icon_bytes = None
        if icon_member is not None:
            f = tf.extractfile(icon_member)
            if f is not None:
                icon_bytes = f.read()

    manifest = {}
    for line in manifest_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        manifest[k.strip()] = v.strip()
    return manifest, icon_bytes

def load_existing():
    if not INDEX.exists():
        return {"schema_version": "2", "source_info": {}, "apps": {}}
    try:
        return json.loads(INDEX.read_text(encoding="utf-8"))
    except Exception:
        return {"schema_version": "2", "source_info": {}, "apps": {}}

def _release_time(release):
    value = release.get("published_at") or release.get("created_at") or ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)

def latest_non_draft_release(repo):
    """
    获取最新的非 Draft Release。
    与 /releases/latest 不同，这里会包含 Pre-release。
    """
    url = f"https://api.github.com/repos/{repo}/releases?per_page=30"
    releases = request_json(url)

    candidates = [r for r in releases if not r.get("draft", False)]
    if not candidates:
        return None

    # 明确按发布时间选择最新，避免依赖 API 返回顺序。
    return max(candidates, key=_release_time)

def choose_fpk_asset(release):
    assets = release.get("assets") or []
    candidates = [a for a in assets if str(a.get("name", "")).lower().endswith(".fpk")]
    if not candidates:
        return None

    def score(a):
        n = str(a.get("name", "")).lower()
        s = 0
        if "x86" in n or "amd64" in n:
            s += 10
        if "arm" in n or "aarch64" in n:
            s -= 20
        return s

    candidates.sort(key=score, reverse=True)
    return candidates[0]

def compact_changelog(text, prerelease=False):
    text = (text or "").strip()
    prefix = "【Pre-release 自动构建】\n\n" if prerelease else ""
    if not text:
        return prefix + "由 GitHub Actions 自动同步的 fnOS 构建。"
    return prefix + text[:6000]

def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    existing = load_existing()

    out = {
        "schema_version": "2",
        "source_info": cfg["source_info"],
        "apps": dict(existing.get("apps") or {}),
    }

    changed_any = False

    for item in cfg["repositories"]:
        repo = item["repo"]
        print(f"\n=== 检查 {repo} ===")

        release = latest_non_draft_release(repo)
        if release is None:
            print("没有可用 Release，跳过。")
            continue

        if release.get("prerelease"):
            print("发现最新 Pre-release，将收录。")
        else:
            print("发现最新正式 Release，将收录。")

        asset = choose_fpk_asset(release)
        if asset is None:
            print("该 Release 中没有 .fpk，跳过。")
            continue

        download_url = asset["browser_download_url"]
        print("Release:", release.get("tag_name"))
        print("FPK:", asset.get("name"))

        blob = request_bytes(download_url)
        manifest, icon_bytes = parse_manifest(blob)

        appname = manifest.get("appname", "").strip()
        version = manifest.get("version", "").strip()
        platform = manifest.get("platform", "").strip()
        service_port = manifest.get("service_port", "").strip()

        if not appname or not version:
            raise RuntimeError(f"{repo}: FPK manifest 缺少 appname/version")
        if platform not in ("x86", "all"):
            raise RuntimeError(
                f"{repo}: 当前只收录 x86/all 包，实际 platform={platform!r}"
            )

        sha256 = hashlib.sha256(blob).hexdigest()
        size = len(blob)

        icon_rel = f"assets/icons/{appname}.png"
        if icon_bytes:
            (ROOT / icon_rel).write_bytes(icon_bytes)

        old_app = out["apps"].get(appname, {})
        releases = dict(old_app.get("releases") or {})

        releases[version] = {
            "changelog": compact_changelog(
                release.get("body"),
                prerelease=bool(release.get("prerelease")),
            ),
            "updated_at": release.get("published_at")
            or release.get("created_at")
            or "",
            "service_port": service_port,
            "packages": {
                "x86": {
                    "download_url": download_url,
                    "sha256": sha256,
                    "size": size,
                    "updated_at": release.get("published_at")
                    or release.get("created_at")
                    or "",
                    "run_as": "package",
                    "install_type": "",
                    "is_docker": False,
                    "service_port": service_port,
                }
            },
        }

        app_obj = {
            "display_name": item["display_name"],
            "desc": item["desc"],
            "platform": ["x86"],
            "categories": item["categories"],
            "icon_url": icon_rel,
            "readme_url": f"https://github.com/{repo}",
            "bug_report_url": item.get(
                "bug_report_url", f"https://github.com/{repo}/issues"
            ),
            "maintainer": item["maintainer"],
            "maintainer_url": item["maintainer_url"],
            "distributor": item.get(
                "distributor", cfg["source_info"]["author"]
            ),
            "distributor_url": f"https://github.com/{repo}",
            "run_as": "package",
            "install_type": "",
            "is_docker": False,
            "service_port": service_port,
            "releases": releases,
        }

        if old_app != app_obj:
            changed_any = True

        out["apps"][appname] = app_obj

        release_type = "Pre-release" if release.get("prerelease") else "正式 Release"
        print(f"收录: {appname} {version} ({release_type})")
        print(f"SHA256: {sha256}")
        print(f"大小: {size} bytes")

    out["apps"] = dict(
        sorted(out["apps"].items(), key=lambda x: x[0].lower())
    )
    INDEX.write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    verify = json.loads(INDEX.read_text(encoding="utf-8"))
    if verify.get("schema_version") != "2":
        raise RuntimeError('schema_version 必须是字符串 "2"')
    if not isinstance(verify.get("apps"), dict):
        raise RuntimeError("apps 必须是对象")

    print(f"\n完成，共 {len(verify['apps'])} 个应用。")
    if not changed_any:
        print("没有发现新的应用元数据变化。")

if __name__ == "__main__":
    main()
