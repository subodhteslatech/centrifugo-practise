import jwt
import time
import asyncio
import json
import websockets
# import threading


class CentrifugoClient:
    def __init__(self):
        self.websocket: websockets.ClientConnection | None = None
        self.channel = None
        self.uri = "ws://localhost:8000/connection/websocket"

    def _generate_token(self, user_id: str):
        payload = {"sub": user_id, "exp": int(time.time()) + 3600}
        return jwt.encode(
            payload,
            "eeRi1TwYHLjTmDEX7EJ-Tprq2nwyMrSgV3LjQrD43WvgWy9PBRzoEffwc60gMCvSOzVe4GPFqUHmOGpSoNr2Ug",
            algorithm="HS256",
        )

    async def connect(self):
        try:
            if self.websocket is None:
                raise Exception("WebSocket is not connected")

            await self.websocket.send(
                json.dumps(
                    {
                        "connect": {"token": self._generate_token(str(time.time()))},
                        "id": 1,
                    }
                )
            )
            # response = await self.websocket.recv()
            # print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")

    async def disconnect(self):
        if self.websocket is None:
            raise Exception("WebSocket is not connected")
        await self.websocket.close()
        exit(0)

    async def subscribe(self):
        if self.websocket is None:
            raise Exception("WebSocket is not connected")

        channel = input("Enter channel to subscribe: ")
        self.channel = channel

        await self.websocket.send(
            json.dumps(
                {
                    "subscribe": {"channel": channel},
                    "id": 2,
                }
            )
        )

    async def publish(self):
        if self.websocket is None:
            raise Exception("WebSocket is not connected")

        if self.channel is None:
            raise Exception("No channel subscribed")

        msg = input("Enter message to publish: ")

        await self.websocket.send(
            json.dumps(
                {
                    "publish": {"channel": self.channel, "data": {"text": msg}},
                    "id": 3,
                }
            )
        )

    async def listen_messages(self):
        if self.websocket is None:
            raise Exception("WebSocket is not connected")

        await self.connect()
        self.channel = "chat"
        await self.subscribe()
        try:
            while True:
                print("Inside Block")
                message = await self.websocket.recv()
                print(f"Received message: {message}")
        except Exception as e:
            print(f"Error: {e}")

    async def run(self):
        try:
            async with websockets.connect(self.uri) as websocket:
                self.websocket = websocket
                asyncio.create_task(self.listen_messages())
                await asyncio.sleep(3600)
                while True:
                    try:
                        print("1 - connect")
                        print("2 - subscribe")
                        print("3 - publish")
                        print("4 - disconnect")

                        event = input("Enter event: ")

                        events = {
                            "1": self.connect,
                            "2": self.subscribe,
                            "3": self.publish,
                            "4": self.disconnect,
                        }

                        if event in events:
                            await events[event]()
                        else:
                            print("Unknown event")

                        # await self.listen_messages()

                    except websockets.ConnectionClosed:
                        await self.disconnect()

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    centrifugo_client = CentrifugoClient()

    asyncio.run(centrifugo_client.run())
