import asyncio
import logging
import os
import signal
from asyncio import Event

from alchemysession import AlchemySessionContainer
from telethon import TelegramClient, events
from telethon.tl.types import PeerUser

from config import MSG_TIMEOUT, PINGER_ENABLED, DATABASE_URL, api_id, api_hash, ADMIN_IDS, BOT_LIST, PINGER_SLEEP_TIME

signals = (signal.SIGTERM, signal.SIGINT)


async def shutdown_handler(signum, loop):
    logging.info(f'Got signal {signum.name}, shutting down')
    tasks = [t for t in asyncio.all_tasks() if t is not
             asyncio.current_task()]

    [task.cancel() for task in tasks]
    logging.info(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks)
    loop.stop()


async def event_wait(evt, timeout):
    try:
        await asyncio.wait_for(evt.wait(), timeout)
    except asyncio.TimeoutError:
        pass
    logging.info("event got: %s", evt.is_set())
    return evt.is_set()


async def process_bots(bot_list, admin_entities, client, error_counters):
    for bot in bot_list:
        logging.info("Sending message to %s", bot)
        got_reply = Event()

        @client.on(events.NewMessage(chats=bot))
        async def handler(event):
            got_reply.set()
            await event.message.mark_read()
            error_counters[bot] = 0

        msg = await client.send_message(bot, '/start')
        logging.info(msg)

        if not await event_wait(got_reply, MSG_TIMEOUT):
            error_counters[bot] += 1
            if error_counters[bot] < 2:
                continue
            logging.info(f"bot={bot} doesn't respond")
            for admin_ent in admin_entities:
                await client.send_message(admin_ent, f"{bot} doesn't respond")


async def run_pinger():
    assert PINGER_ENABLED

    error_counters = {}
    container = AlchemySessionContainer(DATABASE_URL)
    session = container.new_session('session_name_shadow')
    loop = asyncio.get_event_loop()
    try:
        for s in signals:
            loop.add_signal_handler(s, lambda: asyncio.create_task(shutdown_handler(s, loop)))
    except NotImplementedError:
        pass
    try:
        async with TelegramClient(session, api_id, api_hash) as client:
            admin_entities = []
            for admin_id in ADMIN_IDS:
                admin_entities.append(await client.get_entity(PeerUser(admin_id)))
            for bot in BOT_LIST:
                error_counters[bot] = 0
            while True:
                await process_bots(BOT_LIST, admin_entities, client, error_counters)
                logging.info("Sleeping")
                await asyncio.sleep(PINGER_SLEEP_TIME)
    except asyncio.CancelledError:
        logging.info("Pinger was cancelled")
