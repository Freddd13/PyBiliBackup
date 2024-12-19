import asyncio
import re
import json
from typing import Sequence, Tuple

import httpx
import m3u8

from bilix.download.utils import req_retry, raise_api_error
from bilix.utils import legal_title

dft_client_settings = {
    'headers': {'user-agent': 'PostmanRuntime/7.29.0'},
    'http2': True
}


@raise_api_error
async def get_id(client: httpx.AsyncClient, url: str) -> Tuple[str, str, str]:
    res_web = await req_retry(client, url)
    pid = re.findall(r'guid ?= ?"(\w+)"', res_web.text)[0]
    vide = re.findall(r'/(VIDE\w+)\.', url)[0]
    try:
        vida = re.findall(r'videotvCodes ?= ?"(\w+)"', res_web.text)[0]
    except IndexError:
        vida = None
    return pid, vide, vida


@raise_api_error
async def get_media_info(client: httpx.AsyncClient, pid: str) -> Tuple[str, Sequence[str]]:
    """

    :param pid:
    :param client:
    :return: title and m3u8 urls sorted by quality
    """
    res = await req_retry(client, f'https://vdn.apps.cntv.cn/api/getHttpVideoInfo.do?pid={pid}')
    info_data = json.loads(res.text)
    # extract
    title = legal_title(info_data['title'])
    m3u8_main_url = info_data['hls_url']
    res = await req_retry(client, m3u8_main_url)
    m3u8_info = m3u8.loads(res.text)
    if m3u8_info.base_uri is None:
        m3u8_info.base_uri = re.match(r'(https?://[^/]*)/', m3u8_main_url).groups()[0]
    m3u8_urls = list(sorted((i.absolute_uri for i in m3u8_info.playlists), reverse=True,
                            key=lambda s: int(re.findall(r'/(\d+).m3u8', s)[0])))
    return title, m3u8_urls


@raise_api_error
async def get_series_info(client: httpx.AsyncClient, vide: str, vida: str) -> Tuple[str, Sequence[str]]:
    """

    :param vide:
    :param vida:
    :param client:
    :return: title and list of guid(pid)
    """
    params = {'mode': 0, 'id': vida, 'serviceId': 'tvcctv', 'p': 1, 'n': 999}
    res_meta, res_list = await asyncio.gather(
        req_retry(client, f"https://api.cntv.cn/NewVideoset/getVideoAlbumInfoByVideoId?id={vide}&serviceId=tvcctv"),
        req_retry(client, f'https://api.cntv.cn/NewVideo/getVideoListByAlbumIdNew', params=params)
    )
    meta_data = json.loads(res_meta.text)
    list_data = json.loads(res_list.text)
    # extract
    title = legal_title(meta_data['data']['title'])
    pids = [i['guid'] for i in list_data['data']['list']]
    return title, pids
