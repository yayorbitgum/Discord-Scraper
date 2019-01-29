from os import path, makedirs, getcwd, remove
from sys import stderr, stdout, version_info
from json import loads as json_to_array
from threading import Thread
from random import choice
global is_py3, charset

charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwyxz0123456789'
random_string = lambda length: ''.join([choice(charset) for i in range(length)])

if version_info[0] == 3:
    from http.client import HTTPSConnection
    is_py3 = True
elif version_info[0] == 2:
    from urllib2 import build_opener, install_opener, urlopen, HTTPError
    is_py3 = False
else:
    stderr.write('Unsupported version of Python detected!')
    exit(1)

class DiscordRequest:
    def __init__(self, url, headers, types):
        self.domain = url.split('/')[2]
        self.path = '/{0}'.format('/'.join(url.split('/')[3::]))
        self.headers = headers

        self.channel = ''
        self.server = ''
        self.types = types.replace(' ', '').split(',')

        self.imagetypes = [
            'jpg', 'jpeg', 'png', 'gif',
            'tiff', 'tif', 'bmp', 'tga',
            'webp', 'apng'
        ]

        self.videotypes = [
            'ogv', 'webm', 'mp4', 'mp2',
            'mpeg', 'mkv', 'bnk', 'avi',
            'h264', 'h265', 'wmv', 'raw',
            'vob', 'mpg'
        ]

    def download_file(self, file, filename):
        filerr = 0

        with open(filename, 'wb') as binaryfile:
            if is_py3:
                conn = HTTPSConnection(file.split('/')[2], 443)
                conn.request('GET', '/{0}'.format('/'.join(file.split('/')[3::])))
                resp = conn.getresponse()

                if resp.status != 200:
                    filerr = 1
                    stderr.write('Failed to grab binary data for \'{0}\' with an HTTP {1} error.\n'.format(filename, resp.status))
                else:
                    binaryfile.write(resp.read())
            else:
                opener_headers = []
                for k, v in zip(self.headers.keys(), self.headers.values()):
                    opener_headers.append((k, v.encode('iso-8859-1')))

                opener = build_opener()
                opener.addheaders = opener_headers
                install_opener(opener)

                try:
                    binaryfile.write(urlopen(file).read())
                except HTTPError as httperr:
                    filerr = 1
                    stderr.write('Failed to grab binary data for \'{0}\' with an HTTP {1} error.\n'.format(filename, httperr.code))

        if filerr == 1:
            remove(filename)
            filerr = 0

    def get_name_from_id(self, topic, id):
        if is_py3:
            conn = HTTPSConnection(self.domain, 443)
            conn.request('GET', '/api/v6/{0}/{1}'.format(topic, id), headers=self.headers)
            resp = conn.getresponse()

            if resp.status != 200:
                stderr.write('Received HTTP {0} error when gathering JSON data.\n'.format(resp.status))
                contents = []
            else:
                contents = json_to_array(resp.read())
        else:
            opener_headers = []
            for k, v in zip(self.headers.keys(), self.headers.values()):
                opener_headers.append((k, v.encode('iso-8859-1')))

            opener = build_opener()
            opener.addheaders = opener_headers
            install_opener(opener)

            try:
                contents = json_to_array(urlopen('https://{0}/api/v6/{1}/{2}'.format(self.domain, topic, id)).read())
            except HTTPError as httperr:
                stderr.write('Received HTTP {0} error when gathering JSON data.\n'.format(httperr.code))
                contents = []

        if len(contents) > 0:
            if topic == 'guilds':
                self.server = contents['name']
            elif topic == 'channels':
                self.channel = contents['name']
            else:
                stderr.write('Invalid topic \'{0}\' please use either \'guilds\' or \'channels\' for the topic.\n'.format(topic))

    def gather_data(self):
        threads = []

        if self.server == '':
            self.server = random_string(12)
            stderr.write('Failed to gather server name from ID, defaulting to a random folder name: {0}.\n'.format(self.server))

        if self.channel == '':
            self.channel = random_string(12)
            stderr.write('Failed to gather channel name from ID, defaulting to a random folder name: {0}.\n'.format(self.channel))

        filepath = path.join(getcwd(), 'Discord Scrapes', self.server, self.channel)
        filelink = []
        linklink = []
        textlink = []

        if not path.exists(filepath):
            makedirs(filepath)

        if is_py3:
            conn = HTTPSConnection(self.domain, 443)
            conn.request('GET', self.path, headers=self.headers)
            resp = conn.getresponse()

            if resp.status != 200:
                stderr.write('Received HTTP {0} error when gathering JSON data.\n'.format(resp.status))
                contents = []
            else:
                contents = json_to_array(resp.read())
        else:
            opener_headers = []
            for k, v in zip(self.headers.keys(), self.headers.values()):
                opener_headers.append((k, v.encode('iso-8859-1')))

            opener = build_opener()
            opener.addheaders = opener_headers
            install_opener(opener)

            try:
                contents = json_to_array(urlopen('https://{0}{1}'.format(self.domain, self.path)).read())
            except HTTPError as httperr:
                stderr.write('Received HTTP {0} error when gathering JSON data.\n'.format(httperr.code))
                contents = []

        if len(contents) > 0:
            for messages in contents['messages']:
                for message in messages:
                    if len(message['attachments']) > 0:
                        for attachment in message['attachments']:
                            if 'images' in self.types and attachment['filename'].split('.')[-1] in self.imagetypes:
                                filelink.append(attachment['url'])

                            if 'videos' in self.types and attachment['filename'].split('.')[-1] in self.videotypes:
                                filelink.append(attachment['url'])

                            if 'files' in self.types and attachment['filename'].split('.')[-1] not in self.imagetypes and attachment['filename'].split('.')[-1] not in self.videotypes:
                                filelink.append(attachment['url'])

                    if len(message['embeds']) > 0:
                        for embeds in message['embeds']:
                            if 'embeds' in self.types and embeds['type'] == 'link':
                                linklink.append(embeds['url'])

                    if message['content'] != '':
                        if 'texts' in self.types:
                            textlink.append(': '.join([message['author']['id'], message['content']]))


        with open('{0}\\{1}_{2}_text.csv'.format(filepath, self.server, self.channel), 'a') as textfile:
            textfile.write(','.join(set(textlink)))

        with open('{0}\\{1}_{2}_link.csv'.format(filepath, self.server, self.channel), 'a') as textfile:
            textfile.write(','.join(set(textlink)))

        for file in set(filelink):
            filename = '{0}\\{1}_{2}'.format(filepath, file.split('/')[-2], file.split('/')[-1])
            t = Thread(target=self.download_file, args=(file, filename, ))
            threads.append(t)

        for thread in threads:
            thread.start()
            thread.join()

        del threads[:]

if __name__ == '__main__':
    with open('discord.json', 'r') as config:
        config_data = json_to_array(config.read())

    token = config_data['token']
    pages = config_data['pages']
    query = config_data['query']
    agent = config_data['agent']
    types = config_data['types']
    servers = config_data['servers']

    for server, channels in zip(servers.keys(), servers.values()):
        for channel in channels:
            for i in range(0, pages + 1):
                dr = DiscordRequest('https://discordapp.com/api/v6/guilds/{0}/messages/search?has=image&has=video&channel_id={1}&offset={2}&include_nsfw=true'.format(server, channel, i * 25), {'User-agent': agent, 'authorization': token}, types)
                dr.get_name_from_id('guilds', server)
                dr.get_name_from_id('channels', channel)
                dr.gather_data()