from flask import Flask, request, jsonify
import requests
import socketio
import json
import logging
import mem_cache
import threading
import time
import configparser

# 定义后端服务器地址
BACKENDS = {
    "audio": "http://127.0.0.1:50001/voice/inference",
    "video": "http://127.0.0.1:50004/video/inference",
    "picture": "http://127.0.0.1:50007",
}

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(filename)s:%(lineno)d",
)
logger = logging.getLogger(__name__)
log_level = logging.INFO
logger.setLevel(log_level)
server_url = "https://api.roleip.com:8443"
configloader = configparser.ConfigParser()
configloader.read("config.ini")
api_key = configloader.get("settings", "API_KEY", fallback="")
print(api_key)
sio = socketio.Client()


def reconnect():
    logger.info("Reconnecting to server")
    while True:
        try:
            if not sio.connected:
                sio.connect(server_url, retry=True)
                logger.info("Connected to server")
                sio.emit(
                    "agent_join",
                    json.dumps({"api_key": api_key, "service_type": "proxy"}),
                )
                logger.info("Connect sid: {}".format(sio.sid))
        except Exception as e:
            logger.error("Error in reconnect: {}".format(e))
        time.sleep(10)


reconnect_thread = threading.Thread(target=reconnect)
reconnect_thread.daemon = True
reconnect_thread.start()


def send_message(msg_type: str, msg: dict):
    logger.info("Sending message to server: {}".format(msg))
    sio.emit(msg_type, json.dumps(msg))


@sio.on("connect")
def connect():
    logger.info("Connected to server")


def proxy_to_http(tag, req_data):
    backend_url = BACKENDS[tag]
    resp = requests.request(
        method="POST",
        url=backend_url,
        data=req_data,
        allow_redirects=False,
        headers={"Content-Type": "application/json"},
        timeout=30 * 60,
    )
    return resp.content


def handle_msg(tag: str, msg: dict) -> dict:
    logger.info("Received message from server: {}".format(msg))
    retMsg = {
        "room": msg.get("room"),
        "messageId": msg.get("messageId"),
        "messageType": msg.get("messageType"),
        "message": msg.get("message"),
    }
    key = f'{msg.get("messageType")}_{msg.get("messageId")}'
    if mem_cache.get_from_cache(key):
        cache_message = mem_cache.get_from_cache(key)
        if cache_message == msg.get("message"):
            logger.info("The same message,handling, skip it")
            return {}
        else:
            logger.info("The same message, handled, send it")
            retMsg["message"] = cache_message
            return retMsg
    mem_cache.add_to_cache(key, msg.get("message"), 10 * 60)
    retMessage = proxy_to_http(tag, json.dumps(msg.get("message")))
    retMessage = json.loads(retMessage)
    retMsg["message"] = retMessage
    mem_cache.add_to_cache(key, retMessage, 10 * 60)
    return retMsg


@sio.on("agent_audio")
def receive_audio_message(msg):
    try:
        retMsg = handle_msg("audio", msg)
        if retMsg:
            send_message("agent_audio", retMsg)
    except Exception as e:
        logger.error("Error occurred while handling message: {}".format(e))


@sio.on("agent_video")
def receive_video_message(msg):
    try:
        retMsg = handle_msg("video", msg)
        if retMsg:
            send_message("agent_video", retMsg)
    except Exception as e:
        logger.error("Error occurred while handling message: {}".format(e))


@sio.on("agent_picture")
def receive_picture_message(msg):
    try:
        retMsg = handle_msg("picture", msg)
        if retMsg:
            send_message("agent_picture", retMsg)
    except Exception as e:
        logger.error("Error occurred while handling message: {}".format(e))


@sio.on("agent_join")
def join_room(room):
    logger.info("Joining room:".format(room))


@app.route("/")
def route_request():
    # 获取 'Tag' 请求头
    tag = request.headers.get("Tag", "").lower()

    # 根据 'Tag' 转发到不同的后端
    if tag in BACKENDS:
        backend_url = BACKENDS[tag]
        resp = requests.request(
            method=request.method,
            url=backend_url,
            headers={key: value for (key, value) in request.headers if key != "Host"},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
        )

        # 将从后端获得的响应返回给客户端
        excluded_headers = [
            "content-encoding",
            "content-length",
            "transfer-encoding",
            "connection",
        ]
        headers = [
            (name, value)
            for (name, value) in resp.raw.headers.items()
            if name.lower() not in excluded_headers
        ]
        response = app.response_class(resp.content, resp.status_code, headers)
        return response
    else:
        return jsonify(error="Invalid tag"), 400


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=50006)
