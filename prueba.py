import asyncio
import aiohttp
import re
from urllib.parse import quote_plus
from motor.motor_asyncio import AsyncIOMotorClient

GITHUB_API = "https://api.github.com"
GITLAB_API = "https://gitlab.com/api/v4"
GITHUB_TOKEN = "token"

HEADERS_GITHUB = {
    "Accept": "application/vnd.github.v3.diff",
    "Authorization": f"token {GITHUB_TOKEN}"
}

def detect_language_by_extension(filename):
    ext = filename.split('.')[-1].lower()
    if ext in {"c", "h"}:
        return "c"
    elif ext in {"cpp", "cc", "cxx", "hpp", "hxx"}:
        return "cpp"
    elif ext in {"java"}:
        return "java"
    elif ext in {"py"}:
        return "python"
    elif ext in {"ts", "tsx"}:
        return "typescript"
    elif ext in {"js", "jsx"}:
        return "javascript"
    return "unknown"

def extract_entities_from_diff(diff_text, filename=None):
    language = detect_language_by_extension(filename) if filename else "unknown"

    entities = {
        "functions": set(),
        "methods": set(),
        "classes": set(),
        "structs": set(),
        "globals": set(),
        "enums": set(),
        "interfaces": set()
    }

    for line in diff_text.splitlines():
        if not line.startswith('+') and not line.startswith('@@'):
            continue

        if '(' in line:
            match_func = re.search(r'([a-zA-Z_][a-zA-Z0-9_:]*)\s*\(', line)
            if match_func:
                name = match_func.group(1).replace("this.", "").replace("self.", "")
                if "::" in name or (language in {"cpp", "java"} and '.' in name):
                    entities["methods"].add(name)
                else:
                    entities["functions"].add(name)

        if language in {"javascript", "typescript"}:
            match_arrow = re.match(r'^\+?\s*const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\(.*?\)\s*=>', line)
            if match_arrow:
                entities["functions"].add(match_arrow.group(1).replace("this.", "").replace("self.", ""))

        if language in {"cpp", "java", "typescript", "python", "javascript"}:
            match = re.match(r'^\+?\s*class\s+([A-Za-z_][A-Za-z0-9_]*)', line)
            if match:
                entities["classes"].add(match.group(1).replace("this.", "").replace("self.", ""))

        if language in {"c", "cpp"}:
            match = re.match(r'^\+?\s*struct\s+([A-Za-z_][A-Za-z0-9_]*)', line)
            if match:
                entities["structs"].add(match.group(1).replace("this.", "").replace("self.", ""))

        if language in {"java", "typescript", "javascript"}:
            match = re.match(r'^\+?\s*interface\s+([A-Za-z_][A-Za-z0-9_]*)', line)
            if match:
                entities["interfaces"].add(match.group(1).replace("this.", "").replace("self.", ""))

        match = re.match(r'^\+?\s*enum\s+([A-Za-z_][A-Za-z0-9_]*)', line)
        if match:
            entities["enums"].add(match.group(1).replace("this.", "").replace("self.", ""))

        if language in {"c", "cpp", "java"}:
            match = re.match(r'^\+?\s*(?:[a-zA-Z_][a-zA-Z0-9_:<>]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*', line)
            if match:
                entities["globals"].add(match.group(1).replace("this.", "").replace("self.", ""))

    return entities

async def get_diff_and_files_github(repo_full_name, commit_hash, session):
    url = f"{GITHUB_API}/repos/{repo_full_name}/commits/{commit_hash}"
    async with session.get(url, headers={"Accept": "application/vnd.github.v3+json", "Authorization": f"token {GITHUB_TOKEN}"}) as resp:
        data = await resp.json()
        files = data.get("files", [])
        return [(f["filename"], await get_diff_from_github_commit(repo_full_name, commit_hash, session)) for f in files]

async def get_commits_between_github(repo_full_name, base, head, session):
    url = f"{GITHUB_API}/repos/{repo_full_name}/compare/{base}...{head}"
    async with session.get(url, headers={"Accept": "application/vnd.github.v3+json", "Authorization": f"token {GITHUB_TOKEN}"}) as resp:
        data = await resp.json()
        return [commit["sha"] for commit in data.get("commits", [])]

async def get_diff_from_github_commit(repo_full_name, commit_hash, session):
    url = f"{GITHUB_API}/repos/{repo_full_name}/commits/{commit_hash}"
    async with session.get(url, headers={"Accept": "application/vnd.github.v3+json", "Authorization": f"token {GITHUB_TOKEN}"}) as resp:
        data = await resp.json()
        parents = data.get("parents", [])
        if not parents:
            return ""
        parent_sha = parents[0]["sha"]

    diff_url = f"{GITHUB_API}/repos/{repo_full_name}/compare/{parent_sha}...{commit_hash}"
    async with session.get(diff_url, headers=HEADERS_GITHUB) as resp:
        return await resp.text()

