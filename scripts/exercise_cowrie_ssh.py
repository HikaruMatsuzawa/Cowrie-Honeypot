from __future__ import annotations

import argparse
import time

import paramiko


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Connect to local Cowrie and send one command for integration testing."
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2222)
    parser.add_argument("--username", default="root")
    parser.add_argument("--password", default="admin")
    parser.add_argument("--command", default="uname -a")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--delay", type=float, default=0.8)
    args = parser.parse_args(argv)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        look_for_keys=False,
        allow_agent=False,
        timeout=args.timeout,
        auth_timeout=args.timeout,
        banner_timeout=args.timeout,
    )

    try:
        channel = client.invoke_shell()
        time.sleep(args.delay)
        _drain(channel)

        channel.send(f"{args.command}\n")
        time.sleep(args.delay)
        output = _drain(channel)

        channel.send("exit\n")
        time.sleep(args.delay)
        output += _drain(channel)
        print(output, end="")
    finally:
        client.close()

    return 0


def _drain(channel: paramiko.Channel) -> str:
    chunks: list[str] = []
    while channel.recv_ready():
        chunks.append(channel.recv(4096).decode(errors="replace"))
    return "".join(chunks)


if __name__ == "__main__":
    raise SystemExit(main())
