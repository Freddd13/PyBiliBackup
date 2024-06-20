# PyBiliBackup
Automatically backup bilibili videos in your favorites.


## Method
Use RSS to get new videos and bilix to download videos, finally we can upload them to onedrive.
Note: If you want to enable uploading to onedrive: see [About Onedrive](#About-Onedrive).

## Usage

### Use Github Action
1. Fork the repo
2. Use your own information to set the needed secrets in your repo(Repo Settings -- Secrets and variables -- Actions -- Secrets). You need an email with SMTP host, port, account and app password. Check out [User config](#User-config) for the full config we need.
![](docs/add_secrets.png)
3. Enable Workflow r/w permissions
Settings -- Actions -- General
![](docs/enable_rw.png)

Then the action will be triggered when pushing to repo or reaching a certain time everyday. The latter can be set in the auto_download.yml. 

### Use Docker
1. Download the config file:
```
wget https://github.com/Freddd13/pybilibackup/blob/main/localconfig.yaml?raw=true -O .localconfig.yaml
```
2. Replace your own data in the yaml above. Check out [User config](#User-config) for the full config we need.
3. Download image and run:
```
mkdir pybilibackup
touch pybilibackup/_last_download_signal
docker run -d --name pybilibackup \
-v $(pwd)/pybilibackup/.localconfig.yaml:/app/.localconfig.yaml \
-v $(pwd)/pybilibackup/files:/app/files \
-v $(pwd)/pybilibackup/_last_download_signal:/app/_last_download_signal \
fredyu13/pybilibackup:main

# docker exec -it {container_id} /bin/bash 
```

### User config(For Github Action Secrets, but it's similar for yaml)
| Variable                  | Description                                         | Example Value          |
|---------------------------|-----------------------------------------------------|------------------------|
| `savefolder_path`     | backup root folder (relative to the repo)                   | `files` (recommended)      |
| `RSS_url`                 | URL of the RSS feed.                               | `https://rsshub.app`|
| `RSS_key`                 | key of your self-hosted rsshub. url->url/SOMEROUTE?key={key} If you don't know what is it, just leave it empty.                               | `123`|
| `enable_email_notify`      | Whether to notify downloading result via email  (1 enable, 0 disable)  | `1` |
| `Email_sender`            | Email address used to send emails.                 | `sender@example.com`   |
| `Email_receivers`         | Email addresses designated to receive emails.      | `receiver@example.com` |
| `Email_smtp_host`         | SMTP server address used to send emails.           | `smtp.example.com`     |
| `Email_smtp_port`         | SMTP server port used to send emails.              | `11451`                  |
| `Email_mail_license`      | SMTP password or authorization used for sending emails.  | `1145141919810`  |
| `Email_send_logs`      | Whether to send email with logs (1 enable, 0 disable)  | `1`  |
| `enable_od_upload`      | Whether to also upload sheets to onedrive (1 enable, 0 disable)  | `0`  |
| `od_client_id`      | onedrive app client id  | `114514`  |
| `od_client_secret`      | onedrive app client secret value | `114514`  |
| `od_redirect_uri`      | onedrive app redirect_ur  | `http://localhost:9001`  |
| `od_upload_dir`      | which onedrive dir to upload sheets to relative to the root, do NOT start with '/'  | `halycon_sheets`  |
| `BiliBili_ufid`      |  [[uid1, fid1, max_eps], [uid2, fid2, max_eps], ...]                                                                         |


## Develop
### Run locally
1. Clone this repo
2. Create a .localconfig.yaml from localconfig.yaml and fill in your data. Check out [User config](#User-config) for the full config we need.
3. `pip install -r requirements.txt`
4. Set env `BILIBILI_BACKUP_ENV` to `LOCAL`
4. `python main.py`

### Build Docker
1. Clone this repo
2. Create a .localconfig.yaml from localconfig.yaml and fill in your data. 
3. `docker build -t pybilibackup -f docker/Dockerfile .`
4. `docker run -d --name pybilibackup pybilibackup:latest`
The schedule task can be adjusted by modifing the ./docker/crontab.


## Note
### About RSS
Currently the repo depends on [MMS user route rss from RSSHub](https://docs.rsshub.app/routes/social-media#youtube-user). It's recommended to replace the domain with your self-hosted rsshub url, because the public hub can sometimes be banned by source sites. Besides, self-hosting one is quite benefit for your other future usage. If you don't have one, you can use the default url `https://rsshub.app/`.
For more info, please check [RSSHub doc](https://docs.rsshub.app/).


### About Onedrive
To save to onedrive, you need to create an app in [Azure](https://portal.azure.com/#home). Note that currently only onedrive business international is tested.
Check out [here](bili_backup/onedrive/README.md) for detailed instructions of getting required data.
The onedrive needs a login for the first time, after that the token will be saved to `_refresh_token`. As I have no idea how to receive auth callback in github action, the code assumes there's already a token file with token. Thus you need to run on local first to generate the token file. 
For github action:
1. Fork this repo,
2. Follow [Run locally](#Run-locally) (clone your own repo) to run once.
3. Check if the token file generates successfully, and push the code with token file to your repo.
```bash
git add _refresh_token && git commit -m "add token" && git push
```
4. Follow [Use Github Action](#Use-Github-Action)


### About Email
The `enable_email_notify` is used to send you downloading result including sheets and app log. If you disable the email, there's still another way to save your sheets: remove the `MMS_savefolder_path` directory if it exists in the `.gitignore`. The action will update the downloaded sheets to your repo. But it's not a good behavior to share others' sheets without permission, thus it's not recommended to disable email before other uploading method is supported.


## TODO
- [x] docker
- [ ] fix local storage check
- [ ] fix bug when remaining history files
- [ ] add retry history failed videos
- [ ] backup summary
- [ ] config from gist
- [ ] bot


# Disclaimer:
```
This software is provided "as-is" for personal learning and educational purposes only. The use of this software is at your own risk. The developer is not responsible for any consequences that may arise from the use of this software.

By using this software, you acknowledge and agree to the following terms:

Personal Use Only: This software is intended solely for personal learning and educational purposes. Any form of distribution, commercial use, or sharing of this software or its output is strictly prohibited.

Compliance with Laws and Terms of Service: Users must comply with all relevant laws and regulations, as well as Bilibili's Terms of Service, when using this software. The developer does not endorse or condone any actions that violate these terms or any applicable laws.

No Liability: The developer shall not be liable for any direct, indirect, incidental, or consequential damages arising out of the use or inability to use this software. This includes but is not limited to any legal issues, data loss, or damage to your device.

Responsibility for Actions: Users are fully responsible for their actions when using this software. The developer assumes no responsibility for any misuse of the software or violations of Bilibili's Terms of Service.

Modifications and Updates: The developer reserves the right to modify or discontinue the software at any time without prior notice. Users are encouraged to check for updates regularly to ensure compliance with the latest terms and regulations.

By downloading and using this software, you agree to these terms and accept full responsibility for your actions.
```