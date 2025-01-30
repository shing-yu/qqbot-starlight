from common import logger, get_hitokoto, statics
from database import get_session, Users, CheckIn

db = get_session()


def commands_handler(openid: str, command: str, prefix: str = "\n") -> str:
    # 预处理
    command = command[1:] if command.startswith("/") else command
    command = command.split(" ")
    action = command[0]
    args = command[1:] if len(command) > 1 else []

    row = db.query(Users).filter_by(openid=openid).first()
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
                    "📖 /我的 \n查看你的个人信息、积分等等小秘密~ 📜✨ 一切尽在掌握！(๑>◡<๑)🔍\n")
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
