# from ..utils.logger import LoggerManager
# from ..utils.base_request import BaseRequest

import requests
import os

# log_manager = LoggerManager(f"log/{__name__}.log")
# logger = log_manager.logger


class RClone(BaseRequest):
    def __init__(self, remote_path):
        super().__init__()
        self.remote_path = remote_path
        pass

    def upload(self, local_path) -> bool:
        try:
            url = f"http://127.0.0.1:5572/sync/copy?srcFs={local_path}&dstFs={self.remote_path}&createEmptySrcDirs=true"
            response = self._http.post(url)
            response.raise_for_status()

            if "{}" in response.text:
                print(f"Rclone upload success: {self.download_filename}")
                os.remove(self.download_filename)
                return True
            else:
                print(f"Rclone upload failed: {self.download_filename}")
                return False

        except requests.RequestException as e:
            print(f"Rclone request: HTTP post failed: {str(e)}")
            return False
        
        except Exception as e:
            print(f"Rclone request: Unknown Error: {str(e)}")
            return False


if __name__ == "__main__":
    rclone = RClone(remote_path="onedrive-remote:/test_rclone")
    
    rclone.upload("./test_rc.txt")
