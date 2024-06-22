import yaml
import json

from bili_backup.deploy_stragegies import *


with open(".localconfig.yaml", 'r', encoding='utf-8') as yaml_file:
    yaml_content = yaml.safe_load(yaml_file)
json_content = json.dumps(yaml_content, ensure_ascii=False)
print(json_content)
print("config wrote to .localconfig.json")
with open('.localconfig.json', 'w', encoding='utf-8') as json_file:
    json_file.write(json_content)

#json_data = json.dumps(strategy.users, ensure_ascii=False)
