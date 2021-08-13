import discord
import json
import asyncio
import cloudscraper
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime


dataPerSite = 2
sendMessages = []
client = discord.Client()
token = "ODQ5Mjc5NDgyODc5Mjc5MTY0.YLY3Jw.8qbqLnCeHStzvUvHQlYnW6q8InI"
scraper = cloudscraper.create_scraper()
Rerun = False
msgDelay = 2

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
    embededMessage.set_footer(text="THECOOKLAB")
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
            messageList = get_updates(dataPerSite)

        # messageList = get_selfridge(20) #get updates methods to be created
        if len(messageList) != 0:
            print(f'Sending Updates Started at {datetime.now().strftime("%H:%M:%S")}')
            for message in messageList:
                await client.wait_until_ready()
                embededMessage = message_template(message)
                try:
                    await client.get_channel(message['target_channel_id']).send(embed=embededMessage)
                    await asyncio.sleep(1 / 4)  # task runs every 60 seconds
                    print("Message Sent")
                except Exception as E:
                    print(E)
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
        print(f"Got Error Response Code: {content} While Fetching HTML data\n data: {content.content}")  # To check the Error Code of The Fetched Data
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


def get_jdsports(limit: int = -1):
    target_channel_id = 824656840234893392
    link = 'https://www.jdsports.co.uk'
    name = 'jdsports'
    productDetails = []
    t = 1
    try:
        linkList, length = extract_data(link)
    except:
        print('No Data From JDSports')
        return []
    for url in linkList:
        productData = {}
        print(f'{t}. {url}')  # It shows the Current Website Link
        try:
            status, pageData = get_html(url)
        except:
            continue

        if not status or pageData is None:
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
                productData['image'] = get_relatedImages(productData['brand'] + ' ' + productData['name'])
            try:
                productData['size'] = pageData.findAll('div', {'class': 'options', 'id': 'productSizeStock'}).text.strip()
            except:
                productData['size'] = []
            try:
                productData['color'] = pageData.find('div', {"class": "tab-info"}).find('h3').text
            except:
                productData['color'] = 'Available'
            productDetails.append(productData)
        except:
            print('parsing Error')
            continue
        if t == limit:
            break
        t += 1
        # print(t)
    print(len(productDetails))
    return productDetails


def get_footpatrol(limit: int = -1):
    target_channel_id = 824656840234893392
    link = 'https://www.footpatrol.com'
    name = 'footpatrol'
    productDetails = []
    t = 1
    try:
        linkList, length = extract_data(link)
    except:
        print('No Data From FootPatrol')
        return []
    for url in linkList:
        productData = {}
        print(f'{t}. {url}')  # It shows the Current Website Link
        try:
            status, pageData = get_html(url)
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
                productData['image'] = get_relatedImages(productData['brand'] + ' ' + productData['name'])

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


def get_sizecouk(limit: int = -1):
    target_channel_id = 824656840234893392
    link = 'https://www.size.co.uk'
    name = 'size.co'
    productDetails = []
    t = 1
    try:
        linkList, length = extract_data(link)
    except:
        print('No Data From SizeCo')
        return []
    for url in linkList:
        productData = {}
        print(f'{t}. {url}')  # It shows the Current Website Link
        try:
            status, pageData = get_html(url)
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
                productData['image'] = get_relatedImages(productData['brand'] + ' ' + productData['name'])

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


def get_selfridge(limit: int = -1):
    target_channel_id = 824415772981067846
    link = 'https://www.selfridges.com'
    name = 'selfridges'
    productDetails = []
    t = 1
    linkList, length = extract_data(link)
    if limit == -1:
        limit = length
    for url in linkList:
        if t > limit:
            break
        productData = {}
        print(f'{t}. {url}')  # It shows the Current Website Link
        try:
            status, pageData = get_html(url)
        except:
            continue

        if not status:
            print(pageData)  # It shows the Error Code
            continue
        time.sleep(0.01)

        # print(pageData.prettify())      # To see the contents of the Incoming HTML File
        # break                           # Uncomment this if you want to inspect the elements of the incoming html page
        try:
            productData['target_channel_id'] = target_channel_id
            productData['site'] = [link, name]
            productData['name'] = pageData.find('span', {'class': "a-txt-product-description"}).text.strip()
            productData['url'] = url
            productData['price'] = '£' + pageData.find('span', {'data-js-action': "updatePrice"}).text
            productData['brand'] = pageData.find('span', {'class': 'a-txt-brand-name'}).text.strip()
            try:
                productData['image'] = pageData.find('img', {'class': 'c-image-gallery__img'}).get('src')
            except:
                productData['image'] = get_relatedImages(productData['brand'] + ' ' + productData['name'])

            productData['size'] = [x.text.strip() for x in pageData.findAll('span',
                                                                            {'class': 'c-select__dropdown-item'})]
            productData['color'] = productData['size'].pop(0)
            productDetails.append(productData)
        except:
            continue
        t += 1
        # print(t)
        if t > limit:
            break
    return productDetails


