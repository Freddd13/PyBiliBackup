'''
Date: 2023-10-23 18:04:14
LastEditors: Kumo
LastEditTime: 2024-12-19 18:55:05
Description: 
'''
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
print(sys.path)

import httpx
import asyncio
from bilix.sites.bilibili import DownloaderBilibili
from bilix.sites.bilibili.api import get_video_info

from .base_downloader import BaseDownloader
from ..utils.proxy_decorator import MY_PROXY
from ..utils.singleton import SingletonMeta, InstanceRegistry
from ..utils.logger import LoggerManager

from typing import Union, Sequence, Tuple, List

from datetime import datetime, timezone, timedelta
import time
import os
import json
import requests

log_manager = LoggerManager(f"log/{__name__}.log")
logger = log_manager.logger


# @log_manager.apply_log_method_to_all_methods
class Bilix(BaseDownloader, metaclass=SingletonMeta):
    _name = "bilix_handler"
    def __init__(self):
        super().__init__()
        InstanceRegistry.register_instance(self)
        InstanceRegistry.register_handler_instance(self)
        self._files = []
        self._video_links = []
        self._success = True


    async def download_video_action(self, video_link, path
                        #             , quality: Union[str, int] = 0, image=False, subtitle=False,
                        #  dm=False, only_audio=False, p_range: Sequence[int] = None, codec: str = ''
                         ):
        async with DownloaderBilibili(video_concurrency=1) as d:
            await d.get_series(video_link, path, image=False, subtitle=True, dm=True)


    def download_video(self, video_link:str, path:str) -> bool:
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            asyncio.run(self.download_video_action(video_link, path))
            return True
        except Exception as e:
            logger.error(f"Fail to download {video_link}: {str(e)}")
            return False
            

    def download_videos(self, video_links:list, path:str) -> bool:
        for link in video_links:
            if not self.download_video(link, path):
                logger.error(f"Fail to download {link}")
                self._success = False
        return self._success
    

    async def _get_video_metadata_action(self, url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com'
        }
        cookies = {
            'CURRENT_FNVAL': '4048'
        }
        async with httpx.AsyncClient(headers=headers, cookies=cookies, http2=True) as client:
            info = await get_video_info(client, url)

            return info


    def get_video_metadata(self, url):
        return asyncio.run(self._get_video_metadata_action(url))


        
    @property
    def file_paths(self):
        return self._files

    @property
    def success(self):
        return self._success

    @property
    def sheet_links(self):
        return self._video_links


# # dft_client_settings = {
# #     'headers': {'user-agent': 'PostmanRuntime/7.29.0', 'referer': 'https://www.bilibili.com'},
# #     'cookies': {'CURRENT_FNVAL': '4048'},
# #     'http2': True
# # }