'''
Date: 2023-10-23 18:04:14
LastEditors: Kumo
LastEditTime: 2024-06-20 21:25:51
Description: 
'''

import asyncio
from bilix.sites.bilibili import DownloaderBilibili

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
        asyncio.run(self.download_video_action(video_link, path))
        return True
            

    def download_videos(self, video_links:list, path:str) -> bool:
        for link in video_links:
            if not self.download_video(link, path):
                logger.error(f"Fail to download {link}")
                self._success = False
        return self._success
           

    @property
    def file_paths(self):
        return self._files

    @property
    def success(self):
        return self._success

    @property
    def sheet_links(self):
        return self._video_links
