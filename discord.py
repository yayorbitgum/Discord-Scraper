"""
@author:  Dracovian
@date:    2021-02-10
@fork:    Yayorbitgum
@update:  2022-01-30
@license: WTFPL
"""
# datetime.timedelta: Used to subtract an entire day from the current one.
# datetime.datetime:  Used to retrieve the current day.
from datetime import timedelta, datetime
# module.DiscordScraper: Used to access the Discord Scraper class functions.
from module import DiscordScraper
# module.DiscordScraper.loads: Used to access the json.loads function documented in the DiscordScraper class file.
from module.DiscordScraper import loads


def getLastMessageGuild(scraper, guild_messages, guild_channel):
    """
    Use the official Discord API to retrieve the last publicly viewable message in a channel.
    :param scraper: The DiscordScraper class reference that we will be using.
    :param guild_messages: The ID for the guild that we're wanting to scrape from.
    :param guild_channel: The ID for the channel that we're wanting to scrape from.
    """
    # Generate a valid URL to the documented API function for retrieving channel messages
    # (we don't care about the 100 message limit this time).
    message_limit = 1
    lastmessage = f'https://discord.com/api' \
                  f'/{scraper.apiversion}' \
                  f'/channels/{guild_channel}' \
                  f'/messages?limit={message_limit}'
    # Update the HTTP request headers to set the referer to the current guild channel URL.
    scraper.headers.update({'Referer': f'https://discord.com/channels/{guild_messages}/{guild_channel}'})

    try:
        # Execute the network query to retrieve the JSON data.
        response = DiscordScraper.requestData(lastmessage, scraper.headers)
        # If we returned nothing then return nothing.
        if response is None:
            return None

        # Read the response data and convert it into a dictionary object.
        data = loads(response.read())
        # Retrieve the snowflake of the post and convert it into a timestamp.
        timestamp = DiscordScraper.snowflakeToTimestamp(int(data[0]['id']))
        # Return the datetime object from the given timestamp above.
        return datetime.fromtimestamp(timestamp)

    except Exception as ex:
        print(ex)


def startDM(scraper, alias, channel, day=None):
    """
    The initialization function for the scraper script to grab direct message contents.
    :param scraper: The DiscordScraper class reference that we will be using.
    :param alias: The named alias for the direct message.
    :param channel: The ID for the direct message we're wanting to scrape from.
    :param day: The datetime object for the day that we're wanting to scrape.
    """
    # TODO: I still need to get around to implementing DM scraping,
    #  hopefully I can figure out a method of getting the true DM url
    #  from a user ID/Snowflake value to make things easier to configure.
    pass


def grab_text_message_content(data):
    console_line_limit = 80
    with open("scrapes/messages_test.txt", "a", encoding="utf-8") as messages_file:
        for message in data['messages']:
            unpacked = message[0]
            write_line = f"{unpacked['author']['username']}: {unpacked['content']}"
            messages_file.write(write_line)

            if len(write_line) > console_line_limit:
                print(f'SAVING: "{write_line[0:console_line_limit]}"...')
            else:
                print(f'SAVING: "{write_line}"')


