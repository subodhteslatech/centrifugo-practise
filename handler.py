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
