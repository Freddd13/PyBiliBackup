'''
Date: 2023-10-23 18:04:39
LastEditors: Kumo
LastEditTime: 2024-06-20 21:13:36
Description: 
'''
from .base_rss import BaseRSSParser
from ..utils.singleton import SingletonMeta, InstanceRegistry
from ..utils.logger import LoggerManager

from ..utils.video_data import VideoData
from ..utils.utils import legal_title

import feedparser
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup

from datetime import datetime, timezone, timedelta
import os
import time
import requests

log_manager = LoggerManager(f"log/{__name__}.log")
logger = log_manager.logger


# @log_manager.apply_log_method_to_all_methods
class UserStarsHandler(BaseRSSParser, metaclass=SingletonMeta):
    _name = "mms"
    def __init__(self, rss_url="https://rsshub.app/", rss_key = ""):
        super().__init__()
        InstanceRegistry.register_instance(self)
        
        self._url = rss_url
        self._is_available = True
        self._feed = None
        self._rss_key = rss_key

        self.test_source()


    @property
    def is_available(self):
        return self._is_available


    def test_source(self):
        pass


    def get_latest_entries(self, uid, fid):
        num_pages_to_check = 1  # TODO
        all_items = []
        logger.info("requesting and merging rss data...")
        for i in range(num_pages_to_check):
            key = f"?key={self._rss_key}" if self._rss_key else ""
            url = os.path.join(self._url, f"bilibili/fav/{uid}/{fid}/1{key}").replace('\\', '/')
            
            response = self._http.get(url,proxies=self._proxy_dict)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for item in root.findall(".//item"):
                    all_items.append(ET.tostring(item, encoding="unicode"))
            else:       
                return None
                
        # merge RSS XML
        merged_rss = f"""
        <rss version="2.0">
        <channel>
            {''.join(all_items)}
        </channel>
        </rss>
        """    
        return feedparser.parse(merged_rss)  


    def get_new_videos(self, uid, fid, last_timestamp = None):  # timestamp-->sheet_num for now
        # entry_links, entry_times, entry_titles = [], [], []
        if last_timestamp:
            return NotImplementedError
        
        video_meta_list = []
        # if not last_timestamp:
        #    last_timestamp = -1

        for entry in self.get_latest_entries(uid, fid).entries:
            if (entry.title=="已失效视频"):
                logger.warning(f"跳过失效视频 {entry.link}")
                continue
            logger.info("标题:"+entry.title)

            dt = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z")
            this_timestamp = dt.timestamp()
            # if this_timestamp <= last_timestamp:
            #     logger.warn("Nothing new")
            #     break

            # deal with desc
            soup = BeautifulSoup(entry.description, 'html.parser')
            img_tag = soup.find('img')
            thumb_url = img_tag['src'] if img_tag else ''

            for img in soup.find_all('img'):
                img.decompose()
            clean_description = soup.get_text(separator='', strip=True)

            bv = entry.link.split("/")[-1]
            video_meta_list.append(VideoData(legal_title(entry.title), entry.published, this_timestamp, entry.author, bv, entry.link, clean_description, thumb_url=thumb_url))

        return video_meta_list
