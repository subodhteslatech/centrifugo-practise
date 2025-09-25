from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from datetime import datetime
import requests
import os

from schema import Chat
from handler import SocketHandler
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()
API_KEY = os.environ.get("CENTRIFUGO_API_KEY")

CENTRIFUGO_BASE_URL = "http://localhost:8000"


@app.post("/chat")
def send_chat(chat: Chat):
    if chat.created_at is None:
        chat.created_at = datetime.now()

    print(API_KEY)

    headers = {"Content-type": "application/json", "X-API-KEY": API_KEY}
    data = {
        "channel": f"chat:#{'123722'}",
        # "channel": "channel",
        "data": {
            "sender": chat.sender,
            "msg": chat.msg,
            "created_at": chat.created_at.isoformat(),
        },
    }

    response = requests.post(
        f"{CENTRIFUGO_BASE_URL}/api/publish", json=data, headers=headers
    )

    if response.status_code != 200:
        print(response.status_code)
        print(response.text)
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return chat


@app.post("/subscribe")
def subscribe(user: str):
    headers = {"Content-type": "application/json", "X-API-KEY": API_KEY}

    print(f"Subscribing {user} to channel chat:#{user}")
    data = {"user": "123722", "channel": f"chat:#{'123722'}"}

    response = requests.post(
        f"{CENTRIFUGO_BASE_URL}/api/subscribe", json=data, headers=headers
    )
    print("Subscribe Response:")
    print(response.status_code)
    print(response.text)
    if response.status_code != 200:
        print(response.status_code)
        print(response.text)
        raise HTTPException(status_code=response.status_code, detail=response.text)

    if response.status_code == 200 and response.json().get("error", None):
        raise HTTPException(status_code=400, detail=response.json())

    return {"msg": f"Subscribed {user} to channel chat:#{user}"}


@app.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    try:
        socket_handler = SocketHandler(websocket)
        await socket_handler.connect()

    except WebSocketDisconnect:
        await socket_handler.disconnect()

    except Exception as e:
        await socket_handler.disconnect(str(e))
