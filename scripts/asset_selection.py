"""Conservative same-application version ordering for aggregate releases."""
import re


def choose_versioned_asset(assets, asset_prefix, score):
    # Keep architecture preference, explicit asset_name (handled by caller), and
    # legacy order when version parsing is unsafe. Never reorder across apps.
    ranked = sorted(assets, key=score, reverse=True)
    if not ranked or not asset_prefix:
        return ranked[0] if ranked else None
    best_score = score(ranked[0])
    peers = [a for a in ranked if score(a) == best_score]
    versions = []
    for asset in peers:
        name = str(asset.get('name', ''))
        if not name.startswith(asset_prefix):
            return ranked[0]
        match = re.match(r'^v?(\d+(?:\.\d+)+)(?=$|[-_+.])', name[len(asset_prefix):])
        if not match:
            return ranked[0]
        parts = [int(part) for part in match.group(1).split('.')]
        while len(parts) > 1 and parts[-1] == 0:
            parts.pop()
        versions.append(tuple(parts))
    # max keeps existing order for equal versions; upload dates are not versions.
    return max(zip(versions, peers), key=lambda pair: pair[0])[1]
