#!/usr/bin/env python

#
# Dead simple server-sent event (SSE) server. No authentication, no frills.
# Server is protected by nginx's "internal" flag and authenticated by Django
# and an X-Accel-Redirect
#
# GET:/ -- subscribes to messages
# GET:/test -- test page
#
# Publish valid JSON strings to redis channel sse::messages
#

import asyncio
from weakref import WeakSet

from aiohttp import web
from aiohttp_sse import sse_response
import aioredis


MESSAGE_DELAYS = {
    'metadata': 5,  # Arbitrary, based on empirical evidence
}
REDIS_PUBSUB_CHANNEL = "sse::messages"  # Duplicated in backend/jew_pizza/constants.py
DISCONNECT = object()
TEST_HTML = open("/app/test.html", "rb").read()


async def process_delayed_message(app, message, delay):
    await asyncio.sleep(delay)
    process_message(app, message, can_delay=False)


def process_message(app, message, can_delay=True):
    message_split = message.split(":", 1)
    if len(message_split) == 2:
        message_type, message_body = message_split
        if can_delay and (delay := MESSAGE_DELAYS.get(message_type)):
            if app['DEBUG']:
                print(f'Delaying {message_type} message for {delay} seconds')

            asyncio.create_task(process_delayed_message(app, message, delay))

        else:
            app["last_messages"][message_type] = message_body

            num_written = 0
            for num_written, queue in enumerate(app["client_queues"], 1):
                queue.put_nowait(message)

            if app["DEBUG"]:
                print(f'Sent {message_type!r} to {num_written} subscriber(s): {message_body}')


async def redis_subscriber(app):
    try:
        redis = await aioredis.from_url("redis://redis")
        pubsub = redis.pubsub()
        await pubsub.subscribe(REDIS_PUBSUB_CHANNEL)

        while True:
            async for message in pubsub.listen():
                if message["type"] == "message" and message["data"]:
                    process_message(app, message["data"].decode())

    except asyncio.CancelledError:
        pass


async def subscribe(request):
    request.app["client_queues"].add(queue := asyncio.Queue())

    async with sse_response(request, headers={"Access-Control-Allow-Origin": "*"}) as resp:
        for message_type, message_body in request.app["last_messages"].items():
            await resp.send(f"{message_type}:{message_body}")
        while message := await queue.get():
            if message is DISCONNECT:
                break
            await resp.send(message)
    return resp


async def test(response):
    if response.app["DEBUG"]:
        return web.FileResponse("/app/test.html")
    else:
        return web.Response(body=TEST_HTML, content_type="text/html")


async def on_startup(app):
    app["client_queues"] = WeakSet()
    app["last_messages"] = {}
    app["redis_subscriber"] = asyncio.create_task(redis_subscriber(app))


async def on_shutdown(app):
    app["redis_subscriber"].cancel()
    await app["redis_subscriber"]
    for queue in app["client_queues"]:
        await queue.put(DISCONNECT)


app = web.Application()
app.router.add_route("GET", "/", subscribe)
app.router.add_route("GET", "/test", test)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
app["DEBUG"] = False

if __name__ == "__main__":
    app["DEBUG"] = True
    web.run_app(app, host="0.0.0.0", port=8001)
