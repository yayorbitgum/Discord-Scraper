from http.client import HTTPSConnection, HTTPConnection
from os import makedirs, getcwd, path
from traceback import format_exc
from re import findall as regex


class Client(object):
    
    def __init__(self, url, headers={}):
        self.scheme = 'https' if url.split('/')[0] == 'https:' else 'http'
        self.domain = url.split('/')[2].split(':')[0]
        self.port = 443 if self.scheme == 'https' else 80
            
        self.path = '/%s' % '/'.join(url.split('/')[3:])
        self.head = headers
        
    def GetConnection(self):
        return HTTPSConnection(self.domain, self.port) if self.scheme == 'https' \
            else HTTPConnection(self.domain, self.port)
            
    def GetResponse(self, connection, uri=None):
        try:
            connection.request('GET', self.path if uri is None else uri, headers=self.head)
            response = connection.getresponse()
            
            if 199 < response.status < 300:
                return response
            
            elif 299 < response.status < 400:
                location = '/%s' % '/'.join(response.getheader('location').split('/')[3:])
                connection = self.GetConnection()
                return self.GetResponse(connection, location)
                
            raise Exception
        except Exception:
            return None
        
    def GetData(self, connection, uri=None):
        try:
            response = self.GetResponse(connection, uri)
            if response is None:
                raise Exception
            
            return response.read().decode('utf-8', 'ignore')
        except Exception:
            return None
        
    def DownloadFile(self, response, filename):
        try:
            with open(filename, 'wb') as file:
                file.write(response.read())
                
        except:
            print(format_exc())
            return None
        
    def StreamFile(self, response, filename, filesize, streamsize):
        try:
            with open(filename, 'ab') as file:
                if response.getheader('accept-ranges') != 'bytes':
                    file.write(response.read()) # Ignore the filestream since the source doesn't support it.
                    file.close()
                    return True
                
                buffer = streamsize - 1
                for byte in range(0, filesize, buffer):
                    self.head.update({'content-range': f'bytes {byte + 1 if byte > 0 else 0}-{buffer}/{filesize}' if filesize >= streamsize else f'bytes {byte + 1 if byte > 0 else 0}-{filesize}/{filesize}'})
                    
                    connection = self.GetConnection()
                    resp = self.GetResponse(connection)
                    
                    if resp is None:
                        file.close()
                        raise Exception
                    
                    file.write(resp.read())
                    buffer += streamsize
                    
            return True
        except Exception:
            print(format_exc())
            return False
        
    def Download(self, filename, streamsize):
        try:
            if path.isfile(filename):
                print('Skipping duplicate file...')
                return None
            
            connection = self.GetConnection()
            response = self.GetResponse(connection)
            
            if response is None:
                raise Exception
            
            filepath = path.split(filename)[:-1][0]
            if not path.exists(filepath):
                makedirs(filepath)
                
            filesize = int(response.getheader('content-length'))
            self.StreamFile(response, filename, filesize, streamsize) if filesize >= streamsize \
                else self.DownloadFile(response, filename)
                
        except Exception:
            print(format_exc())
            return None
