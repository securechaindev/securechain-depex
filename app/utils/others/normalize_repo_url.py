from re import match, sub
from urllib.parse import urlparse


async def normalize_git_like(url: str) -> str:
    u = url.strip()
    if u.startswith("git+"):
        u = u[4:]
    m = match(r"git@([^:]+):(.+)", u)
    if m:
        host, path = m.groups()
        u = f"https://{host}/{path}"
    if u.startswith("ssh://git@"):
        u = "https://" + u[len("ssh://git@"):]
    if u.startswith("git://"):
        u = "https://" + u[len("git://"):]
    return u


async def normalize_repo_url(url: str | None) -> str | None:
    if not url:
        return None
    u = await normalize_git_like(url)
    parsed = urlparse(u)
    if not parsed.scheme:
        u = "https://" + u
        parsed = urlparse(u)
    clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    clean = sub(r"\.git/?$", "", clean).rstrip("/")
    git_hosting_pattern = r"(https?://[^/]+/[^/]+/[^/]+)(?:/.*)?$"
    git_match = match(git_hosting_pattern, clean)
    if git_match:
        host = parsed.netloc.lower()
        if any(platform in host for platform in ['github.com', 'gitlab.com', 'bitbucket.org']):
            clean = git_match.group(1)
    return clean
