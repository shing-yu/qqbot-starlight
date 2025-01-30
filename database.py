from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from apscheduler.schedulers.background import BackgroundScheduler
from common import logger

Base = declarative_base()


class Users(Base):
    __tablename__ = "users"
    uid: Column = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    openid: Column = Column(String(100), unique=True, nullable=False)
    nickname: Column = Column(String(100))
    role: Column = Column(String(100), default="user")
    rewards: Column = Column(Integer, default=0)


class CheckIn(Base):
    __tablename__ = "checkin"
    uid: Column = Column(Integer, primary_key=True, nullable=False)


engine = create_engine("sqlite:///data.db", echo=False, isolation_level="READ UNCOMMITTED")

Base.metadata.create_all(engine)


def get_session():
    session = sessionmaker(bind=engine)
    return session()


# 定时清空签到表
def clear_checkin():
    db = get_session()
    db.query(CheckIn).delete()
    db.commit()
    logger.info("签到表已清空")


scheduler = BackgroundScheduler()
scheduler.add_job(clear_checkin, "cron", hour=0, minute=0)
scheduler.start()
