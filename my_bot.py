# -*- coding: utf-8 -*-
import socket
import time

server = "irc.ppy.sh"
host = ""
passwd = ""
BB = 'BanchoBot'
check_str = 'check.lskdjg;ankjnizv'

irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("connecting to:", server)
irc.connect((server, 6667))
irc.send(("PASS " + passwd + "\n").encode('utf-8'))
irc.send(("NICK " + host + "\n").encode('utf-8'))


def read_line():
    c = irc.recv(1)
    bline = c
    while c != b'\n':
        c = irc.recv(1)
        bline += c
    return bline.decode('utf-8')[:-1]


def read_codes(codes, end):
    codes = {str(x) for x in codes}
    end = str(end)
    codes.add(end)

    while True:
        cline = read_line()
        l = cline.split(maxsplit=2)
        if l[0] == ':cho.ppy.sh' and l[1] in codes:
            print(cline[:-1])
        if l[1] == end:
            break


def send(chan, msgline):
    irc.send(('PRIVMSG %s :%s\n' % (chan, msgline)).encode('utf-8'))


read_codes([371, 372], 376)  # welcome message

# получить список каналов
# irc.send(("LIST\n").encode('utf-8'))
# read_codes([321,322],323)

refs = {host.lower(): host}

channel0 = '#mp_53783601'
irc.send(("JOIN " + channel0 + "\n").encode('utf-8'))


# room_name = 'Играть хочу!   |   |'
# send(BB, '!mp make ' + room_name)

class Room:
    def __init__(self):
        self.players = ['']*16
        self.host = ''
        self.map_id = '0'
        self.room_mods = []
        self.player_mods = [[]]*16
        self.keys = {}


    def remove(self, nick):
        for x in range(16):
            if self.players[x] == nick:
                self.players[x] = ''
                if self.host == nick:
                    self.host = ''

    def clearhost(self):
        self.host = ''


room = Room()

addref = []

timer = time.time()  # таймер для сообщении hostme

fl_settings = False
n_settings = 0
time_settings = time.time() - 300
prev_n = 0


class MyException(Exception):
    pass


