import redis
import json
from datetime import datetime

# Redis连接配置
REDIS_CONFIG = {
    'host': '8.138.24.168',
    'port': 6379,
    'password': '123456',
    'db': 0,
    'decode_responses': True
}

def connect_redis():
    """连接到Redis"""
    try:
        r = redis.Redis(**REDIS_CONFIG)
        r.ping()  # 测试连接
        print("✅ 成功连接到Redis服务器")
        return r
    except Exception as e:
        print(f"❌ 连接Redis失败: {e}")
        return None

def show_crawled_data(r):
    """显示爬虫相关的数据"""
    # 查找所有以crawl:data:开头的键
    keys = r.keys("crawl:data:*")
    print(f"\n🔍 找到 {len(keys)} 个数据键")
    
    # 查看待处理的数据ID
    pending_ids = r.smembers("crawl:pending:ids")
    print(f"\n⏳ 待处理数据ID数量: {len(pending_ids)}")
    
    # 显示最近几条数据的详细信息
    if keys:
        print("\n📄 最近几条数据详情:")
        # 按键名排序，获取最新的几个
        recent_keys = sorted(keys)[-5:]  # 获取最后5个
        
        for i, key in enumerate(recent_keys, 1):
            try:
                # 检查键的类型
                key_type = r.type(key)
                print(f"\n--- 数据 {i} (类型: {key_type}) ---")
                print(f"键名: {key}")
                
                if key_type == 'hash':
                    data = r.hgetall(key)
                    # 显示重要字段
                    print(f"标题: {data.get('title', 'N/A')}")
                    print(f"发布时间: {data.get('publishDate', 'N/A')}")
                    print(f"来源URL: {data.get('sourceUrl', 'N/A')}")
                    print(f"分类: {data.get('category', 'N/A')}")
                    print(f"地区: {data.get('region', 'N/A')}")
                    print(f"来源机构: {data.get('sourceOrg', 'N/A')}")
                    
                    # 显示附件信息
                    attachments_json = data.get('attachments', '[]')
                    try:
                        attachments = json.loads(attachments_json)
                        if attachments:
                            print("📎 附件:")
                            for att in attachments[:5]:  # 显示前5个附件
                                print(f"  • {att.get('name', '未知')} ({att.get('type', '未知类型')})")
                            if len(attachments) > 5:
                                print(f"  ... 还有 {len(attachments) - 5} 个附件")
                        else:
                            print("📎 无附件")
                    except json.JSONDecodeError:
                        print("📎 附件信息解析失败")
                elif key_type == 'string':
                    # 如果是字符串类型，直接获取值
                    value = r.get(key)
                    print(f"值: {value}")
                else:
                    print(f"不支持的键类型: {key_type}")
                    
            except Exception as e:
                print(f"获取数据失败: {e}")

def main():
    """主函数"""
    print("🔍 开始检查Redis中的爬虫数据...")
    
    # 连接Redis
    r = connect_redis()
    if not r:
        return
    
    # 显示爬虫数据
    show_crawled_data(r)
    
    print("\n✅ 数据检查完成")

if __name__ == "__main__":
    main()