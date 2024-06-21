from ..utils.logger import LoggerManager
from ..utils.base_request import BaseRequest
from ..utils.utils import delete_contents, delete_contents_keep_structure

import requests
import os
import time
import subprocess

log_manager = LoggerManager(f"log/{__name__}.log")
logger = log_manager.logger


class RClone(BaseRequest):
    def __init__(self, local_base_path_relative_to_repo, remote_base_path_relative_to_repo, rclone_port=5572):
        super().__init__()
        self.rclone_port = rclone_port
        self.local_base_path_relative_to_repo = local_base_path_relative_to_repo
        self.remote_base_path_relative_to_repo = remote_base_path_relative_to_repo

        self._rclone_start_timeout = 10

    def check_rclone_port(self, port):
        try:
            response = subprocess.run("ps -A | grep rclone", shell=True, capture_output=True, text=True)

            print(response.stdout)
            if f"rclone" in response.stdout:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Failed to check rclone port: {str(e)}")
            return False

    def start_rclone(self):
        if not self.check_rclone_port(self.rclone_port):
            logger.info("RClone is not running, starting rclone...")

            try:
                subprocess.Popen(
                    ["nohup", "rclone", "rcd", "--rc-no-auth"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setpgrp  # 防止子进程接受到父进程的信号
                )
            except Exception as e:
                logger.error(f"Failed to start rclone: {e}")
                return False

            # wait for rclone to start
            start_time = time.time()
            while not self.check_rclone_port(self.rclone_port):
                if time.time() - start_time > self._rclone_start_timeout:
                    logger.error("Failed to start rclone within timeout")
                    return False
                time.sleep(1)

            logger.info("Start Rclone rcd success!")
        return True


    def upload(self, files_to_upload=None, remove_local=False):
        if not self.start_rclone():
            return False
        
        try:
            logger.info(f"Uploading the following files...\n{'\n'.join(files_to_upload)}")

            abs_path = os.path.join(os.getcwd(), self.local_base_path_relative_to_repo)
            url = f"http://127.0.0.1:5572/sync/copy?srcFs={abs_path}&dstFs={self.remote_base_path_relative_to_repo}&createEmptySrcDirs=true"
            response = self._http.post(url)
            response.raise_for_status()

            if "{}" in response.text:
                logger.info(f"Rclone upload {len(files_to_upload)} files successfully")
                if remove_local:
                    delete_contents(abs_path)
                return True
            else:
                logger.error(f"Rclone upload failed")
                return False

        except requests.RequestException as e:
            logger.error(f"Rclone request: HTTP post failed: {str(e)}")
            return False
        
        except Exception as e:
            logger.error(f"Rclone request: Unknown Error: {str(e)}")
            return False