def startGuild(scraper, guild, channel, day=None):
    """
    The initialization function for the scraper script.
    :param scraper: The DiscordScraper class reference that we will be using.
    :param guild: The ID for the guild that we're wanting to scrape from.
    :param channel: The ID for the channel that we're wanting to scrape from.
    """
    # Get the snowflakes for the current day.
    snowflakes = DiscordScraper.getDayBounds(day.day, day.month, day.year)
    # Generate a valid URL to the undocumented API function for the search feature.
    search_api_url = f'https://discord.com/api/{scraper.apiversion}' \
                     f'/channels/{channel}/messages/search' \
                     f'?min_id={snowflakes[0]}' \
                     f'&max_id={snowflakes[1]}' \
                     f'&{scraper.query}'

    # Update the HTTP request headers to set the referer to the current guild channel URL.
    scraper.headers.update({'Referer': f'https://discord.com/channels/{guild}/{channel}'})
    # ----------------------------------------------------
    # Generate the guild name.
    if scraper.guildname is None:
        scraper.grabGuildName(guild)
    # Generate the channel name.
    if scraper.channelname is None:
        scraper.grabChannelName(channel)
    # Generate the scrape folders.
    scraper.createFolders()

    # ----------------------------------------------------
    # Grab the API response for the search query URL.
    response = DiscordScraper.requestData(search_api_url, scraper.headers)
    # If we returned nothing then continue on to the previous day.
    if response is None:
        # Set the day to yesterday.
        day += timedelta(days=-1)
        # Recursive recall with next day.
        startGuild(scraper, guild, channel, day)

    # ----------------------------------------------------
    # Read the response data.
    data = loads(response.read().decode('iso-8859-1'))
    # Get the number of posts.
    posts = data['total_results']

    # ----------------------------------------------------
    # Determine if we have multiple offsets.
    if posts > 25:
        pages = int(posts / 25) + 1
        for page in range(2, pages + 1):
            # Generate a valid URL to the undocumented API function for the search feature.
            search_api_url = f'https://discord.com/api/{scraper.apiversion}' \
                     f'/channels/{channel}/messages/search' \
                     f'?min_id={snowflakes[0]}' \
                     f'&max_id={snowflakes[1]}' \
                     f'&{scraper.query}' \
                     f'&offset={25 * (page - 1)}'

            # Update the HTTP request headers to set the referer to the current guild channel URL.
            scraper.headers.update({'Referer': f'https://discord.com/channels/{guild}/{channel}'})

            # ----------------------------------------------------
            # Grab the API response for the search query URL.
            response = DiscordScraper.requestData(search_api_url, scraper.headers)
            # Read the response data.
            data2 = loads(response.read().decode('iso-8859-1'))

            # ----------------------------------------------------
            grab_text_message_content(data2)
            # Append the messages from data2 into data.
            for message in data2['messages']:
                data['messages'].append(message)

        # Cache the JSON data if there's anything to cache
        # (don't fill the cache directory with useless API response junk).
        if posts > 0:
            scraper.downloadJSON(data, day.year, day.month, day.day)
        # Check the mimetypes of the embedded and attached files.
        scraper.checkMimetypes(data)

    # ----------------------------------------------------
    # Set the day to yesterday.
    day += timedelta(days=-1)
    # Return the new day
    return day


# ----------------------------------------------------------------------------------------------------------------------
def start(scraper, guild, channel, day=None):
    """
    The initialization function for the scraper script.
    :param scraper: The DiscordScraper class reference that we will be using.
    :param guild: The ID for the guild that we're wanting to scrape from.
    :param channel: The ID for the channel that we're wanting to scrape from.
    """
    # Determine if we've already initialized the DiscordScraper class.
    # If so re-initialize a new one.
    if scraper is not None:
        scraper = DiscordScraper()

    # Determine if the day is empty, default to the current day if so.
    if day is None:
        day = datetime.today()

    # The smallest snowflake that Discord recognizes is from January 1, 2015.
    while day >= datetime(2015, 1, 1):
        day = startGuild(scraper, guild, channel, day)

    if day.year <= 2014:
        print("Requested date is from 2014 or older and is unavailable. Program will now exit.")
        exit(0)


# ----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    # Create a variable that references the Discord Scraper class.
    discordscraper = DiscordScraper()

    # Iterate through the guilds to scrape.
    for guild, channels in discordscraper.guilds.items():
        print(f'Scraping {guild}...')
        # Iterate through the channels to scrape in the guild.
        for channel in channels:
            print(f'\t- Scraping {channel}...')
            # Retrieve the datetime object for the most recent post in the channel.
            lastdate = getLastMessageGuild(discordscraper, guild, channel)
            # Start the scraper for the current channel.
            start(discordscraper, guild, channel, lastdate)

    # Iterate through the direct messages to scrape.
    for alias, channel in discordscraper.directs.items():
        # Start the scraper for the current direct message.
        startDM(discordscraper, alias, channel)
