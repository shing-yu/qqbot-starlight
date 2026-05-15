# 开发备注
# 相同msg_id和msg_seq的消息会被去重，故最后回复的消息默认设置为了100
import botpy
from common import logger, ID, SECRET
from handlers import commands_handler
from botpy.message import GroupMessage, C2CMessage

intents = botpy.Intents.all()
client = botpy.Client(intents=intents)

@client.on("ready")
async def on_ready():
    logger.info(f"机器人已启动")

@client.on("group_at_message_create")
async def on_group_at_message_create(message: GroupMessage):
    content = message.content.lstrip(" ")
    logger.info(f"{message.group_openid}||{message.author.member_openid}||{content}")
    # await message.reply(content="\n请私聊使用机器人功能哦~", msg_seq=100)
    result = await commands_handler(message.author.member_openid, content, message)
    if result:
        await message.reply(content=result, msg_seq=100)

@client.on("group_message_create")
async def on_group_message_create(message: GroupMessage):
    content = message.content.lstrip(" ")
    logger.info(f"{message.group_openid}||{message.author.member_openid}||{content}")
    # await message.reply(content="\n请私聊使用机器人功能哦~", msg_seq=100)
    result = await commands_handler(message.author.member_openid, content, message, prefix="")
    if result:
        await message.reply(content=result, msg_seq=100, at_user=True)

@client.on("c2c_message_create")
async def on_c2c_message_create(message: C2CMessage):
    content = message.content.lstrip(" ")
    logger.info(f"C2C||{message.author.user_openid}||{content}")
    result = await commands_handler(message.author.user_openid, content, message, prefix="")
    if result:
        await message.reply(content=result, msg_seq=100)


if __name__ == "__main__":
    client.run(appid=ID, secret=SECRET)