async def get_commits_between_gitlab(repo_url, base, head, session):
    match = re.match(r'https://gitlab\\.com/([^/]+/[^/]+)', repo_url)
    if not match:
        return []
    project_path = match.group(1)
    encoded_project = quote_plus(project_path)
    url = f"{GITLAB_API}/projects/{encoded_project}/repository/compare?from={base}&to={head}"
    async with session.get(url) as resp:
        data = await resp.json()
        return [commit["id"] for commit in data.get("commits", [])]

async def get_diff_from_gitlab_commit(repo_url, commit_hash, session):
    match = re.match(r'https://gitlab\\.com/([^/]+/[^/]+)', repo_url)
    if not match:
        return ""
    project_path = match.group(1)
    encoded_project = quote_plus(project_path)
    url = f"{GITLAB_API}/projects/{encoded_project}/repository/commits/{commit_hash}/diff"
    async with session.get(url) as resp:
        return await resp.json()

async def extract_entities_from_github_commits(repo_full_name, commits, session):
    all_entities = {k: set() for k in ["functions", "methods", "classes", "structs", "globals", "enums", "interfaces"]}
    for sha in commits:
        try:
            url = f"{GITHUB_API}/repos/{repo_full_name}/commits/{sha}"
            async with session.get(url, headers={"Accept": "application/vnd.github.v3+json", "Authorization": f"token {GITHUB_TOKEN}"}) as resp:
                data = await resp.json()
                for file in data.get("files", []):
                    filename = file.get("filename")
                    diff = await get_diff_from_github_commit(repo_full_name, sha, session)
                    entities = extract_entities_from_diff(diff, filename)
                    for key in all_entities:
                        all_entities[key].update(entities[key])
        except Exception as e:
            print(f"Error GitHub {sha}: {e}")
    return all_entities

async def extract_entities_from_gitlab_commits(repo_url, commits, session):
    all_entities = {k: set() for k in ["functions", "methods", "classes", "structs", "globals", "enums", "interfaces"]}
    for sha in commits:
        try:
            diffs = await get_diff_from_gitlab_commit(repo_url, sha, session)
            for file in diffs:
                filename = file.get("new_path")
                diff = file.get("diff", "")
                entities = extract_entities_from_diff(diff, filename)
                for key in all_entities:
                    all_entities[key].update(entities[key])
        except Exception as e:
            print(f"Error GitLab {sha}: {e}")
    return all_entities

async def process_vulnerabilities():
    client = AsyncIOMotorClient("mongodb://mongoDepex:mongoDepex@localhost:27017/admin")
    db = client["osv"]
    collection = db["vulnerabilities"]

    async with aiohttp.ClientSession() as session:
        i = 0
        async for vuln in collection.find():
            print(i)
            print(vuln.get("id", "sin id"))
            i += 1
            if "affected" not in vuln:
                continue

            for affected in vuln["affected"]:
                if "ranges" not in affected:
                    continue
                for r in affected["ranges"]:
                    if r.get("type") != "GIT":
                        continue

                    repo_url = r.get("repo", "")
                    events = r.get("events", [])
                    introduced_commit = next((e["introduced"] for e in events if "introduced" in e), None)
                    fixed_commit = next((e["fixed"] for e in events if "fixed" in e), None)

                    if not introduced_commit or not fixed_commit:
                        continue

                    try:
                        if "github.com" in repo_url:
                            match = re.match(r'https://github.com/([^/]+/[^/]+)(\\.git)?', repo_url)
                            if not match:
                                continue
                            repo_full_name = match.group(1)
                            commits = await get_commits_between_github(repo_full_name, introduced_commit, fixed_commit, session)
                            entities = await extract_entities_from_github_commits(repo_full_name, commits, session)

                        elif "gitlab.com" in repo_url:
                            commits = await get_commits_between_gitlab(repo_url, introduced_commit, fixed_commit, session)
                            entities = await extract_entities_from_gitlab_commits(repo_url, commits, session)

                        else:
                            print(f"Repositorio no soportado: {repo_url}")
                            continue

                        entities_serializable = {k: list(v) for k, v in entities.items() if v}
                        if any(entities_serializable.values()):
                            await collection.update_one(
                                {"_id": vuln["_id"]},
                                {"$set": {"affected_artefacts": entities_serializable}}
                            )
                            print(entities_serializable)

                    except Exception as e:
                        print(f"Error procesando {repo_url}: {e}")
            print("--------------------------------")

asyncio.run(process_vulnerabilities())