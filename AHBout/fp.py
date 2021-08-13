import time
import gatherer
import discord
import asyncio
from datetime import datetime

dataPerSite = 2
sendMessages = []
client = discord.Client()
token = "ODQ5Mjc5NDgyODc5Mjc5MTY0.YLY3Jw.8qbqLnCeHStzvUvHQlYnW6q8InI"
Rerun = False
prevData = []

codeList = {
    'https://www.jdsports.co.uk': ['/men/mens-footwear/brand/jordan/latest/?max=72',
                                   ['li', {'class': 'productListItem'}]],
    'https://www.footpatrol.com': [
        '/footwear/brand/jordan/latest/?fp_sort_order=latest',
        ['li', {'class': 'productListItem'}]],
    'https://www.size.co.uk': ['/mens/footwear/brand/jordan/latest/',
                               ['li', {'class': 'productListItem'}]],
    'https://www.selfridges.com': ['/GB/en/cat/mens/shoes/jordan/nike/?fh_sort_by=newest',
                                   ['div', {'class': 'col-xs-6 col-sm-4 c-listing-items__item'}]],
    'https://www.endclothing.com': [
        '/gb/latest-products/latest-sneakers?brand=Nike%20Jordan&brand=Nike%20SB&page=1',
        ['a', {'data-test': "ProductCard__ProductCardSC"}]],
    'https://www.sneakersnstuff.com': ['/en/858/mens-new-arrivals?p=5954&orderBy=Published',
                                       ['article', {'class': 'card product'}]],
    'https://www.asos.com': [
        '/men/new-in/new-in-shoes/cat/?cid=17184&currentpricerange=5-195&nlid=mw%7Cnew'
        '%20in%7Cnew%20products%7Cshoes&refine=brand:2986&sort=freshness',
        ['article', {'class': '_2qG85dG'}]]}


def message_template(message: {}):
    embededMessage = discord.Embed(title=message['brand'] + ' ' + message['name'], url=message['url'], color=0xBF40BF,
                                   description='New Product')
    embededMessage.set_thumbnail(url=message['image'])
    embededMessage.add_field(name='Brand', value=message['brand'], inline=True)
    embededMessage.add_field(name="Price", value=message['price'], inline=True)
    if message['size'] is not None and len(message['size']) != 0:
        sizeStr = '\n'.join(message['size'])
        if len(sizeStr) > 1020:
            sizeStr = sizeStr[0:1018] + '+more'
        embededMessage.add_field(name="Sizes", value=sizeStr, inline=False)
    else:
        embededMessage.add_field(name="Availability", value='In Stock', inline=False)
    if message['color'] == '':
        message['color'] = "Available"
    embededMessage.add_field(name="Colors", value=message['color'], inline=True)
    embededMessage.add_field(name="Website", value=message['site'][0], inline=True)
    embededMessage.set_footer(text="THECOOKLAB")
    return embededMessage


async def my_background_task():
    global Rerun, sendMessages, msgDelay
    await client.wait_until_ready()
    while True:
        messageList = get_updates(dataPerSite)

        if len(messageList) != 0:
            print(f'Sending Updates Started at {datetime.now().strftime("%H:%M:%S")}')
            for message in messageList:
                await client.wait_until_ready()
                embededMessage = message_template(message)
                try:
                    await client.get_channel(message['target_channel_id']).send(embed=embededMessage)
                    await asyncio.sleep(1 / 20)  # task runs every 60 seconds
                    print("Message Sent")
                except Exception as E:
                    print(E)
                    continue

            messageList.clear()
        print(f'Updates Sent at {datetime.now().strftime("%H:%M:%S")}')
        time.sleep(60 * msgDelay)


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


def get_footpatrol(limit: int = -1):
    global prevData
    target_channel_id = 824656840234893392
    link = 'https://www.footpatrol.com'
    name = 'footpatrol'
    productDetails = []
    t = 1
    try:
        linkList, length = gatherer.extract_data(link)
    except:
        print('No Data From FootPatrol')
        return []
    for url in linkList:
        if url in prevData:
            continue
        else:
            if len(prevData) >= 100:
                prevData.clear()
            prevData.append(url)

        productData = {}
        print(f'{t}. {url}')  # It shows the Current Website Link
        try:
            status, pageData = gatherer.get_html(url)
        except:
            continue

        if not status:
            print(pageData)  # It shows the Error Code
            continue
        time.sleep(0.025)

        # print(pageData.prettify())      # To see the contents of the Incoming HTML File
        # break                           # Uncomment this if you want to inspect the elements of the incoming html page
        try:
            productData['target_channel_id'] = target_channel_id
            productData['site'] = [link, name]
            productData['name'] = pageData.find('h1', {'itemprop': "name"}).text.strip()
            productData['url'] = url
            productData['price'] = pageData.find('span', {'class': "pri"}).text
            productData['brand'] = pageData.find('h1', {'itemprop': "name"}).text.strip().split()[0]
            try:
                productData['image'] = pageData.find('img', {'class': 'c-image-gallery__img'}).get('src')
            except:
                productData['image'] = gatherer.get_relatedImages(productData['brand'] + ' ' + productData['name'])

            productData['size'] = pageData.find('div', {'class': 'options', 'id': 'productSizeStock'}).text.strip()
            try:
                productData['color'] = pageData.find('div', {"class": "tab-info"}).find('h3').text
            except:
                productData['color'] = 'Available'
            productDetails.append(productData)
        except:
            continue

        if t == limit:
            break
        t += 1
        # print(t)
    print(len(productDetails))
    return productDetails


def get_updates(num: int = -1):
    dataDict = []
    retry = []

    for tries in range(3):
        retry = get_footpatrol(num)
        if len(retry) != 0:
            break
        time.sleep(5)
        tries += 1
    dataDict.extend(retry)

    for i in dataDict:
        print(i)
    print(len(dataDict))
    return dataDict


if __name__ == '__main__':
    t1 = str(input("Enter Token: "))
    if t1 != '':
        token = t1
    dataPerSite = int(input("Enter Data Per Site to be Gathered: "))
    msgDelay = int(input("Enter Delay: "))
    client.loop.create_task(my_background_task())
    client.run(token)
