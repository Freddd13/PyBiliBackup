from ..utils.proxy_decorator import IS_AUTHOR_ENV
from ..utils.base_request import BaseRequest
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class BaseDownloader(BaseRequest):
    def __init__(self):
        super().__init__()

    @classmethod
    def get_all_instances(cls):
        return list(cls._instances)
    

    def download_video(self, video_link:str, path:str):
        return NotImplementedError
    

    def download_videos(self, video_links:list, path:str):
        return NotImplementedError
