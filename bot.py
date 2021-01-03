from discord import Client
import aioredis
from logging import getLogger

from elastic_helper import ElasticSearchClient
from sql_helper import SQLConnection
from sql_helper.metrics import sql_wrapper

from nqn_common import dpy, GlobalContext

from rabbit_parsers import DemoBaseRabbit


log = getLogger(__name__)


async def initialise(config, postgres_pool):
    elastic = ElasticSearchClient(config["elastic"]["hosts"])
    bot = Client()

    log.info("Connecting to Redis")
    persistent_redis = await aioredis.create_redis_pool(config["persistent_redis_uri"], encoding="utf-8")
    nonpersistent_redis = await aioredis.create_redis_pool(config["nonpersistent_redis_uri"], encoding="utf-8")

    log.info("Connecting to PostgreSQL")
    postgres: SQLConnection = SQLConnection(
        postgres_pool,
        bot.get_guild,
        sql_wrapper("commands")
    )

    await dpy.connect(
        bot,
        nonpersistent_redis,
        config["discord"]["proxy"],
        config["discord"]["token"]
    )

    log.info("Connecting to RabbitMQ")
    guild_cache = dpy.GuildCache(bot, nonpersistent_redis)
    rabbit = DemoBaseRabbit(bot, guild_cache, config["rabbit_uri"])

    log.info("Initialising global context")
    bot.global_ctx = GlobalContext.from_databases(
        owner=bot.owner,
        bot_user=bot.user,
        postgres=postgres,
        elastic=elastic,
        persistent_redis=persistent_redis,
        nonpersistent_redis=nonpersistent_redis,
        get_guild=bot.get_guild,
        get_emoji=bot.get_emoji,
        emote_hasher_url=config["hasher_url"],
        webhook_url=config["webhook_url"],
        user_emote_cache_time=config.get("user_emote_cache_time", 10),
        broadcast_prefix=rabbit.send_prefix
    )

    log.info("Bot initialised, connecting to Discord")
    await guild_cache.load_state_from_redis()
    await bot.global_ctx.aliases.update_alias_servers()

    async def cleanup():
        pass

    dpy.take_over_the_world(
        rabbit=rabbit,
        redis=nonpersistent_redis,
        process_name="demo_base_bot",
        world_takeover_sleep=config.get("world_takeover_sleep", 5),
        cleanup=cleanup()
    )

    log.info("Finished initialising")
