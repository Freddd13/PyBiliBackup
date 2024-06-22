import base64

# 读取 rclone.conf 文件内容
with open('rclone.conf', 'rb') as file:
    file_content = file.read()

# 将文件内容编码为 Base64
encoded_content = base64.b64encode(file_content).decode('utf-8')

print(encoded_content)
