from ..utils.logger import LoggerManager
from ..utils.base_request import BaseRequest

import requests
import os
import time

log_manager = LoggerManager(f"log/{__name__}.log")
logger = log_manager.logger


class Onedrive(BaseRequest):
    def __init__(self, local_base_path_relative_to_repo, remote_base_path_relative_to_repo, om):
        super().__init__()
        self.om = om
        self.last_token_refresh_timestamp = 0
        self.max_token_valid_time = 40 * 60 # 40 minutes
        self.retry_time = 5
        self.local_base_path_relative_to_repo = local_base_path_relative_to_repo
        self.remote_base_path_relative_to_repo = remote_base_path_relative_to_repo


    def upload(self, files_to_upload=None, remove_local=False):
        all_od_upload_success = True
        failed_files = []
        ### upload video
        num_subvideo_download=0
        for file in files_to_upload:
            num_subvideo_download += 1
            if time.time() - self.last_token_refresh_timestamp > self.max_token_valid_time:
                self.last_token_refresh_timestamp = time.time()
                if not self.om.try_refresh_token():
                    logger.error('OnedriveAPI: cannot refresh onedrive token')
                    return False

            # get filename from path with extension
            relative_path = file.replace(f"{self.local_base_path_relative_to_repo}", "", 1)
            if relative_path.startswith('/'):
                relative_path = relative_path[1:]
            upload_target = os.path.join( self.remote_base_path_relative_to_repo, relative_path).replace('\\','/')


            upload_success = False
            for i in range(self.retry_time):
                if self.om.upload_large_file(file, upload_target, verbose_prefix=f"({num_subvideo_download}/{len(files_to_upload)}) "):
                    # delete file
                    if remove_local:
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
                logger.error('Upload failed for {file} to onedrive')

        return all_od_upload_success



