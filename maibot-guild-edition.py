#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from collections import defaultdict
from itertools import count
import json
import os.path
from posixpath import split
import threading
from typing import Dict, List
import re 
import aiohttp
import qqbot

from src.libraries.tool import hash
from src.libraries.maimaidx_music import *
from src.libraries.image import *
from src.libraries.maimai_best_40 import generate
from src.libraries.maimai_best_50 import generate50

from qqbot.core.util.yaml_util import YamlUtil
from qqbot.model.message import MessageEmbed, MessageEmbedField, MessageEmbedThumbnail, CreateDirectMessageRequest, \
    MessageArk, MessageArkKv, MessageArkObj, MessageArkObjKv

test_config = YamlUtil.read(os.path.join(os.path.dirname(__file__), "config.yaml"))
music_aliases = defaultdict(list)
f = open('src/static/aliases.csv', 'r', encoding='utf-8')
tmp = f.readlines()
f.close()
for t in tmp:
    arr = t.strip().split('\t')
    for i in range(len(arr)):
        if arr[i] != "":
            music_aliases[arr[i].lower()].append(arr[0])

def song_txt(music: Music):
    return Message([
        {
            "type": "text",
            "data": {
                "text": f"{music.id}. {music.title}\n"
            }
        },
        {
            "type": "image",
            "data": {
                "file": f"https://www.diving-fish.com/covers/{music.id}.jpg"
            }
        },
        {
            "type": "text",
            "data": {
                "text": f"\n{'/'.join(music.level)}"
            }
        }
    ])
def inner_level_q(ds1, ds2=None):
    result_set = []
    diff_label = ['Bas', 'Adv', 'Exp', 'Mst', 'ReM']
    if ds2 is not None:
        music_data = total_list.filter(ds=(ds1, ds2))
    else:
        music_data = total_list.filter(ds=ds1)
    for music in sorted(music_data, key = lambda i: int(i['id'])):
        for i in music.diff:
            result_set.append((music['id'], music['title'], music['ds'][i], diff_label[i], music['level'][i]))
    return result_set

wm_list = ['拼机', '推分', '越级', '下埋', '夜勤', '练底力', '练手法', '打旧框', '干饭', '抓绝赞', '收歌']

