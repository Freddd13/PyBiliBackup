from ..utils.base_request import BaseRequest
from ..utils.proxy_decorator import IS_AUTHOR_ENV
from ..utils.singleton import SingletonMeta, InstanceRegistry

import feedparser
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class BaseRSSParser(BaseRequest, metaclass=SingletonMeta):
    def __init__(self):
        super().__init__()


    @classmethod
    def get_all_instances(cls):
        return list(cls._instances)


    def get_latest_entries(self):
        return NotImplementedError
    

    def get_download_data(self):
        return NotImplementedError
