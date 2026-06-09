from ..core.context import CommandContext
from ..core.features import CommandType, Feature


class EvalFeature(
    Feature,
    name="eval",
    description="Evaluate Python code.",
    category="lol",
):
    @Feature.command(
        CommandType.PREFIX,
        name="eval",
        description="Evaluate Python code.",
        category="testing",
    )
    async def eval_command(self, ctx: CommandContext, *, code: str) -> None:
        await ctx.send(f"You said `{code}`")

    @Feature.command(
        CommandType.PREFIX,
        name="eval2",
        description="Evaluate Python code.",
    )
    async def eval2_command(self, ctx: CommandContext, *, code: str) -> None:
        await ctx.send(f"You said `{code}`")

    @Feature.command(
        CommandType.SLASH,
        name="eval",
        description="Evaluate Python code.",
    )
    async def eval_slash_command(self, ctx: CommandContext, code: str) -> None:
        await ctx.send(f"You said `{code}`")

    # @Feature.command(CommandType.USER, name="eval")
    # async def eval_user_command(
    #    self,
    #    ctx: CommandContext,
    #    user: discord.Member | discord.User,
    # ) -> None:
    #    await ctx.response.send_message(f"hello, you used eval on {user.mention}")
