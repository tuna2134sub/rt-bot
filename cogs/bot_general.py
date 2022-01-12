# RT - Bog General

from typing import Dict

from traceback import TracebackException
from collections import defaultdict
from inspect import cleandoc
from functools import partial
from itertools import chain
from random import choice
from time import time

from discord.ext import commands, tasks
import discord

from ujson import loads
import subprocess

from .server_tool import PERMISSION_TEXTS
from rtlib.ext import Embeds, componesy
from rtlib import RT


ERROR_CHANNEL = 842744343911596062

INFO_DESC = {
    "ja": """どうもRTという新時代Botです。
このBotは役職,投票,募集,チケットパネルやチャンネルステータスなどの定番機能はもちろん、声の変えれる読み上げやプレイリストのある音楽プレイヤーなどもある多機能Botです。
そして荒らし対策として使える画像,ウェブ,合言葉認証やスパム対策機能まであります。
またその他にもスレッド自動アーカイブ対策,自己紹介テンプレートに使える常に下にくるメッセージ,NSFW誤爆対策に使える自動画像スポイラーそしてボイスチャンネルロールなどあったら便利な機能もたくさんあります。
さあ是非このBotを入れて他のBotを蹴り飛ばしましょう！""",
    "en": """It's a new era Bot called RT.
This Bot is a multifunctional Bot with standard functions such as job title, voting, recruitment, ticket panel and channel status, as well as a music player with voice changing reading and playlists.
And there are images, web, password authentication and spam prevention functions that can be used as a troll countermeasure.
Other useful features include automatic thread archiving, always-on messages for self-introduction templates, an automatic image spoiler for NSFW detonation, and voice channel rolls.
Come on, let's put this Bot in and kick the other Bots."""
}
INFO_ITEMS = (("INVITE", {"ja": "招待リンク", "en": "invite link"}),
              ("SS", {"ja": "サポートサーバー", "en": "support server"}),
              ("URL", {"ja": "RTのウェブサイト", "en": "RT offical website"}),
              ("GITHUB", {"ja": "Github", "en": "Github"}))
INFO_INVITE = "https://discord.com/api/oauth2/authorize?client_id=716496407212589087&permissions=8&redirect_uri=https%3A%2F%2Frt-bot.com&response_type=code&scope=bot%20applications.commands"
INFO_SS, INFO_URL = "https://discord.gg/ugMGw5w", "https://rt-bot.com"
INFO_GITHUB = """* [RT-Team](https://github.com/RT-Team)
* [RT-Backend](https://github.com/RT-Team/rt-backend)
* [RT-Bot](https://github.com/RT-Team/rt-bot)
* [RT-Frontend](https://github.com/RT-Team/rt-frontend)"""

CREDIT_ITEMS = (("DEV", {"ja": "開発者", "en": "main developer"}),
                ("DESIGN", {"ja": "デザイン", "en": "designer"}),
                ("ICON", {"ja": "RTのアイコン", "en": "RT's icon"}),
                ("LANGUAGE", {"ja": "プログラミング言語", "en": "programing language"}),
                ("SERVER", {"ja": "サーバーについて", "en": "about server"}),
                ("ETC", {"ja": "その他", "en": "etc"}))
CREDIT_DEV = """<:tasren:731263470636498954> tasuren [WEBSITE](http://tasuren.f5.si)
<:takkun:731263181586169857> Takkun [SERVER](https://discord.gg/VX7ceJw)
<:Snavy:788377881092161577> Snavy [SERVER](https://discord.gg/t8fsvk3)"""
CREDIT_DESIGN = """<:yutam:732948166881575022> YUTAM
<:omochi_nagamochi:733618053631311924> 餅。"""
CREDIT_ICON = "Made by Takkun `CC BY-SA 4.0`"
CREDIT_LANGUAGE = {
    "ja": "使用言語：Python, APIラッパー：nextcord",
    "en": "language:Python, wrapper:nextcord"
}
CREDIT_SERVER = {
    "ja": cleandoc(
        """ウェブサーバーOS：Arch Linux (Snavyさんが貸してくれています。感謝感激です！)
        BotのサーバーOS:Ubuntu Server"""
    ),
    "en": "webserver os:Arch Linux\nSnavy is lend server to me. Thank you to Snavy "
}
CREDIT_ETC = {
    "ja": "* Githubのコントリビューター達\n* 翻訳協力者\nありがとうございます。",
    "en": "* Github's sontributors\n* translators \nThank you."
}
THANKYOU_TEMPLATE = cleandoc(
    """RTの導入ありがとうございます。
    よろしくお願いします。
    もし何かバグや要望があればウェブサイトから公式サポートサーバーにてお伝えください。
    公式ウェブサイト：https://rt-bot.com
    チュートリアル　：https://rt-team.github.io/notes/tutorial"""
)


