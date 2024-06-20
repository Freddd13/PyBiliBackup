'''
Date: 2023-10-23 23:09:59
LastEditors: Kumo
LastEditTime: 2024-06-20 20:50:36
Description: 
'''

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .utils import legal_title
from .proxy_decorator import IS_AUTHOR_ENV
from .logger import LoggerManager

log_manager = LoggerManager(f"log/{__name__}.log")
logger = log_manager.logger

class BaseRequest:
    def __init__(self):
        self._retry_strategy = Retry(
            total=5, 
            backoff_factor=1, 
            status_forcelist=[429, 500, 502, 503, 504], 
            allowed_methods=["HEAD", "GET", "OPTIONS"]  
        )

        self._adapter = HTTPAdapter(max_retries=self._retry_strategy)
        self._http = requests.Session()
        self._http.mount("https://", self._adapter)
        self._http.mount("http://", self._adapter)
        self._proxy_dict = {
            'http': '127.0.0.1:51837',
            'https': '127.0.0.1:51837',
        } if IS_AUTHOR_ENV else {}

    
    def download(self, url, file_path) -> bool:
        try:
            with self._http.get(url, stream=True, proxies=self._proxy_dict) as response:
                response.raise_for_status()
                print(url)
                print("IIII:", file_path)
                with open(file_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
            logger.info(f"File downloaded successfully: {file_path}")
            return True
        except requests.RequestException as e:
            logger.error(f"An error occurred: {e}")
            return False
        


