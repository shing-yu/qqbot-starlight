from botpy import logging
import requests
import tomli as toml

logger = logging.get_logger()

try:
    with open("static.toml", "r", encoding="utf-8") as f:
        # 读取静态自动回复
        statics = toml.loads(f.read())
except FileNotFoundError:
    statics = {}


def get_hitokoto() -> tuple:
    """
    获取一言
    """
    response = requests.get("https://v1.hitokoto.cn", timeout=4.5)
    data = response.json()
    hitokoto = data["hitokoto"]
    from_ = data["from"] if data["from"] != "原创" else data["creator"]+"（原创）"
    return hitokoto, from_
