#!/usr/bin/env python3
"""Small CONNECT proxy that exposes only the OpenAI API to agent containers."""

from __future__ import annotations

import asyncio
import os
from contextlib import suppress


ALLOWED_HOSTS = frozenset({"api.openai.com"})
CHATGPT_ALLOWED_HOSTS = frozenset({"auth.openai.com", "chatgpt.com"})
HEADER_LIMIT = 16 * 1024
CONNECT_TIMEOUT_SECONDS = 15


def _allowed_hosts() -> frozenset[str]:
    if os.environ.get("DEEPEE_CHATGPT_AUTH") == "1":
        return ALLOWED_HOSTS | CHATGPT_ALLOWED_HOSTS
    return ALLOWED_HOSTS


async def _close(writer: asyncio.StreamWriter) -> None:
    writer.close()
    with suppress(ConnectionError):
        await writer.wait_closed()


async def _reply(writer: asyncio.StreamWriter, status: str) -> None:
    body = f"{status}\n".encode("ascii")
    writer.write(
        f"HTTP/1.1 {status}\r\nConnection: close\r\nContent-Length: {len(body)}\r\n\r\n".encode("ascii")
        + body
    )
    await writer.drain()


async def _relay(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while data := await reader.read(64 * 1024):
            writer.write(data)
            await writer.drain()
    except (ConnectionError, asyncio.CancelledError):
        pass


def _parse_authority(authority: str) -> tuple[str, int]:
    if "@" in authority or authority.count(":") != 1:
        raise ValueError("invalid authority")
    host, port_text = authority.rsplit(":", 1)
    host = host.rstrip(".").lower()
    if not host or port_text != "443":
        raise ValueError("only HTTPS port 443 is allowed")
    return host, 443


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    peer = writer.get_extra_info("peername")
    upstream_writer: asyncio.StreamWriter | None = None
    try:
        header = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), CONNECT_TIMEOUT_SECONDS)
        if len(header) > HEADER_LIMIT:
            raise ValueError("header too large")
        request_line = header.split(b"\r\n", 1)[0].decode("ascii", errors="strict")
        method, authority, version = request_line.split(" ")
        host, port = _parse_authority(authority)
        if method != "CONNECT" or not version.startswith("HTTP/1.") or host not in _allowed_hosts():
            await _reply(writer, "403 Forbidden")
            return

        upstream_reader, upstream_writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            CONNECT_TIMEOUT_SECONDS,
        )
        writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        await writer.drain()
        downstream = asyncio.create_task(_relay(reader, upstream_writer))
        upstream = asyncio.create_task(_relay(upstream_reader, writer))
        done, pending = await asyncio.wait(
            {downstream, upstream},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        await asyncio.gather(*done, *pending, return_exceptions=True)
    except (ValueError, UnicodeError, asyncio.IncompleteReadError, asyncio.LimitOverrunError):
        with suppress(ConnectionError):
            await _reply(writer, "400 Bad Request")
    except (OSError, asyncio.TimeoutError):
        with suppress(ConnectionError):
            await _reply(writer, "502 Bad Gateway")
    finally:
        if upstream_writer is not None:
            await _close(upstream_writer)
        await _close(writer)
        print(f"closed tunnel from {peer}", flush=True)


async def main() -> None:
    port = int(os.environ.get("DEEPEE_PROXY_PORT", "3128"))
    server = await asyncio.start_server(handle_client, "0.0.0.0", port, limit=HEADER_LIMIT)
    print(f"OpenAI API egress proxy listening on {port}", flush=True)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
