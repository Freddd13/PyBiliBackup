from cryptography.fernet import Fernet
import os

DB_plaintext_path = "./database.db"
DB_encrypted_path = "./database.encdb"

def load_key():
    return os.getenv("Backup_database_key").encode()


def encrypt_file(cipher, input_file, output_file):
    """加密文件"""
    with open(input_file, 'rb') as f:
        data = f.read()
    encrypted_data = cipher.encrypt(data)
    with open(output_file, 'wb') as f:
        f.write(encrypted_data)
    os.remove(input_file)

def decrypt_file(cipher, input_file, output_file):
    """解密文件"""
    with open(input_file, 'rb') as f:
        encrypted_data = f.read()
    decrypted_data = cipher.decrypt(encrypted_data)
    with open(output_file, 'wb') as f:
        f.write(decrypted_data)
    os.remove(input_file)

