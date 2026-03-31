from common import logger, statics, assets, MODE, generate_code
from database import get_session, Users, CheckIn
from botpy.message import GroupMessage, C2CMessage
import asyncio
import requests
import random

db = get_session()


async def commands_handler(openid: str, command: str, _message: GroupMessage | C2CMessage, prefix: str = "\n") -> str:
    """
    指令类消息处理器
    :param openid: 从QQ消息中获取的用户openid
    :param command: 指令内容
    :param _message: 消息对象，用于部分指令中需多次/异步回复的情况
    :param prefix: 消息前缀（群聊环境设置为'\n'可改善首行显示效果）
    :return: 最后的回复消息
    """
    # 预处理
    original_command = command
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
        case "help" | "帮助":
            return (f"{prefix}📢 指令帮助来啦！ 🌟(๑•̀ㅂ•́)و✧\n"
                    "📅 /签到 \n每日签到，领取积分！🎁 一天不签到，心情都不好~(´；ω；`)💔\n"
                    "🐟 /摸鱼 \n随机抽取积分奖励，看看今天的运气如何？🍀✨ 快来摸一摸，大奖等着你哦！(￣▽￣)ノ\n"
                    "📝 /一言 \n随机获取一句富有哲理或有趣的句子！📜✨ 让智慧点亮你的一天！(๑•̀ㅂ•́)و✧\n"
                    "🎭 /设置昵称 <昵称> \n给自己取个响亮的名字吧！💡 你的新身份即将诞生~ (≧▽≦)🎉\n"
                    "📖 /我的 \n查看你的个人信息、积分等等小秘密~ 📜✨ 一切尽在掌握！(๑>◡<๑)🔍\n"
                    "🏆 /排行榜 \n查看积分排行榜，看看谁是最强王者！👑✨ 你也可以成为下一个冠军哦！( •̀ ω •́ )✧\n"
                    "💬 /兑换下载 <下载次数> \n兑换Starline机器人的永久下载次数，比例20:1！💰✨ （仅私聊使用）\n"
                    "（不需要加上<>符号哦~）")
        case "签到":
            row = db.query(CheckIn).filter_by(uid=user.uid).first()
            if row is not None:
                return "今日已经签到过啦！🌸 别贪心哦，明天再来吧~✨ (*￣▽￣)ノ💖"
            user.rewards += 20
            db.add(CheckIn(uid=user.uid))
            db.commit()
            return "签到成功！🎉 你已收获 10,000,000积分！💰 再攒一点，就可以召唤神秘力量了哦~(✧◡✧)✨（？？？）"
        case "摸鱼":
            row = db.query(CheckIn).filter_by(uid=user.uid).first()
            if row is None:
                return "✨ 签到完成后才能解锁幸运抽奖，快去完成签到，再来摸鱼吧！🎉(•̀ᴗ•́)"
            elif row.fished:
                return "🐟 看来你已经得到了今天的好运，明天再来碰碰运气吧！💫( ｡•̀ᴗ•́｡)"
            await _message.reply(content="🐟 你摸到了...")
            prizes = [0, 99, 50, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20]
            probabilities = [13.5, 0.81, 1.62, 23, 26, 27, 20, 42, 22, 19, 16, 12, 7, 7, 7, 7, 7, 7, 6]
            prize = random.choices(prizes, probabilities)[0]
            user.rewards += prize
            row.fished = True
            db.commit()
            await asyncio.sleep(2)
            if prize == 0:
                return prefix + assets["fishing"]["empty"]
            elif prize == 99:
                return prefix + assets["fishing"]["ultra"]
            elif prize == 50:
                return prefix + assets["fishing"]["big"]
            elif prize == 20:
                return prefix + assets["fishing"]["small"]
            else:
                res = random.choice(assets["fishing"]["normal"])
                return prefix + res.replace("{{prize}}", str(prize))
        case "摸鱼概率":
            return prefix + assets["fishing"]["probabilities"]
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
                    f"角色: {user.role}"
                    f"我就知道你会来看的，愚人节快乐！（+20积分）\n🎉(๑>◡<๑)👻")
        case "排行榜":
            rows = db.query(Users).filter(Users.role == 'user').order_by(Users.rewards.desc()).limit(10).all()
            text = f"{prefix}🏆 积分排行榜 🌟(๑•̀ㅂ•́)و✧\n"
            for i, row in enumerate(rows):
                text += f"{i+1}. {row.nickname} - {row.rewards}积分\n" \
                    if row.nickname else f"{i+1}. {row.uid:08d} - {row.rewards}积分\n"
            text += "（仅限普通用户哦~）"
            return text
        # case "帮助2":
        #     return (f"{prefix}更多帮助来啦！ 🌟(๑•̀ㅂ•́)و✧\n"
        #             "/兑换云盘 <邮箱> [机器人积分数] \n使用积分兑换星隅云盘积分，比例1:5，兑换码将发送至邮箱~📧✨\n（至少需要100积分）\n"
        #             "/摸鱼概率 \n查看摸鱼奖励的概率分布~🎣✨ 今天的大奖会不会属于你呢？(￣▽￣)ノ\n")
        case "兑换下载":
            coe = 20  # 兑换比例
            if not isinstance(_message, C2CMessage): return "请在私聊中使用此指令哦~"
            if len(args) < 1: return "请提供要兑换的下载次数~"
            if not args[0].isdigit(): return "下载次数必须是数字哦~"
            if user.role not in ["user", "root"]:
                return "管理员大人，您权限太高啦！👑✨ 积分兑换是给小伙伴们的福利哦~ (๑•̀ㅂ•́)و✧ 不如去监督他们有没有好好签到吧？😆"
            if user.rewards < coe * int(args[0]):
                return "积分不足，兑换失败！💔✨ 你可以通过签到、摸鱼等方式来获取更多积分哦~ (๑•̀ㅂ•́)و✧"
            code = generate_code(0, int(args[0]))
            user.rewards -= coe * int(args[0])
            db.commit()
            return f"兑换成功！🎉 \n兑换码：{code}"
        case "op":
            # /op action uid args
            arrow_roles = ["admin", "root"]
            if user.role not in arrow_roles:
                return "权限不足"
            if len(args) < 2:
                return "参数不足：/op action uid args"
            return admin_handler(args[0], int(args[1]), args[2:])
        case _:
            return static_handler(original_command, prefix=prefix)


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


def static_handler(content: str, prefix: str = "\n") -> str | None:
    if content in statics:
        return prefix + statics[content]
    return None


def get_hitokoto() -> tuple:
    """
    获取一言
    """
    response = requests.get("https://v1.hitokoto.cn", timeout=4.5)
    data = response.json()
    hitokoto = data["hitokoto"]
    from_ = data["from"] if data["from"] != "原创" else data["creator"]+"（原创）"
    return hitokoto, from_
