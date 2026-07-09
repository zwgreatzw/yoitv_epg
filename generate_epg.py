import json
import urllib.request
import datetime
import gzip  # 新增：引入解压缩模块
from xml.sax.saxutils import escape

# 你的源数据接口
API_URL = "http://live.yoitv.com:9083/api?action=listLives&cid=3140463FA6B2AC641D4D63F9534B6D94&uid=C2D9261F3D5753E74E97EB28FE2D8B26&details=0&page_size=200&sort=no%20asc&sort=created_time%20desc&type=video&no_epg=0&referer=http%3A%2F%2Fplay.yoitv.com"

def format_time(ts):
    # 将时间戳转换为 XMLTV 标准的 UTC 格式
    return datetime.datetime.utcfromtimestamp(ts).strftime('%Y%m%d%H%M%S +0000')

def main():
    print("正在拉取 JSON 数据...")
    
    # 新增：伪装成正常的电脑浏览器，并告诉服务器我们接受 gzip 压缩
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate'
    }
    req = urllib.request.Request(API_URL, headers=headers)
    
    with urllib.request.urlopen(req) as response:
        # 新增：判断服务器返回的数据是否被 gzip 压缩过
        if response.info().get('Content-Encoding') == 'gzip':
            print("检测到 GZIP 压缩，正在解压数据...")
            f = gzip.GzipFile(fileobj=response)
            data = json.loads(f.read().decode('utf-8'))
        else:
            data = json.loads(response.read().decode('utf-8'))

    channels = data.get('result', [])
    
    xml_out = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_out.append('<!DOCTYPE tv SYSTEM "xmltv.dtd">')
    xml_out.append('<tv generator-info-name="CF-Worker-EPG-Merged">')

    print(f"成功获取 {len(channels)} 个频道，正在生成 XML...")

    # 1. 生成所有的 <channel> 标签
    for ch in channels:
        ch_name = escape(ch.get('name', '未知频道'))
        
        xml_out.append(f'  <channel id="{ch_name}">')
        xml_out.append(f'    <display-name>{ch_name}</display-name>')
        xml_out.append(f'    <icon src=""/>')
        xml_out.append(f'    <url></url>')
        xml_out.append('  </channel>')

    # 2. 生成所有的 <programme> 标签
    for ch in channels:
        ch_name = escape(ch.get('name', '未知频道'))
        epg_raw = ch.get('record_epg', '[]')
        
        if not epg_raw:
            continue
        
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
                
            if i < len(epg_list) - 1:
                stop_ts = epg_list[i+1]['time']
            else:
                stop_ts = start_ts + 3600
                
            start_str = format_time(start_ts)
            stop_str = format_time(stop_ts)
            
            xml_out.append(f'  <programme start="{start_str}" stop="{stop_str}" channel="{ch_name}">')
            xml_out.append(f'    <title lang="ja">{title}</title>')
            xml_out.append(f'    <desc lang="ja">{title}</desc>')
            xml_out.append(f'    <category lang="ja">一般</category>')
            xml_out.append('  </programme>')

    xml_out.append('</tv>')

    with open('epg.xml', 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml_out))
        
    print("恭喜，epg.xml 生成完毕！")

if __name__ == "__main__":
    main()
