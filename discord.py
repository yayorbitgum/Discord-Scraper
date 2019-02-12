"""
The modules (imports)

The os module will be used to create directories and delete files.
The sys module will be used to output text without being messed up by threading.
The json module will be used to convert a JSON (JavaScript Object Notation) string to a Python dictionary.
The unicodedata module will be used to handle those nasty UCS2 encoded characters that don't play well with UTF/ISO-8859-1 encoded files.
The threading module will be used to run this script's functions on multiple software threads (increasing system resource usage for faster runtime).
The random module will be used to generate the random alphanumeric values by the random_string lambda function.
"""
from os import path, makedirs, getcwd, remove
from sys import stderr, stdout, version_info
from json import loads as json_to_array
from unicodedata import normalize
from threading import Thread
from random import choice

"""
The global variable

textlink will be an array/list to keep track of the current page of textual contents since threading is screwy (appending duplicates ad infinitum making for excessively large filesizes when grabbing channel text).
imagetypes will be an array/list to keep track of the allowed image file extensions (again the future mimetype implementation will make this obsolete).
videotypes will be an array/list to keep track of the allowed video file extensions (again the future mimetype implementation will make this obsolete).
"""
textlink = ['id,server_id,channel_id,timestamp,author_id,author_name,content,embeds']

imagetypes = [
    'jpg', 'jpeg', 'png', 'gif',
    'tiff', 'tif', 'bmp', 'tga',
    'webp', 'apng'
]

videotypes = [
    'ogv', 'webm', 'mp4', 'mp2',
    'mpeg', 'mkv', 'bnk', 'avi',
    'h264', 'h265', 'wmv', 'raw',
    'vob', 'mpg'
]

"""
The anonymous functions (lambda functions)

random_string(length):  This function should return a random alphanumeric value of length 'length' when called.
fix_utf_errors(string): This function should return a string that is safe to write in an ISO-8859-1 encoded file.
py3_url_split(url):     This function should return a single-dimensional dictionary which is used by http.client to make server requests.
"""
random_string = lambda length: ''.join([choice('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789') for i in range(length)])
fix_utf_errors = lambda string: normalize('NFKC', string).encode('iso-8859-1', 'ignore').decode('iso-8859-1')
py3_url_split = lambda url: [url.split('/')[2], '/{0}'.format('/'.join(url.split('/')[3::]))]

"""
Website Request class

This portion of the script is what allows us to make web requests without
needing to worry about creating separate scripts for Python 2.7 and Python 3
compatibility like I did in the past commits.

You can simply reuse this portion of the script if you were wanting to make
a web scraper that works with Python 2.7 and Python 3 interpreters. I don't
have any interest in supporting older versions of Python 2 and if we ever
get a Python 4 release, then I'll be sure to make updates to this portion
of the script.
"""
if version_info[0] == 3:
    from http.client import HTTPSConnection

    class Request:
        def __init__(self, headers):
            self.headers = headers

        def grab_page(self, url, binary=False, error='Received HTTP {0} error when gathering JSON data.\n'):
            domain, path = py3_url_split(url)
            conn = HTTPSConnection(domain, 443)
            conn.request('GET', path, headers=self.headers)

            resp = conn.getresponse()
            if resp.status == 200:
                return resp.read() if binary else json_to_array(resp.read())
            else:
                stderr.write(error.format(resp.status))
                stdout.write(resp.read().decode('iso-8859-1'))
                return ''


elif version_info[0] == 2 and version_info[1] >= 7:
    from urllib2 import build_opener, install_opener, urlopen, HTTPError

    class Request:
        def __init__(self, headers):
            self.headers = headers

        def grab_page(self, url, binary=False, error='Received HTTP {0} error when gathering JSON data.\n'):
            opener_headers = []
            for k, v in zip(self.headers.keys(), self.headers.values()):
                opener_headers.append((k, v.encode('iso-8859-1')))

            opener = build_opener()
            opener.addheaders = opener_headers
            install_opener(opener)

            try:
                return urlopen(url).read() if binary else json_to_array(urlopen(url).read())
            except HTTPError as err:
                stderr.write(error.format(err.code))
                return ''

else:
    stderr.write('Unsupported version of Python detected!')
    exit(1)

"""
Discord Scraper class

This class will serve the purpose of grabbing data from Discord's servers.
You can still make requests to other web servers without this class.

If you were to make updates to this script to work with future versions of
the Discord API, this would be the class you need to modify.

The current API version of Discord from the time of this script: v6
"""

