import asyncio
import logging
import signal
from asyncio import Event

from alchemysession import AlchemySessionContainer
from telethon import TelegramClient, events
from telethon.tl.types import PeerUser

from config import get_config

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


async def process_bots(bot_list, admin_entities, client, error_counters, msg_timeout):
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

        if not await event_wait(got_reply, msg_timeout):
            error_counters[bot] += 1
            if error_counters[bot] < 2:
                continue
            logging.info(f"bot={bot} doesn't respond")
            for admin_ent in admin_entities:
                await client.send_message(admin_ent, f"{bot} doesn't respond")


async def run_pinger():
    conf = get_config()
    assert conf.pinger_enabled

    error_counters = {}
    container = AlchemySessionContainer(conf.db_url)
    session = container.new_session('session_name_shadow_new')
    loop = asyncio.get_event_loop()
    try:
        for s in signals:
            loop.add_signal_handler(s, lambda: asyncio.create_task(shutdown_handler(s, loop)))
    except NotImplementedError:
        pass
    try:
        async with TelegramClient(session,
                                  conf.pinger_config.api_id,
                                  conf.pinger_config.api_hash) as client:
            admin_entities = []
            for admin_id in conf.admin_ids:
                admin_entities.append(await client.get_entity(PeerUser(admin_id)))
            for bot in conf.pinger_config.bot_list:
                error_counters[bot] = 0
            while True:
                await process_bots(conf.pinger_config.bot_list,
                                   admin_entities,
                                   client, error_counters,
                                   conf.pinger_config.msg_timeout)
                logging.info("Sleeping")
                await asyncio.sleep(conf.pinger_config.pinger_sleep_time)
    except asyncio.CancelledError:
        logging.info("Pinger was cancelled")
