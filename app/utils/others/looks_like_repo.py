from re import compile
from urllib.parse import urlparse

REPO_HOSTS = {
    "github.com", "gitlab.com", "bitbucket.org",
    "www.github.com", "www.gitlab.com", "www.bitbucket.org",
}

async def looks_like_repo(url: str | None) -> bool:
    if not url:
        return False
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    if host not in REPO_HOSTS:
        return False
    path = parsed.path.strip("/")
    if not path:
        return False
    parts = path.split("/")
    if parts[0].lower() == "orgs":
        return False
    if len(parts) < 2:
        return False
    owner, repo = parts[0], parts[1]
    if not owner or not repo:
        return False
    allowed = compile(r"^[A-Za-z0-9._-]+$")
    if not allowed.match(owner) or not allowed.match(repo):
        return False
    return True
