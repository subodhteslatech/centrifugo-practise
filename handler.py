from websockets.asyncio.client import connect
from fastapi import WebSocket
import json

"""
websocket data structure:
    {
        "event": "message",
        "channel": "chat",
        "data": {
            "sender": "username",
            "msg": "Hello, World!",
        }
    }
"""

active_connections = {}

chat_history = {}


class SocketHandler:
    def __init__(self, websocket: WebSocket):
        self.websocket: WebSocket = websocket
        self.channel = None
        # self.active_connections: dict[str, list[WebSocket]] = {}
        self.data = {}

    def _set_channel(self, data: dict) -> None:
        print(self.channel)

        channel = self.data.get("channel", None)
        if channel is not None:
            self.channel = channel
            print(f"Channel set to: {self.channel}")
            return

        raise ValueError("Channel is not set in data")

    def _set_data(self, data: str):
        self.data = json.loads(data)

    async def subcribe(self) -> None:
        if self.channel is None:
            raise ValueError("Channel is not set")

        if self.channel not in active_connections:
            active_connections[self.channel] = []

        if self.websocket in active_connections[self.channel]:
            await self.websocket.send_text(
                str({"msg": "Already subscribed to channel"})
            )
            return

        active_connections[self.channel].append(self.websocket)
        await self.websocket.send_text(
            str({"msg": f"Subscribed to channel {self.channel}"})
        )

        print(active_connections)
        print(active_connections[self.channel])

        for connection in active_connections[self.channel]:
            if connection != self.websocket:
                await connection.send_text(
                    str({"msg": "A new user has joined the channel"})
                )

        print(chat_history)

        for message in chat_history.get(self.channel, []):
            await self.websocket.send_text(str(message))

    async def publish(self) -> None:
        if self.channel is None:
            raise ValueError("Channel is not set")

        if self.websocket not in active_connections.get(self.channel, []):
            await self.websocket.send_text(
                str({"msg": "You are not subscribed to this channel"})
            )

            return

        message = self.data.get("data", None)
        if message is None:
            raise ValueError("Message is not set in data")

        for connection in active_connections.get(self.channel, []):
            await connection.send_text(str(message))

        print(message)

        chat_history[self.channel] = chat_history.get(self.channel, [])
        chat_history[self.channel].append(message)
        print(chat_history)

    async def connect(self):
        await self.websocket.accept()

        while True:
            data = await self.websocket.receive_text()

            events = {
                "subscribe": self.subcribe,
                "publish": self.publish,
            }

            self._set_data(data)
            event = self.data.get("event", None)
            if event in events:
                self._set_channel(self.data)
                await events[event]()
            else:
                await self.websocket.send_text(str({"msg": f"Unknown event: {event}"}))

    async def disconnect(self, msg: str | None = None):
        if self.channel is None:
            await self.websocket.close()

        if msg is not None:
            await self.websocket.send_text(
                str({"msg": f"Disconnected from channel {self.channel}", "reason": msg})
            )

        active_connections[self.channel].remove(self.websocket)
        if not active_connections[self.channel]:
            del active_connections[self.channel]

        for connection in active_connections.get(self.channel, []):
            if connection != self.websocket:
                await connection.send_text(str({"msg": "A user has left the channel"}))

        await self.websocket.close()


class CentrifugoHandler:
    def __init__(self, websocket: WebSocket, user_id: str):
        from app import API_KEY, CENTRIFUGO_BASE_URL

        self.user_id = user_id
        self.api_key = API_KEY
        self.base_url = CENTRIFUGO_BASE_URL
        self.websocket: WebSocket = websocket
        self.channel = None

    def _set_channel(self, data: dict) -> None:
        print(self.channel)

        channel = self.data.get("channel", None)
        if channel is not None:
            self.channel = channel
            print(f"Channel set to: {self.channel}")
            return

        raise ValueError("Channel is not set in data")

    def _set_data(self, data: str):
        self.data = json.loads(data)

    def _call_api(self, endpoint: str, data: dict):
        import requests

        headers = {"Content-type": "application/json", "X-API-KEY": self.api_key}

        response = requests.post(
            f"{self.base_url}/api/{endpoint}", json=data, headers=headers
        )

        if response.status_code != 200:
            print(response.status_code)
            print(response.text)
            raise Exception(f"Error: {response.status_code}, {response.text}")

        if response.status_code == 200 and response.json().get("error", None):
            raise Exception(f"Error: {response.json()}")

        return response.json()

    async def subcribe(self) -> None:
        data = {
            "user": self.user_id,
            "channel": "chat",
        }

        response = self._call_api("subscribe", data)
        print("Subscribe Response:")
        print(response)

        await self.websocket.send_text(
            str({"msg": f"Subscribed to channel {self.channel}"})
        )

    async def publish(self) -> None:
        data = {
            "channel": "chat",
            "data": self.data.get("data", None),
        }

        response = self._call_api("publish", data)

        print("Publish Response:")
        print(response)

        await self.websocket.send_text(str({"msg": "Message published"}))

    async def centrifugo_connect(self):
        # await self.websocket.accept()

        # while True:
        #     data = await self.websocket.receive_text()

        #     events = {
        #         "subscribe": self.subcribe,
        #         "publish": self.publish,
        #     }

        #     self._set_data(data)
        #     event = self.data.get("event", None)
        #     if event in events:
        #         self._set_channel(self.data)
        #         await events[event]()
        #     else:
        #         await self.websocket.send_text(str({"msg": f"Unknown event: {event}"}))

        async with connect("ws://localhost:8000/connection/websocket") as websocket:
            try:
                response = await websocket.recv()
                print(f"Response: {response}")
            except Exception as e:
                print(f"Error: {e}")
