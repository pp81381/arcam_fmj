"""Test with a fake server"""

import asyncio
from arcam.fmj import CommandCodes, AnswerCodes, ResponseException, CommandNotRecognised
from arcam.fmj.server import Server
from arcam.fmj.client import Client
from arcam.fmj.state import State
import pytest
import logging
from unittest.mock import MagicMock, call

_LOGGER = logging.getLogger(__name__)

@pytest.mark.asyncio
@pytest.fixture
async def server(event_loop):
    async with Server('localhost', 8888) as s:
        s.register_handler(0x01, CommandCodes.POWER, bytes([0xF0]),
            lambda **kwargs: (AnswerCodes.STATUS_UPDATE, bytes([0x00]))
        )
        s.register_handler(0x01, CommandCodes.VOLUME, bytes([0xF0]),
            lambda **kwargs: (AnswerCodes.STATUS_UPDATE, bytes([0x01]))
        )
        yield s

@pytest.mark.asyncio
@pytest.fixture
async def client(event_loop):
    async with Client("localhost", 8888, loop=event_loop) as c:
        yield c

@pytest.mark.asyncio
async def test_power(event_loop, server, client):
    data = await client.request(0x01, CommandCodes.POWER, bytes([0xF0]))
    assert data == bytes([0x00])

@pytest.mark.asyncio
async def test_multiple(event_loop, server, client):
    data = await asyncio.gather(
        client.request(0x01, CommandCodes.POWER, bytes([0xF0])),
        client.request(0x01, CommandCodes.VOLUME, bytes([0xF0])),
    )
    assert data[0] == bytes([0x00])
    assert data[1] == bytes([0x01])

@pytest.mark.asyncio
async def test_invalid_command(event_loop, server, client):
    with pytest.raises(CommandNotRecognised):
        await client.request(0x01, 0xff, bytes([0xF0]))

@pytest.mark.asyncio
async def test_state(event_loop, server, client):
    state = State(client, 0x01)
    await state.update()
    assert state.get(CommandCodes.POWER) == bytes([0x00])
    assert state.get(CommandCodes.VOLUME) == bytes([0x01])