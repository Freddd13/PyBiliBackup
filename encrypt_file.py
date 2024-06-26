from bili_backup.deploy_stragegies import get_strategy
from bili_backup.database.safety.crypt import *

if __name__ == '__main__':
    get_strategy()
    key = load_key()
    cipher = Fernet(key)

    if os.path.exists(DB_plaintext_path):
        encrypt_file(cipher, DB_plaintext_path, DB_encrypted_path)

    # if os.path.exists(DB_encrypted_path):
    #     decrypt_file(cipher, DB_encrypted_path, DB_plaintext_path)
