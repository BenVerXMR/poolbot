import ch
import urllib
import json
import requests
import datetime
import math
import time
import re

def prettyTimeDelta(seconds):
  seconds = int(seconds)
  days, seconds = divmod(seconds, 86400)
  hours, seconds = divmod(seconds, 3600)
  minutes, seconds = divmod(seconds, 60)
  if days > 0:
      return '%dd %dh' % (days, hours)
  elif hours > 0:
      return '%dh %dm' % (hours, minutes)
  elif minutes > 0:
      return '%dm %ds' % (minutes, seconds)
  else:
      return '%ds' % (seconds)

class bot(ch.RoomManager):
  
  def onInit(self):
    self.setNameColor("505050")
    self.setFontColor("000000")
    self.setFontFace("Arial")
    self.setFontSize(11)

  def onConnect(self, room):
    print("Connected")

  def onReconnect(self, room):
    print("Reconnected")

  def onDisconnect(self, room):
    print("Disconnected")  

  def onMessage(self, room, user, message):

    if self.user == user: return
    
    try:
      cmds = ['/help', '/luck', '/poolluck', '/price', '/block', '/window', '/test'] # update if new command
      wholeAnswer = []
      searchObj = re.findall(r'(/\w+)+', message.body, re.I)
      if searchObj:
          command = list(set(cmds) & set(searchObj))
          if command:
              command.reverse()
          else:
              return
      else:
        return
      room.message("I'm sorry {}, I might have misunderstood what you wrote... Could you repeat please?".format(user.name))

    for i in range(len(command)):
         cmd = command[i]    

    try:                  # probably completly unnecessary try (leftover form first version)
      if cmd[0] == "/":
          prfx = True
          cmd = cmd[1:]
      else:
          prfx = False
    except:
      room.message("I'm sorry, I might have a reading problem... Could you please repeat that @{}?".format(user.name))
      
    if cmd.lower() == "help" and prfx:
        room.message("Available commands (use: /command): help, luck, poolluck, price, block, window")
      
    if cmd.lower() == "luck" and prfx:
        poolStats = requests.get("https://supportxmr.com/api/pool/stats/").json()
        networkStats = requests.get("https://supportxmr.com/api/network/stats/").json()
        rShares = poolStats['pool_statistics']['roundHashes']
        diff = networkStats['difficulty']
        luck = int(rShares*100/diff)
        if (luck >= 0) and (luck <= 1):
          room.message("We are at %s%% for the next block. Great! We just found one! *burger*" % str(luck))
        elif (luck > 1) and (luck <= 20):
          room.message("We are at %s%% for the next block. Noice :)" % str(luck))
        elif (luck > 20) and (luck <= 80):
          room.message("We are at %s%% for the next block. Looking good and green 8)" % str(luck))
        elif (luck > 80) and (luck <= 100):
          room.message("We are at %s%% for the next block. Still green but..." % str(luck))
        elif (luck > 100) and (luck <= 120):
          room.message("We are at %s%% for the next block. A bit reddish." % str(luck))
        elif (luck > 120) and (luck <= 150):
          room.message("We are at %s%% for the next block. Getting more red every hash :(" % str(luck))
        elif (luck > 150) and (luck <= 200):
          room.message("We are at %s%% for the next block. Wouldn't mind finding one NOW!" % str(luck))
        elif (luck > 200) and (luck <= 300):
          room.message("We are at %s%% for the next block. Damn time to find one, don't you think?" % str(luck))
        elif (luck > 300) and (luck <= 400):
          room.message("We are at %s%% for the next block. That's a lot of red." % str(luck))
        else:
          room.message("We are at %s%% for the next block. Aiming for a new record, are we?" % str(luck))
          
    if cmd.lower() == "poolluck" and prfx:
        poolstats = requests.get("https://supportxmr.com/api/pool/stats/").json()
        blocknum = poolstats['pool_statistics']['totalBlocksFound']
        blocklist = requests.get("https://supportxmr.com/api/pool/blocks/pplns?limit=" + str(blocknum)).json()
        totaldiff = 0
        totalshares = 0
        startingblock = 1  # number of the starting block from which to scan the list
        for i in reversed(range(0, blocknum-startingblock+1)):
            totalshares += blocklist[i]['shares']
            if blocklist[i]['valid'] == 1:
                totaldiff += blocklist[i]['diff']
        room.message("Overall pool luck is " + str(totalshares*100/totaldiff) + "%")
        
    if cmd.lower() == "price" and prfx:
        self.setFontFace("8")
        poloniex = requests.get("https://poloniex.com/public?command=returnTicker").json()
        BTC_XMR_polo = poloniex['BTC_XMR']['last']
        USDT_XMR_polo = poloniex['USDT_XMR']['last']
        cryptocompare = requests.get("https://min-api.cryptocompare.com/data/price?fsym=XMR&tsyms=BTC,USD").json()
        BTC_XMR_cc = cryptocompare['BTC']
        USD_XMR_cc = cryptocompare['USD']
        room.message(("\r|| {0:.<15} | {1:.<6} {2:.^5.5} |  {3:.<6} {4:.^7.7} ||"
                      "\r|| {5:.<15} | {6:.<6} {7:.^5.2f} |  {8:.<6} {9:.^7.5f} ||")
                     .format("Poloniex", "USDT", USDT_XMR_polo, "BTC", BTC_XMR_polo,
                             "Cryptocompare", "USD", USD_XMR_cc, "BTC", BTC_XMR_cc))
        self.setFontFace("0")
        
    if cmd.lower() == "block2" and prfx:
        poolstats = requests.get("https://supportxmr.com/api/pool/stats/").json()
        lastblocktime = datetime.datetime.utcfromtimestamp(poolstats['pool_statistics']['lastBlockFoundTime'])
        blocknum = poolstats['pool_statistics']['totalBlocksFound']
        nowtime = datetime.datetime.utcnow()
        delta = nowtime - lastblocktime
        room.message("Last block (#" + str(blocknum) + ") was found on " + str(lastblocktime) + " UTC, " + str(math.floor(d.seconds/3600)) + "h:" + str(math.floor(d.seconds/60%60)) + "m ago")

    if cmd.lower() == "block" and prfx:
        lastBlock = requests.get("https://supportxmr.com/api/pool/blocks/pplns?limit=1").json()
        lastBlockFoundTime = lastBlock[0]['ts']
        lastBlockReward = str(lastBlock[0]['value'])
        lastBlockLuck = int(lastBlock[0]['shares']*100/lastBlock[0]['diff'])
        xmr = (lastBlockReward[:1] + "." + lastBlockReward[1:5])
        nowTS = time.time()
        timeAgo = prettyTimeDelta(int(nowTS - lastBlockFoundTime/1000))
        room.message("Block worth " + xmr + " XMR was found "+str(timeAgo)+" ago with " + str(lastBlockLuck) + "% luck.")
        
    if cmd.lower() == "window" and prfx:
        histRate = requests.get("https://supportxmr.com/api/pool/chart/hashrate/").json()
        networkStats = requests.get("https://supportxmr.com/api/network/stats/").json()
        diff = networkStats['difficulty']
        l = len(histRate)
        hashRate = 0
        for i in range(l):
          hashRate += histRate[i]['hs']
        avgHashRate = hashRate/l
        window = prettyTimeDelta(2*diff/avgHashRate)
        room.message("Current payout window is roughly {0}".format(window))
        
    if cmd.lower() == "test" and prfx:
            justsain = ("Testing, one, two, three","Oak is strong and also gives shade",
                        "Cats and dogs each hate the other", "The pipe began to rust while new",
                        "The ripe taste of cheese improves with age", "Open the crate but don't break the glass",
                        "The hog crawled under the high fence","Don't try. Do. Or do not.")
            room.message("{0}. Test successful {1}".format(random.choice(justsain), user.name))

rooms = [""] #list rooms you want the bot to connect to
username = "" #for tests can use your own - triger bot as anon
password = ""

bot.easy_start(rooms,username,password)
