# RT - Original Command

from discord.ext import commands
import discord

from rtlib import mysql, DatabaseManager


class DataManager(DatabaseManager):

    DB = "OriginalCommand"

    def __init__(self, db):
        self.db = db

    async def init_table(self, cursor) -> None:
        await cursor.create_table(
            self.DB, {
                "GuildID": "BIGINT", "Command": "TEXT",
                "Content": "TEXT", "Reply": "TINYINT"
            }
        )

    async def write(
        self, cursor, guild_id: int, command: str,
        content: str, reply: bool
    ) -> None:
        target = dict(GuildID=guild_id, Command=command)
        change = dict(Content=content, Reply=reply)
        if await cursor.exists(self.DB, target):
            await cursor.update_data(self.DB, change, target)
        else:
            target.update(change)
            await cursor.insert_data(self.DB, target)

    async def delete(self, cursor, guild_id: int, command: str) -> None:
        target = dict(GuildID=guild_id, Command=command)
        if await cursor.exists(self.DB, target):
            print(target)
            await cursor.delete(self.DB, target)
        else:
            raise KeyError("そのコマンドが見つかりませんでした。")

    async def read(self, cursor, guild_id: int) -> list:
        target = {"GuildID": guild_id}
        if await cursor.exists(self.DB, target):
            return [row async for row in cursor.get_datas(self.DB, target)]
        else:
            return []

    async def read_all(self, cursor) -> list:
        return [row async for row in cursor.get_datas(self.DB, {})]


class OriginalCommand(commands.Cog, DataManager):
    def __init__(self, bot):
        self.bot = bot
        self.data = {}
        self.bot.loop.create_task(self.on_ready())

    async def on_ready(self):
        super(commands.Cog, self).__init__(
            self.bot.mysql
        )
        await self.init_table()
        await self.update_cache()

    async def update_cache(self):
        self.data = {}
        for row in await self.read_all():
            if row:
                if row[0] not in self.data:
                    self.data[row[0]] = {}
                self.data[row[0]][row[1]] = {
                    "content": row[2],
                    "reply": row[3]
                }

    LIST_MES = {
        "ja": ("自動返信一覧", "部分一致"),
        "en": ("AutoReply", "Partially consistent")
    }

    @commands.group(
        aliases=["cmd", "コマンド", "こまんど"],
        extras={
            "headding": {
                "ja": "自動返信、オリジナルコマンド機能",
                "en": "Auto reply, Original Command."
            }, "parent": "ServerUseful"
        }
    )
    async def command(self, ctx):
        """!lang ja
        --------
        自動返信、オリジナルコマンド機能です。  
        `rt!command`で登録されているコマンドの確認が可能です。

        Aliases
        -------
        cmd, こまんど, コマンド

        !lang en
        --------
        Auto reply, original command.  
        You can do `rt!command` to see commands which has registered.

        Aliases
        -------
        cmd"""
        if not ctx.invoked_subcommand:
            if (data := self.data.get(ctx.guild.id)):
                lang = self.bot.cogs["Language"].get(ctx.author.id)
                embed = discord.Embed(
                    title=self.LIST_MES[lang][0],
                    description="\n".join(
                        (f"{cmd}：{data[cmd]['content']}\n　"
                         f"{self.LIST_MES[lang][1]}：{bool(data[cmd]['reply'])}")
                        for cmd in data
                    ),
                    color=self.bot.colors["normal"]
                )
                await ctx.reply(embed=embed)
            else:
                await ctx.reply(
                    {"ja": "自動返信はまだ登録されていません。",
                     "en": "AutoReplies has not registered anything yet."}
                )

    @command.command("set", aliases=["せっと"])
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 7, commands.BucketType.guild)
    async def set_command(self, ctx, command, auto_reply: bool, *, content):
        """!lang ja
        --------
        オリジナルコマンドを登録します。

        Parameters
        ----------
        command : str
            コマンド名です。
        auto_reply : bool
            部分一致で返信をするかどうかです。  
            これをonにするとcommandがメッセージに含まれているだけで反応します。  
            offにするとcommandがメッセージに完全一致しないと反応しなくなります。
        content : str
            返信内容です。

        Examples
        --------
        `rt!command set ようこそ off ようこそ！RTサーバーへ！！`
        `rt!command set そうだよ on そうだよ(便乗)`

        Aliases
        -------
        せっと

        !lang en
        --------
        Register original command.

        Parameters
        ----------
        command : str
            Command name.
        auto_reply : bool
            This is whether or not to reply with a partial match.  
            If you turn this on, it will respond only if the command is included in the message.  
            If you turn it off, it will not respond unless the command is an exact match to the message.
        content : str
            The content of the reply.

        Examples
        --------
        `rt!command set Welcome! off Welcome to RT Server!!`
        `rt!command set Yes on Yes (free ride)`"""
        await ctx.trigger_typing()
        if len(self.data.get(ctx.guild.id, ())) == 50:
            await ctx.reply(
                {"ja": "五十個より多くは登録できません。",
                 "en": "You cannot register more than 50."}
            )
        else:
            await self.write(ctx.guild.id, command, content, auto_reply)
            await self.update_cache()
            await ctx.reply("Ok")

    @command.command("delete", aliases=["del", "rm", "さくじょ", "削除"])
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 7, commands.BucketType.guild)
    async def delete_command(self, ctx, *, command):
        """!lang ja
        --------
        コマンドを削除します。

        Parameters
        ----------
        command : str
            削除するコマンドの名前です。

        Aliases
        -------
        del, rm, さくじょ, 削除

        !lang en
        --------
        Delete command.

        Parameters
        ----------
        command : str
            Target command name.

        Aliases
        -------
        del, rm"""
        await ctx.trigger_typing()
        try:
            await self.delete(ctx.guild.id, command)
        except KeyError:
            await ctx.reply(
                {"ja": "そのコマンドが見つかりませんでした。",
                 "en": "The command is not found."}
            )
        else:
            await self.update_cache()
            await ctx.reply("Ok")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return

        if ((data := self.data.get(message.guild.id))
                and message.author.id != self.bot.user.id
                and not message.content.startswith(
                    tuple(self.bot.command_prefix))
                ):
            for command in data:
                if ((data[command]["reply"] and command in message.content)
                        or command == message.content):
                    await message.reply(data[command]["content"])
                    break


def setup(bot):
    bot.add_cog(OriginalCommand(bot))
