
from cryptography.fernet import Fernet


# 生成密钥
key = Fernet.generate_key()

# 将密钥保存到文件
with open("secret.key", "wb") as key_file:
    key_file.write(key)

# 输出Base64编码的密钥
print(key.decode())