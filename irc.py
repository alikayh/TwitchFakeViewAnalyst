import streamlit as st
import socket
import datetime

class Tag:
    def __init__(self, input=[]):
        i = 0
        self.attr = {}
        for item in input:
            self.attr[item[:item.find("=")]] = item[item.find("=") + 1:]

    def isBan(self):
        if ("ban-duration" in self.attr) or ("login" in self.attr):
            return False
        if ("target-user-id" in self.attr) and ("ban-duration" not in self.attr):
            return True

    def isTimeout(self):
        if ("ban-duration" in self.attr) and ("target-user-id" in self.attr):
            return True
        else:
            return False

    def isEmoteOnly(self):
        if ("emote-only" in self.attr) and ("display-name" not in self.attr):
            return True
        else:
            return False

    def isFollowersOnly(self):
        if "followers-only" in self.attr:
            return True
        else:
            return False

    def isSubsOnly(self):
        if "subs-only" in self.attr:
            return True
        else:
            return False

    def isR9K(self):
        if "r9k" in self.attr:
            return True
        else:
            return False

    def isSlow(self):
        if "slow" in self.attr:
            return True
        else:
            return False

    def show(self):
        print("{}".format(self.attr))

class TwitchChat:
    SERVER = "irc.twitch.tv"
    PORT = 6667
    irc = socket.socket()
    BOT = ""
    PASS = ""
    feed_flag = False
    command_queue = []
    recent_join_counter = 0
    recent_join_timer = -1

    def __init__(self, user, password):
        self.BOT = user
        self.PASS = password
        self.irc.connect((self.SERVER, self.PORT))

    def sendIRC(self, command):
        self.irc.send(command.encode())

    def setUsername(self, user):
        self.BOT = user

    def setPassword(self, password):
        self.PASS = password

    def identify(self):
        self.sendIRC("PASS " + self.PASS + "\n" + "NICK " + self.BOT + "\n")

    def requestCAP(self):
        self.sendIRC("CAP REQ :twitch.tv/membership\r\n")

    def joinChannel(self, channel):
        if self.recent_join_counter < 19:
            self.sendIRC("JOIN #" + channel.lower() + "\n")
            self.recent_join_counter += 1
            if self.recent_join_timer == -1:
                self.recent_join_timer = datetime.datetime.now()
            return True
        else:
            self.time_difference = datetime.datetime.now() - self.recent_join_timer
            if self.time_difference.total_seconds() > 10:
                self.sendIRC("JOIN #" + channel.lower() + "\n")
                self.recent_join_timer = datetime.datetime.now()
                self.recent_join_counter = 1
                return True
            else:
                self.command_queue.append(["JOIN", channel])
                return False

    def leaveChannel(self, channel):
        self.sendIRC("PART #" + channel + "\n")

    def readFeed(self, feed_placeholder):
        while self.feed_flag == False:
            if self.command_queue:
                if self.command_queue[0][0] == "JOIN":
                    self.time_difference = datetime.datetime.now() - self.recent_join_timer
                    if self.time_difference.total_seconds() > 10:
                        if self.joinChannel(self.command_queue[0][1]):
                            self.command_queue.pop(0)

            feedBuffer = self.irc.recv(4096)
            try:
                feed = feedBuffer.decode()
            except:
                print("Error in decoding feedBuffer")
            for line in feed.split("\r\n"):
                if len(line) > 0:
                    self.processFeed(line, feed_placeholder)

    def processFeed(self, feed, feed_placeholder):
        if feed.find("PING :tmi.twitch.tv") >= 0:
            self.onPing(feed)
        elif feed[0] == ":":
            self.processEvent(feed, feed_placeholder)

    def processEvent(self, feed, feed_placeholder):
        feed = feed.replace("\r", "").replace("\n", "")
        tmi = feed.find("tmi.twitch.tv")
        tagList = feed[1:tmi - 1].split(";")
        tags = None

        if len(tagList) > 1:
            tags = Tag(tagList)

        body = feed[tmi + 14:]
        hashtag = body.find("#")
        colon = body.find(":")

        if body.find("PRIVMSG") == 0:
            channel = body[8:colon - 1]
            message = body[colon + 1:]
            self.onMessage(feed_placeholder, tags, channel, message)

    def onPing(self, feed):
        self.sendIRC("PONG :tmi.twitch.tv\r\n")

    def onMessage(self, feed_placeholder, tags, channel, message):
        feed_placeholder.markdown(f"**Channel**: {channel} | **Message**: {message}")

st.title("Twitch Chat Viewer")
user = st.text_input("Bot Username")
password = st.text_input("Bot Password", type="password")
channel = st.text_input("Channel Name")
if st.button("Connect"):
    tc = TwitchChat(user, password)
    tc.identify()
    tc.requestCAP()
    if tc.joinChannel(channel):
        feed_placeholder = st.empty()
        tc.readFeed(feed_placeholder)
