import html
import re
import shutil
import os

# https://github.com/HFrost0/bilix/blob/41fa4b3ca59ee724a943585ba09c93ff4ca28e9f/bilix/utils.py
def legal_title(*parts: str, join_str: str = '-'):
    """
    join several string parts to os illegal file/dir name (no illegal character and not too long).
    auto skip empty.

    :param parts:
    :param join_str: the string to join each part
    :return:
    """
    return join_str.join(filter(lambda x: len(x) > 0, map(replace_illegal, parts)))


def replace_illegal(s: str):
    """strip, unescape html and replace os illegal character in s"""
    s = s.strip()
    s = html.unescape(s)  # handel & "...
    s = re.sub(r"[/\\:*?\"<>|\n\t]", '', s)  # replace illegal filename character
    return s




def delete_contents(directory):
    if os.path.exists(directory) and os.path.isdir(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # 删除文件或符号链接
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # 删除目录及其所有内容
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
    else:
        print(f"The directory {directory} does not exist or is not a directory")


def delete_contents_keep_structure(directory):
    if os.path.exists(directory) and os.path.isdir(directory):
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    os.unlink(file_path)  # 删除文件或符号链接
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                try:
                    for subdir_file in os.listdir(dir_path):
                        subdir_file_path = os.path.join(dir_path, subdir_file)
                        if os.path.isfile(subdir_file_path) or os.path.islink(subdir_file_path):
                            os.unlink(subdir_file_path)  # 删除文件或符号链接
                        elif os.path.isdir(subdir_file_path):
                            shutil.rmtree(subdir_file_path)  # 删除子目录及其所有内容
                except Exception as e:
                    print(f'Failed to clear {dir_path}. Reason: {e}')
    else:
        print(f"The directory {directory} does not exist or is not a directory")