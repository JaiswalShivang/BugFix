import sys
import asyncio
from services.switch.room import SwitchRoom
from services.switch.real_client import SwitchPlatformClient

def main():
    real_client = SwitchPlatformClient()
    room = SwitchRoom()

    if len(sys.argv) > 1:
        arg = " ".join(sys.argv[1:])

        if real_client.is_configured():
            remote_res = real_client.post_message(arg)
            if remote_res.get("remote_connected"):
                print("[REMOTE SWITCH CONFIRMED]:", remote_res.get("data"))
                return
            else:
                print(f"[SWITCH NOTICE - FALLBACK TO LOCAL]: Remote connection failed: {remote_res.get('reason')}")
        else:
            print("[SWITCH NOTICE - SIMULATED LOCAL PROTOCOL]: SWITCH_API_KEY not provided in environment. Executing via local clean-room Switch protocol.")

        if arg.startswith("!"):
            output = room.execute_command(arg)
            print(output)
        else:
            res = asyncio.run(room.post_message("human", arg))
            for item in res:
                print(f"[{item['sender']}]: {item['text']}")
    else:
        print("Usage: python -m services.switch.cli [!command | @agent prompt]")

if __name__ == "__main__":
    main()
