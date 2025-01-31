from common import logger, statics, send_code, COOKIE, MODE
from database import get_session, Users, CheckIn
from botpy.message import GroupMessage, C2CMessage
import asyncio
import requests

db = get_session()


def commands_handler(openid: str, command: str, _message: GroupMessage | C2CMessage, prefix: str = "\n") -> str:
    """
    指令类消息处理器
    :param openid: 从QQ消息中获取的用户openid
    :param command: 指令内容
    :param _message: 消息对象，用于部分指令中需多次/异步回复的情况
    :param prefix: 消息前缀（群聊环境设置为'\n'可改善首行显示效果）
    :return: 最后的回复消息
    """
    # 预处理
    command = command[1:] if command.startswith("/") else command
    command = command.split(" ")
    action = command[0]
    args = command[1:] if len(command) > 1 else []

    row = db.query(Users).filter_by(openid=openid).first()

    if MODE == "DEBUG" and row.role != "root":
        return "当前正在进行维护测试，请稍后再试~"
    if row is None:
        logger.info(f"未查询到用户：{openid[:4]}")
        db.add(Users(openid=openid))
        db.commit()
        row = db.query(Users).filter_by(openid=openid).first()
        logger.info(f"已自动注册用户：{openid[:4]}")

    user = row

    # 处理
    match action:
        case "ping":
            return "pong"
        case "echo":
            return "".join(args)
        case "help" | "帮助":
            return (f"{prefix}📢 指令帮助来啦！ 🌟(๑•̀ㅂ•́)و✧\n"
                    "🔁 /echo <内容> \n让机器人变成你的回声精灵！✨ 你说啥，我就说啥！🎤( •̀ ω •́ )✧\n"
                    "📅 /签到 \n每日签到，领取积分！🎁 一天不签到，心情都不好~(´；ω；`)💔\n"
                    "📝 /一言 \n随机获取一句富有哲理或有趣的句子！📜✨ 让智慧点亮你的一天！(๑•̀ㅂ•́)و✧\n"
                    "🎭 /设置昵称 <昵称> \n给自己取个响亮的名字吧！💡 你的新身份即将诞生~ (≧▽≦)🎉\n"
                    "📖 /我的 \n查看你的个人信息、积分等等小秘密~ 📜✨ 一切尽在掌握！(๑>◡<๑)🔍\n"
                    "（不需要加上<>符号哦~）（使用 /帮助2 查看更多指令）")
        case "签到":
            row = db.query(CheckIn).filter_by(uid=user.uid).first()
            if row is not None:
                return "今日已经签到过啦！🌸 别贪心哦，明天再来吧~✨ (*￣▽￣)ノ💖"
            user.rewards += 10
            db.add(CheckIn(uid=user.uid))
            db.commit()
            return "签到成功！🎉 你已收获 10积分！💰 再攒一点，就可以召唤神秘力量了哦~(✧◡✧)✨"
        case "一言":
            try:
                hitokoto, from_ = get_hitokoto()
                return f"{prefix}{hitokoto}\n——{from_}"
            except Exception as e:
                logger.error("获取一言失败", e)
                return "获取一言API失败"
        case "设置昵称":
            if len(args) < 1:
                return "哎呀！昵称不能是空气哦！☁️ 快给自己取个可爱的名字吧~ (≧▽≦)💡"
            nickname = "".join(args)
            user.nickname = nickname
            db.commit()
            return f"昵称设置成功！🎈 以后就叫 {nickname} 啦！💖 这个名字很棒呢！(๑>◡<๑)🎵"
        case "我的":
            return (f"{prefix}UID: {user.uid:08d}\n"
                    f"昵称: {user.nickname}\n"
                    f"积分: {user.rewards}\n"
                    f"角色: {user.role}")
        case "排行榜":
            rows = db.query(Users).filter(Users.role == 'user').order_by(Users.rewards.desc()).limit(10).all()
            text = f"{prefix}🏆 积分排行榜 🌟(๑•̀ㅂ•́)و✧\n"
            for i, row in enumerate(rows):
                text += f"{i+1}. {row.nickname} - {row.rewards}积分\n" \
                    if row.nickname else f"{i+1}. {row.uid:08d} - {row.rewards}积分\n"
            text += "（仅限普通用户哦~）"
            return text
        case "帮助2":
            return (f"{prefix}更多帮助来啦！ 🌟(๑•̀ㅂ•́)و✧\n"
                    "/兑换云盘 <邮箱> [机器人积分数] \n使用积分兑换星隅云盘积分，比例1:5，兑换码将发送至邮箱~📧✨\n（至少需要100积分）\n")
        case "兑换云盘":
            if len(args) < 1:
                return "参数不足"
            if user.role not in ["user", "root"]:
                return "管理员大人，您权限太高啦！👑✨ 积分兑换是给小伙伴们的福利哦~ (๑•̀ㅂ•́)و✧ 不如去监督他们有没有好好签到吧？😆"
            email = args[0]
            return cloud_handler(user, email, args[1] if len(args) > 1 else None, _message)
        case "op":
            # /op action uid args
            arrow_roles = ["admin", "root"]
            if user.role not in arrow_roles:
                return "权限不足"
            if len(args) < 2:
                return "参数不足：/op action uid args"
            return admin_handler(args[0], int(args[1]), args[2:])
        case _:
            return "未知命令"


