import config
import socketio
import json
import logging
from tts_app.voice_api.views import inner_voice_bert_vits2_api
import mem_cache


logger = logging.getLogger(__name__)
log_level = config.get_config("LOG_LEVEL")
logger.setLevel(log_level)
server_url = config.get_config("SERVER_URL")
api_key = config.get_config("API_KEY")
sio = socketio.Client()
sio.connect(server_url)
sio.emit("agent_join", json.dumps({"api_key": api_key, "service_type": "vits"}))


@sio.on("connect")
def connect():
    logger.info("Connected to server")
    sio.emit("agent_join", json.dumps({"api_key": api_key, "service_type": "vits"}))


@sio.on("agent_message")
def receive_message(msg):
    try:
        # json 字符串转字典
        logger.info("Received message from server: {}".format(msg))
        retMsg = {
            "room": msg.get("room"),
            "messageId": msg.get("messageId"),
            "messageType": msg.get("messageType"),
            "message": msg.get("message"),
        }
        if mem_cache.get_from_cache(msg.get("messageId")):
            cache_message = mem_cache.get_from_cache(msg.get("messageId"))
            if cache_message == msg.get("message"):
                logger.info("The same message,handling, skip it")
                return
            else:
                logger.info("The same message, handled, send it")
                retMsg["message"] = cache_message
                send_message("agent_message", retMsg)
                return
        mem_cache.add_to_cache(msg.get("messageId"), msg.get("message"), 10 * 60)
        retMessage = inner_voice_bert_vits2_api(msg.get("message"))
        retMsg["message"] = retMessage
        mem_cache.add_to_cache(msg.get("messageId"), retMessage, 10 * 60)
        send_message("agent_message", retMsg)
    except Exception as e:
        logger.error("Error occurred while handling message: {}".format(e))


@sio.on("agent_join")
def join_room(room):
    logger.info("Joining room:", room)


def send_message(msg_type: str, msg: dict):
    logger.info("Sending message to server: {}".format(msg))
    sio.emit(msg_type, json.dumps(msg))
