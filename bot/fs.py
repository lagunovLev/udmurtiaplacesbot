import gridfs
import env_variables
from database import db_client

fs = gridfs.GridFS(db_client[env_variables.db_name])