def admin_handler(action: str, uid: int, args: list) -> str:
    user = db.query(Users).filter_by(uid=uid).first()
    if user is None:
        return f"未查询到用户：{uid:08d}"
    match action:
        case "addrewards":
            if len(args) < 1:
                return "参数不足"
            rewards = int(args[0])
            user.rewards += rewards
            db.commit()
            return f"已添加{rewards}积分 to {uid:08d}"
        case "setrole":
            if len(args) < 1:
                return "参数不足"
            role = args[0]
            user.role = role
            db.commit()
            return f"已设置角色 {role} to {uid:08d}"
        case "setname":
            if len(args) < 1:
                return "参数不足"
            nickname = "".join(args)
            user.nickname = nickname
            db.commit()
            return f"已设置昵称 {nickname} to {uid:08d}"
        case _:
            return "未知操作"


def static_handler(content: str, prefix: str = "\n") -> str:
    if content in statics:
        return prefix + statics[content]


def cloud_handler(user: Users, email: str, rewards: str, message: GroupMessage | C2CMessage) -> str:
    """
    云盘兑换处理
    :param user: 用户对象
    :param email: 用户提供的邮箱
    :param rewards: 使用的积分【可选】
    :param message: 消息对象，邮件发送过程较慢，需发送等待提示
    :return: 最后兑换结果
    """
    if rewards:
        try:
            rewards = int(rewards)
        except ValueError:
            return "参数错误"
    else:
        rewards = user.rewards
    if rewards < 100:
        return "至少需要100积分"
    if rewards > user.rewards:
        return "积分不足"
    score = rewards * 5
    user.rewards = user.rewards - rewards
    db.commit()
    logger.info(f"用户{user.uid}尝试兑换{score}云盘积分，使用{rewards}积分")
    asyncio.create_task(message.reply(content="正在兑换，请稍候..."))
    response = requests.post("https://cloud.shingyu.cn/api/v3/admin/redeem",
                             json={"id": 0, "num": 1, "time": score, "type": 2},
                             headers={"Cookie": COOKIE})
    if response.status_code != 200 or response.json()["code"] != 0:
        user.rewards = user.rewards + rewards
        db.commit()
        return "兑换失败，请联系管理员，积分已返还"
    name = user.nickname if user.nickname else f"{user.uid:08d}"
    if send_code(email, "您的云盘兑换码", response.json()["data"][0], name, str(score), str(rewards)):
        return "兑换成功，兑换码已发送至邮箱"
    else:
        user.rewards = user.rewards + rewards
        db.commit()
        return "邮件发送失败，积分已返还"


def get_hitokoto() -> tuple:
    """
    获取一言
    """
    response = requests.get("https://v1.hitokoto.cn", timeout=4.5)
    data = response.json()
    hitokoto = data["hitokoto"]
    from_ = data["from"] if data["from"] != "原创" else data["creator"]+"（原创）"
    return hitokoto, from_
