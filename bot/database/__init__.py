from pymongo import MongoClient
import env_variables

db_client: MongoClient = MongoClient(f'{env_variables.db_host}')  # :{config.db_port}

