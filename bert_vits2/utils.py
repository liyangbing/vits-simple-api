import os
import sys
import logging
import torch
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import socket
import hmac
import io
import hashlib
import platform

from contants import config

MATPLOTLIB_FLAG = False

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
logger = logging


def get_mac_address():
    if platform.system() == "Windows":
        import pythoncom
        import wmi

        # 初始化COM线程
        pythoncom.CoInitialize()
        c = wmi.WMI()
        for interface in c.Win32_NetworkAdapterConfiguration(IPEnabled=True):
            return interface.MACAddress
    elif platform.system() == "Linux":
        import subprocess

        result = subprocess.run(["ifconfig"], capture_output=True, text=True)
        output = result.stdout
        for line in output.split("\n"):
            if "ether" in line:
                return line.split()[1]
    else:
        raise NotImplementedError("Unsupported operating system")


def generate_machine_specific_key(password, hostname=None, mac_address=None):
    if not hostname:
        # 如果未提供主机名，获取机器的主机名
        hostname = socket.gethostname()
    if not mac_address:
        # 如果未提供MAC地址，获取机器的MAC地址
        mac_address = get_mac_address()
    # 合并MAC地址和主机名
    combined_data = mac_address.encode("utf-8") + hostname.encode("utf-8")
    # 使用用户提供的密码作为密钥，使用HMAC生成哈希值
    hashed_data = hmac.new(
        password.encode("utf-8"), combined_data, hashlib.sha256
    ).digest()
    # 生成的哈希值可以用作AES密钥
    return hashed_data


# Function to decrypt data
def decrypt(key, iv, ct_bytes):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt_bytes = unpad(cipher.decrypt(ct_bytes), AES.block_size)
    return pt_bytes


# Read model file
def read_model(filename):
    with open(filename, "rb") as f:
        return f.read()


def load_checkpoint(
    checkpoint_path,
    model,
    optimizer=None,
    skip_optimizer=False,
    version=None,
    api_key=None,
):
    assert os.path.isfile(checkpoint_path)
    if api_key:
        key = generate_machine_specific_key(api_key)
        # Decrypt the encrypted model
        encrypted_model_with_iv = read_model(checkpoint_path)
        iv = encrypted_model_with_iv[:16]
        encrypted_model_data = encrypted_model_with_iv[16:]
        decrypted_model = decrypt(key, iv, encrypted_model_data)
        # 使用io.BytesIO创建一个类似文件的对象
        model_stream = io.BytesIO(decrypted_model)
        checkpoint_dict = torch.load(model_stream, map_location=config.system.device)
        model_stream.close()
    else:
        checkpoint_dict = torch.load(checkpoint_path, map_location=config.system.device)
    iteration = checkpoint_dict["iteration"]
    learning_rate = checkpoint_dict["learning_rate"]
    if (
        optimizer is not None
        and not skip_optimizer
        and checkpoint_dict["optimizer"] is not None
    ):
        optimizer.load_state_dict(checkpoint_dict["optimizer"])
    elif optimizer is None and not skip_optimizer:
        # else: #Disable this line if Infer ,and enable the line upper
        new_opt_dict = optimizer.state_dict()
        new_opt_dict_params = new_opt_dict["param_groups"][0]["params"]
        new_opt_dict["param_groups"] = checkpoint_dict["optimizer"]["param_groups"]
        new_opt_dict["param_groups"][0]["params"] = new_opt_dict_params
        optimizer.load_state_dict(new_opt_dict)
    saved_state_dict = checkpoint_dict["model"]
    if hasattr(model, "module"):
        state_dict = model.module.state_dict()
    else:
        state_dict = model.state_dict()
    new_state_dict = {}
    for k, v in state_dict.items():
        try:
            # assert "emb_g" not in k
            # print("load", k)
            new_state_dict[k] = saved_state_dict[k]
            assert saved_state_dict[k].shape == v.shape, (
                saved_state_dict[k].shape,
                v.shape,
            )
        except:
            # Handle legacy model versions and provide appropriate warnings
            if "ja_bert_proj" in k:
                v = torch.zeros_like(v)
                if version is None:
                    logger.error(f"{k} is not in the checkpoint")
                    logger.warning(
                        f'If you\'re using an older version of the model, consider adding the "version" parameter to the model\'s config.json. For instance: "version": "1.0.1"'
                    )
            elif "flow.flows.0.enc.attn_layers.3" in k:
                logger.error(f"{k} is not in the checkpoint")
                logger.warning(
                    f'If you\'re using a transitional version, please add the "version": "1.1.0-transition" parameter to the model\'s config.json. For instance: "version": "1.1.0-transition"'
                )
            elif "en_bert_proj" in k:
                v = torch.zeros_like(v)
                if version is None:
                    logger.error(f"{k} is not in the checkpoint")
                    logger.warning(
                        f'If you\'re using an older version of the model, consider adding the "version" parameter to the model\'s config.json. For instance: "version": "1.1.1"'
                    )
            else:
                logger.error(f"{k} is not in the checkpoint")

            new_state_dict[k] = v
    if hasattr(model, "module"):
        model.module.load_state_dict(new_state_dict, strict=False)
    else:
        model.load_state_dict(new_state_dict, strict=False)
    # print("load ")
    logger.info(
        "Loaded checkpoint '{}' (iteration {})".format(checkpoint_path, iteration)
    )
    return model, optimizer, learning_rate, iteration


def process_legacy_versions(hps):
    version = getattr(hps, "version", getattr(hps.data, "version", None))
    if version:
        prefix = version[0].lower()
        if prefix == "v":
            version = version[1:]
    return version
