import time
import os
import sys

def main():
    while True:
        with open("artifacts/code_fixer.heartbeat", "w") as f:
            f.write(str(time.time()))
        time.sleep(5)

if __name__ == "__main__":
    os.makedirs("artifacts", exist_ok=True)
    main()
