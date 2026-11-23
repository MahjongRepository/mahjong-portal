# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_CLIENT_URL = "https://game.maj-soul.com/1/"
TEXTURE_PROFILES = ("ASTC", "DXT")
UNITY_FALLBACK_VERSION = "2022.3.62f2c1"
VERSION_ASSETS = {
    "MyAssets/docs_version/version.json": "resource_version",
    "MyAssets/docs_version/lua_version.json": "lua_version",
}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

LOADER_RE = re.compile(r"""Build/([^"']+?\.loader\.js)""")
PRODUCT_VERSION_RE = re.compile(r"""productVersion\s*:\s*["']([^"']+)["']""")
LOADER_VERSION_RE = re.compile(r"-WebGL-release-(\d+(?:\.\d+)*)(?:\((\d+)\))?")


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_text(session, url: str, timeout: int) -> str:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    return response.text


def fetch_json(session, url: str, timeout: int) -> Any:
    return json.loads(fetch_text(session, url, timeout))


def fetch_bytes(session, url: str, timeout: int) -> bytes:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return response.content


def origin_of(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def join_url(base: str, *parts: str) -> str:
    current = base.rstrip("/") + "/"
    for part in parts:
        current = urljoin(current, part.lstrip("/"))
    return current


def parse_client_html(html: str) -> dict[str, Any]:
    """Версия приложения из index.html веб-клиента."""
    loader_match = LOADER_RE.search(html)
    loader = loader_match.group(1) if loader_match else None
    issuer = None
    if loader and "-WebGL-release-" in loader:
        issuer = loader.split("-WebGL-release-", 1)[0]

    product_match = PRODUCT_VERSION_RE.search(html)
    version = product_match.group(1) if product_match else None
    build = None
    if loader:
        loader_version = LOADER_VERSION_RE.search(loader)
        if loader_version:
            version = version or loader_version.group(1)
            build = loader_version.group(2)
    return {
        "product_version": version,
        "build": int(build) if build else None,
        "issuer": issuer,
        "loader": loader,
    }


def choose_url(entries: list[dict]) -> str:
    if not entries:
        raise ValueError("Пустой список CDN-адресов")
    ordered = sorted(
        entries,
        key=lambda item: (item.get("Priority", 0), item.get("weight", 0)),
        reverse=True,
    )
    url = ordered[0].get("url")
    if not url:
        raise ValueError(f"В записи отсутствует url: {ordered[0]!r}")
    return url


def resolve_bundle_profile(
    session,
    client_url: str,
    issuer: str | None,
    timeout: int = 30,
    profiles: tuple[str, ...] = TEXTURE_PROFILES,
) -> dict[str, str]:
    settings_url = join_url(
        origin_of(client_url),
        f"assetbundles/clientBundleSettings/{issuer or 'chs_t'}-release.json",
    )
    client_settings = fetch_json(session, settings_url, timeout)
    warehouse = (client_settings.get("warehouses") or [])[0]
    warehouse_url = join_url(choose_url(warehouse.get("urls") or []), warehouse["warehouseSettingPath"])
    warehouse_settings = fetch_json(session, warehouse_url, timeout)
    bundle_base = join_url(choose_url(warehouse_settings.get("urls") or []), warehouse_settings["bundlePath"])

    errors = []
    for profile in profiles:
        profile_base = join_url(bundle_base, profile) + "/"
        try:
            bundle_hash = fetch_text(session, join_url(profile_base, "bundle_hash.txt"), timeout).strip()
        except requests.RequestException as exc:
            errors.append(f"{profile}: {exc}")
            continue
        if bundle_hash:
            return {
                "bundle_profile": profile,
                "bundle_hash": bundle_hash,
                "profile_base_url": profile_base,
                "settings_url": settings_url,
            }
        errors.append(f"{profile}: пустой bundle_hash.txt")
    raise RuntimeError("Не найден пригодный профиль текстур: " + "; ".join(errors))


def versions_from_unity(session, profile_base_url: str, timeout: int = 120) -> dict[str, Any]:
    """Точное содержимое MyAssets/docs_version/*.json из Unity-бандлов."""
    import UnityPy  # зависимость нужна только для этого режима

    UnityPy.config.FALLBACK_UNITY_VERSION = UNITY_FALLBACK_VERSION
    info_bytes = fetch_bytes(session, join_url(profile_base_url, "bundle_info_so.majset"), timeout)
    bundle_infos = asset_infos = None
    for obj in UnityPy.load(info_bytes).objects:
        if obj.type.name != "MonoBehaviour":
            continue
        tree = obj.read_typetree()
        if tree.get("m_Name") == "BundleInfoSO" or ("bundleInfos" in tree and "assetInfos" in tree):
            bundle_infos, asset_infos = (tree["bundleInfos"], tree["assetInfos"])
            break
    if asset_infos is None:
        raise RuntimeError("BundleInfoSO не найден в bundle_info_so.majset")

    needed: dict[int, dict[str, str]] = {}
    for asset in asset_infos:
        path = asset.get("assetPath")
        if path in VERSION_ASSETS and asset.get("ownerBundleIndex") is not None:
            needed.setdefault(int(asset["ownerBundleIndex"]), {})[path] = VERSION_ASSETS[path]

    result: dict[str, Any] = {}
    for bundle_index, targets in needed.items():
        bundle_name = bundle_infos[bundle_index]["name"]
        bundle_bytes = fetch_bytes(session, join_url(profile_base_url, bundle_name), timeout)
        texts: dict[str, bytes] = {}
        for obj in UnityPy.load(bundle_bytes).objects:
            if obj.type.name != "TextAsset":
                continue
            asset = obj.read()
            script = getattr(asset, "m_Script", b"")
            if isinstance(script, str):
                script = script.encode("utf-8", "surrogateescape")
            texts[getattr(asset, "m_Name", "")] = script
        for path, key in targets.items():
            file_name = path.rsplit("/", 1)[-1]
            for candidate in (file_name, file_name.rsplit(".", 1)[0]):
                if candidate in texts:
                    result[key] = json.loads(texts[candidate].decode("utf-8")).get("version")
                    break
    return result


def collect(timeout) -> dict[str, Any]:
    session = make_session()

    html = fetch_text(session, DEFAULT_CLIENT_URL, timeout)
    client_info = parse_client_html(html)

    profile = resolve_bundle_profile(
        session,
        DEFAULT_CLIENT_URL,
        client_info.get("issuer"),
        timeout,
    )
    report = versions_from_unity(session, profile["profile_base_url"], timeout)

    return {"resource_version": report["resource_version"], "package_version": client_info["product_version"]}
