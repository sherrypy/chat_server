# -*- coding: utf-8 -*-
import socket, select, string
import sys
import logging
import time
import threading
from collections import defaultdict
import emoji

HOST = ''   # Symbolic name meaning all available interfaces
PORT = 8888 # Arbitrary non-privileged port
BUF_SIZE = 4096
TIMEOUT = 5

class ChatServer(threading.Thread):
    def __init__(self, conn, addr):
	threading.Thread.__init__(self)
	self.conn = conn
	self.addr = addr
    self.id   = addr[1]
	self.ip   = addr[0]
	self.name = ''
    self.group = list()

    def print_indicator(self, prompt):
    	self.conn.send('%s\n>> ' % (prompt,))

    def login(self):
        global clients
        global messages
        global accounts
        global onlines

        logging.info('Connected from: %s:%s' %
                     (self.addr[0], self.addr[1]))
        clients.add((self.conn, self.addr))
        msg = '\n----Welcome to Chat Server!----\n'
        msg += '[ Please enter your name: ]'
        self.print_indicator(msg)
        name = self.conn.recv(BUF_SIZE).strip()
        # if it is a new user, create an account for it.
        if name not in accounts:
            accounts[name] = {
                'pass': '',
                'lastlogin': time.ctime()
            }
            self.name = name
            logging.info('%s logged as %s ' % (self.addr[0], self.name))
            messages[name] = []
            self.print_indicator(
                '[ Hello %s, please create your password:]' % (self.name,))
            password = self.conn.recv(BUF_SIZE)
            accounts[self.name]['pass'] = password.strip()
            self.print_indicator(
                '\nEnter `!q` to quit.\
                \nEnter`/help` to see all commands.\n')
            self.print_indicator(
                '[ Welcome,%s! Enjoy your chat!]\n%s' % 
                (self.name,emoji.welcome()))
        else:
            self.name = name
            msg = '[ Hello %s, please enter your password:]\n' % (self.name,)
            # print accounts
            self.print_indicator(msg)
            while True:
                password = self.conn.recv(BUF_SIZE).strip()
                if password != accounts[self.name]['pass']:
                    self.print_indicator(
                        '[ Incorrect password, please enter again]\n')
                else:
                    self.conn.send(
                        '[ Welcome back, last login: %s]\n' %
                        (accounts[self.name]['lastlogin'],))
                    accounts[self.name]['lastlogin'] = time.ctime()
                    self.print_indicator(
                        '\nEnter `!q` to quit.\
                        \nEnter`/help` to see all commands.\n')
                    break
            self.conn.send(self.show_mentions(self.name))
        self.broadcast('[%s] is online now' % (self.name,), clients, False)
        onlines[self.name] = self.conn

    def logoff(self):
        global clients
        global onlines
        global groups
        global mute
        self.conn.send('[ Bye! ]\n')
        del onlines[self.name]
        try:
            del mute[self.id]
        except:
            pass
        #remove user from all joined groups
        for group_name in self.group:
            groups[group_name].remove((self.conn, self.addr, self.name))
        clients.remove((self.conn, self.addr))
        #broadcast to active users
        if onlines:
            self.broadcast('[ %s ] is offline now.\n' %
                           (self.name,), clients)
        self.conn.close()
        exit()

    def check_keyword(self, buf):
        if buf.find('/help') == 0:
            self.help()
            return True
        if buf.find('!q') == 0:
            self.logoff()
        if buf.find('/g') == 0:
            self.list_group()
            return True
        if buf.find('/u') == 0:
            self.list_user()
            return True
        if buf.find('/mute') == 0:
            self.mute_broadcast()
            return True
        if buf.find('/msg') == 0:
            self.cancel_mute()
            return True
        if buf.find('#') == 0:
            group_keyword = buf.split(' ')[0][1:]
            group_component = group_keyword.split('/')

            # to post in a group
            if len(group_component) == 1:
                group_name = group_component[0]
                try:
                    msg = '[%s]%s: %s' % (
                        group_name, self.name, buf.split(' ', 1)[1])
                    self.group_post(group_name, msg)
                except IndexError:
                    self.print_indicator(
                        '--command not found.\
                        \nEnter `/help` to see all commands.')

            # to join / leave a group, show group member list
            elif len(group_component) == 2:
                group_name = group_component[0]
                if group_component[1] == 'join':
                    self.group_join(group_name)
                elif group_component[1] == 'leave':
                    self.group_leave(group_name)
                elif group_component[1] == 'list':
                    self.group_members(group_name)
            return True

        if buf.find('@') == 0:
            to_user = buf.split(' ')[0][1:]
            from_user = self.name
            msg = buf.split(' ', 1)[1]

            # if user is online
            if to_user in onlines:
                onlines[to_user].send('@%s: %s\n>> ' % (from_user, msg))
                self.mention(from_user, to_user, msg, 1)
            # offline
            else:
                self.mention(from_user, to_user, msg)
            return True

        # emoji
        if buf.find('/welcome') == 0:
            self.print_indicator(emoji.welcome())
            return True
        if buf.find('/h5') == 0:
            self.print_indicator(emoji.highFive())
            return True
        if buf.find('/fight') == 0:
            self.print_indicator(emoji.fight())
            return True
        if buf.find('/down') == 0:
            self.print_indicator(emoji.lieDown())
            return True
        if buf.find('/confuse') == 0:
            self.print_indicator(emoji.confuse())
            return True
        if buf.find('/love') == 0:
            self.print_indicator(emoji.love())
            return True
        if buf.find('/cry') == 0:
            self.print_indicator(emoji.cry())
            return True
        if buf.find('/angry') == 0:
            self.print_indicator(emoji.angry())
            return True
        if buf.find('/happy') == 0:
            self.print_indicator(emoji.happy())
            return True
        if buf.find('/awk') == 0:
            self.print_indicator(emoji.awkward())
            return True

    #show all active users
    def list_user(self):
        res = ''
        for user in onlines.keys():
            if user == self.name:
                res += '%s *\n' % user
            else:
                res += '%s\n' % user
        self.print_indicator(
            '[List of online users] \n%s' % (res,))

    #show all the groups
    def list_group(self):
        res = ''
        for k,v in groups.items():
            if (self.conn, self.addr, self.name) in v:
                res += '%s (%s) *\n' % (k, len(v))
            else:
                res += '%s (%s)\n' % (k, len(v))
        self.print_indicator(
            '[List of chat groups] \n%s' % (res,))

    #send message only to group members
    def group_post(self, group_name, msg):
        global groups
        # if the group does not exist, create it
        groups.setdefault(group_name, list())

        # if current user is a member of the group
        if (self.conn, self.addr, self.name) in groups[group_name]:
            self.group_broadcast(msg, groups[group_name])
        else:
            self.print_indicator(
                '## You are current not a member of group [%s]' % 
                (group_name,))

    #show group members
    def group_members(self, group_name):
        if (self.conn, self.addr, self.name) in groups[group_name]:
            res = ''
            for group_member in groups[group_name]:
                if self.name == group_member[2]:
                    res += '%s *\n' % group_member[2]
                else:
                    res += '%s\n' % group_member[2]
            self.print_indicator(
                '## Members of group [%s] \n%s' % (group_name, res))
        else:
            self.print_indicator(
                '## You are current not a member of group [%s]' % 
                (group_name,))

    #join a group chat
    def group_join(self, group_name):
        global groups
        if group_name in self.group:
            self.print_indicator(
                '## You are already a member of the group [%s]' %
                (group_name,))
        else:
            self.group.append(group_name)
            groups.setdefault(group_name, list())
            groups[group_name].append((self.conn, self.addr, self.name))
            self.print_indicator(
                '## You have joined the group [%s]' %(group_name,))

    #leave a group chat
    def group_leave(self, group_name):
        global groups
        if group_name in self.group:
            self.group.remove(group_name)
            try:
                groups[group_name].remove((self.conn, self.addr, self.name))
                self.print_indicator(
                    '## You have left the group [%s]' %(group_name,))
            except Exception, e:
                pass
        else:
            self.print_indicator(
                '## You are current not a member of group [%s]' % 
                (group_name,))

    #send message only to a specific user
    def mention(self, from_user, to_user, msg, read=0):
        global messages
        # print 'Messages', messages
        if to_user in messages:
            messages[to_user].append([from_user, msg, read])
            self.print_indicator('## Message has sent to [%s]' % (to_user,))
        else:
            self.print_indicator('## No such user named [%s]' % (to_user,))

    #show messages directly sent to a user
    def show_mentions(self, name):
        global messages
        res = '[ Here are your messages:]\n'
        if not messages[name]:
            res += '   No messages available\n>> '
            return res
        for msg in messages[name]:
            if msg[2] == 0:
                res += '(NEW) %s: %s\n' % (msg[0], msg[1])
                msg[2] = 1
            else:
                res += '      %s: %s\n' % (msg[0], msg[1])
        res += '>> '
        return res
    
    #start receiving message from broadcast method
    def cancel_mute(self):
        global mute
        try:
            #if user on mute mode
            del mute[self.id]
        except:
            pass
        self.print_indicator('[ You are receiving broadcast messages ]')

    #stop receiving message from broadcast method
    def mute_broadcast(self):
        global mute
        mute[self.id] = 1
        self.print_indicator('[ You have muted the broadcast messages ]')

    #only send message to group members
    def group_broadcast(self, msg, receivers, to_self=True):
        for conn, addr, name in receivers:
            # if the client is not the current user
            if addr[1] != self.id:
                conn.send(msg + '\n>> ')
            # if current user
            else:
                self.conn.send('>> ') if to_self else self.conn.send('')

    def broadcast(self, msg, receivers, to_self=True):
        for conn, addr in receivers:
            # if the client is not the current user
            if addr[1] != self.id:
                if not mute.get(addr[1]):
                    conn.send(msg + '\n>> ')
            # if current user
            else:
                self.conn.send('>> ') if to_self else self.conn.send('')

    def help(self):
        self.print_indicator(
            '[ This is Sherry\'s chat server. @author: Sherry.Xiao ]\
            \n/help : print all available commands.\
            \n!q    : quit chat server.\
            \n/u    : print all active users.\
            \n/g    : print all chat groups.\
            \n/mute : mute boradcast messages.\
            \n/msg  : start to receiving broadcast messages.\
            \n#[group_name]/join        : join group [group_name].\
            \n#[group_name]/leave       : leave group [group_name].\
            \n#[group_name]/list        : print all group members.\
            \n#[group_name] [message]   : send message to all group members.\
            \n@[user_name]              : send message to user [user_name].\
            \n-------ascii art------\
            \n[/welcome] [/h5] [/fight] [/down] [/confuse]\
            \n[/love] [/cry] [/angry] [/happy] [/awk]\n')

    def run(self):
        global messages
        global accounts
        global clients
        self.login()

        while True:
            try:
                self.conn.settimeout(TIMEOUT)
                buf = self.conn.recv(BUF_SIZE).strip()
                logging.info('%s@%s: %s' % (self.name, self.addr[0], buf))
                # if message is empty
                if not buf.strip():
                    self.print_indicator(
                        '[Message to be sent cannot be empty!]')
                    continue
                # check features
                if not self.check_keyword(buf):
                    # client broadcasts message to all
                    self.broadcast('%s: %s' % (self.name, buf), clients)

            except Exception, e:
                # timed out
                pass

def main():
    global clients
    global messages
    global accounts
    global onlines
    global groups
    global mute

    # logging setup
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s: %(message)s',
                        datefmt='%d/%m/%Y %I:%M:%S %p')

    # initialize global vars
    clients = set()
    messages = {}
    accounts = {}
    onlines = {}
    groups = {}
    mute = defaultdict()

    # set up socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print 'Socket created'
    #s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    #Bind socket to local host and port
    try:
        s.bind((HOST, PORT))
    except socket.error as msg:
        print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()    
    print 'Socket bind complete'
     
    #Start listening on socket
    s.listen(20)
    print 'Socket now listening'

    while True:
        try:
            conn, addr = s.accept()
            server = ChatServer(conn, addr)
	    server.start()
            #start_new_thread(server.run(),(conn,addr))
        except Exception, e:
            print e

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print '#####EXITED####\n'
