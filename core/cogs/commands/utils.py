from disnake.ext import commands
import disnake
from PIL import Image, ImageDraw, ImageFont
import io

class Utilities(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super(Utilities, self).__init__()
        self.bot = bot

    @commands.slash_command(name="watermark")
    async def watermark(self, interaction, attachment: disnake.Attachment ,text: str = commands.Param(max_length=50, min_length=1, default="Synth")):
        await interaction.response.defer()
        # Watermark System. TODO: rewrite this shit lol
        if attachment.content_type == "image/png" or attachment.content_type == "image/jpeg" or attachment.content_type == "image/jpg":
            image_bytes = await attachment.read()
            image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

            base_size = min(image.size) // 8
            font = ImageFont.truetype("arial.ttf", base_size)

            text_image = Image.new("RGBA", image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(text_image)
            
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            position = ((image.width - text_width) // 2, (image.height - text_height) // 2)

            draw.text(position, text, font=font, fill=(255, 255, 255, 128))

            rotated_text_image = text_image.rotate(40, expand=True)
            rotated_text_image = rotated_text_image.crop(rotated_text_image.getbbox())

            final_image = Image.new("RGBA", image.size)
            final_image.paste(rotated_text_image, (0, 0), rotated_text_image)
            final_image = Image.alpha_composite(image, final_image)

            image_stream = io.BytesIO()
            final_image.save(image_stream, format="PNG")
            image_stream.seek(0)

            file = disnake.File(fp=image_stream, filename="watermarked_image.png")
            await interaction.send("Watermark", file=file)
        else:
            await interaction.send("This is not an image!", ephemeral=True)

def setup(bot: commands.Bot) -> None:
    bot.add_cog(Utilities(bot))
