import yaml
import json

from bili_backup.deploy_stragegies import *

strategy = get_strategy()
json_data = json.dumps(strategy.users)
print("write `BiliBili_users`into github action secrect name and the following into secret value:")
print(json_data)
