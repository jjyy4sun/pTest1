#encoding=utf8
from asyncore import dispatcher
from asynchat import async_chat
import socket,asyncore

PORT = 5005
NAME = 'TestChat'
class EndSession(Exception):pass

class CommandHandler:
    '''类似于标准库中的cmd.Cmd的简单命令处理程序'''

    def unknown(self,session,cmd):
        '''响应未知命令'''
        session.push('Unknown command:%s\r\n' % cmd)

    def handle(self,session,line):
        '''处理从给定的会话中接受行'''
        if not line.strip():return
        #分离命令
        parts = line.split(' ',1)
        cmd = parts[0]
        try:
            line = pars[1].strip()
        except IndexError as e:
            line = ''
        meth = getattr(self,'do_'+cmd,None)
        try:
            meth(session,line)
        except TypeError:
            self.unknown(session,cmd)

class Room(CommandHandler):
    '''包括一个或多个会话的泛型环境。它负责基本的命令处理和广播'''
    def __init__(self,server):
        self.server = server
        self.sessions = []
    def add(self,session):
        self.sessions.append(session)
    def remove(self,session):
        self.sessions.remove(session)
    def broadcast(self,line):
        for session in self.sessions:
            session.push(line)
    def do_logout(self,session,line):
        raise EndSession

class LoginRoom(Room):
    '''为刚刚连接上的用户建立自己的房间'''
    def add(self,session):
        Room.add(self,session)
        self.broadcast('Weclome to %s\r\n' self.server.name)
    def unknown(self,session,cmd):
        session.push('Please log in\nUse "login <nick>"\r\n')
    def do_login(self,session,line):
        name = line.strip()
        if not name:
            session.push('Please Enter a name\r\n')
        elif name in self.server.users:
            session.push('The name has been taken.\r\n')
            session.push('Please try again."\r\n')
        else:
            session.name = name
            session.enter(self.server.main_room)
class ChatRoom(Room):
    '''为多用户相互聊天准备房间'''
    def add(self,session):
        self.broadcast(session.name+' has entered the room\r\n')
        self.server.users[session.name] = session
        Room.add(self,session)
    def remove(self,session):
        self.broadcast(session.name+' has left the room\r\n')
    def do_say(self,session,line):
        self.broadcast(session.name+': '+line+'\r\n')
    def do_look(self,session,line):
        session.push('The following are in this room:\r\n')
        for other in self.sessions:
            session.push(other.name+'\r\n')
    def do_who(self,session,line):
        session.push('The following are logged in:\r\n')
        for name in self.server.users:
            session.push(name+'\r\n')

class LogoutRoom(Room):
    '''为单用户准备简单的房间，只用于用户名从服务器移除'''
    def add(self,session):
        try:del self.server.users[session.name]
        except KeyError:pass
class ChatSession(async_chat):
    '''单会话，负责和单用户通信'''
    def __init__(self,server,sock):
        async_chat.__init__(self,sock)
        self.sever = server
        self.set_terminator('\r\n')
        self.data = []
        self.name = None
        self.enter(LoginRoom(sever))
    def enter(self,room):
        try: cur = self.room
        except AttributeError:pass
        else:cur.remove(self)
        self.room = room
        room.add(self)
    def collect_incoming_data(self,data):
        self.data.append(data)
    def found_terminator(self):
        line = ''.join(self.data)
        self.data = []
        try:self.room.handle(self,line)
        except EndSession:
            self.handle_close()
    def handle_close(self):
        async_chat.handle_close(self)
        self.enter(LogoutRoom(self.server))
            
            