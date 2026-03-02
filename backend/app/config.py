
from os import environ
from os.path import abspath, dirname
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env if it exists.
basedir = abspath(dirname(__file__))


def _as_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}

class Config(object):
    """Base Config Object"""
    

    FLASK_DEBUG                             = _as_bool(environ.get('DEBUG', 'False'))
    SECRET_KEY                              = environ.get('SECRET_KEY', 'Som3$ec5etK*y')
    UPLOADS_FOLDER                          = environ.get('UPLOADS_FOLDER') 
    IMAGE_FOLDER                            = environ.get('IMAGE_FOLDER') 

    ENV                                     = environ.get('FLASK_DEBUG') 
    FLASK_RUN_PORT                          = int(environ.get('FLASK_RUN_PORT', 8080))
    FLASK_RUN_HOST                          = environ.get('FLASK_RUN_HOST', '127.0.0.1')

    # MONGODB VARIABLES
    DB_USERNAME                             = environ.get('DB_USERNAME', '')
    DB_PASSWORD                             = environ.get('DB_PASSWORD', '')
    DB_SERVER                               = environ.get('DB_SERVER') or 'localhost'
    DB_PORT_RAW                             = environ.get('DB_PORT')
    DB_PORT                                 = int(DB_PORT_RAW) if (DB_PORT_RAW and DB_PORT_RAW.isdigit()) else 27017
    MONGO_URI                               = environ.get('MONGO_URI') or f'mongodb://{DB_SERVER}:{DB_PORT}/ELET2415'

    PROPAGATE_EXCEPTIONS                    = False
 
 
