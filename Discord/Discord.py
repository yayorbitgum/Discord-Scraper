from .SetFile import SetFile
from .Client import Client

from time import strptime, gmtime, mktime, time
from os import makedirs, unlink, getcwd, path
from unicodedata import normalize, category
from traceback import format_exc
from mimetypes import MimeTypes
from json import loads, dumps
from sqlite3 import connect
from random import choice


def RandomString(length):
    return ''.join([choice('0123456789ABCDEF') for i in range(length)])


def GetMimetype(filename):
    return MimeTypes().guess_type(filename)[0] \
        if MimeTypes().guess_type(filename)[0] is not None \
        else 'application/octet-stream'
        

def Snowflake(timestamp):
    return (timestamp - 1420070400000) << 22


def Timestamp(snowflake):
    return ((snowflake >> 22) + 1420070400000) / 1000.0


def DateStruct(timestamp):
    return strptime(timestamp, '%d %m %Y %H:%M:%S')


def GetDate(day, month, year):
    min_time = mktime(DateStruct(f'{day:02} {month:02} {year} 00:00:00'))
    max_time = (min_time + 86400.00) * 1000
    min_time = min_time * 1000
    
    return [Snowflake(int(min_time)), Snowflake(int(max_time))]


def SafeName(filename):
    output = []
    
    for char in normalize('NFD', filename):
        if category(char) != 'Mn' and char not in '\\/<>:"|?*':
            output.append(char)
            
    return ''.join(output)


