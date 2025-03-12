import gridfs
from bot import env_variables
from bot.database import db_client

fs = gridfs.GridFS(db_client[env_variables.db_name])


def get_file_binary(id: str):
    with open(fs.get(id), 'rb') as file:
        return file.read()
