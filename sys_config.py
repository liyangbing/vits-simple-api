import os
import logging
import configparser

def get_config(config_key=None):
    # 创建 ConfigParser 对象
    configloader = configparser.ConfigParser()
    # 读取配置文件
    configloader.read("config.ini")
    app_configs = {
        # 获取配置文件中的参数值
        "DATA_DIR": configloader.get("settings", "DATA_DIR", fallback="/data"),
        "API_KEY": os.environ.get("ROLEIP_API_KEY")
        or configloader.get("settings", "API_KEY", fallback=""),
        "SECRET_KEY": os.environ.get("ROLEIP_SECRET_KEY")
        or configloader.get("settings", "SECRET_KEY", fallback=""),
        # 设置打印级别
        "LOG_LEVEL": logging.INFO,
        "DEBUG": False,
        "TESTING": False,
        # oss配置
        "TENCENT_COS_DOMAIN": "https://oss.roleip.com",
        "BUCKET": "net-pan-1323472688",
        "REGION": "ap-shanghai",
        "OSS_PREFIX": "https://oss.roleip.com/roleip/",
        "ACCESS_KEY_ID": os.environ.get("ACCESS_KEY_ID") or "",
        "ACCESS_KEY_SECRET": os.environ.get("ACCESS_KEY_SECRET") or "",
        "SERVER_URL": configloader.get(
            "settings", "SERVER_URL", fallback="https://api.roleip.com:8443"
        ),
    }

    if config_key:
        return app_configs.get(config_key)
    else:
        return app_configs
