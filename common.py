import os
from botpy import logging
import tomli as toml
from dotenv import load_dotenv

import hmac
import hashlib
import base64
import secrets

load_dotenv()
MODE = os.getenv("MODE")
ID = os.getenv("ID")
SECRET = os.getenv("SECRET")
CODE_SECRET = os.getenv("CODE_SECRET")

logger = logging.get_logger()

try:
    with open("static.toml", "r", encoding="utf-8") as f:
        # 读取静态自动回复
        statics = toml.loads(f.read())
except FileNotFoundError:
    statics = {}

try:
    with open("assets/assets.toml", "r", encoding="utf-8") as f:
        # 读取回复资源
        assets = toml.loads(f.read())
except FileNotFoundError:
    raise FileNotFoundError("assets.toml 不存在")


def generate_code(identifier: int, number: int):
    secret_key = CODE_SECRET
    # 校验输入
    if identifier not in (0, 1):
        raise ValueError("类型必须是0或1")
    if not (0 <= number <= 999999):
        raise ValueError("额度必须在0-999999范围内")

    # 转换为字母标识
    type_char = 'A' if identifier == 0 else 'B'

    # 生成6位数字字符串
    data_str = f"{number:06d}"

    # 生成8位随机盐
    salt = secrets.token_hex(4).upper()

    # 构造签名数据
    raw_data = f"{type_char}{data_str}{salt}"
    digest = hmac.new(secret_key.encode(), raw_data.encode(), hashlib.sha256).digest()

    # 生成校验码（Base64去符号处理）
    checksum = base64.b64encode(digest).decode()[:10]
    checksum = checksum.replace('+', 'X').replace('/', 'Y').upper()

    return f"{type_char}{data_str}{salt}{checksum}"