class BotGeneral(commands.Cog):

    STATUS_TEXTS = (
        ("{}help | {} servers", lambda bot: len(bot.guilds)),
        ("{}help | {} users", lambda bot: len(bot.users))
    )

    def __init__(self, bot: RT):
        self.bot, self.rt = bot, bot.data
        self.wslatency = "..."
        self.cache: Dict[int, Dict[str, float]] = defaultdict(dict)
        self.remove_cache.start()

        self.make_embed_template()

    def make_embed_template(self):
        # RT情報Embedsを作る。
        embeds = self.info_embeds = []
        # RTの情報のEmbedを作る。
        embed = discord.Embed(
            title="RT 情報",
            description=INFO_DESC,
            color=self.bot.colors["normal"]
        )
        for item_variable_name, item_name in INFO_ITEMS:
            embed.add_field(
                name=item_name, value=eval("INFO_" + item_variable_name),
                inline=False
            )
        embeds.append(embed)
        # クレジットのEmbedを作る。
        embed = discord.Embed(
            title="RT クレジット",
            color=self.bot.colors["normal"]
        )
        for item_variable_name, item_name in CREDIT_ITEMS:
            embed.add_field(
                name=item_name, value=eval("CREDIT_" + item_variable_name),
                inline=False
            )
        embeds.append(embed)
        # 使用しているライブラリ
        with open("requirements.txt") as f:
            libs = f.read()
        embed = discord.Embed(
            title="使用しているライブラリ",
            description=f"```md\n{libs}\n```",
            color=self.bot.colors["normal"]
        )
        embeds.append(embed)
        del embed, libs

        self._now_status_index = 0
        self._start_time = time()
        self.status_updater.start()

    @commands.Cog.listener()
    async def on_ready(self):
        self.on_error_channel = self.bot.get_channel(ERROR_CHANNEL)

    def _get_ping(self) -> str:
        # pingを返します。
        return "%.1f" % round(self.bot.latency * 1000, 1)

    def cog_unload(self) -> None:
        self.status_updater.cancel()
        self.remove_cache.cancel()

    @tasks.loop(seconds=60)
    async def status_updater(self) -> None:
        # RTのステータスを更新するループです。
        await self.bot.wait_until_ready()

        await self.bot.change_presence(
            activity=discord.Activity(
                name=(now := self.STATUS_TEXTS[self._now_status_index])[0]
                    .format(self.bot.command_prefix[0], now[1](self.bot)),
                type=discord.ActivityType.watching, state="RT Discord Bot",
                details=f"PING：{self._get_ping()}\n絶賛稼働中...",
                timestamps={"start": self._start_time},
                buttons={"label": "RTのホームページに行く！", "url": "https://rt-bot.com/"}
            )
        )

        self._now_status_index = 0 if self._now_status_index else 1

    @commands.command(
        extras={"headding": {"ja": "レイテンシを表示します。", "en": "Show you RT latency."},
                "parent": "RT"},
        slash_command=True,
        description="レイテンシを表示します。 / Show you RT latency."
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def ping(self, ctx):
        """!lang ja
        --------
        RTのレイテンシを表示します。  
        返信された数字が400以降だとネット回線が悪いです。

        !lang en
        --------
        You can view RT latency.  
        If latency is over to 400, network is bad."""
        embed = discord.Embed(
            title={
                "ja": "現在のRTのレイテンシ",
                "en": "Latency of current RT"
            }, color=self.bot.Colors.normal
        )
        embed.add_field(
            name="Discord Connection Latency",
            value=f"{self._get_ping()}ms"
        )
        # Backendとの通信状況を調べる。
        if self.bot.backend:
            start = time()
            async with self.bot.session.get(
                f"{self.bot.get_url()}/api/ping"
            ) as r:
                if await r.text() == "pong":
                    embed.add_field(
                        name="Backend Connection Latency",
                        value="%.1fms" % round((time() - start) * 1000, 1)
                    )
        await ctx.reply(embed=embed)
        
    @commands.command(
        extras={"headding": {
            "ja": "回線速度テストします",
            "en": "Do a speed test"
        }, "parent": "RT"},
        aliases=["st"]
    )
    @commands.cooldown(1, 10800, commands.BucketType.guild)
    async def speedtest(self, ctx):
        embed = discord.Embed(
            title="速度回線テスト", description="測定中です...", color=self.bot.Colors.normal
        )
        message = await ctx.send(embed=embed)
        process = self.bot.loop.run_in_executor(
            None, subprocess.run, partial(["speedtest-cli", "--json"]), capture_output=True
        )
        data = loads(process.stdout)
        embed = discord.Embed(title="速度回線テスト")
        embed.add_field(name="ダウンロード", value=data["download"])
        embed.add_field(name="アップロード", value=data["upload"])
        await message.edit(embed=embed)

    @commands.command(
        extras={"headding": {
            "ja": "RTの招待リンクを含めた情報を表示します。",
            "en": "Show you RT's invite link."
        }, "parent": "RT"},
        aliases=["credit", "invite", "about", "情報", "じょうほう"]
    )
    @commands.cooldown(1, 180, commands.BucketType.user)
    async def info(self, ctx, secret_arg = None):
        """!lang ja
        --------
        RTの情報を表示します。  
        RTの基本情報(招待リンク,ウェブサイトURL)やクレジットなどを確認することができます。  
        このコマンドは三分に一度実行可能です。
        
        !lang en
        --------
        Show you RT's information.  
        It inclued invite link."""
        if secret_arg is None:
            await ctx.reply(
                content=f"Servers:{len(self.bot.guilds)}, Users:{len(self.bot.users)}",
                embeds=Embeds(
                    "RtInfo", ctx.author, 180, self.info_embeds
                )
            )
        else:
            await ctx.reply(f"{secret_arg}...、あなた何奴！？")

    @tasks.loop(seconds=5)
    async def remove_cache(self):
        # クールダウンを一度送信したら次送信しないようにするために使うキャッシュの期限切れの削除をする。
        now = time()
        for aid, cmds in list(self.cache.items()):
            for cmd, timeout in list(cmds.items()):
                if now > timeout:
                    del self.cache[aid][cmd]

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        # エラー時のメッセージ。翻訳はdescriptionのみ。
        kwargs, color = {}, self.bot.colors["error"]
        if isinstance(error, commands.CommandNotFound):
            # 実行しようとしたコマンドを考える。
            suggestion = f"`{suggestion}`" if (
                suggestion := "`, `".join(
                    command.name for command in self.bot.commands
                    if any(
                        any(
                            len(cmd_name[i:i + 3]) > 2
                            and cmd_name[i:i + 3] in ctx.message.content
                            for i in range(3)
                        ) for cmd_name in chain(
                            (command.name,), command.aliases
                        )
                    )
                )
            ) else "?"
            title = "404 Not Found"
            description = {
                "ja": "そのコマンドが見つかりませんでした。\n" \
                    f"`rt!help <word>`で検索が可能です。\nもしかして：{suggestion}",
                "en": f"It can't found that command.\n`rt!help <word>`This can search command.\nSuggetion:{suggestion}"}
            color = self.bot.colors["unknown"]
        elif isinstance(error, discord.Forbidden):
            title = "500 Internal Server Error"
            description = {
                "ja": "RTに権限がないため正常にコマンドを実行できませんでした。",
                "en": "The command could not be executed successfully because RT does not have permissions."
            }
        elif isinstance(error, commands.CommandOnCooldown):
            if (ctx.command.qualified_name in self.cache.get(ctx.author.id, {})
                    and not hasattr(ctx, "__setting_context__")):
                return
            else:
                title = "429 Too Many Requests"
                description = {"ja": ("現在このコマンドはクールダウンとなっています。\n"
                                    + "{:.2f}秒後に実行できます。".format(
                                        error.retry_after)),
                            "en": ("Currently, this command is on cooldown.\n"
                                    + "You can do this command after {:.2f} seconds.".format(
                                        error.retry_after))}
                self.cache[ctx.author.id][ctx.command.qualified_name] = \
                    time() + error.retry_after
                color = self.bot.colors["unknown"]
        elif isinstance(error, (commands.MemberNotFound,
                        commands.UserNotFound)):
            title = "400 Bad Request"
            description = {"ja": "指定されたユーザーが見つかりませんでした。",
                           "en": "I can't found that user."}
        elif isinstance(error, commands.ChannelNotFound):
            title = "400 Bad Request"
            description = {"ja": "指定されたチャンネルが見つかりませんでした。",
                           "en": "I can't found that channel"}
        elif isinstance(error, commands.RoleNotFound):
            title = "400 Bad Request"
            description = {"ja": "指定されたロールが見つかりませんでした。",
                           "en": "I can't found that role."}
        elif isinstance(error, commands.BadBoolArgument):
            title = "400 Bad Request"
            description = {"ja": ("指定された真偽値が無効です。\n"
                                  + "有効な真偽値：`on/off`, `true/false`, `True/False`"),
                           "en": ("The specified boolean value is invalid\n"
                                  + "Valid boolean value:`on/off`, `true/false`, `True/False`")}
        elif isinstance(
            error, (commands.BadArgument,
                commands.MissingRequiredArgument,
                commands.ArgumentParsingError,
                commands.TooManyArguments,
                commands.BadUnionArgument,
                commands.BadLiteralArgument)
        ):
            title = "400 Bad Request"
            description = {
                "ja": f"コマンドの引数が適切ではありません。\nまたは必要な引数が足りません。\nCode:`{error}`",
                "en": "It's command's function is bad."
            }
        elif isinstance(error, commands.MissingPermissions):
            title = "403 Forbidden"
            description = {
                "ja": "あなたの権限ではこのコマンドを実行することができません。\n**実行に必要な権限**\n" \
                    + ", ".join(
                        f"`{PERMISSION_TEXTS.get(name, name)}`"
                        for name in error.missing_permissions
                    ),
                "en": "You can't do this command.\n**You need these permissions**\n`" \
                    + "`, `".join(error.missing_permissions) + "`"
            }
        elif isinstance(error, commands.MissingRole):
            title = "403 Forbidden"
            description = {"ja": "あなたはこのコマンドの実行に必要な役職を持っていないため、このコマンドを実行できません。",
                           "en": "You can't do this command. Because you need permission"}
        elif isinstance(error, commands.CheckFailure):
            title = "403 Forbidden"
            description = {"ja": "あなたはこのコマンドを実行することができません。",
                           "en": "You can't do this command."}
        elif isinstance(error, commands.CommandInvokeError):
            return await self.on_command_error(ctx, error.original)
        else:
            error_message = "".join(
                TracebackException.from_exception(error).format()
            )

            print(error_message)

            title = "500 Internal Server Error"
            description = {
                "ja": (f"コマンドの実行中にエラーが発生しました。\n"
                       + f"```python\n{error_message}\n```"),
                "en": (f"I made an error!\n"
                       + f"```python\n{error_message}\n```"),
            }

            view = componesy.View("InternalServerErrorView", timeout=60)
            view.add_item(
                "link_button", style=discord.ButtonStyle.link,
                label="サポートサーバー / SupportServer", url=INFO_SS
            )
            kwargs["view"] = view

        if (length := len(description)) > 4096:
            description = description[4096 - length + 1:]
        if "400" in title:
            # 引数がおかしい場合はヘルプボタンを表示する。
            if (url := self.get_command_url(ctx.command)):
                kwargs["view"] = componesy.View("BAView")
                kwargs["view"].add_item(
                    "link_button", label="ヘルプを見る", emoji="❔",
                    url=url
                )

        kwargs["embed"] = discord.Embed(
            title=title, description=description, color=color
        )
        await ctx.send(**kwargs)

    def get_help_url(self, category: str, name: str) -> str:
        return f"https://rt-bot.com/help.html?g={category}&c={name}"

    def get_command_url(self, command: commands.Command) -> str:
        "渡されたコマンドのヘルプのURLを返します。"
        for name in self.bot.cogs["Help"].CATEGORIES:
            if self.bot.cogs["Help"].CATEGORIES[name] == command.extras.get(
                "parent", command.__original_kwargs__.get("parent", "")
            ):
                return self.get_help_url(name, command.name)
        return ""

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        try:
            await guild.owner.send(THANKYOU_TEMPLATE)
        except:
            tentative = None
            for channel in guild.text_channels:
                if "bot" in channel.name:
                    tentative = channel
                    break
                elif any(word in channel.name for word in ("雑談", "general")):
                    tentative = channel
            else:
                if tentative is None:
                    tentative = choice(guild.text_channels)
            await tentative.send(THANKYOU_TEMPLATE)


def setup(bot):
    bot.add_cog(BotGeneral(bot))
