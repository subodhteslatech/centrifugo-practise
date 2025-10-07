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
        self.channel_list = []
        self.uri = "ws://192.168.1.242:8000/connection/websocket"
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

        channel = await self.ainput("Enter channel to subscribe (default 'chat:123'): ")
        if channel.strip():
            self.channel = channel.strip()

        if self.channel in self.channel_list:
            print(f"Already subscribed to channel: {self.channel}")
            return

        self.channel_list.append(self.channel)

        await self.websocket.send(
            json.dumps(
                {
                    "subscribe": {"channel": self.channel},
                    "id": 2,
                }
            )
        )

        print("Subscribed to channel:", self.channel)

        await self.get_history()

        await self.get_user_presence()

    async def publish(self):
        try:
            if self.websocket is None:
                raise Exception("WebSocket is not connected")

            if self.channel is None:
                raise Exception("No channel subscribed")

            # msg = input("Enter message to publish: ")
            # msg = f"message from {self.user_id}"
            print("channel list")
            for ch in self.channel_list:
                print(f"- {ch}")

            channel = await self.ainput(
                f"Enter channel to publish (default '{self.channel}'): "
            )
            if channel.strip():
                self.channel = channel.strip()
            msg = await self.ainput("Enter message to publish: ")

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
            await self.disconnect()

    async def listen_messages(self):
        if self.websocket is None:
            raise Exception("WebSocket is not connected")

        # await self.connect()
        # self.channel = "chat"
        # await self.subscribe()
        try:
            while True:
                print()
                print()
                message = await self.websocket.recv()
                print(f"Received message: {message}")

                if message == "{}":
                    await self.websocket.send(message)
        except Exception as e:
            print(f"Error: {e}")

    async def get_history(self):
        if self.websocket is None:
            raise Exception("WebSocket is not connected")

        if self.channel is None:
            raise Exception("No channel subscribed")

        await self.websocket.send(
            json.dumps(
                {
                    "history": {"channel": self.channel, "limit": 10},
                    "id": 4,
                }
            )
        )
        print("Requested history for channel:", self.channel)

    async def get_user_presence(self):
        if self.websocket is None:
            raise Exception("WebSocket is not connected")

        if self.channel is None:
            raise Exception("No channel subscribed")

        await self.websocket.send(
            json.dumps(
                {
                    "presence": {"channel": self.channel},
                    "id": 5,
                }
            )
        )
        print("Requested presence for channel:", self.channel)

    async def ainput(self, prompt: str = ""):
        return await asyncio.to_thread(input, prompt)

    async def run(self):
        try:
            async with websockets.connect(self.uri) as websocket:
                self.websocket = websocket
                asyncio.create_task(self.listen_messages())
                # await asyncio.sleep(3600)
                await self.connect()
                await asyncio.sleep(1)
                # await self.subscribe()
                # await asyncio.sleep(1)
                # await asyncio.sleep(3600)
                while True:
                    try:
                        print("Enter a event to perform:")
                        print("1. Subscribe to channel")
                        print("2. Publish message to channel")
                        print("3. Get channel history")
                        print("4. Get user presence")
                        print("5. Exit")

                        choice = await self.ainput("Enter choice: ")

                        events = {
                            "1": self.subscribe,
                            "2": self.publish,
                            "3": self.get_history,
                            "4": self.get_user_presence,
                            "5": self.disconnect,
                        }

                        if choice in events:
                            await events[choice]()
                        else:
                            print("Invalid choice")

                    # try:
                    #     # await asyncio.sleep(5)

                    #     await self.publish()

                    #     # await asyncio.sleep(10)

                    except websockets.ConnectionClosed:
                        await self.disconnect()

                    except KeyboardInterrupt:
                        print("Exiting...")
                        await self.disconnect()

                    except Exception as e:
                        print(f"Error during publish: {e}")
                        await self.disconnect()

        except Exception as e:
            print(f"Error: {e}")
            await self.disconnect()


if __name__ == "__main__":
    centrifugo_client = CentrifugoClient()

    asyncio.run(centrifugo_client.run())
