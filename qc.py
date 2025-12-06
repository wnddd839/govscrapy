import asyncio
import sys
import aiohttp
import csv
import re
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin

# 配置参数
INPUT_CSV = "政务公开信息.csv"  # 输入CSV文件路径（包含子链接的列名应为'url'）
OUTPUT_CSV = "output_results.csv"  # 输出结果CSV路径
RETRY_TIMES = 2  # 重试次数
CONCURRENT_LIMIT = 3  # 并发限制

# 提取附件URL的正则表达式
ATTACHMENT_PATTERN = re.compile(r'href="(.*?\.(?:xls|xlsx|pdf|doc|docx|zip|rar))"', re.IGNORECASE)

async def fetch(session, url, semaphore):
    """异步请求网页内容"""
    async with semaphore:
        try:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    return await response.text()
                print(f"请求失败: {url} (状态码: {response.status})")
                return None
        except Exception as e:
            print(f"请求异常: {url} - {str(e)}")
            return None

def clean_html(content):
    """清洗HTML内容，提取div#font内的文本"""
    if not content:
        return ""
    soup = BeautifulSoup(content, "html.parser")
    font_div = soup.find("div", id="font")
    if not font_div:
        return ""
    
    # 移除脚本和样式
    for script in font_div(["script", "style"]):
        script.decompose()
    
    # 提取文本并清洗
    text = font_div.get_text(separator="\n", strip=True)
    # 去除多余空行
    return re.sub(r'\n+', '\n', text)

def extract_attachments(content, base_url):
    """提取附件URL"""
    if not content:
        return []
    attachments = []
    # 从HTML中提取链接
    soup = BeautifulSoup(content, "html.parser")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if any(ext in href.lower() for ext in ['.xls', '.xlsx', '.pdf', '.doc', '.docx', '.zip', '.rar']):
            # 补全相对URL
            full_url = urljoin(base_url, href)
            attachments.append(full_url)
    return list(set(attachments))  # 去重

async def process_url(session, url, semaphore):
    """处理单个URL"""
    # 多次重试
    for attempt in range(RETRY_TIMES + 1):
        html = await fetch(session, url, semaphore)
        if html:
            content = clean_html(html)
            attachments = extract_attachments(html, url)
            return {
                "url": url,
                "content": content,
                "attachments": ", ".join(attachments),
                "status": "success"
            }
        elif attempt < RETRY_TIMES:
            print(f"重试 {url} (第{attempt+1}次)")
            await asyncio.sleep(1)  # 重试间隔
    
    return {
        "url": url,
        "content": "",
        "attachments": "",
        "status": "failed"
    }

async def main():
    # 读取输入CSV
    input_links = []
    if not Path(INPUT_CSV).exists():
        print(f"输入文件 {INPUT_CSV} 不存在")
        return
    
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "url" not in reader.fieldnames:
            print("输入CSV必须包含'url'列")
            return
        input_links = [row["url"] for row in reader]
    
    if not input_links:
        print("没有需要处理的链接")
        return
    
    # 异步处理所有链接
    semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)
    async with aiohttp.ClientSession() as session:
        tasks = [process_url(session, url, semaphore) for url in input_links]
        results = await asyncio.gather(*tasks)
    
    # 处理失败的链接（二次重试）
    failed_urls = [res["url"] for res in results if res["status"] == "failed"]
    if failed_urls:
        print(f"\n开始二次重试 {len(failed_urls)} 个失败链接")
        tasks = [process_url(session, url, semaphore) for url in failed_urls]
        retry_results = await asyncio.gather(*tasks)
        
        # 更新结果
        for retry_res in retry_results:
            for i, res in enumerate(results):
                if res["url"] == retry_res["url"]:
                    results[i] = retry_res
                    break
    
    # 写入输出CSV
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["url", "content", "attachments", "status"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n处理完成，结果已写入 {OUTPUT_CSV}")
    success_count = sum(1 for res in results if res["status"] == "success")
    print(f"成功: {success_count}/{len(results)}, 失败: {len(results)-success_count}")

if __name__ == "__main__":
    # 解决Windows事件循环问题
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())