class DiscordScraper:
    def __init__(self):
        with open('discord.json', 'r') as config_file:
            config = json_to_array(config_file.read())

        self.pages = config['pages']
        self.query = config['query']
        self.types = config['types'].replace(' ', '').split(',')
        self.header = {'user-agent': config['agent'], 'authorization': config['token']}
        self.servers = config['servers']

    def get_server_name_by_id(self, server_id):
        request = Request(self.header)
        server_data = request.grab_page('https://discordapp.com/api/v6/guilds/{0}'.format(server_id))

        if len(server_data) > 0:
            return server_data['name']
        else:
            random_name = random_string(12)
            stderr.write('Unable to fetch server name from id, so we\'ll be using {0} instead.'.format(random_name))
            return random_name

    def get_channel_name_by_id(self, channel_id):
        request = Request(self.header)
        channel_data = request.grab_page('https://discordapp.com/api/v6/channels/{0}'.format(channel_id))

        if len(channel_data) > 0:
            return channel_data['name']
        else:
            random_name = random_string(12)
            stderr.write('Unable to fetch channel name from id, so we\'ll be using {0} instead.'.format(random_name))
            return random_name

    def create_folders(self, server_id, channel_id):
        if not path.exists(path.join(getcwd(), 'Discord Scrapes', self.get_server_name_by_id(server_id), self.get_channel_name_by_id(channel_id))):
            makedirs(path.join(getcwd(), 'Discord Scrapes', self.get_server_name_by_id(server_id), self.get_channel_name_by_id(channel_id)))

        return path.join(getcwd(), 'Discord Scrapes', self.get_server_name_by_id(server_id), self.get_channel_name_by_id(channel_id))

    def grab_data(self, page):
        threads = []

        for server in self.servers.keys():
            for channels in self.servers.values():
                for channel in channels:
                    folder = self.create_folders(server, channel)
                    request = Request(self.header)
                    contents = request.grab_page('https://discordapp.com/api/v6/guilds/{0}/messages/search?channel_id={1}&offset={2}&{3}'.format(server, channel, 25 * page, self.query))

                    for messages in contents['messages']:
                        filelink = []

                        for message in messages:
                            for attachment in message['attachments']:
                                if 'image' in self.types and attachment['filename'].split('.')[-1] in imagetypes:
                                    filelink.append(attachment['url'])
                                if 'video' in self.types and attachment['filename'].split('.')[-1] in videotypes:
                                    filelink.append(attachment['url'])
                                if 'file' in self.types and attachment['filename'].split('.')[-1] not in imagetypes and videotypes:
                                    filelink.append(attachment['url'])

                            if 'text' in self.types:
                                if len(message['embeds']) > 0:
                                    embed_urls = []

                                    for embed in message['embeds']:
                                        embed_urls.append(embed['url'])

                                    embed_data = ';'.join(embed_urls)
                                else: embed_data = 'null'

                                if(len(fix_utf_errors(message['content']).replace(',', '.').replace('\r', ' ').replace('\n', ' ')) > 0):
                                    textdata = fix_utf_errors(message['content']).replace(',', '.').replace('\r', ' ').replace('\n', ' ')
                                else: textdata = 'null'

                                object = [message['id'], server, message['channel_id'], message['timestamp'], message['author']['id'], '#'.join([fix_utf_errors(message['author']['username']), message['author']['discriminator']]), textdata, embed_data]
                                textlink.append(','.join(object))

                        for file in filelink:
                            t = Thread(target=self.download_binary, args=(file, folder, ))
                            threads.append(t)

        for thread in threads:
            thread.start()
            thread.join()

        del threads[:]

    def download_binary(self, url, folder):
        request = Request({'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'})
        filename = '{0}_{1}'.format(url.split('/')[-2], url.split('/')[-1])

        binary_data = request.grab_page(url, True, 'Received HTTP {0} error when gathering binary data for \'%s\'.\n' % url)
        if len(binary_data) > 0:
            with open(path.join(folder, filename), 'wb') as binary:
                binary.write(binary_data)

    def download_log(self, folder):
        if path.exists(path.join(folder, 'channels.csv')):
            remove(path.join(folder, 'channels.csv'))

        with open(path.join(folder, 'channels.csv'), 'a') as csv:
            for text in textlink:
                csv.write('{0}\n'.format(text))

"""
The start of this script.

No matter how you decide to run this script, this portion should be the first one called.
This makes it easier for me to sort out non-class functions from the start of the script.
"""
if __name__ == '__main__':
    ds = DiscordScraper()
    threads = []

    for i in range(ds.pages):
        t = Thread(target=ds.grab_data, args=(i, ))
        threads.append(t)

    for thread in threads:
        thread.start()
        thread.join()

    ds.download_log(path.join(getcwd(), 'Discord Scrapes'))
    del threads[:]
    del textlink[:]