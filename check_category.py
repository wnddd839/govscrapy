import redis
import os
import yaml

# Load Redis config
config_path = os.path.join(os.path.dirname(__file__), 'config', 'redis_config.yml')
with open(config_path, 'r', encoding='utf-8') as f:
    redis_config = yaml.safe_load(f)['redis']

r = redis.Redis(
    host=redis_config['host'],
    port=redis_config['port'],
    password=redis_config['password'],
    db=1,
    decode_responses=True
)

# Get keys
keys = r.keys("gov:data:*")
print(f"Scanning {len(keys)} keys for long categories...")

count = 0
for key in keys:
    if r.type(key) == 'hash':
        cat = r.hget(key, 'category')
        if cat and len(cat) > 20:
            print(f"⚠️ Found long category in {key}:")
            print(f"   Length: {len(cat)}")
            print(f"   Value: {cat}")
            print(f"   Title associated: {r.hget(key, 'title')}")
            print("-" * 20)
            count += 1

if count == 0:
    print("✅ No long categories found (> 20 chars).")
else:
    print(f"❌ Found {count} items with long categories.")
