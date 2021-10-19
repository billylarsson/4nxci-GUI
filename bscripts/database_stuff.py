from script_pack.sqlite_handler import SQLite
import os

sqlite = SQLite(
    DATABASE_FILENAME=os.environ['DATABASE_FILENAME'],
    DATABASE_FOLDER=os.environ['DATABASE_FOLDER'],
    DATABASE_SUBFOLDER=os.environ['DATABASE_SUBFOLDER'],
    INI_FILENAME=os.environ['INI_FILENAME'],
    INI_FILE_DIR=os.environ['INI_FILE_DIR'],
)

class DB:
    class settings:
        config =  sqlite.db_sqlite('settings', 'config', 'blob')



