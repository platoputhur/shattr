import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


def get_config(name):
    return os.environ.get(name, "")
