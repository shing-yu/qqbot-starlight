import os
from botpy import logging
import tomli as toml
from dotenv import load_dotenv

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr

load_dotenv()
MODE = os.getenv("MODE")
ID = os.getenv("ID")
SECRET = os.getenv("SECRET")
COOKIE = os.getenv("COOKIE")
CODE_URL = os.getenv("CODE_URL")

logger = logging.get_logger()


def safe_wrapper(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
            return True
        except Exception as e:
            logger.exception(e)
            return False
    return wrapper


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


smtp_host = os.getenv("SMTP_HOST")
smtp_port = int(os.getenv("SMTP_PORT"))
smtp_user = os.getenv("SMTP_USER")
smtp_name = os.getenv("SMTP_NAME")
smtp_pass = os.getenv("SMTP_PASS")

with open("template.html", "r", encoding="utf-8") as f:
    template = f.read()


@safe_wrapper
def send_code(email, subject, code, name, score, rewards):
    msg = MIMEMultipart()
    msg["From"] = formataddr((smtp_name, smtp_user))
    msg["To"] = email
    msg["Subject"] = subject
    msg.attach(MIMEText(template.replace("{{code}}", code)
                        .replace("{{name}}", name)
                        .replace("{{score}}", score)
                        .replace("{{rewards}}", rewards)
                        .replace("{{siteTitle}}", smtp_name)
                        .replace("{{activationUrl}}", CODE_URL),
                        "html"))
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, email, msg.as_string())
        logger.info(f"兑换码已发送至{email}")
    return True
