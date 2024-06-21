from bilix.sites.bilibili.api import get_video_info

# import httpx
# from bilix.sites.bilibili import api
# import asyncio

# # dft_client_settings = {
# #     'headers': {'user-agent': 'PostmanRuntime/7.29.0', 'referer': 'https://www.bilibili.com'},
# #     'cookies': {'CURRENT_FNVAL': '4048'},
# #     'http2': True
# # }

# async def test():
#     client = httpx.AsyncClient(headers={'user-agent': 'PostmanRuntime/7.29.0', 'referer': 'https://www.bilibili.com'}, cookies={'CURRENT_FNVAL': '4048'}, http2=True)
#     url = "https://www.bilibili.com/video/BV1S1421r77j"
#     # url = "https://www.bilibili.com/video/BV1mt411y7Kg/"
#     info = await get_video_info(client, url)
#     print(len(info.pages))
#     await client.aclose()  # 确保关闭客户端

# if __name__ == "__main__":
#     asyncio.run(test())

from bili_backup.downloader.bilix import Bilix

b = Bilix()

b.get_video_metadata("https://www.bilibili.com/video/BV1S1421r77j")