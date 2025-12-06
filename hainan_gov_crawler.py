import requests
from bs4 import BeautifulSoup
import time
import random
import csv
from datetime import datetime
import os

# 基础URL（分页规则：第1页list3.shtml，第2页起list3_页码.shtml）
base_url = "https://www.hainan.gov.cn/hainan/gwyzk/list3{}.shtml"

# 请求头（使用浏览器真实UA，避免被拦截）
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# 爬取页数
total_pages = 10

# CSV文件名
csv_filename = "政务公开信息.csv"

# 存储所有有效数据（含历史数据+新爬取数据）
all_data = []
# 去重集合（基于链接）
existing_urls = set()

def load_existing_data():
    """加载已存在的数据"""
    global all_data, existing_urls
    
    # 创建数据目录（如果不存在）
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # 文件路径
    file_path = os.path.join(data_dir, csv_filename)
    
    # 读取历史数据（若有）
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader)  # 跳过表头
            for row in reader:
                if len(row) >= 3 and row[2]:
                    title, publish_time, sub_url = row[0].strip(), row[1].strip(), row[2].strip()
                    all_data.append([title, publish_time, sub_url])
                    existing_urls.add(sub_url)
        print(f"已加载 {len(all_data)} 条历史数据")
    except FileNotFoundError:
        print("未找到历史数据文件，将创建新文件")
    except Exception as e:
        print(f"读取历史数据失败：{str(e)}")

def crawl_page(page):
    """爬取单个页面"""
    url = base_url.format("" if page == 1 else f"_{page}")
    max_retries = 1  # 最多重试1次
    retry_count = 0  # 当前重试次数
    
    while retry_count <= max_retries:
        try:
            # 请求间隔（8-9秒）
            time.sleep(random.uniform(8, 9))
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = "utf-8"
            soup = BeautifulSoup(response.text, "html.parser")
            
            div_list = soup.find_all("div", class_=["list_div", "mar-top2"])
            page_data = []
            
            for div in div_list:
                # 提取标题
                title_div = div.find("div", class_=["list-right_title", "fon_1"])
                if not title_div:
                    continue
                title_tag = title_div.find("a")
                title = title_tag.text.strip() if title_tag else ""
                
                # 提取子链接
                sub_url = title_tag["href"] if (title_tag and "href" in title_tag.attrs) else ""
                if sub_url.startswith("/"):
                    sub_url = f"https://www.hainan.gov.cn{sub_url}"
                
                # 提取发布时间
                time_td = div.find("td", attrs={"width": "50%", "align": "left"})
                publish_time = time_td.text.replace("发布时间：", "").strip() if time_td else ""
                
                # 去重 + 数据有效性校验
                if title and publish_time and sub_url and sub_url not in existing_urls:
                    print(f"标题：{title}")
                    print(f"发布时间：{publish_time}")
                    print(f"链接：{sub_url}")
                    print("-" * 80)
                    
                    page_data.append([title, publish_time, sub_url])
                    existing_urls.add(sub_url)
            
            # 爬取成功，返回数据
            print(f"\n第{page}页爬取成功！")
            return page_data
        
        except Exception as e:
            retry_count += 1
            if retry_count <= max_retries:
                # 重试前等待20秒
                print(f"\n第{page}页爬取失败（{retry_count}/{max_retries}）：{str(e)}")
                print(f"将在20秒后重新请求第{page}页...")
                time.sleep(20)  # 固定等待20秒重试
            else:
                # 重试次数用尽，跳过该页
                print(f"\n第{page}页重试次数用尽，爬取失败：{str(e)}")
                return []

def sort_by_publish_time(row):
    """按发布时间排序"""
    try:
        return datetime.strptime(row[1], "%Y-%m-%d")
    except:
        return datetime.min

def save_data():
    """保存数据到CSV文件"""
    # 按发布时间排序（降序）
    all_data.sort(key=sort_by_publish_time, reverse=True)
    
    # 创建数据目录（如果不存在）
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # 文件路径
    file_path = os.path.join(data_dir, csv_filename)
    
    # 覆盖写入CSV
    with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["标题", "发布时间", "链接"])
        writer.writerows(all_data)
    
    print(f"\n爬取完成！共获取{len(all_data)}条有效数据（已去重+按发布时间排序），保存至：{file_path}")

def main():
    """主函数"""
    print("开始爬取海南省政务公开信息...")
    
    # 加载历史数据
    load_existing_data()
    
    # 爬取新数据
    for page in range(1, total_pages + 1):
        print(f"\n正在爬取第{page}页...")
        page_data = crawl_page(page)
        all_data.extend(page_data)
    
    # 保存数据
    save_data()

if __name__ == "__main__":
    main()