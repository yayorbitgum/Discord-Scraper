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
                   
        except:
            print(format_exc())
            exit(1)

    def GetServerName(self, id):
        try:
            client = Client(f'https://discordapp.com/api/v6/guilds/{id}', self.head)
            connection = client.GetConnection()
            data = client.GetData(connection)
            
            if data is None:
                raise Exception
            
            jsondata = loads(data.encode())
            if len(jsondata) == 0:
                raise Exception
            
            return jsondata['name']
        except Exception:
            print(format_exc())
            return RandomString(16)
        
    def GetChannelName(self, id):
        try:
            client = Client(f'https://discordapp.com/api/v6/channels/{id}', self.head)
            connection = client.GetConnection()
            data = client.GetData(connection)
            
            if data is None:
                raise Exception
            
            jsondata = loads(data.encode())
            if len(jsondata) == 0:
                raise Exception
            
            return jsondata['name']
        except Exception:
            print(format_exc())
            return RandomString(16)
        
    def DownloadFiles(self, server, channel, files):
        localhead = {'user-agent': self.config['User Agent']}
        if len(files['images']) == 0 and len(files['videos']) == 0:
            return None
        
        try:
            for image in files['images']:
                filename = f"{image['id']}_{image['url'].split('/')[-1].split('?')[0]}"
                client = Client(image['url'], localhead)
                
                filepath = path.join(getcwd(), 'Scrapes', server, channel)
                if not path.exists(filepath):
                    makedirs(filepath)
                    
                filename = path.join(filepath, filename)
                if not path.isfile(filename):
                    client.Download(filename, self.config['Stream Size'])
        except:
            print(format_exc())
            pass
        
        try:
            for video in files['videos']:
                filename = f"{video['id']}_{video['url'].split('/')[-1].split('?')[0]}"
                client = Client(video['url'], localhead)
                
                filepath = path.join(getcwd(), 'Scrapes', server, channel)
                if not path.exists(filepath):
                    makedirs(filepath)
                    
                filename = path.join(filepath, filename)
                if not path.isfile(filename):
                    client.Download(filename, self.config['Stream Size'])
                
        except:
            print(format_exc())
            pass
        
    def CheckFiles(self, server, channel, jsondata):
        try:
            if jsondata is None:
                raise Exception
            
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
                        try:
                            fid = attachment['id']
                            filename = attachment['filename']
                            url = attachment['proxy_url']
                            
                            if self.config['Grab Images'] and GetMimetype(filename).split('/')[0] == 'image':
                                files['images'].append({'id': fid, 'url': url})
                        except KeyError:
                            pass
                       
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
                
        except:
            print(format_exc())
            return None
        
    def GrabData(self):
        try:
            timezone = gmtime(time())
            query = ''
            
            query = f'{query}&has=image' if self.config['Grab Images'] else query
            query = f'{query}&has=video' if self.config['Grab Videos'] else query
            nsfw = '&include_nsfw=true' if self.config['Grab NSFW Content'] else '&include_nsfw=false'
            
            for server, channels in self.servers.items():
                server_name = self.GetServerName(server)
                
                for channel in channels:
                    channel_name = self.GetChannelName(channel)
            
                    for year in range(timezone.tm_year, 2014, -1):
                        for month in range(12, 0, -1):
                            for day in range(31, 0, -1):
                                
                                if year == timezone.tm_year:
                                    if month > timezone.tm_mon:
                                        continue
                                    
                                    if month == timezone.tm_mon and day > timezone.tm_mday:
                                        continue
                                
                                try:
                                    today = GetDate(day, month, year)
                                    self.head.update({'referer': f'https://discordapp.com/channels/{server}/{channel}'})
                                    client = Client(f'https://discordapp.com/api/v6/guilds/{server}/messages/search?min_id={today[0]}&max_id={today[1]}&channel_id={channel}{nsfw}', self.head)
                                    
                                    connection = client.GetConnection()
                                    data = client.GetData(connection)
                                    
                                    if data is None:
                                        continue
                                    
                                    jsondata = loads(data.encode())
                                    self.CheckFiles(server_name, channel_name, jsondata)
                                        
                                except ValueError:
                                    continue
                                
        except:
            print(format_exc())
