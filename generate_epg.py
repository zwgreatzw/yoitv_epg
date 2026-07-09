import json
import urllib.request
import datetime
from xml.sax.saxutils import escape

# 你的源数据接口
API_URL = "http://live.yoitv.com:9083/api?action=listLives&cid=3140463FA6B2AC641D4D63F9534B6D94&uid=C2D9261F3D5753E74E97EB28FE2D8B26&details=0&page_size=200&sort=no%20asc&sort=created_time%20desc&type=video&no_epg=0&referer=http%3A%2F%2Fplay.yoitv.com"

def format_time(ts):
    # 将时间戳转换为 XMLTV 标准的 UTC 格式
    return datetime.datetime.utcfromtimestamp(ts).strftime('%Y%m%d%H%M%S +0000')

def main():
    print("正在拉取 JSON 数据...")
    req = urllib.request.Request(API_URL)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))

    channels = data.get('result', [])
    
    xml_out = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_out.append('<!DOCTYPE tv SYSTEM "xmltv.dtd">')
    # 按照你给的格式，这里加上 generator-info-name
    xml_out.append('<tv generator-info-name="CF-Worker-EPG-Merged">')

    print(f"成功获取 {len(channels)} 个频道，正在生成 XML...")

    # 1. 生成所有的 <channel> 标签
    for ch in channels:
        # 为了方便对应，这里我们直接用频道的名字（如：日テレ）作为 ID
        ch_name = escape(ch.get('name', '未知频道'))
        
        xml_out.append(f'  <channel id="{ch_name}">')
        xml_out.append(f'    <display-name>{ch_name}</display-name>')
        xml_out.append(f'    <icon src=""/>') # 补充空图标标签，防止解析报错
        xml_out.append(f'    <url></url>')    # 补充空URL标签
        xml_out.append('  </channel>')

    # 2. 生成所有的 <programme> 标签
    for ch in channels:
        ch_name = escape(ch.get('name', '未知频道'))
        epg_raw = ch.get('record_epg', '[]')
        
        if not epg_raw:
            continue
        
        # record_epg 在 JSON 中是字符串，需要二次解析
        try:
            epg_list = json.loads(epg_raw)
        except json.JSONDecodeError:
            continue
            
        for i in range(len(epg_list)):
            prog = epg_list[i]
            start_ts = prog.get('time', 0)
            title = escape(prog.get('title', '未知节目'))
            
            if start_ts == 0:
                continue
                
            # 计算结束时间：当前节目结束时间 = 下一个节目的开始时间
            if i < len(epg_list) - 1:
                stop_ts = epg_list[i+1]['time']
            else:
                # 最后一个节目，默认给 1 个小时的时长
                stop_ts = start_ts + 3600
                
            start_str = format_time(start_ts)
            stop_str = format_time(stop_ts)
            
            xml_out.append(f'  <programme start="{start_str}" stop="{stop_str}" channel="{ch_name}">')
            xml_out.append(f'    <title lang="ja">{title}</title>')
            # 兼容性处理：把 title 复制一份给 desc，防止播放器因为缺少 desc 报错
            xml_out.append(f'    <desc lang="ja">{title}</desc>')
            # 兼容性处理：补上 category 标签
            xml_out.append(f'    <category lang="ja">一般</category>')
            xml_out.append('  </programme>')

    xml_out.append('</tv>')

    # 写入文件
    with open('epg.xml', 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_out))
        
    print("恭喜，epg.xml 生成完毕！")

if __name__ == "__main__":
    main()