class Discord(object):
    
    def __init__(self, config):
        try:
            cfg = SetFile(config)
            cfg.parse()
            
            self.config = cfg.items
            self.servers = {}
            
            self.head = {
                'authorization': self.config['Token'],
                'user-agent': self.config['User Agent']
            }
            
            for k, v in cfg.items.items():
                if k.startswith('SERVER_'):
                    self.servers.update({k.split('_')[1]: v})
        except Exception:
            print(format_exc())
            exit(1)

    def GetServerName(self, id):
        try:
            client = Client(f'https://discordapp.com/api/v6/guilds/{id}', self.head)
            connection = client.GetConnection()
            data = client.GetData(connection)
            
            if data is None:
                raise Exception()
            
            jsondata = loads(data.encode())
            if len(jsondata) == 0:
                raise Exception()
            
            return jsondata['name']
        except Exception:
            print(f'Failed to grab server name for {id}, generating a random name instead...')
            return RandomString(16)
        
    def GetChannelName(self, id):
        try:
            client = Client(f'https://discordapp.com/api/v6/channels/{id}', self.head)
            connection = client.GetConnection()
            data = client.GetData(connection)
            
            if data is None:
                raise Exception()
            
            jsondata = loads(data.encode())
            if len(jsondata) == 0:
                raise Exception()
            
            return jsondata['name']
        except Exception:
            print(f'Failed to grab channel name for {id}, generating a random name instead...')
            return RandomString(16)
        
    def DownloadFiles(self, server, channel, files):
        try:
            localhead = {'user-agent': self.config['User Agent']}
            for image in files['images']:
                filename = f"{image['id']}_{image['url'].split('/')[-1].split('?')[0]}"
                client = Client(image['url'], localhead)
                
                connection = client.GetConnection()
                response = client.GetResponse(connection)
                
                filepath = path.join(getcwd(), 'Scrapes', server, channel)
                if not path.exists(filepath):
                    makedirs(filepath)
                    
                filename = path.join(filepath, filename)
                if not path.isfile(filename):
                    client.Download(response, filename, self.config['Stream Size'])
                
            for video in files['videos']:
                filename = f"{video['id']}_{video['url'].split('/')[-1].split('?')[0]}"
                client = Client(video['url'], localhead)
                
                connection = client.GetConnection()
                response = client.GetResponse(connection)
                
                filename = path.join(getcwd(), self.config['Base Dir'], server, channel, filename)
                if not path.isfile(filename):
                    client.Download(response, filename, self.config['Stream Size'])
                
        except Exception:
            print(format_exc())
            return False
        
    def CheckFiles(self, server, channel, jsondata):
        try:
            if jsondata is None:
                raise Exception()
            
            texts = []
            files = {
                'images': [],
                'videos': []
            }
            
            for messages in jsondata['messages']:
                for message in messages:
                    text = message['content']
                    authorname = '%s#%s' % (message['author']['username'], message['author']['discriminator'])
                    authorid = message['author']['id']
                    timestamp = message['timestamp']
                    
                    if self.config['Grab Text']:
                        texts.append({
                            'content': text,
                            'timestamp': timestamp,
                            'author': {
                                'id': authorid,
                                'name': authorname
                            }
                        })
                    
                    for attachment in message['attachments']:
                        fid = attachment['id']
                        filename = attachment['filename']
                        url = attachment['proxy_url']
                        
                        if self.config['Grab Images'] and GetMimetype(filename).split('/')[0] == 'image':
                            files['images'].append({'id': fid, 'url': url})
                        
                    for embed in message['embeds']:
                        try:
                            if embed['image'] and self.config['Grab Images']:
                                fid = embed['image']['id']
                                url = embed['image']['proxy_url']
                                files['images'].append({'id': fid, 'url': url})
                        except KeyError:
                            pass
                        
                        try:
                            if embed['video'] and self.config['Grab Videos']:
                                fid = embed['video']['id']
                                url = embed['video']['proxy_url']
                                files['videos'].append({'id': fid, 'url': url})
                        except KeyError:
                            pass
                
            if self.config['Grab Text']:
                if self.config['Text Store Method'] == 'JSON':
                    self.WriteJSON(SafeName(server), SafeName(channel), texts)
                elif self.config['Text Store Method'] == 'SQLite':
                    self.WriteSQL(SafeName(server), SafeName(channel), texts)
                
            self.DownloadFiles(SafeName(server), SafeName(channel), files)
        except Exception:
            print(format_exc())
            return None
        
    def WriteSQL(self, server, channel, texts):
        ''
        
    def WriteJSON(self, server, channel, texts):
        try:
            filepath = path.join(getcwd(), 'Texts', server)
            if not path.exists(filepath):
                makedirs(filepath)
                
            filename = path.join(filepath, f'{channel}.json')
            if path.isfile(filename):
                unlink(filename)
                
            with open(filename, 'a') as jsonfile:
                jsonfile.write(f'{dumps(texts)},\n')
                
        except Exception:
            print(format_exc())
            return None
        
    def GrabData(self):
        try:
            timezone = gmtime(time())
            query = '&has=embed'
            
            query = f'{query}&has=image' if self.config['Grab Images'] else query
            query = f'{query}&has=video' if self.config['Grab Videos'] else query
            nsfw = '&include_nsfw=true' if self.config['Grab NSFW Content'] else '&include_nsfw=false'
            
            for year in range(timezone.tm_year, 2015, -1):
                for month in range(12, 1, -1):
                    for day in range(31, 1, -1):
                        
                        if month > timezone.tm_mon and year == timezone.tm_year:
                            continue
                        
                        if month == timezone.tm_mon and day > timezone.tm_mday:
                            continue
                        
                        for server, channels in self.servers.items():
                            servername = self.GetServerName(server)
                            
                            for channel in channels:
                                today = GetDate(day, month, year)
                                channelname = self.GetChannelName(channel)
                                self.head.update({'referer': f'https://discordapp.com/channels/{server}/{channel}'})
                                
                                client = Client(f'https://discordapp.com/api/v6/guilds/{server}/messages/search?min_id={today[0]}&max_id={today[1]}{query}&channel_id={channel}{nsfw}', self.head)
                                connection = client.GetConnection()
                                data = client.GetData(connection)
                                
                                if data is None:
                                    raise Exception(f'Unable to grab data between {day:02d}-{month:02d}-{year} and {day+1:02d}-{month:02d}-{year}')
                                
                                jsondata = loads(data.encode())
                                self.CheckFiles(servername, channelname, jsondata)
        except ValueError:
            pass
        
        except Exception:
            print(format_exc())
            pass