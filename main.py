'''
Date: 2023-10-23 18:24:31
LastEditors: Kumo
LastEditTime: 2024-06-20 22:46:35
Description: 
'''
from bili_backup.cloudreve import Cloudreve
from bili_backup.email import EmailHandler
from bili_backup.deploy_stragegies import *
from bili_backup.utils.proxy_decorator import IS_AUTHOR_ENV

from bili_backup.utils.singleton import get_instance, get_handler, GetHandlers
from bili_backup.utils.logger import LoggerManager
from bili_backup.rss_sources.user_stars import UserStarsHandler

from bili_backup.downloader.bilix import Bilix

from bili_backup.onedrive.onedrive import OnedriveManager

from bili_backup.safety.crypt import *

import sqlite3

import os
import time


log_manager = LoggerManager(f"log/{__name__}.log")
logger = log_manager.logger
ERROR_MSGS = []

# od const
last_token_refresh_timestamp = 0
max_token_valid_time = 40 * 60  # use 40 minutes

# other const
REMOVE_LOCAL_FILES = True


###################### db #####################
def init_db(db_path):
    """初始化数据库并创建表"""
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
    
    conn = sqlite3.connect(db_path)
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


def add_user(uid, name, db_path="downloads.db"):
    """添加用户"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (uid, name) VALUES (?, ?)", (uid, name))
    conn.commit()
    conn.close()

def add_collection(fid, uid, name, db_path="downloads.db"):
    """添加收藏夹"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO collections (fid, uid, name) VALUES (?, ?, ?)", (fid, uid, name))
    conn.commit()
    conn.close()

def add_video(bv, title, url, db_path="downloads.db"):
    """添加视频"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO videos (bv, title, url) VALUES (?, ?, ?)", (bv, title, url))
    conn.commit()
    conn.close()

def add_video_to_collection(fid, bv, db_path="downloads.db"):
    """将视频添加到收藏夹"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO collection_videos (fid, bv) VALUES (?, ?)", (fid, bv))
    conn.commit()
    conn.close()

