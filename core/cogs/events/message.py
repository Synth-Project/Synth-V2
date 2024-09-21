import disnake
from disnake.ext import commands
import g4f

from core.misc.embed import CustomEmbed


class MessageLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(MessageLogging, self).__init__()

        self.bot = bot
        self.conversation_history = {}

    async def ask_gpt(self, prompt: str, user_id: int) -> str:
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        self.conversation_history[user_id].append({"role": "user", "content": prompt})
        messages = self.conversation_history[user_id]
        response = await g4f.ChatCompletion.create_async(
            model=g4f.models.gpt_4o, messages=messages
        )
        self.conversation_history[user_id].append(
            {"role": "assistant", "content": response}
        )
        return response

    def split_message(self, message: str, limit: int = 2000):
        return [message[i : i + limit] for i in range(0, len(message), limit)]

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message) -> None:
        if message.author.bot or message.content.startswith("!"):
            return
        async with message.channel.typing():
            response = await self.ask_gpt(message.content, message.author.id)
            print(message.author.name)
            print(self.conversation_history)
            embed = CustomEmbed(title="⚙ | GPT", description=response).get_embed()
            await message.reply(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(MessageLogging(bot))
