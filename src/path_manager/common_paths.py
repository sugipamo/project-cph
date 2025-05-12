import os

CONTAINER_WORKSPACE = "/workspace"
HOST_WORKSPACE = "./workspace"

TEMP_DIR = os.path.abspath('.temp')
CONTAINER_TEMP_DIR = "/workspace/.temp"

OJTOOLS_COOKIE_HOST = os.path.abspath(".local/share/online-judge-tools/cookie.jar")
OJTOOLS_COOKIE_CONT = "/root/.local/share/online-judge-tools/cookie.jar" 