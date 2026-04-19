import asyncio
import json
import websockets

async def test():
    uri = "ws://localhost:8000/ws/chat"
    try:
        async with websockets.connect(uri) as websocket:
            resp1 = await websocket.recv()
            print("Initial:", resp1)

            payload = {
                "type": "message",
                "content": "how are you today? Answer in 1 sentence.",
                "mode": "auto"
            }
            await websocket.send(json.dumps(payload))

            full_reply = ""
            while True:
                resp = await websocket.recv()
                data = json.loads(resp)
                if data.get("type") == "token":
                    full_reply += data["content"]
                    print(data["content"], end="", flush=True)
                elif data.get("type") == "done":
                    print("\n[Done]")
                    break
                else:
                    print("\n[System/Other]", data)
                    
            if not full_reply:
                print("Failed: No text received")
    except Exception as e:
        print(f"Connection error: {e}")

asyncio.run(test())
