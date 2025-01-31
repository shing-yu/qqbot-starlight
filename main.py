import botpy
from common import logger, ID, SECRET
from handlers import commands_handler, static_handler
from botpy.message import GroupMessage, C2CMessage


class MyClient(botpy.Client):
    async def on_ready(self):
        logger.info(f"机器人{self.robot.name}已启动")

    @staticmethod
    async def on_group_at_message_create(message: GroupMessage):
        content = message.content[1:] if message.content.startswith(" ") else message.content
        logger.info(f"{message.group_openid}||{message.author.member_openid}||{content}")
        if content.startswith("/"):
            result = await commands_handler(message.author.member_openid, content, message)
            await message.reply(content=result)
        else:
            result = static_handler(content)
            if result:
                await message.reply(content=result)

    @staticmethod
    async def on_c2c_message_create(message: C2CMessage):
        content = message.content[1:] if message.content.startswith(" ") else message.content
        logger.info(f"C2C||{message.author.user_openid}||{content}")
        if content.startswith("/"):
            result = await commands_handler(message.author.user_openid, content, message, prefix="")
            await message.reply(content=result)
        else:
            result = static_handler(content, prefix="")
            if result:
                await message.reply(content=result)


if __name__ == "__main__":
    intents = botpy.Intents.all()
    client = MyClient(intents=intents)
    client.run(appid=ID, secret=SECRET)
