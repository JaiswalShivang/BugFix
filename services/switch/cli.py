import sys
import asyncio
from services.switch.room import SwitchRoom

def main():
    room = SwitchRoom()
    if len(sys.argv) > 1:
        arg = " ".join(sys.argv[1:])
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
