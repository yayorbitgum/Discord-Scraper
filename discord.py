# START OF FILE
# START OF HEADER

"""
@author:  Dracovian
@date:    2020-11-07
@license: WTFPL
"""

# END OF HEADER
# START OF IMPORTS

"""
datetime.timedelta: Used to subtract an entire day from the current one.
datetime.datetime:  Used to retrieve the current day.
"""
from datetime import timedelta, datetime

"""
module.DiscordScraper: Used to access the Discord Scraper class functions.
"""
from module import DiscordScraper

# END OF IMPORTS
# START OF FUNCTIONS

def startDM(scraper, alias, channel, day=None):
    """
    The initialization function for the scraper script to grab direct message contents.
    :param scraper: The DiscordScraper class reference that we will be using.
    :param alias: The named alias for the direct message.
    :param channel: The ID for the direct message we're wanting to scrape from.
    :param day: The datetime object for the day that we're wanting to scrape.
    """

    pass

def startGuild(scraper, guild, channel, day=None):
    """
    The initialization function for the scraper script.
    :param scraper: The DiscordScraper class reference that we will be using.
    :param guild: The ID for the guild that we're wanting to scrape from.
    :param channel: The ID for the channel that we're wanting to scrape from.
    :param day: The datetime object for the day that we're wanting to scrape.
    """

    # Determine if the day is empty, default to the current day if so.
    if day is None:
        # day = datetime.today() # TODO: Uncomment this for release
        day = datetime(2020, 10, 8, 0, 0, 0, 0, None)

    # Determine if the year is no less than 2015 since any time before this point will be guaranteed invalid.
    if day.year > 2014:

        # Get the snowflakes for the current day.
        snowflakes = DiscordScraper.getDayBounds(day.day, day.month, day.year)

        # Generate a valid URL to the undocumented API function for the search feature.
        search = 'https://discordapp.com/api/{0}/channels/{1}/messages/search?min_id={2}&max_id={3}&{4}'.format(scraper.apiversion, channel, snowflakes[0], snowflakes[1], scraper.query)

        # Update the HTTP request headers to set the referer to the current guild channel URL.
        scraper.headers.update({'Referer': 'https://discordapp.com/channels/{0}/{1}'.format(guild, channel)})

        # Generate the guild name.
        scraper.grabGuildName(guild)

        # Generate the channel name.
        scraper.grabChannelName(channel)

        # Generate the scrape folders.
        scraper.createFolders()

        # Grab the API response for the search query URL.
        response = DiscordScraper.requestData(search, scraper.headers)

        # If we returned nothing then continue on to the previous day.
        if response is None:

            # Set the day to yesterday.
            day += timedelta(days=-1)

            # Recursively call this function with the new day.
            startGuild(scraper, guild, channel, day)
        
        # Read the response data.
        data = response.read()

        # Check the mimetypes of the embedded and attached files.
        scraper.checkMimetypes(data)

        # Set the day to yesterday.
        day += timedelta(days=-1)

        # Recursively call this function with the new day.
        startGuild(scraper, guild, channel, day)

# END OF FUNCTIONS
# START OF ENTRYPOINT

if __name__ == '__main__':
    """
    This is the entrypoint for our script since __name__ is going to be set to __main__ by default.
    """

    # Create a variable that references the Discord Scraper class.
    discordscraper = DiscordScraper()

    # Iterate through the guilds to scrape.
    for guild, channels in discordscraper.guilds.items():

        # Iterate through the channels to scrape in the guild.
        for channel in channels:

            # Start the scraper for the current channel.
            startGuild(discordscraper, guild, channel)
    
    # Iterate through the direct messages to scrape.
    for alias, channel in discordscraper.directs.items():

        # Start the scraper for the current direct message.
        startDM(discordscraper, alias, channel)

# END OF ENTRYPOINT
# END OF FILE