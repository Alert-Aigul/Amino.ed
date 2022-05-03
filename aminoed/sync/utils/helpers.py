from ...utils.helpers import *

def set_cache(key: str, value: Any) -> Any:
    try:
        with open(".ed.cache") as file:
            cache = loads(file.read())
    except FileNotFoundError:
        cache = {}
    
    cache.update({
        key: value
    })
    
    with open(".ed.cache", "w") as file:
        file.write(dumps(cache))


def get_cache(key: str, default: Any = None) -> Any:
    try:
        with open(".ed.cache") as file:
            cache: dict = loads(file.read())
    except FileNotFoundError:
        return default
    
    return cache.get(key, default)
