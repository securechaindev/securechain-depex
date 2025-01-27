from xmltodict import parse


async def analyze_pom_xml(
    requirement_files: dict[str, dict[str, dict | str]],
    repository_path: str,
    requirement_file_name: str,
) -> dict[str, dict[str, dict | str]]:
    file = open(repository_path + requirement_file_name)
    try:
        pom_dict = parse(file.read())
    except Exception as _:
        return requirement_files
    requirement_file_name = requirement_file_name.replace("/master/", "").replace(
        "/main/", ""
    )
    requirement_files[requirement_file_name] = {
        "manager": "maven",
        "dependencies": {},
    }
    if "project" in pom_dict:
        if "dependencyManagement" in pom_dict["project"]:
            if (
                "dependencies" in pom_dict["project"]
                and "dependencies" in pom_dict["project"]["dependencyManagement"]
                and pom_dict["project"]["dependencyManagement"]["dependencies"]
            ):
                if "dependency" in pom_dict["project"]["dependencies"]:
                    if isinstance(
                        pom_dict["project"]["dependencies"]["dependency"], list
                    ) and isinstance(
                        pom_dict["project"]["dependencyManagement"]["dependencies"][
                            "dependency"
                        ],
                        list,
                    ):
                        pom_dict["project"]["dependencies"]["dependency"].extend(
                            pom_dict["project"]["dependencyManagement"]["dependencies"][
                                "dependency"
                            ]
                        )
                    elif isinstance(
                        pom_dict["project"]["dependencies"]["dependency"], list
                    ) and isinstance(
                        pom_dict["project"]["dependencyManagement"]["dependencies"][
                            "dependency"
                        ],
                        dict,
                    ):
                        pom_dict["project"]["dependencies"]["dependency"].append(
                            pom_dict["project"]["dependencyManagement"]["dependencies"][
                                "dependency"
                            ]
                        )
                    elif isinstance(
                        pom_dict["project"]["dependencies"]["dependency"], dict
                    ) and isinstance(
                        pom_dict["project"]["dependencyManagement"]["dependencies"][
                            "dependency"
                        ],
                        list,
                    ):
                        pom_dict["project"]["dependencyManagement"]["dependencies"][
                            "dependency"
                        ].append(pom_dict["project"]["dependencies"]["dependency"])
                        pom_dict["project"]["dependencies"]["dependency"] = pom_dict[
                            "project"
                        ]["dependencyManagement"]["dependencies"]["dependency"]
                    else:
                        pom_dict["project"]["dependencies"]["dependency"] = [
                            pom_dict["project"]["dependencies"]["dependency"],
                            pom_dict["project"]["dependencyManagement"]["dependencies"][
                                "dependency"
                            ],
                        ]
            else:
                pom_dict["project"]["dependencies"] = pom_dict["project"][
                    "dependencyManagement"
                ]["dependencies"]
        if (
            "dependencies" in pom_dict["project"]
            and pom_dict["project"]["dependencies"] is not None
            and "dependency" in pom_dict["project"]["dependencies"]
        ):
            properties = {}
            if (
                "properties" in pom_dict["project"]
                and pom_dict["project"]["properties"]
            ):
                properties.update(pom_dict["project"]["properties"])
            if "parent" in pom_dict["project"] and pom_dict["project"]["parent"]:
                properties.update(pom_dict["project"]["parent"])
            if isinstance(pom_dict["project"]["dependencies"]["dependency"], list):
                dependencies = pom_dict["project"]["dependencies"]["dependency"]
            else:
                dependencies = [pom_dict["project"]["dependencies"]["dependency"]]
            for dependency in dependencies:
                if "scope" not in dependency or dependency["scope"] in (
                    "compile",
                    "runtime",
                    "provided",
                ):
                    version = ""
                    if "version" in dependency and dependency["version"] is not None:
                        version = (
                            pom_dict["project"]["version"]
                            if "$" in dependency["version"]
                            and "project.version" in dependency["version"]
                            and "version" in pom_dict["project"]
                            else dependency["version"]
                        )
                        if "properties" in pom_dict["project"] or not any(
                            "$" in att
                            for att in (
                                dependency["groupId"],
                                dependency["artifactId"],
                                version,
                            )
                        ):
                            if "$" in dependency["groupId"]:
                                property_ = (
                                    dependency["groupId"]
                                    .replace("$", "")
                                    .replace("{", "")
                                    .replace("}", "")
                                )
                                if property_ and property_ in properties:
                                    if isinstance(properties[property_], list):
                                        dependency["groupId"] = properties[property_][0]
                                    else:
                                        dependency["groupId"] = properties[property_]
                                else:
                                    continue
                            if "$" in dependency["artifactId"]:
                                property_ = (
                                    dependency["artifactId"]
                                    .replace("$", "")
                                    .replace("{", "")
                                    .replace("}", "")
                                )
                                if property_ and property_ in properties:
                                    if isinstance(properties[property_], list):
                                        dependency["artifactId"] = properties[
                                            property_
                                        ][0]
                                    else:
                                        dependency["artifactId"] = properties[property_]
                                else:
                                    continue
                            if "$" in version:
                                property_ = (
                                    version.replace("$", "")
                                    .replace("{", "")
                                    .replace("}", "")
                                )
                                if property_ and property_ in properties:
                                    if isinstance(properties[property_], list):
                                        version = properties[property_][0]
                                    else:
                                        version = properties[property_]
                                else:
                                    version = ""
                            if not any(
                                char in version for char in ["[", "]", "(", ")"]
                            ):
                                version = "[" + version + "]"
                    version = version if version else "any"
                    requirement_files[requirement_file_name]["dependencies"].update(
                        {(dependency["groupId"], dependency["artifactId"]): version}
                    )
    return requirement_files
