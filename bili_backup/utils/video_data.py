
import os
class VideoData:# TODO test no desc
    def __init__(self, title, pubdate, timestamp, author, bv, link, desc, is_series=False, episode = None, thumb_url=None, dm_url=None, subtitle_url=None) -> None:
        self.title = title
        self.pubdate = pubdate
        self.timestamp = timestamp
        self.author = author
        self.link = link
        self.desc = desc
        self.thumb_url = thumb_url
        self.dm_url = dm_url
        self.subtitle_url = subtitle_url
        
        self.is_series = is_series
        self.episode = episode
        self.bv = bv
    
    def to_nfo(self, output_parent_path = ""):
        nfo_content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<movie>
    <title>{self.title}</title>
    <plot>{self.desc}</plot>
    <director>{self.author}</director>
    <url>{self.link}</url>
    <thumb>{self.thumb_url}</thumb>
    <episode>{self.episode}</episode>
</movie>"""

    # <danmaku>{self.dm_url}</danmaku>
    # <subtitle>{self.subtitle_url}</subtitle>
        
        with open(os.path.join(output_parent_path, self.title + ".nfo"), 'w', encoding='utf-8') as file:
            file.write(nfo_content)


    def display(self):
        print("=" * 100)
        print(f"Title: {self.title}")
        print(f"Author: {self.author}")
        print(f"Pubdate: {self.pubdate}")
        print(f"Timestamp: {self.timestamp}")
        print(f"Link: {self.link}")
        print(f"Description: {self.desc}")
        print(f"Is series: {self.is_series}")
        print(f"Thumb url: {self.thumb_url}")
        print(f"Danmaku url: {self.dm_url}")
        print(f"Subtitle url: {self.subtitle_url}")
        print(f"Episode: {self.episode}")
        print("=" * 100 + '\n')
