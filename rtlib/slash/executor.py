# rtlib.slash - Command Executor

from typing import Type, List

from discord.ext import commands
import discord

from inspect import signature, isfunction, iscoroutinefunction
from .application_command import ApplicationCommand
from .option import Option
from .types import Context


async def executor(
        bot: Type[commands.Bot], application: ApplicationCommand,
        command: Type[commands.Command], type_: int,
        options: List[Option] = None
    ) -> None:
    if type_ == 2:
        # グループコマンドならコマンドをオプションの中から探し出しまたそれを実行する。
        option = options[0]
        return await executor(
            bot, application,
            discord.utils.get(command.commands, name=option.name),
            option.type, option.options
        )
    else:
        # グループコマンドじゃないならそれはコマンドのはず。
        # なので引数を用意してコマンドを実行する。
        # まずはContextを作る。
        ctx = Context(bot, application)

        # コマンドにあるcheckを実行する。
        if await bot.can_run(ctx):
            # optionsの中に引数に設定されたものがあるからそれを取り出す。
            args = ([application.command.cog]
                    if application.command.cog else [])
            args.append(ctx)
            kwargs = {}
            state = bot._connection

            for parameter, option in zip(
                list(
                    signature(
                        command.callback
                    ).parameters.values()
                )[len(args):],
                options
            ):
                annotation = parameter.annotation
                if isinstance(annotation, Option):
                    annotation = annotation.annotation
                # 型変換を行う。
                if annotation == discord.User:
                    option.value = discord.User(
                        state=state, data=option.value
                    )
                elif annotation == discord.Member:
                    option.value = discord.Member(
                        data=option.value, guild=ctx.guild, state=state
                    )
                elif annotation == discord.Member:
                    option.value = discord.Role(
                        guild=ctx.guild, state=state, data=option.value
                    )
                elif annotation in (
                    discord.TextChannel, discord.VoiceChannel,
                    discord.Thread, discord.StageChannel,
                    discord.CategoryChannel
                ):
                    option.value = ctx.guild.get_channel_or_thread(
                        int(option.value)
                    )
                elif isfunction(annotation):
                    coro = annotation(option.value)
                    if iscoroutinefunction(annotation):
                        option.value = await coro
                    else:
                        option.value = coro
                kwargs[parameter.name] = option.value

            # 取り出した引数を使ってコマンドを実行する。
            await command.callback(*args, **kwargs)
        else:
            ctx.send = ctx.reply
            bot.dispatch("command_error", ctx, commands.CheckFailure("足りない役職があります。"))