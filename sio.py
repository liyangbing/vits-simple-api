import config
import socketio
import json
import logging
import tts_app.voice_api.views as views


logger = logging.getLogger(__name__)
log_level = config.get_config("LOG_LEVEL")
logger.setLevel(log_level)
server_url = config.get_config("SERVER_URL")
api_key = config.get_config("API_KEY")
sio = socketio.Client()
sio.connect(server_url)
sio.emit("agent_join", json.dumps({"api_key": api_key, "service_type": "wav2lip"}))


@sio.on("connect")
def connect():
    logger.info("Connected to server")


@sio.on("agent_message")
def receive_message(msg):
    # json 字符串转字典
    msg = json.loads(msg)
    logger.info("Received message from server:", msg)
    retMsg = {
        "room": msg.get("room"),
        "messageId": msg.get("messageId"),
        "messageType": msg.get("messageType"),
        "message": msg.get("message"),
    }

    retMessage = views.inner_voice_bert_vits2_api(msg.get("message"))
    retMsg["message"] = retMessage
    send_message("agent_message",retMsg)


@sio.on("agent_join")
def join_room(room):
    logger.info("Joining room:", room)


def send_message(msg_type: str, msg: dict):
    logger.info("Sending message to server:", msg)
    sio.emit(msg_type, json.dumps(msg))
