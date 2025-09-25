import jwt
import time
import asyncio
import json
from websockets.asyncio.client import connect, ClientConnection

# from handler import CentrifugoHandler


# class CentrifugoClient:


def generate_token(user_id: str):
    payload = {"sub": user_id, "exp": int(time.time()) + 3600}
    return jwt.encode(
        payload,
        "sbxvU9g6ZxNDkiabr3V776rRvZNBs8qdJNdutrLBm2jJ93rNnuD6Ra9eGwD9RvnmZjYk1I8j7E8pUbPgrLmBSg",
        algorithm="HS256",
    )


async def client():
    async with connect("ws://localhost:8000/connection/websocket") as websocket:
        try:
            print(websocket)
            send = await websocket.send(
                json.dumps(
                    {
                        "connect": {
                            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3IiwiZXhwIjoxNzU5MzEwMjIwLCJpYXQiOjE3NTg3MDU0MjB9.-FjgvD-aebizrhpfP5kIxHlknGMG19F-Ls4rtvYdPrQ"
                        },
                        "id": 1,
                    }
                )
            )
            print(send)
            response = await websocket.recv()
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")


class CentrifugoClient:
    def __init__(self):
        self.websocket: ClientConnection | None = None
        self.channel = None

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

    async def run(self):
        try:
            async with connect("ws://localhost:8000/connection/websocket") as websocket:
                self.websocket = websocket

                while True:
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

                    async for message in self.websocket.recv_streaming(decode=None):
                        print(f"Message: {message}")
                        if message is None:
                            break

                    # response = await self.websocket.recv()
                    # print(f"Response: {response}")

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    centrifugo_client = CentrifugoClient()

    asyncio.run(centrifugo_client.run())
