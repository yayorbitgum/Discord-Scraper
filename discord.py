from time import time, gmtime, strptime, mktime, timezone
from json import loads as json_to_array
from os import path, makedirs, getcwd
from sys import stderr, version_info
from unicodedata import normalize
from mimetypes import MimeTypes
from random import choice

random_string = lambda length: ''.join([choice('0123456789ABCDEF') for i in range(length)])
fix_utf_error = lambda string: normalize('NFKC', string).encode('iso-8859-1', 'ignore').decode('iso-8859-1')
py3_url_split = lambda    url: [url.split('/')[2], '/%s' % '/'.join(url.split('/')[3::])]
get_snowflake = lambda timems: (timems - 1420070400000) << 22
get_timestamp = lambda sflake: ((sflake >> 22) + 1420070400000) / 1000.0
get_mimetype  = lambda string: MimeTypes().guess_type(string)[0] if len(MimeTypes().guess_type(string)) > 0 else 'application/octet-stream'
get_tstruct   = lambda string: strptime(string, '%d %m %Y %H:%M:%S')
get_tzoffset  = lambda hour:   hour + (timezone / 3600) - 1

def get_day(day, month, year):
    min_ts = mktime(get_tstruct('%02d %02d %d 00:00:00' % (day, month, year))) * 1000
    max_ts = (mktime(get_tstruct('%02d %02d %d 00:00:00' % (day, month, year))) + 86400.0) * 1000

    return [
        get_snowflake(int(min_ts)),
        get_snowflake(int(max_ts))
    ]

