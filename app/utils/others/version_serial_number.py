from re import VERBOSE, compile

_STAGE_MAP = {
    "dev": "dev",
    "alpha": "alpha",
    "a": "alpha",
    "beta": "beta",
    "b": "beta",
    "rc": "rc",
    "post": "post",
}

_STAGE_ORDER = {
    "dev": 0,
    "alpha": 1,
    "beta": 2,
    "rc": 3,
    "release": 4,
    "post": 5,
}

_VERSION_RE = compile(
    r"""
    ^.*?
    (?:(?P<epoch>\d+)!)?
    (?P<release>\d+(?:\.\d+){0,2})
    (?:
        (?P<suffix>[a-zA-Z]+)
        (?P<suffix_num>\d*)
    )?
    (?:
        post(?P<post_num>\d*)
    )?
    (?:\+[0-9A-Za-z.-]+)?
    $
    """,
    VERBOSE,
)

async def version_to_serial_number(version_str: str) -> int | None:
    m = _VERSION_RE.match(version_str)
    if not m:
        return None
    try:
        epoch = int(m.group("epoch")) if m.group("epoch") else 0
        release = m.group("release")
        parts = release.split(".")
        if len(parts) > 3:
            return None
        while len(parts) < 3:
            parts.append("0")
        major, minor, patch = map(int, parts)
        major = epoch * 1000 + major
        suffix = m.group("suffix")
        suffix_num = m.group("suffix_num")
        post_num = m.group("post_num")
        if suffix:
            norm = _STAGE_MAP.get(suffix.lower())
            if not norm:
                return None
            stage = norm
            stage_num = int(suffix_num) if suffix_num else 0
            if post_num:
                return None
        else:
            if post_num is not None:
                stage = "post"
                stage_num = int(post_num) if post_num else 0
            else:
                stage = "release"
                stage_num = 0
        if not (0 <= major < 10000 and 0 <= minor < 1000 and 0 <= patch < 1000 and 0 <= stage_num < 1000):
            return None
        stage_code = _STAGE_ORDER[stage]
        return (
            major * 10**12 +
            minor * 10**9 +
            patch * 10**6 +
            stage_code * 10**3 +
            stage_num
        )
    except Exception:
        return None