try:
    while True:
        if time.time() - time_settings >= 300:
            send(channel0, '!mp settings')
            fl_settings = True
            time_settings = time.time()
        line = read_line()
        sl = line.split(maxsplit=3)
        if len(sl) < 3 and sl[0] != 'PING':
            print('Wrong line')
            raise MyException()
        nick = sl[0][1:].split('!')[0]

        # обработка сообщений банчобота
        if nick == BB and sl[1] == 'PRIVMSG':
            channel = sl[2]
            msg = line.split(':', maxsplit=2)[2].split(maxsplit=2)
            print('%s/> %s: %s' % (channel, nick, ' '.join(msg)))
            nick = nick.lower()

            # обработка вывода !mp settings
            if fl_settings:
                if n_settings != 0 and msg[0] == 'Slot':
                    n = int(msg[1])
                    if n > prev_n + 1:
                        for i in range(prev_n, n - 1):
                            room.players[i] = ''
                    prev_n = n
                    m_ = [x.strip() for x in msg[2].split('/', maxsplit=4)[4].split(maxsplit=1)[1].split('   ', maxsplit=1)]
                    room.players[n - 1] = m_[0]
                    if len(m_) > 1:
                        m = [x.strip() for x in m_[1][1:-1].split('/')]
                    room.player_mods[n - 1] = m.copy()
                    if 'Host' in m:
                        fl = True
                        m.remove('Host')
                    else:
                        fl = False

                    if fl:
                        room.host = m_[0]
                        print(m_[0], ':', 'host')

                    n_settings -= 1
                    if n_settings <= 0:
                        fl_settings = False

                elif msg[0] == 'Players:':
                    n_settings = int(msg[1])
                    prev_n = 0

                elif msg[0] == 'Active':
                    m = ' '.join(msg)
                    m = [x.strip() for x in m.split(':')]
                    room.keys[m[0]] = [x.strip() for x in m[1].split(',')]

                elif msg[0] == 'Team':
                    m = ' '.join(msg)
                    m = [x.strip() for x in m.split(',')]
                    m0 = m[0]
                    m1 = m[1]
                    m0 = [x.strip() for x in m0.split(':')]
                    room.keys[m0[0]] = m0[1]
                    m1 = [x.strip() for x in m1.split(':')]
                    room.keys[m1[0]] = m1[1]

            if msg[0] == 'Created':
                channel0 = '#mp_' + msg[2].split()[2].split('/')[4]
                print('joining channel ' + channel0)
                send(channel0, '!mp password')
                send(channel0, '!mp invite ' + host)
            elif msg[0] == 'Beatmap' and msg[1] == 'changed':
                room.map_id = msg[2].split('/')[-1][:-1]
            elif len(addref) != 0:
                if msg[0] == 'User' and msg[1] == 'not':
                    send(channel0, "Player '" + addref[0] + "' doesn't exist!")
                    addref = addref[1:]
                elif msg[0] == 'Stats':
                    player = msg[2][1:].split(')', maxsplit=1)[0]
                    if player.lower() == addref[0]:
                        refs[player.lower()] = player
                        addref = addref[1:]
                    else:
                        send(channel0, "Error! Try again.")
                        addref = []
                if len(addref) != 0 and addref[0] == check_str:
                    addref = []
                    send(channel0, 'done')
            elif msg[1] == 'joined':
                n = int(msg[2].split()[2][:-1])
                room.players[n - 1] = msg[0]
            elif msg[1] == 'left':
                room.remove(msg[0])
            elif msg[1] == 'moved':
                room.remove(msg[0])
                n = int(msg[2].split()[2])
                room.players[n - 1] = msg[0]
            elif msg[1] == 'became':
                room.host = msg[0]
            elif msg[0] == 'Cleared':
                room.host = ''
            elif msg[0] == 'Changed':
                msg = msg[2].split(maxsplit=2)
                if msg[0] == 'host':
                    room.host = msg[2]
                msg = ' '.join(msg)
                msg = msg.split()
                if msg[2] == 'size':
                    for x in range(int(msg[3]), 16):
                        if room.host == room.players[x]:
                            room.host = ''
                        room.players[x] = ''
        elif sl[1] == 'PRIVMSG':
            channel = sl[2]
            msg = line.split(':', maxsplit=2)[2]
            print('%s/> %s: %s' % (channel, nick, msg))
            nick = nick.lower()
            if msg[:4].lower() == '!mp ':
                com = msg[4:].lower().split(maxsplit=1)
                if com[0] == 'settings' and nick == host:
                    fl_settings = True

            if msg[:4].lower() == '!do ':
                com = msg[4:].lower().split(maxsplit=1)
                '''
                if com[0] == 'make':
                   if nick == host:
                      if len(com) == 2:
                         chs.add(com[1])
                         print('making room..')
                         send('banchobot', '!mp make ' + com[1])
                      else:
                         send(nick, 'No name provided')'''
                # addref
                if com[0] == 'addref':
                    if nick in refs and len(com) > 1:
                        for x in com[1].split(','):
                            addref += [x.strip().lower()]
                            send(BB, 'stats ' + x.strip())
                        addref += [check_str]
                # removeref
                elif com[0] == 'removeref':
                    if nick in refs and len(com) > 1:

                        for x in com[1].split(','):
                            x = x.strip()
                            fl = refs.pop(x, None)
                            if fl is None:
                                send(channel, x + ' is not referee')
                        if host not in refs:
                            refs[host.lower()] = host
                            send(channel, "You can't remove me!")
                        send(channel, 'done')
                # host
                elif com[0] == 'host':
                    if nick in refs and len(com) > 1:
                        send(channel, '!mp host ' + com[1])
                # size
                elif com[0] == 'size':
                    if nick in refs and len(com) > 1:
                        send(channel, '!mp size ' + com[1])
                # listrefs
                elif com[0] == 'listrefs':
                    if nick in refs:
                        send(channel, 'refs: ' + str(list(refs.values())))
                # start
                elif com[0] == 'start':
                    if nick in refs:
                        send(channel, '!mp start ' + ('' if len(com) == 1 else com[1]))
                # abort
                elif com[0] == 'abort':
                    if nick in refs:
                        send(channel, '!mp abort')
                # clearhost
                elif com[0] == 'clearhost':
                    if nick in refs:
                        send(channel, '!mp clearhost')
                # kick
                elif com[0] == 'kick':
                    if nick in refs and len(com) > 1:
                        send(channel, '!mp kick ' + com[1])
                # move
                elif com[0] == 'move':
                    if nick in refs and len(com) > 1:
                        send(channel, '!mp move ' + com[1])
                # np
                elif com[0] == 'np':
                    send(channel, 'Now playing [https://osu.ppy.sh/b/' + room.map_id + ' this map]')
                # settings
                elif com[0] == 'settings':
                    send(channel, str(room.players))
                    send(channel, str(room.keys))
                    if room.host != '':
                        send(channel, room.host + ' is host')
                    else:
                        send(channel, "There's no host")
                # hostme
                elif com[0] == 'hostme' and room.host == '':
                    send(channel, '!mp host ' + nick)
                # stop
                elif com[0] == 'stop' and nick == host:
                    raise MyException()
                # help
                elif com[0] == 'help':
                    send(nick,
                         "I'm a bot. You can use !do commands only if you're referee! PM kirndy for bot commands.")
                    '''if (nick in refs):
                       send(nick,"Here's commands you can use:")
                       send(nick,"!do addref ref1 [, ref2...]")
                       send(nick,"!do removeref ref1 [, ref2...]")
                       send(nick,"!do listrefs")
                       send(nick,"!do start [seconds]")
                       send(nick,"!do abort")
                       send(nick,"!do host [nick]")
                       send(nick,"!do size [size]")
                       send(nick,"!do clearhost")
                       send(nick,"!do kick nick")
                       send(nick,"!do move nick slot")
                       #send(nick,"!do lock")
                       #send(nick,"!do unlock")
                    send(nick,"!do help -- bot's commands")
                    send(nick,"!do np")'''

        # вывод сообщения hostme
        time_ = time.time()
        if room.host == '' and time_ - timer > 30:
            timer = time_
            # send(channel0, 'You can use !do hostme')

        # ответ серверу
        if sl[0] == 'PING':
            irc.send(('PONG ' + line[5:] + '\r\n').encode('utf-8'))

except MyException:
    # send(channel0, '!mp close')
    irc.send("QUIT quit\n".encode('utf-8'))
    print('stop')
