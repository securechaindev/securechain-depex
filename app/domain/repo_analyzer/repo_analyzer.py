from glob import glob
from os import makedirs
from os.path import exists, isdir, join
from shutil import rmtree

from aiofiles import open

from app.constants import ALL_REQUIREMENT_FILES
from app.http_session import HTTPSessionManager

from .requirement_files import AnalyzerRegistry


class RepositoryAnalyzer:
    def __init__(self, http_session: HTTPSessionManager):
        self.registry = AnalyzerRegistry()
        self.http_session = http_session

    async def analyze(self, owner: str, name: str) -> dict[str, dict[str, dict | str]]:
        requirement_files: dict[str, dict[str, dict | str]] = {}
        repository_path = await self.download_repository(owner, name)

        try:
            requirement_file_names = await self.get_req_files_names(repository_path)

            for requirement_file_name in requirement_file_names:
                analyzer = self.registry.get_analyzer(requirement_file_name)
                if analyzer:
                    requirement_files = await analyzer.analyze(
                        requirement_files, repository_path, requirement_file_name
                    )
        finally:
            if exists(repository_path):
                rmtree(repository_path)

        return requirement_files

    async def download_repository(self, owner: str, name: str) -> str:
        repository_path = f"repositories/{owner}/{name}"
        if exists(repository_path):
            rmtree(repository_path)
        makedirs(repository_path)

        session = await self.http_session.get_session()
        await self.download_directory_contents(session, owner, name, "", repository_path)
        return repository_path

    async def download_directory_contents(
        self,
        session,
        owner: str,
        name: str,
        path: str,
        repository_path: str,
    ) -> None:
        url = f"https://api.github.com/repos/{owner}/{name}/contents/{path}"
        async with session.get(url) as resp:
            if resp.status != 200:
                return
            contents = await resp.json()

        for item in contents:
            if item["type"] == "file" and any(
                extension in item["name"] for extension in ALL_REQUIREMENT_FILES
            ):
                raw_url = item["download_url"]
                async with session.get(raw_url) as file_resp:
                    if file_resp.status == 200:
                        file_content = await file_resp.text()
                        relative_path = item["path"]
                        filepath = join(repository_path, relative_path)
                        file_dir = filepath.rsplit("/", 1)[0]
                        if not exists(file_dir):
                            makedirs(file_dir)
                        async with open(filepath, "w") as f:
                            await f.write(file_content)
            elif item["type"] == "dir":
                await self.download_directory_contents(
                    session, owner, name, item["path"], repository_path
                )

    async def get_req_files_names(self, directory_path: str) -> list[str]:
        requirement_files = []
        paths = glob(directory_path + "/**", recursive=True)
        for _path in paths:
            if not isdir(_path) and self.is_req_file(_path):
                requirement_files.append(
                    _path.replace(directory_path, "")
                    .replace("/", "")
                )
        return requirement_files

    def is_req_file(self, requirement_file_name: str) -> bool:
        return any(
            extension in requirement_file_name for extension in ALL_REQUIREMENT_FILES
        )
