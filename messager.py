import time

import discord
import asyncio
messages = [{'name': 'Nike Blazer Low',
             'url': 'https://www.jdsports.co.uk/product/black-nike-blazer-low/16140811/',
             'price': '£85.00', 'sizes': ['6 / 16140811.0194955932933',
                                          '6.5 / 16140811.0194955932940',
                                          '7 / 16140811.0194955932957',
                                          '7.5 / 16140811.0194955932964',
                                          '8 / 16140811.0194955932971',
                                          '8.5 / 16140811.0194955932988',
                                          '9 / 16140811.0194955932995',
                                          '9.5 / 16140811.0194955933008',
                                          '10 / 16140811.0194955933015',
                                          '10.5 / 16140811.0194955933022',
                                          '11 / 16140811.0194955933039',
                                          '11.5 / 16140811.0194955933046',
                                          '13 / 16140811.0194955933060'],
             'image': 'https://i8.amplience.net/i/jpl/jd_412997_a?qlt=92&w=160&h=113&v=1',
             'brand': "Nike"}]

client = discord.Client()
target_channel_id = 824656840234893392
token = "ODQzMTM4MzE3NjQ1MzgxNjUy.YJ_fvw._r7lPGQ0cJHctmR7pDcieHql5E0"


async def my_background_task(messages):
    await client.wait_until_ready()
    counter = 0
    k = 0
    while True:
        for message in messages:
            embededMessage = discord.Embed(title=message['name'],
                                           url=message['url'],
                                           color=0xBF40BF,
                                           description="New Product")
            embededMessage.set_thumbnail(url=message['image'])
            embededMessage.add_field(name="Price", value=message['price'], inline=False)
            for i in message['sizes']:
                embededMessage.add_field(name="sizes", value=i, inline=False)
            embededMessage.set_footer(text="THECOOKLAB")

            await client.get_channel(target_channel_id).send(embed=embededMessage)
            await asyncio.sleep(1)  # task runs every 60 seconds
        time.sleep(60*30)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.loop.create_task(my_background_task(messages))
client.run(token)
