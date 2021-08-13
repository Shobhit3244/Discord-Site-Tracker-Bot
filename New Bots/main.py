import discord
import asyncio
import cloudscraper
import requests
from bs4 import BeautifulSoup
import time
import json
# import keep_alive
from datetime import datetime


dataFile: str = 'MessageData.txt'
dataPerSite = 2
sendMessages = []
client = discord.Client()
token = "ODQ5Mjc5NDgyODc5Mjc5MTY0.YLY3Jw.8qbqLnCeHStzvUvHQlYnW6q8InI"
scraper = cloudscraper.create_scraper()
Rerun = False
msgDelay = 2

codeList = {
    'https://www.footlocker.sg': [
        '/en/men/shoes/',
        ['div', {'class': 'fl-category--productlist--item'}]],
}


def timeTracker(startTime):
    currentTime = time.time()
    maxTime = startTime + 10
    if maxTime < currentTime:
        raise Exception("Max Time Used")


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
    embededMessage.set_footer(text="BULLY AIO")
    return embededMessage


async def my_background_task():
    global Rerun, dataPerSite, msgDelay
    await client.wait_until_ready()
    while True:
        if not Rerun:
            print("Generating New Message List")
            messageList = get_updates(dataPerSite)
        else:
            print("Gathering New Update List")
            messageList = check_messages()

        # messageList = get_selfridge(20) #get updates methods to be created
        if len(messageList) != 0:
            print(f'Updates Sending Started at {datetime.now().strftime("%H:%M:%S")}')
            for message in messageList:
                embededMessage = message_template(message)
                try:
                    await client.get_channel(message['target_channel_id']).send(embed=embededMessage)
                    await asyncio.sleep(1 / 4)  # task runs every 60 seconds
                except:
                    continue

            messageList.clear()
            print(f'Updates Sent at {datetime.now().strftime("%H:%M:%S")}')

        else:
            print('No Latest Products Uploaded')
        Rerun = True
        # break  # Uncomment this while Testing to send the messages Once
        time.sleep(60 * msgDelay)    # It is the time in which the loop will Rerun in seconds


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


def get_html(url: str):
    try:
        content = scraper.get(url)
    except:
        return False, 'CloudFlare 2 Detected'
    reader = BeautifulSoup(content.content, 'html.parser')
    if str(content).strip() != "<Response [200]>":
        print(f"Got Error Response Code: {content} While Fetching HTML data\n")  # To check the Error Code of The Fetched Data
        return False, f"Got Error Response Code: {content}"
    else:
        return True, reader


def get_relatedImages(query: str):
    GOOGLE_IMAGE = 'https://www.google.com/search?site=&tbm=isch&source=hp&biw=1873&bih=990&'
    if " " in query:
        query = '%20'.join(query.split(' '))
    url = GOOGLE_IMAGE + 'q=' + query
    response = requests.get(url).content
    soup = BeautifulSoup(response, 'html.parser')
    # print(url)                # Uncomment to see the image url
    return soup.find('img', {"class": "t0fcAb"}).get('src')


def extract_data(site: str):
    global codeList
    # print(site)
    # required_data = ['name', 'url', 'price', 'size', 'image', 'brand']
    availability, receivedData = get_html(site + codeList[site][0])
    # print(receivedData.prettify())        # To see the contents of the Incoming HTML File

    if not availability:
        return ['Error Fetching Data: Please Try Again Later'], availability

    listingsSites = receivedData.findAll(codeList[site][1][0], codeList[site][1][1])
    linkList = set()

    for products in listingsSites:
        try:
            link = products.find('a')['href']
        except:
            link = products.get('href')
        # print(link)       # To See the List of Product Links on the Search Page
        if link.startswith(site):
            linkList.add(link)
        else:
            linkList.add(site + link)

    print(len(linkList))       # To See the number of links found
    return linkList, len(linkList)


def get_flocker(limit: int = -1):
    target_channel_id = 839890080838451200
    link = 'https://www.footlocker.sg'
    name = 'footlocker'
    productDetails = []
    t = 0
    linkList, length = extract_data(link)
    if limit == -1:
        limit = length
    for url in linkList:

        if t == limit:
            break
        productData = {}
        print(f'{t+1}. {url}')  # It shows the Current Website Link
        try:
            status, pageData = get_html(url)
        except:
            continue

        if not status:
            print(pageData)  # It shows the Error Code
            continue
        time.sleep(0.2)

        # print(pageData.prettify())      # To see the contents of the Incoming HTML File
        # break                           # Uncomment this if you want to inspect the elements of the incoming html page
        try:
            productData['target_channel_id'] = target_channel_id
            productData['site'] = [link, name]
            productData['name'] = pageData.find('h1', {'class': 'fl-product-details--headline'}).text.strip()
            productData['url'] = url
            productData['price'] = pageData.find('span', {'class': 'fl-price--sale'}).text.strip()
            productData['brand'] = pageData.find('h1', {'class': 'fl-product-details--headline'}).text.strip().split()[0]
            productData['image'] = get_relatedImages(productData['brand'] + ' ' + productData['name'])
            try:
                productData['size'] = [h.text.strip() for h in
                                       pageData.findAll('button', {'class': 'fl-product-size--item'})]
            except:
                productData['size'] = ['Not Available']
            try:
                productData['color'] = pageData.find('p', {'class': 'ProductDetails-form__label'}).text
            except:
                productData['color'] = 'Available'
        except:
            print("parsing Error")
            continue
        productDetails.append(productData)
        t += 1
        # print(t)
    return productDetails


def get_updates(num: int = -1):
    global dataFile
    dataDict = []
    dataDict.extend(get_flocker(num))
    print("got footlocker")

    for i in dataDict:
        print(i)
    print(len(dataDict))
    with open(dataFile, 'w') as messageFile:
        json.dump(dataDict, messageFile)
    return dataDict


def check_messages():
    global dataPerSite, Rerun, dataFile
    with open(dataFile, 'r') as messageFile:
        messages = json.load(messageFile)
    newMessages = get_updates(dataPerSite)
    del_data = []
    for i in newMessages:
        if i in messages:
            del_data.append(i)

        elif i not in messages:
            messages.append(i)

    if len(del_data) > 0:
        for i in del_data:
            newMessages.remove(i)

    with open(dataFile, 'w') as messageFile:
        json.dump(messages, messageFile)
    Rerun = False
    return newMessages


def reset():
    global dataFile, Rerun
    with open(dataFile, 'w') as file:
        file.write(' ')
    Rerun = False


if __name__ == '__main__':
    # get_updates()
    # keep_alive.keep_alive()
    client.loop.create_task(my_background_task())
    client.run(token)
