from typing import Union

import disnake
from disnake import ui, ButtonStyle, MessageInteraction


class PreviousButton(ui.Button):
    def __init__(self, disabled):
        super().__init__(
            label="<=",
            style=ButtonStyle.blurple,
            disabled=disabled,
            custom_id="previous",
        )

    async def callback(self, inter: MessageInteraction) -> None:
        """
        Callback for the button.
        :param inter: MessageInteraction
        :return: None
        """
        view: CreatePaginator = self.view
        try:
            if view.author_id:
                if inter.author.id != view.author_id:
                    return await inter.send(
                        "You cannot interact with these buttons.", ephemeral=True
                    )
            if view.current_embed:
                await inter.response.edit_message(
                    embed=view.embeds[view.current_embed - 1]
                )
                view.current_embed = view.current_embed - 1

                if view.current_embed == 0:
                    self.disabled = True
                for btn in view.children:
                    if btn.custom_id == "next":
                        btn.disabled = False
                await inter.edit_original_message(view=view)

        except:
            await inter.send("Unable to change the page.", ephemeral=True)


class NextButton(ui.Button):
    def __init__(self, disabled):
        super().__init__(
            label="=>", style=ButtonStyle.blurple, disabled=disabled, custom_id="next"
        )

    async def callback(self, inter: MessageInteraction) -> None:
        view: CreatePaginator = self.view
        try:
            if view.author_id:
                if inter.author.id != view.author_id:
                    return await inter.send(
                        "You cannot interact with these buttons.", ephemeral=True
                    )

            await inter.response.edit_message(embed=view.embeds[view.current_embed + 1])
            view.current_embed += 1

            if view.current_embed + 1 == len(view.embeds):
                self.disabled = True
            for btn in view.children:
                if btn.custom_id == "previous":
                    btn.disabled = False
            await inter.edit_original_message(view=view)

        except:
            await inter.send("Unable to change the page.", ephemeral=True)


class CreatePaginator(ui.View):
    """
    Paginator for Embeds.
    :param embeds: The list of embeds.
    :param author_id: The author of the embeds.
    :param timeout: The timeout of the paginator.
    :return:
    """

    def __init__(self, embeds, author_id: int = None, timeout: float = None):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.author_id = author_id
        self.current_embed = 0

        for index, embed in enumerate(self.embeds):
            embed.set_footer(text=f"Page {index + 1}/{len(self.embeds)}")

        disabled = len(embeds) == 1
        self.add_item(PreviousButton(True))
        self.add_item(NextButton(disabled))

    @staticmethod
    def generate_embeds(
        items: list,
        items_per_embed: int,
        empty_list_message: str,
        title: str = None,
        description: str = None,
    ) -> list[disnake.Embed]:
        splitted_items = [
            items[i : i + items_per_embed]
            for i in range(0, len(items), items_per_embed)
        ]
        embeds = []

        if len(items) == 0:
            embed = disnake.Embed(
                title=title,
                description=empty_list_message,
            )
            return [embed]

        for chunk in splitted_items:
            embed = custom_embed(title=title, description=description or "")
            embed.description += "\n" * 1

            for item in chunk:
                if isinstance(item, tuple):
                    embed.add_field(name=item[0], value=item[1], inline=item[2])
                else:
                    embed.description += f"{item}\n"

            embeds.append(embed)

        return embeds


def custom_embed(
    title: str = None,
    description: str = "",
    color: Union[disnake.Colour, int, None] = 0x2F3236,
    image: str = None,
    thumbnail: str = None,
) -> disnake.Embed:
    """
    Create a custom embed.
    :param title: The title of the embed.
    :param description: The description of the embed.
    :param color: The color of the embed.
    :param image: The image of the embed.
    :param thumbnail: The thumbnail of the embed.
    :return: The created embed.
    """

    embed = disnake.Embed()
    embed.set_footer(text="Synth © 2024 | All Rights Reserved")

    embed.title = title
    embed.description = description
    embed.colour = color
    embed.set_image(url=image)
    embed.set_thumbnail(url=thumbnail)

    return embed
