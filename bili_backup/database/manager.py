import sqlite3
import os

class DBManager:
    def __init__(self, db_path="downloads.db"):
        self.db_path = db_path
        self.init_db()


    def init_db(self):
        """初始化数据库并创建表"""
        if not os.path.exists(os.path.dirname(self.db_path)):
            os.makedirs(os.path.dirname(self.db_path))
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                uid TEXT PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')

        # 创建收藏夹表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collections (
                fid TEXT PRIMARY KEY,
                uid TEXT NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY (uid) REFERENCES users (uid)
            )
        ''')

        # 创建视频表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                bv TEXT PRIMARY KEY,
                title TEXT,
                url TEXT
            )
        ''')

        # 创建收藏夹视频表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collection_videos (
                fid TEXT NOT NULL,
                bv TEXT NOT NULL,
                FOREIGN KEY (fid) REFERENCES collections (fid),
                FOREIGN KEY (bv) REFERENCES videos (bv),
                PRIMARY KEY (fid, bv)
            )
        ''')

        conn.commit()
        conn.close()


    def add_user(self, uid, name):
        """添加用户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (uid, name) VALUES (?, ?)", (uid, name))
        conn.commit()
        conn.close()

    def add_collection(self, fid, uid, name):
        """添加收藏夹"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO collections (fid, uid, name) VALUES (?, ?, ?)", (fid, uid, name))
        conn.commit()
        conn.close()

    def add_video(self, bv, title, url):
        """添加视频"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO videos (bv, title, url) VALUES (?, ?, ?)", (bv, title, url))
        conn.commit()
        conn.close()

    def add_video_to_collection(self, fid, bv):
        """将视频添加到收藏夹"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO collection_videos (fid, bv) VALUES (?, ?)", (fid, bv))
        conn.commit()
        conn.close()

    def is_video_downloaded(self, bv):
        """检查视频是否已经下载"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM videos WHERE bv = ?", (bv,))
        result = cursor.fetchone()
        conn.close()
        return result is not None