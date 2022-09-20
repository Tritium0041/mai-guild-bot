import random
import re

from PIL import Image
from nonebot import on_command, on_message, on_notice, require, get_driver, on_regex
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Message, Event, Bot
from src.libraries.image import *
from random import randint


help = on_command('help')


@help.handle()
async def _(bot: Bot, event: Event, state: T_State):
    help_str = '''可用命令如下：
今日舞萌 查看今天的舞萌运势
XXXmaimaiXXX什么 随机一首歌
随机[dx/标准][绿黄红紫白]<难度> 随机一首指定条件的乐曲 例如：随机dx紫13
查歌<乐曲标题的一部分> 查询符合条件的乐曲 例如：查歌 六兆年
[绿黄红紫白]id<歌曲编号> 查询乐曲信息或谱面信息 例如：紫id288
<歌曲别名>是什么歌 查询乐曲别名对应的乐曲 例如：牛奶是什么歌
定数查歌 <定数>  查询定数对应的乐曲
定数查歌 <定数下限> <定数上限>
分数线 <难度+歌曲id> <分数线> 详情请输入“分数线 帮助”查看
b40 [玩家id] 查询玩家查分器数据
天气XX 查询当地天气 例如：天气济南
点歌 点歌插件
此bot基于Diving-Fish/mai-bot项目修改 遵循MIT协议'''
    await help.send(Message([{
        "type": "image",
        "data": {
            "file": f"base64://{str(image_to_base64(text_to_image(help_str)), encoding='utf-8')}"
        }
    }]))


async def _group_poke(bot: Bot, event: Event, state: dict) -> bool:
    value = (event.notice_type == "notify" and event.sub_type == "poke" and event.target_id == int(bot.self_id))
    return value


poke = on_notice(rule=_group_poke, priority=10, block=True)


@poke.handle()
async def _(bot: Bot, event: Event, state: T_State):
    if event.__getattribute__('group_id') is None:
        event.__delattr__('group_id')
    await poke.send(Message([{
        "type": "poke",
        "data": {
            "qq": f"{event.sender_id}"
        }
    }]))