def safe_name(folder):
    output = ""

    for char in folder:
        if char in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_+=.,`~!@#$%^&':
            output = '%s%s' % (output, char)

    return output
            

def create_query_body(**kwargs):
    query = ""

    for key, val in kwargs.items():
        if val == True and key != 'nsfw':
            query = '%s&has=%s' % (query, key[0:-1])
            
        if key == 'nsfw':
            query = '%s&include_nsfw=%s' % (query, str(val).lower())
            
    return query

if version_info.major == 3:
    from http.client import HTTPSConnection

    class Request:
        def __init__(self, headers = {}):
            self.headers = headers

        def grab_page(self, url, binary = False):
            try:
                domain, path = py3_url_split(url)
                conn = HTTPSConnection(domain, 443)
                conn.request('GET', path, headers=self.headers)

                resp = conn.getresponse()
                if str(resp.status)[0] == '2':
                    return resp.read() if binary else json_to_array(resp.read())
                else:
                    stderr.write('Received HTTP %s error: %s' % (resp.status, resp.reason))

            except Exception:
                stderr.write('Unknown exception occurred when grabing page contents.')

elif version_info.major == 2 and version_info.minor >= 7:
    from urllib2 import build_opener, install_opener, urlopen, HTTPError

    class Request:
        def __init__(self, headers = {}):
            self.headers = headers

        def grab_page(self, url, binary = False):
            try:
                opener_headers = []

                for key, val in self.headers.items():
                    opener_headers.append((key, val.encode('iso-8859-1')))

                opener = build_opener()
                opener.addheaders = opener_headers
                install_opener(opener)
                
                return urlopen(url).read() if binary else json_to_array(urlopen(url).read())
            
            except HTTPError as err:
                stderr.write('Received HTTP %s error: %s' % (err.code, err.reason))

            except Exception:
                stderr.write('Unknown exception occurred when grabing page contents.')

else:
    stderr.write('Python %s.%s is not supported in this script.' % (version_info.major, version_info.minor))
    exit(1)

class DiscordScraper:
    def __init__(self, jsonfile = 'discord.json'):
        with open(jsonfile, 'r') as config_file:
            config = json_to_array(config_file.read())

        self.headers = {
            'user-agent': config['agent'],
            'authorization': config['token']
        }

        self.types = config['types']
        self.query = create_query_body(
            images = config['query']['images'],
            files  = config['query']['files' ],
            embeds = config['query']['embeds'],
            links  = config['query']['links' ],
            videos = config['query']['videos'],
            nsfw   = config['query']['nsfw'  ]
        )

        self.directs = config['directs']
        self.servers = config['servers']

    def get_server_name_by_id(self, server):
        try:
            request = Request(self.headers)
            server_data = request.grab_page('https://discordapp.com/api/v6/guilds/%s' % server)

            if len(server_data) > 0:
                return safe_name(server_data['name'])
            else:
                stderr.write('Unable to fetch server name from id, defaulting to a randomly generated name instead.')
                return random_string(12)
        except:
            stderr.write('Unable to fetch server name from id, defaulting to a randomly generated name instead.')
            return random_string(12)

    def get_channel_name_by_id(self, channel):
        try:
            request = Request(self.headers)
            channel_data = request.grab_page('https://discordapp.com/api/v6/channels/%s' % channel)

            if len(channel_data) > 0:
                return safe_name(channel_data['name'])
            else:
                stderr.write('Unable to fetch channel name from id, defaulting to a randomly generated name instead.')
                return random_string(12)
        except:
            stderr.write('Unable to fetch channel name from id, defaulting to a randomly generated name instead.')
            return random_string(12) 

    def create_folders(self, server, channel):
        folder = path.join(getcwd(), 'Discord Scrapes', server, channel)

        if not path.exists(folder):
            makedirs(folder)

        return folder

    def download(self, url, folder):
        try:
            request = Request({'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.90 Safari/537.36'})
            filename = safe_name('%s_%s' % (url.split('/')[-2], url.split('/')[-1]))

            binary_data = request.grab_page(url, True)
            if len(binary_data) > 0:
                with open(path.join(folder, filename), 'wb') as bin:
                    bin.write(binary_data)
            else:
                stderr.write('Failed to grab contents of %s' % url)
        except:
            stderr.write('Failed to grab contents of %s' % url)

    def grab_data(self):
        for dmname, dmchannel in self.directs.items():
            folder = self.create_folders('Direct Messages', dmname)
            tzdata = gmtime(time())

            if self.types['text'] == True:
                with open(path.join(folder, 'messages.csv'), 'w') as log:
                    log.write('channel,messageid,message,timestamp,userid,nickname')

            for year in range(tzdata.tm_year, 2015, -1):
                for month in range(12, 1, -1):
                    for day in range(31, 1, -1):
                        if month > tzdata.tm_mon: continue
                        if month == tzdata.tm_mon and day > tzdata.tm_mday: continue
                                
                        try:
                            min_id, max_id = get_day(day, month, year)
                                    
                            request = Request(self.headers)
                            contents = request.grab_page('https://discordapp.com/api/v6/channels/%s/messages/search?min_id=%s&max_id=%s&%s' % (dmchannel, min_id, max_id, self.query))
                            for messages in contents['messages']:
                                for message in messages:
                                            
                                    for attachment in message['attachments']:
                                        if self.types['images'] == True:
                                            if get_mimetype(attachment['url']).split('/')[0] == 'image':
                                                self.download(attachment['url'], folder)

                                        if self.types['videos'] == True:
                                            if get_mimetype(attachment['url']).split('/')[0] == 'video':
                                                self.download(attachment['url'], folder)

                                        if self.types['files'] == True:
                                            if get_mimetype(attachment['url']).split('/')[0] not in ['image', 'video']:
                                                self.download(attachment['url'], folder)

                                    if self.types['text'] == True:
                                        with open(path.join(folder, 'messages.csv'), 'a') as log:
                                            log.write('\n%s,%s,%s,%s,%s,%s#%s' % (dmchannel, message['id'], message['content'].replace(',', ';').replace('\n', ' '), message['timestamp'], message['author']['id'], message['author']['username'].replace(',', ';'), message['author']['discriminator']))
                                                    
                        except ValueError:
                            continue

                        except Exception:
                            continue
                                
        for server in self.servers.keys():
            for channels in self.servers.values():
                for channel in channels:
                    folder = self.create_folders(self.get_server_name_by_id(server), self.get_channel_name_by_id(channel))
                    tzdata = gmtime(time())

                    if self.types['text'] == True:
                        with open(path.join(folder, 'messages.csv'), 'w') as log:
                            log.write('server,channel,messageid,message,timestamp,userid,nickname')

                    for year in range(tzdata.tm_year, 2015, -1):
                        for month in range(12, 1, -1):
                            for day in range(31, 1, -1):
                                if month > tzdata.tm_mon: continue
                                if month == tzdata.tm_mon and day > tzdata.tm_mday: continue
                                
                                try:
                                    min_id, max_id = get_day(day, month, year)
                                    
                                    request = Request(self.headers)
                                    contents = request.grab_page('https://discordapp.com/api/v6/guilds/%s/messages/search?channel_id=%s&min_id=%s&max_id=%s&%s' % (server, channel, min_id, max_id, self.query))
                                    for messages in contents['messages']:
                                        for message in messages:
                                            
                                            for attachment in message['attachments']:
                                                if self.types['images'] == True:
                                                    if get_mimetype(attachment['url']).split('/')[0] == 'image':
                                                        self.download(attachment['url'], folder)

                                                if self.types['videos'] == True:
                                                    if get_mimetype(attachment['url']).split('/')[0] == 'video':
                                                        self.download(attachment['url'], folder)

                                                if self.types['files'] == True:
                                                    if get_mimetype(attachment['url']).split('/')[0] not in ['image', 'video']:
                                                        self.download(attachment['url'], folder)

                                            if self.types['text'] == True:
                                                with open(path.join(folder, 'messages.csv'), 'a') as log:
                                                    log.write('\n%s,%s,%s,%s,%s,%s,%s#%s' % (server, channel, message['id'], message['content'].replace(',', ';').replace('\n', ' '), message['timestamp'], message['author']['id'], message['author']['username'].replace(',', ';'), message['author']['discriminator']))
                                                    
                                except ValueError:
                                    continue

                                except Exception:
                                    continue
                                
if __name__ == '__main__':
    ds = DiscordScraper()
    ds.grab_data()