async def _message_handler(event, message: qqbot.Message):
    """
    定义事件回调的处理

    :param event: 事件类型
    :param message: 事件对象（如监听消息是Message对象）
    """
    msg_api = qqbot.AsyncMessageAPI(t_token, False)
    # 打印返回信息
    content = message.content
    qqbot.logger.info("event %s" % event + ",receive message %s" % content)
    if "/随机 " in content:
        split = content.split("/随机 ")
        music_data = total_list.filter(level=split)
        if len(music_data) == 0:
            rand_result = "没有这样的乐曲哦。"
        #else:
            #rand_result = song_txt(music_data.random())
        else:
            result = music_data.random()
            text1 = result["id"]+" "+result["title"]+f'\n{"/".join(result["level"])}'
            imge = "https://www.diving-fish.com/covers/"+result["id"]+".jpg"
        msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content=text1,image=imge)
        await msg_api.post_message(message.channel_id,msgtosend)
    
    if "/定数查歌 " in content:
        argv = content.split("/定数查歌 ")
        result_set = inner_level_q(float(str(argv[1])))
        if len(result_set) > 80:
            s=f"结果过多（{len(result_set)} 条），请缩小搜索范围。"
            msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content=s)
            await msg_api.post_message(message.channel_id,msgtosend)
            return
        s= ""
        for elem in result_set:
            s += f"{elem[0]}. {elem[1]} {elem[3]} {elem[4]}({elem[2]})\n"
        msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content=s)
        await msg_api.post_message(message.channel_id,msgtosend)

    if "/今日舞萌" in content:
        qid = int(message.author.id)
        h = hash(qid)
        rp = h % 100
        wm_value = []
        for i in range(11):
            wm_value.append(h & 3)
            h >>= 2
        s = f"今日人品值：{rp}\n"
        for i in range(11):
            if wm_value[i] == 3:
                s += f'宜 {wm_list[i]}\n'
            elif wm_value[i] == 0:
                s += f'忌 {wm_list[i]}\n'
        s += "TritiumBot提醒您：打机时不要大力拍打或滑动哦\n今日推荐歌曲："
        music = total_list[h % len(total_list)]
        text1= s+music["id"]+"."+music["title"]+"\n"+f'\n{"/".join(music["level"])}'
        imge = "https://www.diving-fish.com/covers/"+music["id"]+".jpg"
        msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content=text1,image=imge)
        await msg_api.post_message(message.channel_id,msgtosend)
    if "/help" in content:
        help_str = '''可用命令如下：
/今日舞萌 查看今天的舞萌运势
/随机 <难度> 随机一首指定条件的乐曲 例如：随机 13
/查歌<乐曲标题的一部分> 查询符合条件的乐曲 例如：查歌 六兆年
/id<歌曲编号> 查询乐曲信息或谱面信息 例如：id288
/模糊查歌 <歌曲别名> 查询乐曲别名对应的乐曲 例如：模糊查歌 牛奶
/定数查歌 <定数>  查询定数对应的乐曲
/b40 [玩家id] 查询玩家查分器数据
/b50 [玩家id] 查询玩家splash查分器数据
此bot基于Diving-Fish/mai-bot项目修改'''
        msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content=help_str)
        await msg_api.post_message(message.channel_id,msgtosend)


    if "/青野" in content:
        msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content="烧🔥🔥🔥🥵🥵🥵🥵",image="https://s3.bmp.ovh/imgs/2022/04/10/2105589093d4af5a.jpg")
        await msg_api.post_message(message.channel_id,msgtosend)
    

    if "/查歌 " in content:
        argv = content.split("/查歌 ")
        name = str(argv[1])
        if name == "":
            return
        res = total_list.filter(title_search=name)
        if len(res) == 0:
            s = "没有找到这样的乐曲。"
            msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content=s)
            await msg_api.post_message(message.channel_id,msgtosend)
        elif len(res) < 80:
            search_result = ""
            for music in sorted(res, key = lambda i: int(i['id'])):
                search_result += f"{music['id']}. {music['title']}\n"
            msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content=search_result)
            await msg_api.post_message(message.channel_id,msgtosend)
        else:
            s=f"结果过多（{len(res)} 条），请缩小查询范围。"
            msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content=s)
            await msg_api.post_message(message.channel_id,msgtosend)
    

    if "/id " in content:
        argv = content.split("/id ")
        res = argv[1].split(" ")
        musicid = res[0]
        if len(res) != 2 :
            musicdiff =""
        else:
            musicdiff = res[1]
        level_labels = ['绿', '黄', '红', '紫', '白']
        qqbot.logger.info(str(res))
        if musicdiff != "":
            try:
                level_index = level_labels.index(musicdiff)
                level_name = ['Basic', 'Advanced', 'Expert', 'Master', 'Re: MASTER']
                name = musicid
                music = total_list.by_id(name)
                chart = music['charts'][level_index]
                ds = music['ds'][level_index]
                level = music['level'][level_index]
                file = f"https://www.diving-fish.com/covers/{music['id']}.jpg"
                if len(chart['notes']) == 4:
                    msg = f'''{level_name[level_index]} {level}({ds})
    TAP: {chart['notes'][0]}
    HOLD: {chart['notes'][1]}
    SLIDE: {chart['notes'][2]}
    BREAK: {chart['notes'][3]}
    谱师: {chart['charter']}'''
                else:
                     msg = f'''{level_name[level_index]} {level}({ds})
    TAP: {chart['notes'][0]}
    HOLD: {chart['notes'][1]}
    SLIDE: {chart['notes'][2]}
    TOUCH: {chart['notes'][3]}
    BREAK: {chart['notes'][4]}
    谱师: {chart['charter']}'''
                text1=music["id"]+"."+music["title"]+"\n"+msg
                msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content=text1,image=file)
                await msg_api.post_message(message.channel_id,msgtosend)
            except Exception:
                msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content="未找到该谱面")
        else:
            name = musicid
            music = total_list.by_id(name)
            try:
                file = f"https://www.diving-fish.com/covers/{music['id']}.jpg"
                text1 = music["id"]+"."+music["title"]+f"\n艺术家: {music['basic_info']['artist']}\n分类: {music['basic_info']['genre']}\nBPM: {music['basic_info']['bpm']}\n版本: {music['basic_info']['from']}\n难度: {'/'.join(music['level'])}"
                msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content=text1,image=file)
                await msg_api.post_message(message.channel_id,msgtosend)
            except Exception:
                msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content="未找到该谱面")
                await msg_api.post_message(message.channel_id,msgtosend)
    if "/b40 "in content:
        username = content.split("/b40 ")
        payload = {'username': username[1]}
        img, success = await generate(payload)
        if success == 400:
            text1="未找到此玩家，请确保此玩家的用户名和查分器中的用户名相同。"
            msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content=text1)
            await msg_api.post_message(message.channel_id,msgtosend)
        elif success == 403:
            text1="该用户禁止了其他人获取数据。"
            msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content=text1)
            await msg_api.post_message(message.channel_id,msgtosend)
        else:
            msgtosend = qqbot.MessageSendRequest(msg_id=message.id,image="http://120.53.228.242/temp.png")
            await msg_api.post_message(message.channel_id,msgtosend)
    if "/b50 "in content:
        username = content.split("/b50 ")
        payload = {'username': username[1],'b50':  True}
        img, success = await generate50(payload)
        if success == 400:
            text1="未找到此玩家，请确保此玩家的用户名和查分器中的用户名相同。"
            msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content=text1)
            await msg_api.post_message(message.channel_id,msgtosend)
        elif success == 403:
            text1="该用户禁止了其他人获取数据。"
            msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content=text1)
            await msg_api.post_message(message.channel_id,msgtosend)
        else:
            msgtosend = qqbot.MessageSendRequest(msg_id=message.id,image="http://120.53.228.242/temp50.png")
            await msg_api.post_message(message.channel_id,msgtosend)
    if "/模糊查歌 " in content:
        argv = content.split("/模糊查歌 ")
        if argv[1] not in music_aliases:
            text1="未找到此歌曲\n舞萌 DX 歌曲别名收集计划：https://docs.qq.com/sheet/DVFhLellwYUJKZnJp"
            return
        result_set = music_aliases[argv[1]]
        if len(result_set) == 1:
            music = total_list.by_title(result_set[0])
            text1 = "您要找的是不是：\n"+music["id"]+"."+music["title"]+f'\n{"/".join(music["level"])}'
            imge = "https://www.diving-fish.com/covers/"+music["id"]+".jpg"
            msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content=text1,image=imge)
            await msg_api.post_message(message.channel_id,msgtosend)
        else:
            s = '\n'.join(result_set)
            text1=f"您要找的可能是以下歌曲中的其中一首：\n{ s }"
            msgtosend = qqbot.MessageSendRequest(msg_id=message.id,content=text1)
            await msg_api.post_message(message.channel_id,msgtosend)

    
if __name__ == "__main__":
    # async的异步接口的使用示例
    t_token = qqbot.Token(test_config["token"]["appid"], test_config["token"]["token"])
    qqbot_handler = qqbot.Handler(
        qqbot.HandlerType.AT_MESSAGE_EVENT_HANDLER, _message_handler
    )
    qqbot.async_listen_events(t_token, False, qqbot_handler)
