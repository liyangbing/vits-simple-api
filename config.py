import os
import sys
import logging
import configparser
import torch

JSON_AS_ASCII = False

MAX_CONTENT_LENGTH = 5242880

# Flask debug mode
DEBUG = False

# Server port
PORT = 23456

# Absolute path of vits-simple-api
ABS_PATH = os.path.dirname(os.path.realpath(__file__))

print(ABS_PATH)

# Upload path
UPLOAD_FOLDER = ABS_PATH + "/upload"


# Cahce path
CACHE_PATH = "/data/2d-digital"
DATA_DIR = "/data"

# Logs path
LOGS_PATH = ABS_PATH + "/logs"

# Set the number of backup log files to keep.
LOGS_BACKUPCOUNT = 30

# If CLEAN_INTERVAL_SECONDS <= 0, the cleaning task will not be executed.
CLEAN_INTERVAL_SECONDS = 0

# save audio to CACHE_PATH
SAVE_AUDIO = True

# zh ja ko en... If it is empty, it will be read based on the text_cleaners specified in the config.json.
LANGUAGE_AUTOMATIC_DETECT = []

# Set to True to enable API Key authentication
API_KEY_ENABLED = False

# API_KEY is required for authentication
API_KEY = ""

# WTForms CSRF 保护
SECRET_KEY = ""

# Control whether to enable the admin backend functionality
IS_ADMIN_ENABLED = True  # Set to True to enable the admin backend, set to False to disable it

# Define the route for the admin backend
ADMIN_ROUTE = '/admin'  # You can change this to your desired route

# logging_level:DEBUG/INFO/WARNING/ERROR/CRITICAL
LOGGING_LEVEL = "DEBUG"

# Language identification library. Optional fastlid, langid
LANGUAGE_IDENTIFICATION_LIBRARY = "langid"

# To use the english_cleaner, you need to install espeak and provide the path of libespeak-ng.dll as input here.
# If ESPEAK_LIBRARY is set to empty, it will be read from the environment variable.
# For windows : "C:/Program Files/eSpeak NG/libespeak-ng.dll"
ESPEAK_LIBRARY = ""

# Fill in the model path here
MODEL_LIST = [
    # VITS
    # [ABS_PATH + "/Model/Nene_Nanami_Rong_Tang/1374_epochs.pth", ABS_PATH + "/Model/Nene_Nanami_Rong_Tang/config.json"],
    # [ABS_PATH + "/Model/Zero_no_tsukaima/1158_epochs.pth", ABS_PATH + "/Model/Zero_no_tsukaima/config.json"],
    # [ABS_PATH + "/Model/g/G_953000.pth", ABS_PATH + "/Model/g/config.json"],
    # [ABS_PATH + "/Model/vits_chinese/vits_bert_model.pth", ABS_PATH + "/Model/vits_chinese/bert_vits.json"],
    # HuBert-VITS (Need to configure HUBERT_SOFT_MODEL)
    # [ABS_PATH + "/Model/louise/360_epochs.pth", ABS_PATH + "/Model/louise/config.json"],
    # W2V2-VITS (Need to configure DIMENSIONAL_EMOTION_NPY)
    # [ABS_PATH + "/Model/w2v2-vits/1026_epochs.pth", ABS_PATH + "/Model/w2v2-vits/config.json"],
    # Bert-VITS2
    # [ABS_PATH + "/Model/bert_vits2/G_9000.pth", ABS_PATH + "/Model/bert_vits2/config.json"],
]

# hubert-vits: hubert soft model
HUBERT_SOFT_MODEL = ABS_PATH + "/Model/hubert-soft-0d54a1f4.pt"

# w2v2-vits: Dimensional emotion npy file
# load single npy: ABS_PATH+"/all_emotions.npy
# load mutiple npy: [ABS_PATH + "/emotions1.npy", ABS_PATH + "/emotions2.npy"]
# load mutiple npy from folder: ABS_PATH + "/Model/npy"
DIMENSIONAL_EMOTION_NPY = ABS_PATH + "/Model/npy"

# w2v2-vits: Need to have both `model.onnx` and `model.yaml` files in the same path.
# DIMENSIONAL_EMOTION_MODEL = ABS_PATH + "/Model/model.yaml"


CHINESE_ROBERTA_WWM_EXT_LARGE = ABS_PATH + "bert_vits2/bert/chinese-roberta-wwm-ext-large"
BERT_BASE_JAPANESE_V3 = ABS_PATH + "bert_vits2/bert/bert-base-japanese-v3"
BERT_LARGE_JAPANESE_V2 = ABS_PATH + "bert_vits2/bert/bert-large-japanese-v2"
DEBERTA_V2_LARGE_JAPANESE = ABS_PATH + "bert_vits2/bert/deberta-v2-large-japanese"
DEBERTA_V3_LARGE = ABS_PATH + "bert_vits2/bert/deberta-v3-large"
DEBERTA_V2_LARGE_JAPANESE_CHAR_WWM = ABS_PATH + "bert_vits2/bert/deberta-v2-large-japanese-char-wwm"
WAV2VEC2_LARGE_ROBUST_12_FT_EMOTION_MSP_DIM = ABS_PATH + "bert_vits2/emotional/wav2vec2-large-robust-12-ft-emotion-msp-dim"
VITS_CHINESE_BERT = ABS_PATH + "vits/bert"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# VITS
DYNAMIC_LOADING = False

"""
Default parameter
"""

ID = 0

FORMAT = "wav"

LANG = "auto"

LENGTH = 1

NOISE = 0.33

NOISEW = 0.4

# 长文本分段阈值，segment_size<=0表示不分段.
# Batch processing threshold. Text will not be processed in batches if segment_size<=0
SEGMENT_SIZE = 50

# Bert_VITS2
SDP_RATIO = 0.2
LENGTH_ZH = 0
LENGTH_JA = 0
LENGTH_EN = 0
STYLE_WEIGHT = 0.7


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
        "ACCESS_KEY_ID": os.environ.get("ACCESS_KEY_ID")
        or "",
        "ACCESS_KEY_SECRET": os.environ.get("ACCESS_KEY_SECRET")
        or "",
        "SERVER_URL": "http://122.51.13.196:50002",
    }

    if config_key:
        return app_configs.get(config_key)
    else:
        return app_configs
