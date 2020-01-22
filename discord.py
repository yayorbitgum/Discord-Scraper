from Discord import Discord
from os import getcwd, path

if __name__ == '__main__':
    setfile = path.join(getcwd(), 'discord.set')
    discord = Discord(setfile)
    discord.GrabData()