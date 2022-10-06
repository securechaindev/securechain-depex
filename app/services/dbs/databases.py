import motor.motor_asyncio

from app.config import settings


client = motor.motor_asyncio.AsyncIOMotorClient(settings.DATABASE_URL)

depex_db = client.depex
env_variable_collection = depex_db.get_collection('env_variables')
graph_collection = depex_db.get_collection('graphs')
depex_package_edge_collection = depex_db.get_collection('package_edges')
requirement_file_collection = depex_db.get_collection('requirement_files')

nvd_db = client.nvd
cve_collection = nvd_db.get_collection('cves')

pypi_db = client.pypi
pypi_package_edge_collection = pypi_db.get_collection('package_edges')
package_collection = pypi_db.get_collection('packages')
version_collection = pypi_db.get_collection('versions')