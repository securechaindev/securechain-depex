import requests

file = open("all_pypi_packages.txt", "r")

for package in file.read().split("\n"):
    print(package)
    requests.post(f"http://localhost:8000/pypi/package/init?package_name={package}")