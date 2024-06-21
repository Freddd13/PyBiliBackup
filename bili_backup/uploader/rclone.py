from ..utils.logger import LoggerManager
from ..utils.base_request import BaseRequest
from ..utils.utils import delete_contents, delete_contents_keep_structure

import requests
import os
import subprocess

log_manager = LoggerManager(f"log/{__name__}.log")
logger = log_manager.logger


class RClone(BaseRequest):
    def __init__(self, local_base_path_relative_to_repo, remote_base_path_relative_to_repo, rclone_port=5572):
        super().__init__()
        self.rclone_port = rclone_port
        self.local_base_path_relative_to_repo = local_base_path_relative_to_repo
        self.remote_base_path_relative_to_repo = remote_base_path_relative_to_repo

    def check_rclone_port(self, port):
        try:
            response = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
            if f":{port}" in response.stdout:
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"Failed to check rclone port: {str(e)}")
            return False

    def start_rclone(self):
        if not self.check_rclone_port(self.rclone_port):
            logger.info("Starting rclone...")
            os.system("nohup rclone rcd --rc-no-auth >/dev/null 2>&1 &")
            # subprocess.run(["nohup", "rclone", "rcd", "--rc-no-auth", ">/dev/null", "2>&1", "&"])
            if not self.check_rclone_port(self.rclone_port):
                logger.error("Failed to start rclone")
                return False
        logger.info("Rclone is running")
        return True


    def upload(self, files_to_upload=None, remove_local=False):
        if not self.start_rclone():
            return False
        
        try:
            abs_path = os.path.join(os.getcwd(), self.local_base_path_relative_to_repo)
            url = f"http://127.0.0.1:5572/sync/copy?srcFs={abs_path}&dstFs={self.remote_base_path_relative_to_repo}&createEmptySrcDirs=true"
            response = self._http.post(url)
            response.raise_for_status()
            print(response.text)
            if "{}" in response.text:
                logger.info(f"Rclone upload success")
                if remove_local:
                    delete_contents_keep_structure(abs_path)
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

