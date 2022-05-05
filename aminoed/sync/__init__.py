from threading import Thread as ThreadIt

from .global_client import Client
from .community_client import CommunityClient
from .utils import exceptions, models, types, helpers
from .websocket import WebSocketClient

from .utils.helpers import *
from .utils.types import *
from .utils.models import *
from .utils.exceptions import *

def run_with_client(**kwargs):
    def start(callback):
        callback(Client(**kwargs))
    return start

def run():
    def start(callback):
        callback()
    return start
