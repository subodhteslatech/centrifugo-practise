import jwt
import time
import asyncio
import json
import websockets
# import threading


class CentrifugoClient:
    def __init__(self):
        self.websocket: websockets.ClientConnection | None = None
        self.channel = "chat:123"
        self.uri = "ws://localhost:8000/connection/websocket"
        self.user_id = str(time.time())

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

            print()
            print()
            print(f"User ID: {self.user_id}")
            print()
            print()

            await self.websocket.send(
                json.dumps(
                    {
                        "connect": {"token": self._generate_token(self.user_id)},
                        "id": 1,
                    }
                )
            )
            # response = await self.websocket.recv()
            # print(f"Response: {response}")

            print("Connected to server")
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

        await self.websocket.send(
            json.dumps(
                {
                    "subscribe": {"channel": self.channel},
                    "id": 2,
                }
            )
        )

        print("Subscribed to channel:", self.channel)

    async def publish(self):
        try:
            if self.websocket is None:
                raise Exception("WebSocket is not connected")

            if self.channel is None:
                raise Exception("No channel subscribed")

            # msg = input("Enter message to publish: ")
            msg = f"message from {self.user_id}"

            await self.websocket.send(
                json.dumps(
                    {
                        "publish": {"channel": self.channel, "data": {"text": msg}},
                        "id": 3,
                    }
                )
            )
        except Exception as e:
            print(f"Error: {e}")

    async def listen_messages(self):
        if self.websocket is None:
            raise Exception("WebSocket is not connected")

        # await self.connect()
        # self.channel = "chat"
        # await self.subscribe()
        try:
            while True:
                print("Inside Block")
                message = await self.websocket.recv()
                print(f"Received message: {message}")

                if message == "{}":
                    await self.websocket.send(message)
        except Exception as e:
            print(f"Error: {e}")

    async def run(self):
        try:
            async with websockets.connect(self.uri) as websocket:
                self.websocket = websocket
                asyncio.create_task(self.listen_messages())
                # await asyncio.sleep(3600)
                await self.connect()
                await asyncio.sleep(1)
                await self.subscribe()
                await asyncio.sleep(1)
                # await asyncio.sleep(3600)
                while True:
                    try:
                        await asyncio.sleep(5)

                        await self.publish()

                        await asyncio.sleep(10)

                    except websockets.ConnectionClosed:
                        print("Connection closed, reconnecting...")
                        await asyncio.sleep(5)
                        await self.disconnect()

                    except Exception as e:
                        print(f"Error during publish: {e}")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    centrifugo_client = CentrifugoClient()

    asyncio.run(centrifugo_client.run())
