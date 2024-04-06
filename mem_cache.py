import threading
import time

# 创建一个全局的缓存字典
global_cache = {}
cache_lock = threading.Lock()


# 添加数据到缓存
def add_to_cache(key, value, expire_time):
    global global_cache
    with cache_lock:
        global_cache[key] = {"value": value, "expire_time": time.time() + expire_time}


# 从缓存中获取数据
def get_from_cache(key):
    global global_cache
    with cache_lock:
        return global_cache.get(key)


# 示例用法
# add_to_cache("name", "Alice", 10)  # 10秒后过期
# add_to_cache("age", 30, 30)  # 30秒后过期

# time.sleep(15)  # 等待一段时间，让部分缓存过期

# print(get_from_cache("name"))  # 输出: None，因为 'name' 已经过期
# print(get_from_cache("age"))  # 输出: 30，因为 'age' 还未过期
