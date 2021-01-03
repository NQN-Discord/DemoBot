from rabbit_helper import Rabbit
from nqn_common.dpy import DpyRabbit


class DemoBaseRabbit(DpyRabbit):
    @Rabbit.receiver(x_message_ttl=60_000)
    async def parse_rendered_emote_1(self, data):
        await self._assert_or_fetch_guild_id(data["guild_id"])
        guild = self.bot.get_guild(int(data["guild_id"]))
        await guild.all()
        print(guild)
        print(data)