def get_endclothing(limit: int = -1):
    target_channel_id = 839890080838451200
    link = 'https://www.endclothing.com'
    name = 'endclothing'
    productDetails = []
    t = 1
    linkList, length = extract_data(link)
    # print(linkList, length)
    if limit == -1:
        limit = length
    for url in linkList:
        productData = {}
        print(f'{t}. {url}')  # It shows the Current Website Link
        status, pageData = get_html(url)

        if not status:
            print(pageData)  # It shows the Error Code
            continue

        # print(pageData.prettify())      # To see the contents of the Incoming HTML File
        # break                           # Uncomment this if you want to inspect the elements of the incoming html page
        try:
            productData['target_channel_id'] = target_channel_id
            productData['site'] = [link, name]
            try:
                here = pageData.find('span', {'class': 'ProductDetails__ProductTitleSC-sc-1fqzeck-2 bLsmoN'}).text
            except:
                here = pageData.find('span', {'data-test': 'ProductDetails__Title'}).text
            productData['name'] = here
            productData['url'] = url
            try:
                prc = pageData.find('span', {'class': 'sc-1fqzeck-6 bCRXkm'}).text.strip()
            except:
                prc = pageData.find('span', {'data-test': 'PDP__Details__FinalPrice'}).text.strip()
            productData['price'] = prc
            productData['brand'] = here.split()[0]
            productData['image'] = get_relatedImages(f"{productData['brand']} {productData['name']}")
            try:
                productData['size'] = [h.get('value').strip() for h in pageData.findAll('div', {'class': 'sc-1rwf8s7-2'})]
            except:
                productData['size'] = ['Not Available']
            try:
                productData['color'] = pageData.find('span', {'class': 'sc-1fqzeck-1 hUcymt'}).text
            except:
                productData['color'] = pageData.find('span',
                                                     {'class': 'ProductDetails__ProductColourSC-sc-1fqzeck-1 dMLKzG'}).text
            productDetails.append(productData)
        except:
            continue
        t += 1
        # print(t)
        if t > limit:
            break
    return productDetails


def get_sneakersnstuff(limit: int = 10):
    target_channel_id = 824416173071269909
    link = 'https://www.sneakersnstuff.com'
    name = 'sneakersnstuff'
    productDetails = []
    t = 1
    linkList, length = extract_data(link)
    if limit == -1:
        limit = length
    for url in linkList:

        if t > limit:
            break
        productData = {}
        print(f'{t}. {url}')  # It shows the Current Website Link
        try:
            status, pageData = get_html(url)
        except:
            continue

        if not status:
            print(pageData)  # It shows the Error Code
            continue
        time.sleep(0.01)

        # print(pageData.prettify())      # To see the contents of the Incoming HTML File
        # break                           # Uncomment this if you want to inspect the elements of the incoming html page
        productData['target_channel_id'] = target_channel_id
        productData['site'] = [link, name]
        productData['name'] = pageData.find('h1', {'class': 'product-view__title'}).text.strip().split('\n')[1]
        productData['url'] = url
        productData['price'] = pageData.find('span', {'class': 'price__current'}).text.strip()
        productData['brand'] = pageData.find('a', {'class': 'product-view__title-link'}).text
        productData['image'] = get_relatedImages(productData['brand'] + ' ' + productData['name'])
        try:
            productData['size'] = [h.get('value').strip() + '/' + w.text.strip() for h in
                                   pageData.findAll('input', {'class': 'product-sizes__input'}) for w in
                                   pageData.findAll('label', {'class': 'product-sizes__label'})]
        except:
            productData['size'] = ['Not Available']
        try:
            productData['color'] = pageData.find('p', {'class': 'product-view__color'}).text
        except:
            productData['color'] = 'Available'
        productDetails.append(productData)
        t += 1
        # print(t)
    return productDetails


def get_asos(limit: int = -1):
    target_channel_id = 824415833115721729
    link = 'https://www.asos.com'
    name = 'asos'
    productDetails = []
    t = 1
    linkList, length = extract_data(link)
    if limit == -1:
        limit = length
    for url in linkList:
        try:
            productData = {}
            print(f'{t}. {url}')  # It shows the Current Website Link
            status, pageData = get_html(url)
            time.sleep(0.01)
            pageData = pageData.find("script", type="application/ld+json")
            product_data = json.loads(pageData.string)
            if not status:
                print(pageData)  # It shows the Error Code
                continue
            # print(pageData.prettify())     # To see the contents of the Incoming HTML File
            # break                          # Uncomment this if you want to inspect the elements of the incoming html page
            try:
                productData['target_channel_id'] = target_channel_id
                productData['site'] = [link, name]
                productData['name'] = product_data["name"]
                productData['url'] = url
                price_endpoint = f"https://www.asos.com/api/product/catalogue/v3/stockprice?productIds={product_data['productID']}&store=COM&currency=GBP"
                productData['price'] = requests.get(price_endpoint).json()[0]["productPrice"]["xrp"]["text"]
                productData['brand'] = product_data["brand"]['name']
                productData['image'] = get_relatedImages(f"{product_data['brand']['name']} {product_data['name']}")
                try:
                    productData['size'] = [str(product_data["productID"]), str(product_data["sku"])]
                except:
                    productData['size'] = ['Not Available']
                productData['color'] = product_data["color"]
                productDetails.append(productData)
            except:
                continue

            if t == limit:
                break
            t += 1
            # print(t)
        except:
            continue
    return productDetails


def get_updates(num: int = -1):
    dataDict = []
    retry = []
    dataDict.extend(get_selfridge(num))
    dataDict.extend(get_sneakersnstuff(num))
    for tries in range(3):
        retry = get_jdsports(num)
        if len(retry) != 0:
            break
        time.sleep(5)
    dataDict.extend(retry)

    for tries in range(3):
        retry = get_footpatrol(num)
        if len(retry) != 0:
            break
        time.sleep(5)
        tries += 1
    dataDict.extend(retry)

    for tries in range(3):
        retry = get_sizecouk(num)
        if len(retry) != 0:
            break
        time.sleep(5)
        tries += 1
    dataDict.extend(retry)

    dataDict.extend(get_endclothing(num))
    dataDict.extend(get_asos(num))

    for i in dataDict:
        print(i)
    print(len(dataDict))
    return dataDict


def reset():
    global dataFile, Rerun
    with open(dataFile, 'w') as file:
        file.write(' ')
    Rerun = False


if __name__ == '__main__':
    client.loop.create_task(my_background_task())
    client.run(token)

