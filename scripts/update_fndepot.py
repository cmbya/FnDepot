#!/usr/bin/env python3
import hashlib
import io
import json
import os
import shutil
import tarfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "apps.json"
V1_INDEX = ROOT / "fnpack.json"
V2_INDEX = ROOT / "fnpack-v2.json"
ICONS = ROOT / "assets" / "icons"
ICONS.mkdir(parents=True, exist_ok=True)

TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()

def headers():
    h = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "fnOS-FnDepot-dual-indexer",
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

        text = f.read().decode("utf-8", errors="replace")

        icon_bytes = None
        if icon_member is not None:
            f = tf.extractfile(icon_member)
            if f is not None:
                icon_bytes = f.read()

    manifest = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        manifest[k.strip()] = v.strip()

    return manifest, icon_bytes

def release_time(release):
    value = release.get("published_at") or release.get("created_at") or ""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)

def latest_non_draft_release(repo):
    releases = request_json(
        f"https://api.github.com/repos/{repo}/releases?per_page=30"
    )
    releases = [r for r in releases if not r.get("draft", False)]
    if not releases:
        return None
    return max(releases, key=release_time)

def choose_fpk_asset(release):
    assets = [
        a for a in (release.get("assets") or [])
        if str(a.get("name", "")).lower().endswith(".fpk")
    ]
    if not assets:
        return None

    def score(a):
        n = str(a.get("name", "")).lower()
        s = 0
        if "x86" in n or "amd64" in n:
            s += 10
        if "arm" in n or "aarch64" in n:
            s -= 20
        return s

    return sorted(assets, key=score, reverse=True)[0]

def clean_changelog(text, prerelease):
    text = (text or "").strip()
    prefix = "【Pre-release 自动构建】\n\n" if prerelease else ""
    if not text:
        return prefix + "由 GitHub Actions 自动同步的 fnOS 构建。"
    # 去掉之前错误写入的内部标记
    text = text.replace("citePre-release 自动构建 ", "")
    return prefix + text[:6000]

def mb_string(size_bytes):
    mb = size_bytes / 1024 / 1024
    if mb < 1:
        return f"{mb:.2f} MB"
    if mb < 10:
        return f"{mb:.1f} MB"
    return f"{mb:.0f} MB"

def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))

    v1 = {}
    v2 = {
        "schema_version": "2",
        "source_info": cfg["source_info"],
        "apps": {},
    }

    # 清理旧 V1 app 目录，避免残留
    managed_names = []

    for item in cfg["repositories"]:
        repo = item["repo"]
        print(f"\n=== 检查 {repo} ===")

        release = latest_non_draft_release(repo)
        if release is None:
            print("没有 Release，跳过")
            continue

        asset = choose_fpk_asset(release)
        if asset is None:
            print("Release 中没有 FPK，跳过")
            continue

        blob = request_bytes(asset["browser_download_url"])
        manifest, icon_bytes = parse_manifest(blob)

        appname = manifest.get("appname", "").strip()
        version = manifest.get("version", "").strip()
        platform = manifest.get("platform", "").strip()
        service_port = manifest.get("service_port", "").strip()

        if not appname or not version:
            raise RuntimeError(f"{repo}: manifest 缺少 appname/version")
        if platform not in ("x86", "all"):
            raise RuntimeError(f"{repo}: 当前只收录 x86/all，实际 {platform!r}")

        sha256 = hashlib.sha256(blob).hexdigest()
        size = len(blob)
        prerelease = bool(release.get("prerelease"))
        changelog = clean_changelog(release.get("body"), prerelease)
        updated_at = (
            release.get("published_at")
            or release.get("created_at")
            or ""
        )
        run_as = item.get("run_as", "package")

        # 保存通用图标
        icon_rel = f"assets/icons/{appname}.png"
        if icon_bytes:
            (ROOT / icon_rel).write_bytes(icon_bytes)

        # V1 老客户端习惯读取 /{appname}/ICON.PNG
        app_dir = ROOT / appname
        app_dir.mkdir(parents=True, exist_ok=True)
        managed_names.append(appname)
        if icon_bytes:
            (app_dir / "ICON.PNG").write_bytes(icon_bytes)

        # ---------- V1 ----------
        # 旧客户端字段：根节点直接 appname -> metadata
        v1[appname] = {
            "display_name": item["display_name"],
            "platform": "x86",
            "version": version,
            "desc": item["desc"],
            "labels": item.get("labels", "原生"),
            "distributor": item.get("distributor", cfg["source_info"]["author"]),
            "distributor_url": f"https://github.com/{repo}",
            "bug_report_url": item.get(
                "bug_report_url",
                f"https://github.com/{repo}/issues",
            ),
            "install_type": "存储空间",
            "isdocker": "false",
            "size": mb_string(size),
            "download_url": asset["browser_download_url"],
            "changelog": changelog,
        }

        # ---------- V2 ----------
        v2["apps"][appname] = {
            "display_name": item["display_name"],
            "desc": item["desc"],
            "platform": ["x86"],
            "categories": item["categories"],
            "icon_url": icon_rel,
            "readme_url": f"https://github.com/{repo}",
            "bug_report_url": item.get(
                "bug_report_url",
                f"https://github.com/{repo}/issues",
            ),
            "maintainer": item["maintainer"],
            "maintainer_url": item["maintainer_url"],
            "distributor": item.get("distributor", cfg["source_info"]["author"]),
            "distributor_url": f"https://github.com/{repo}",
            "run_as": run_as,
            "install_type": "",
            "is_docker": False,
            "service_port": service_port,
            "releases": {
                version: {
                    "changelog": changelog,
                    "updated_at": updated_at,
                    "service_port": service_port,
                    "packages": {
                        "x86": {
                            "download_url": asset["browser_download_url"],
                            "sha256": sha256,
                            "size": size,
                            "updated_at": updated_at,
                            "run_as": run_as,
                            "install_type": "",
                            "is_docker": False,
                            "service_port": service_port,
                        }
                    },
                }
            },
        }

        kind = "Pre-release" if prerelease else "正式 Release"
        print(f"收录: {appname} {version} ({kind})")

    v1 = dict(sorted(v1.items(), key=lambda x: x[0].lower()))
    v2["apps"] = dict(sorted(v2["apps"].items(), key=lambda x: x[0].lower()))

    V1_INDEX.write_text(
        json.dumps(v1, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    V2_INDEX.write_text(
        json.dumps(v2, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # 严格 JSON 自检
    json.loads(V1_INDEX.read_text(encoding="utf-8"))
    v2_check = json.loads(V2_INDEX.read_text(encoding="utf-8"))
    if v2_check.get("schema_version") != "2":
        raise RuntimeError('V2 schema_version 必须为字符串 "2"')

    print(f"\n完成：V1 {len(v1)} 个应用，V2 {len(v2['apps'])} 个应用")
    print("fnpack.json = V1 兼容源")
    print("fnpack-v2.json = V2 新版源")

if __name__ == "__main__":
    main()
