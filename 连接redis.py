import redis

# 填入你阿里云的公网 IP 和刚才设置的密码
HOST = '8.145.38.214'  # <--- 你的服务器 IP
PASSWORD = 'Wei18349276' # <--- 你的 Redis 密码

try:
    print(f"🔌 正在尝试连接 {HOST}...")
    
    # 建立连接 (超时设置短一点，免得卡死)
    r = redis.Redis(host=HOST, port=6379, password=PASSWORD, socket_timeout=3)
    
    # 尝试写入一个数据
    r.set('test_key', 'Hello Aliyun! This is Local.')
    
    # 尝试读取回来
    val = r.get('test_key')
    
    if val == b'Hello Aliyun! This is Local.':
        print("✅✅✅ 成功！天地线已打通！")
        print("你的本地电脑可以控制云端了。")
    else:
        print("❌ 连接成功但读取数据失败。")

except Exception as e:
    print("❌ 连接失败！请检查以下几点：")
    print("1. 阿里云安全组 6379 端口开了没？")
    print("2. 宝塔安全页面 6379 放行了没？")
    print("3. Redis 配置文件 bind 改成 0.0.0.0 了没？")
    print(f"错误信息: {e}")