def is_video_downloaded(bv, db_path="downloads.db"):
    """检查视频是否已经下载"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM videos WHERE bv = ?", (bv,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

####################################################

def parse_last_download(lines):
    last_download = {}
    for line in lines:
        md5, timestamp = line.strip().split(' ')
        last_download[md5] = float(timestamp)
    return last_download

def collect_errors(err):
    logger.error(err)
    ERROR_MSGS.append(err)
 

def traverse_directory(directory):
    first_level_files = []
    subdirectories = {}

    for root, dirs, files in os.walk(directory):
        # 获取第一层文件的路径
        if root == directory:
            for file in files:
                first_level_files.append(os.path.join(root, file))
        
        # 获取子文件夹及其内容
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            subdirectories[dir_path] = []
            for sub_root, sub_dirs, sub_files in os.walk(dir_path):
                for sub_file in sub_files:
                    subdirectories[dir_path].append(os.path.join(sub_root, sub_file))
            # 不需要再遍历子文件夹
            del dirs[:]
    
    return first_level_files, subdirectories


def get_latest_entry(directory):
    entries = [os.path.join(directory, entry) for entry in os.listdir(directory)]
    entries = [e for e in entries if os.path.exists(e) and os.path.basename(e) != 'extra']
    
    if not entries:
        return None, None, 0  
    
    latest_entry = max(entries, key=os.path.getctime)
    latest_entry_time = os.path.getctime(latest_entry)
    
    if os.path.isdir(latest_entry):
        return latest_entry, True, latest_entry_time
    else:
        return latest_entry, False, latest_entry_time


def upload_to_onedrive(om, strategy, files_to_upload):
    global last_token_refresh_timestamp
    all_od_upload_success = True
    failed_files = []
    ### upload video
    num_subvideo_download=0
    for file in files_to_upload:
        num_subvideo_download += 1
        if time.time() - last_token_refresh_timestamp > max_token_valid_time:
            last_token_refresh_timestamp = time.time()
            if not om.try_refresh_token():
                collect_errors('cannot refresh onedrive token')
                return False

        # get filename from path with extension
        relative_path = file.replace(f"{strategy.savefolder_path}", "", 1)
        if relative_path.startswith('/'):
            relative_path = relative_path[1:]
        # upload_target = os.path.join(strategy.od_upload_dir, os.path.basename(relative_path)).replace('\\','/')
        upload_target = os.path.join(strategy.od_upload_dir, relative_path).replace('\\','/')
        # logger.debug(upload_target)

        # retry for max 5 times
        upload_success = False
        for i in range(5):
            if om.upload_large_file(file, upload_target, verbose_prefix=f"({num_subvideo_download}/{len(files_to_upload)}) "):
                # delete file
                if REMOVE_LOCAL_FILES:
                    logger.debug(f"remove {file}")
                    os.remove(file)
                logger.info(f'Upload {os.path.basename(relative_path)} to onedrive successfully')           
                upload_success = True     
                break
            else:
                logger.warning(f"Retry {i+1} times for {file}, sleep for 3s...")
                time.sleep(3)

        if not upload_success:
            all_od_upload_success = False
            failed_files.append(file)
            collect_errors('Failed to upload to onedrive')

    return all_od_upload_success



def main(strategy):
    ## 1.Init
    email_handler = EmailHandler(strategy.enable_email_notify, strategy.smtp_host, strategy.smtp_port, strategy.mail_license, strategy.receivers)
    user_stars_rss = UserStarsHandler(strategy.rss_url, strategy.rss_url_key)
    parser = user_stars_rss
    handler = Bilix()
    if strategy.enable_od_upload:
        om = OnedriveManager(strategy.od_client_id, strategy.od_client_secret, strategy.od_redirect_uri)   

    init_db(DB_plaintext_path) # init database

    ### messy params
    all_tasks_success = True
    num_newly_backup_global = 0
    titles_newly_download_global = []

    if not (parser and parser.is_available): # check rss source
        all_tasks_success = False
        collect_errors(f"RSS source is not available.")

    for user in strategy.users:
        uid = user["uid"]
        username = user["name"]
        collections = user["collections"]
        add_user(uid, username, DB_plaintext_path)
        for collection in collections:
            ## local position
            fid = collection["fid"]
            collection_name = collection["name"]
            collection_max_ep = collection["max_ep"]
            download_folder = os.path.join(strategy.savefolder_path, username, collection_name).replace('\\','/')
            if not os.path.exists(download_folder):
                os.makedirs(download_folder)


            ## init table
            add_collection(fid, uid, collection_name, DB_plaintext_path)
            
            ## get new videos data via RSS
            video_meta_list = parser.get_new_videos(uid, fid)
            if len(video_meta_list) > 0: 
                # for limited space, download one by one
                for video_meta in video_meta_list:
                    all_eps_ok = True
                    if is_video_downloaded(video_meta.bv, DB_plaintext_path):
                        continue

                    # download videos
                    logger.info(f"Downloading {video_meta.title}...")
                    if handler.download_video(video_link=video_meta.link, path=download_folder):
                        logger.info(f"Successfully backup {video_meta.title} into {download_folder}.")

                        ## get all videos to upload
                        entry, is_folder, create_time1 = get_latest_entry(download_folder)
                        if is_folder:
                            videos_to_upload = []
                            for filename in os.listdir(entry):
                                relative_filename = os.path.join(entry, filename).replace('\\','/')
                                if os.path.isfile(relative_filename):
                                    videos_to_upload.append(relative_filename)
                            if len(videos_to_upload) > collection_max_ep:
                                logger.warning(f"Too many eps in video [{entry}], ignore")
                                continue
                            extra_folder = os.path.join(entry, "extra").replace('\\','/')
                        else:
                            # print("not folder")
                            videos_to_upload = [entry]
                            extra_folder = os.path.join(download_folder, "extra").replace('\\','/')

                        ## download cover jpg:
                        local_relative_thumb_url = os.path.join("extra", f"{video_meta.title}.jpg").replace('\\','/')
                        if not handler.download(video_meta.thumb_url, os.path.join(extra_folder, f"{video_meta.title}.jpg")):
                            all_eps_ok = False
                            all_tasks_success = False
                            logger.error("Failed to download cover jpg.")

                        ## add other metadata
                        video_meta.thumb_url = local_relative_thumb_url
                        video_meta.episode = len(videos_to_upload)
                        ## gen nfo file
                        video_meta.to_nfo(extra_folder)
                        

                        ## get all extra files to upload
                        extra_to_upload = []
                        for extra_file in os.listdir(extra_folder):
                            relative_extra_file = os.path.join(extra_folder, extra_file).replace('\\','/')
                            if os.path.isfile(relative_extra_file):
                                extra_to_upload.append(relative_extra_file)
                                                    
                        ## upload to onedrive
                        if strategy.enable_od_upload:
                            ### upload videos
                            is_full_videos_upload_success = upload_to_onedrive(om, strategy, videos_to_upload)

                            ### upload metadata and cover
                            is_full_extra_uoload_success = upload_to_onedrive(om, strategy, extra_to_upload)

                            if not (is_full_videos_upload_success and is_full_extra_uoload_success):
                                # failed_video_metadata_list.append(video_meta)
                                all_tasks_success = False
                                all_eps_ok = False
                        
                        # save to database
                        if all_eps_ok:
                            add_video(video_meta.bv, video_meta.title, video_meta.link, DB_plaintext_path)
                            add_video_to_collection(fid, video_meta.bv, DB_plaintext_path)
                            num_newly_backup_global += 1
                            titles_newly_download_global.append(video_meta.title)
                        else:   # upload videos failled
                            all_tasks_success = False
                            pass #FIXME

                    else:   # download videos failed
                        pass #TODO
                    
            else:
                logger.warning(f"No new video found in {collection_name}.")




    ## send email
    if strategy.enable_email_notify:
        ### check result and prepare mail data
        logger.info("=" * 50)
        logger.info("summary: ")
        has_error_prefix = "[ERROR] " if len(ERROR_MSGS) > 0 else ""
        if all_tasks_success:
            if num_newly_backup_global > 0:
                subject = f"BiliBackup: {has_error_prefix}Successfully backup videos."
                content = "Successfully backup the following video(s):\n{}".format('\n'.join([title for title in titles_newly_download_global]))
                logger.info("All new videos backuped successfully.")

            else:   # nothing new
                subject = f"BiliBackup: {has_error_prefix}There's no new favorite videos."
                content = "There's no new favorite video on bilibili!"
                logger.info("There's no new favorite video on bilibili")

        else:   # download error
            subject = f"BiliBackup: {has_error_prefix}Failed to backup all videos."
            content = "Failed..."
            collect_errors("Failed to backup all videos.")

        if has_error_prefix:
            content += "ERROR msgs: \n{}".format('\n'.join([err for err in ERROR_MSGS]))     
            # content += "Failed to download the following videos:\n{}".format('\n'.join([video_meta.title for video_meta in failed_video_metadata_list]))
        logger.info("=" * 50)   

        email_handler = EmailHandler(strategy.sender, strategy.smtp_host, strategy.smtp_port, strategy.mail_license, strategy.receivers)
        # all_sheets_dir.extend(LoggerManager.get_all_log_filenames())
        email_handler.perform_sending(
            subject, 
            content, 
            log_files=LoggerManager.get_all_log_filenames() if strategy.send_logs else []
        )


if __name__ == "__main__":
    strategy = get_strategy()

    key = load_key()
    cipher = Fernet(key)

    if os.path.exists(DB_encrypted_path):
        decrypt_file(cipher, DB_encrypted_path, DB_plaintext_path)
            

    main(strategy)


    if os.path.exists(DB_plaintext_path):
        encrypt_file(cipher, DB_plaintext_path, DB_encrypted_path)
    # ## save failed metadata
    # # TODO
    # if not os.path.exists("retry"):
    #     os.makedirs("retry")
    # for video_meta in failed_video_metadata_list:
    #     video_meta.to_nfo("retry")




