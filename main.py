'''
Date: 2023-10-23 18:24:31
LastEditors: Kumo
LastEditTime: 2024-06-21 23:23:30
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
from bili_backup.uploader.onedrive import Onedrive
from bili_backup.uploader.rclone import RClone

from bili_backup.database.safety.crypt import *
from bili_backup.database.manager import DBManager


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



def main(strategy):
    # init parser
    parser = UserStarsHandler(strategy.rss_url, strategy.rss_url_key)

    # init downloader
    downloader = Bilix()

    # init uploader
    assert not (strategy.enable_rclone_upload and strategy.enable_od_upload), "Cannot enable both rclone and onedrive upload at the same time."
    if strategy.enable_rclone_upload:
        uploader = RClone(strategy.savefolder_path, strategy.rclone_upload_dir, rclone_port=5572)
    elif strategy.enable_od_upload:
        om = OnedriveManager(strategy.od_client_id, strategy.od_client_secret, strategy.od_redirect_uri)
        uploader = Onedrive(strategy.savefolder_path, strategy.od_upload_dir, om)
    else:
        uploader = None

    # init database manager
    db_manager = DBManager(db_path=DB_plaintext_path)
    
    # init email handler
    email_handler = EmailHandler(strategy.enable_email_notify, strategy.smtp_host, strategy.smtp_port, strategy.mail_license, strategy.receivers)

    # set global messy params
    all_tasks_success = True
    num_newly_backup_global = 0
    titles_newly_download_global = []

    if not (parser and parser.is_available): # check rss source
        all_tasks_success = False
        collect_errors(f"RSS source is not available.")

    else:
        # start to process
        for user in strategy.users:
            uid, username, collections = user["uid"], user["name"], user["collections"]
            db_manager.add_user(uid, username)

            for collection in collections:
                fid, collection_name, collection_max_ep = collection["fid"], collection["name"], collection["max_ep"]

                download_folder = os.path.join(strategy.savefolder_path, username, collection_name).replace('\\','/')
                if not os.path.exists(download_folder):
                    os.makedirs(download_folder)

                ## init fid--uid table if necessary
                db_manager.add_collection(fid, uid, collection_name)
                
                ## get new videos data via RSS
                video_meta_list = parser.get_new_videos(uid, fid)
                if len(video_meta_list) > 0: 
                    ### for limited space, download and upload one by one(, remove one by one)
                    for video_meta in video_meta_list:
                        all_eps_ok = True
                        if db_manager.is_video_downloaded(video_meta.bv):
                            logger.info(f"Video [{video_meta.title}] has been downloaded, skip.")
                            continue

                        #### get info first (currently use bilix api)
                        video_info_fetched = downloader.get_video_metadata(video_meta.link)

                        #### skip videos with many eps
                        num_eps = len(video_info_fetched.pages)
                        if num_eps > collection_max_ep: # check eps
                            logger.warning(f"Too many eps in video [{video_meta.title}], skip")
                        else:  ##### try to download this bv to local
                            logger.info(f"Downloading {video_meta.title}...")
                            if downloader.download_video(video_link=video_meta.link, path=download_folder):
                                logger.info(f"Successfully backup {video_meta.title} into {download_folder}.")

                                ###### get all videos to upload (for onedrive API only)
                                entry, is_folder, _ = get_latest_entry(download_folder)
                                if is_folder:
                                    videos_to_upload = []
                                    for filename in os.listdir(entry):
                                        relative_filename = os.path.join(entry, filename).replace('\\','/')
                                        if os.path.isfile(relative_filename):
                                            videos_to_upload.append(relative_filename)
                                    extra_folder = os.path.join(entry, "extra").replace('\\','/')
                                else:
                                    videos_to_upload = [entry]
                                    extra_folder = os.path.join(download_folder, "extra").replace('\\','/')

                                ###### download cover jpg:
                                local_relative_thumb_url = os.path.join("extra", f"{video_meta.title}.jpg").replace('\\','/')
                                if not downloader.download(video_meta.thumb_url, os.path.join(extra_folder, f"{video_meta.title}.jpg")):
                                    all_eps_ok = False
                                    all_tasks_success = False
                                    logger.error("Failed to download cover jpg.")

                                ###### add other metadata
                                video_meta.thumb_url = local_relative_thumb_url
                                video_meta.episode = len(videos_to_upload)

                                ###### gen nfo file
                                video_meta.to_nfo(extra_folder)
                                
                                ###### get all extra files to upload (for onedrive API only)
                                extra_to_upload = []
                                for extra_file in os.listdir(extra_folder):
                                    relative_extra_file = os.path.join(extra_folder, extra_file).replace('\\','/')
                                    if os.path.isfile(relative_extra_file):
                                        extra_to_upload.append(relative_extra_file)
                                                            
                                
                                ###### upload to remote (optional)
                                if strategy.enable_od_upload:
                                    ### upload videos
                                    is_full_videos_upload_success = uploader.upload(videos_to_upload, remove_local=strategy.remove_local_files)
                                    ### upload metadata and cover
                                    is_full_extra_uoload_success = uploader.upload(extra_to_upload, remove_local=strategy.remove_local_files)

                                    if not (is_full_videos_upload_success and is_full_extra_uoload_success):
                                        # failed_video_metadata_list.append(video_meta)
                                        all_tasks_success = False
                                        all_eps_ok = False

                                elif strategy.enable_rclone_upload:
                                    if not uploader.upload(videos_to_upload, remove_local=strategy.remove_local_files):
                                        all_tasks_success = False
                                        all_eps_ok = False
                            else:
                                ###### failed to download this bv  
                                all_eps_ok = False
                                all_tasks_success = False                            
                                logger.error(f"fail to download {video_meta.title}")

                        #### save to database
                        if all_eps_ok:
                            db_manager.add_video(video_meta.bv, video_meta.title, video_meta.link)
                            db_manager.add_video_to_collection(fid, video_meta.bv)
                            num_newly_backup_global += 1
                            titles_newly_download_global.append(video_meta.title)
                        else:   # failed to fully successfully process this BV
                            all_tasks_success = False
                            pass #FIXME

                else:
                    logger.warning(f"No new video found in {collection_name}.")


    # send email (optional)
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




