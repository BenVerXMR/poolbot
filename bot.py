from math import erf, sqrt
import ch
import urllib
import json
import requests
import random
import time
import re


apiUrl = "https://supportxmr.com/api/"

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
      return '%ds' % (seconds,)

class bot(ch.RoomManager):
  _lastFoundBlockNum = 0
  _lastFoundBlockLuck = 0
  _lastFoundBlockValue = 0
  _lastFoundBlockTime = 0
  NblocksNum = 0
  NblocksAvg = 0
  Nvalids = 0
  
  # Fetch first N blocks and keep them in memory (or in a file? to avoid bloating RAM)
  # When requesting pooleffort, only the last (blocknum - N) blocks will be requested, saving data
  # and speeding up requests and calculations
  # An incremental recalculation could also be implemented, but it may end up losing precision
  # over time. Currently, the error is ~10^(-13)
  # Note: A // 100 * 100 rounds up blocks to the last hundred
  # Eg: 1952 // 100 * 100 == 19 * 100 == 1900 (because floor division "//" returns an int rounded down
  try:
    poolstats = requests.get(apiUrl + "pool/stats/").json()
    totalblocks = poolstats['pool_statistics']['totalBlocksFound']
    totalblocks = int(totalblocks)
    NblocksNum = totalblocks // 100 * 100 # Integer floor division
    Nblocklist = requests.get(apiUrl + "pool/blocks/pplns?limit=" + str(totalblocks)).json()
    Ntotalshares = 0
    Nvalids = 0
    Nlucks = []
    for i in reversed(range(totalblocks)):
      if i == (totalblocks - NblocksNum - 1):
          break # Ignore the last (totalblocks % NblocksNum) blocks (note the off-by-one offset)
      Ntotalshares += Nblocklist[i]['shares']
      if Nblocklist[i]['valid'] == 1:
        Ndiff = Nblocklist[i]['diff']
        Nlucks.append(Ntotalshares/Ndiff)
        Nvalids += 1
        Ntotalshares = 0
    NblocksAvg = sum(Nlucks)/Nvalids
    print("Effort for the first " + str(NblocksNum) + " blocks has been cached")
  except:
    print("Failed fetching the last N blocks - defaulting to 0")
    NblocksNum = 0
    NblocksAvg = 0
    Nvalids = 0

  def getLastFoundBlockNum(self):
    try:
      poolstats = requests.get(apiUrl + "pool/stats/").json()
      blockstats = requests.get(apiUrl + "pool/blocks/pplns?limit=1").json()
      self._lastFoundBlockNum = poolstats['pool_statistics']['totalBlocksFound']
      self._lastFoundBlockLuck = int(round(blockstats[0]['shares']*100/blockstats[0]['diff']))
      self._lastFoundBlockValue = str(round(blockstats[0]['value']/1000000000000, 5))
      self._lastFoundBlockTime = poolstats['pool_statistics']['lastBlockFoundTime']
    except:
      pass          

  def onInit(self):
    self.setNameColor("CC6600")
    self.setFontColor("000000")
    self.setFontFace("0")
    self.setFontSize(11)
    self.getLastFoundBlockNum()          

  def onConnect(self, room):
    print("Connected")
     
  def onReconnect(self, room):
    print("Reconnected")
     
  def onDisconnect(self, room):
    print("Disconnected")
    for room in self.rooms:
      room.reconnect()
    room.message("Warning: self-destruction cancelled. Systems online")

  def checkForNewBlock(self, room):
    prevBlockNum = self._lastFoundBlockNum
    prevBlockNum = int(prevBlockNum)
    prevBlockTime = self._lastFoundBlockTime
    prevBlockTime = int(prevBlockTime)
    if prevBlockNum == 0: # Check for case we can't read the number
      return
    self.getLastFoundBlockNum()
    self._lastFoundBlockNum = int(self._lastFoundBlockNum)
    if self._lastFoundBlockNum > prevBlockNum:
      BlockTimeAgo = prettyTimeDelta(int(int(self._lastFoundBlockTime) - prevBlockTime))
      room.message("*burger* #" + str(self._lastFoundBlockNum) + " | &#x26cf; " + str(self._lastFoundBlockLuck) + "% | &#x23F0; " + str(BlockTimeAgo)+ " | &#x1DAC; " + self._lastFoundBlockValue)

   # def onJoin(self, room, user):
     # print(user.name + " joined the chat!")
     # room.message("Hello "+user.name+", how are you)

   # def onLeave(self, room, user):
     # print(user.name + " have left the chat")
     # room.message(user.name+" has left the building.)

  def onMessage(self, room, user, message):

    if self.user == user: return

    try: 
      cmds = ['/help', '/effort', '/pooleffort', '/price', '/block',
              '/window', '/test'] # Update if new command
      hlps = ['?pplns', '?register', '?RTFN', '?rtfn', '?help', '?bench', '?list', '?daily'] # Update if new helper
      searchObj = re.findall(r'(\/\w+)(\.\d+)?|(\?\w+)', message.body, re.I)
      if '/all' in searchObj:
        room.message(" &#x266b;&#x266c;&#x266a; All you need is love! *h* Love is all you need! :D")
      if '/nextblock' in searchObj:
        room.message("s0on&trade;")
      searchObjCmd = []
      searchObjArg = []
      searchObjHlp = []
      for i in range(len(searchObj)):
        for j in range(len(cmds)):
          if searchObj[i][0] == cmds[j]:
            searchObjCmd.append(searchObj[i][0])
            searchObjArg.append(searchObj[i][1])
        if searchObj[i][2]:
          searchObjHlp.append(searchObj[i][2])
      command = searchObjCmd
      argument = searchObjArg
      helper = searchObjHlp
    except:
      room.message("I'm sorry @{}, I might have misunderstood what you wrote... Could you repeat please?".format(user.name))

    for i in range(len(helper)):
      hlp = helper[i]
      if hlp in hlps:
        hlp = hlp[1:]

        if hlp.lower() == "list":
            room.message("?pplns - links to explanation, ?register - how to register, ?RTFN - notice about expected downtime, ?bench - our benchmarks, ?daily - historical overview of daily burgers")

        if hlp.lower() == "help":
            room.message("The answer to your question was probably given already. If not, it's 42. Now, you can ask the question.")
            
        if hlp.lower() == "register":
            room.message("You don't have to register to mine with us, unless you want to change your payout threshold (min 0.3 XMR). But if you really, really want to just read carefully:\n"
                         "1. Put \"workername:your@email.com\" as password in your miner (\"workername\" is just a name you give to each of your devices, eg: \"laptop-1\").\n"
                         "2. Mine at least one share.\n"
                         "3. Put your address on the Dashboard. You should see a graph with your worker named \"workername\" below.\n"
                         "4. Login to the website with your address and use the email (your@email.com) as password)")

        if hlp.lower() == "pplns":
            room.message("ELI5 - http://give-me-coins.com/support/faq/what-is-pplns/ | \"Trust me, I'm an engineer\" - https://bitcointalk.org/index.php?topic=39832.msg486012#msg486012")

        if hlp.lower() == "rtfn":
            room.message("Seas 'n skies be clear, cap'n!")

        if hlp.lower() == "bench":
           room.message("https://docs.google.com/spreadsheets/d/18IrFEhWP89oG_BTUsQGS5IDG8LUYjCHDiRQkOuQ4a9A/edit#gid=0")

        if hlp.lower() == "daily":
            room.message("https://goo.gl/c1TQgc")
			


    for i in range(len(command)):
      cmd = command[i]
      arg = argument[i]
      cmd = cmd[1:]
      arg = arg[1:]
      
      try:
        
        if cmd.lower() == "help":
            room.message("Available commands (use: /command): test, help, effort, pooleffort, price, block, window")
          
        if cmd.lower() == "effort":
            poolstats = requests.get(apiUrl + "pool/stats/").json()
            networkStats = requests.get(apiUrl + "network/stats/").json()
            lastblock = requests.get(apiUrl + "pool/blocks/pplns?limit=1").json()
            rShares = poolstats['pool_statistics']['roundHashes']
            rShares = int(rShares)
            if lastblock[0]['valid'] == 0:
              previousshares = lastblock[0]['shares'] # If the last block was invalid, add those shares to the current effort
              rShares = rShares + previousshares
            diff = networkStats['difficulty']
            diff = int(diff)
            luck = int(round(100*rShares/diff))
            if rShares == 0:
              room.message("Until further notice I make 0% effort. I'm tired. Ask someone else.")
            elif (luck >= 0) and (luck <= 1):
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
            elif (luck == 404):
              room.message("404 block not found :|")
            elif (luck > 300) and (luck <= 500):
              room.message("We are at %s%% for the next block. That's a lot of red." % str(luck))
            elif (luck > 500) and (luck <= 700):
              room.message("Look, the pool is fine. But we gotta find the damn block! %s%% and counting..." % str(luck))
            elif (luck > 700) and (luck <= 833):
              room.message("We are at %s%% for the next block. Aiming for a new record, are we?" % str(luck))
            else:
              room.message("We are at %s%% for the next block. That's it, we've hit a new record. Good job everyone." % str(luck))
            if lastblock[0]['valid'] == 0:
              room.message("The last block was invalid :(")

        if cmd.lower() == "pooleffort":
            poolstats = requests.get(apiUrl + "pool/stats/").json()
            totalblocks = poolstats['pool_statistics']['totalBlocksFound']
            if not arg.isdigit():
              blocknum = totalblocks
              message = "Overall pool effort is "
            if arg.isdigit(): # no need to include the case blocknum < 0, because when writing "-1" the '-' will be picked up as a non-digit first, thus triggering the previous if
              blocknum = int(arg)                
              if blocknum == 1:
                message = "Just use /block... Effort for the last one was "
              elif blocknum > totalblocks:
                blocknum = totalblocks
                message = "You have to wait till we find so many. So far we found " + str(blocknum) + " blocks, with an overall effort of "
              elif blocknum == 0:
                blocknum = random.randrange(10, totalblocks)
                message = "Yeah, nice try... Here's some random effort for you: "
              elif blocknum == totalblocks:
                message = "Overall pool effort is "
              else:
                message = "Pool effort for the last " + str(blocknum) + " blocks is "
            if self.NblocksNum != 0 and blocknum == totalblocks:
              blockrequest = blocknum - self.NblocksNum # Only request the last blocknum % 100 blocks
            else:
              blockrequest = blocknum
            blocklist = requests.get(apiUrl + "pool/blocks/pplns?limit=" + str(blockrequest)).json()
            totalshares = 0
            valids = 0
            lucks = []
            # Average effort is the average of all efforts: sum of efforts / number of valid blocks.
            # Gotta walk the list in reverse, so that we go through the blocks in the order they
            # were found. Otherwise, invalids will mess up the values, since their shares would go into
            # the previous block instead of the following one.
            for i in reversed(range(blockrequest)):
              totalshares += blocklist[i]['shares']
              if blocklist[i]['valid'] == 1:
                diff = blocklist[i]['diff']
                lucks.append(totalshares/diff)
                valids += 1
                totalshares = 0
              # Disregard the following if block: if the last block was invalid, it will not be taken
              # into account until a valid one is found.
              #if blocklist[blocknum]['valid'] == 0: # I'll leave this here anyway :D
                #lucks.append(totalshares/diff)
                # If the last block was invalid, temporarily pretend that it's valid and take it
                # into accound. The displayed value will be incorrect until a valid block is found.
                # Given the number of blocks found by the pool already, the impact will be negligible.
            if self.NblocksNum != 0 and blocknum == totalblocks:
              totaleffort = (sum(lucks) + self.NblocksAvg * self.Nvalids) / (valids + self.Nvalids)
            else:
              totaleffort = sum(lucks) / valids
            room.message(message + "{:.2f}%".format(100 * totaleffort))

        if cmd.lower() == "price":
            self.setFontFace("8")
            try:
                poloniex = requests.get("https://poloniex.com/public?command=returnTicker").json()
                BTC_XMR_polo = poloniex['BTC_XMR']['last']
                USDT_XMR_polo = poloniex['USDT_XMR']['last']
            except (KeyError, ValueError):
                BTC_XMR_polo = ' n/a '
                USDT_XMR_polo = ' n/a '
            try:
                shapeshift = requests.get("https://shapeshift.io/rate/xmr_btc").json()
                BTC_XMR_shape = shapeshift['rate']   
            except (KeyError, ValueError):
                BTC_XMR_shape = ' n/a '
            try:
                shapeshift = requests.get("https://shapeshift.io/rate/xmr_usdt").json()
                USDT_XMR_shape = shapeshift['rate']
            except (KeyError, ValueError):
                USDT_XMR_shape = ' n/a '
            try:
                kraken = requests.get("https://api.kraken.com/0/public/Ticker?pair=XMRXBT").json()
                BTC_XMR_krak = kraken['result']['XXMRXXBT']['c'][0]
            except (KeyError, ValueError): 
                BTC_XMR_krak = ' n/a '
            try:
                kraken = requests.get("https://api.kraken.com/0/public/Ticker?pair=XMRUSD").json()
                USD_XMR_krak = kraken['result']['XXMRZUSD']['c'][0]
            except (KeyError, ValueError):
                USD_XMR_krak = ' n/a '
            try:
                kraken = requests.get("https://api.kraken.com/0/public/Ticker?pair=XMREUR").json()
                EUR_XMR_krak = kraken['result']['XXMRZEUR']['c'][0]
            except (KeyError, ValueError):
                EUR_XMR_krak = ' n/a '
            room.message(("\n|| {10:<13} | {11:<5} {12:^5.5} | {13:<4} {14:<7.7} | {15:<4} {16:<^5.5} ||"
                          "\n|| {0:<13} | {1:<5} {2:^5.5} | {3:<4} {4:^7.7} ||"
                          "\n|| {5:<13} | {6:<5} {7:^5.5} | {8:<4} {9:<7.7} ||"
                          ).format("Poloniex&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;", "USDT&nbsp;", USDT_XMR_polo, "BTC&nbsp;", BTC_XMR_polo,
                                   "Shapeshift&nbsp;&nbsp;&nbsp;", "USDT&nbsp;", USDT_XMR_shape, "BTC&nbsp;", BTC_XMR_shape,
                                   "Kraken&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;", "USD &nbsp;", USD_XMR_krak, "BTC&nbsp;", BTC_XMR_krak, "EUR&nbsp;", EUR_XMR_krak))
            self.setFontFace("0")

        if cmd.lower() == "block":
            lastBlock = requests.get(apiUrl + "pool/blocks/pplns?limit=1").json()
            lastBlockFoundTime = lastBlock[0]['ts']
            lastBlockReward = lastBlock[0]['value'] / 1000000000000
            lastBlockLuck = lastBlock[0]['shares'] * 100 / lastBlock[0]['diff']
            nowTS = time.time()
            timeAgo = prettyTimeDelta(int(nowTS - lastBlockFoundTime/1000))
            if lastBlock[0]['valid'] == 0:
              room.message("Last block was invalid :( No monies :(")
            elif lastBlockLuck < 2:
              room.message("Block worth {:.4f} XMR was found {} ago quite effortlessly: {:.1f}% effort! :D".format(lastBlockReward, timeAgo, lastBlockLuck)) 
            else:
              room.message("Block worth {:.4f} XMR was found {} ago, with {:.1f}% effort".format(lastBlockReward, timeAgo, lastBlockLuck))

        if cmd.lower() == "window":
            histRate = requests.get(apiUrl + "pool/chart/hashrate/").json()
            networkStats = requests.get(apiUrl + "network/stats/").json()
            diff = networkStats['difficulty']
            length = 20
            hashRate = 0
            for i in range(length):
              hashRate += histRate[i]['hs']
            avgHashRate = hashRate/length
            window = prettyTimeDelta(2*diff/avgHashRate)
            room.message("Current pplns window is roughly {0}".format(window))
        
        if cmd.lower() == "test":
            justsain = ("Attention. Emergency. All personnel must evacuate immediately. You now have 15 minutes to reach minimum safe distance.",
                        "I'm sorry @" + user.name + ", I'm afraid I can't do that.",
                        "@" + user.name + ", you are fined one credit for violation of the verbal morality statute.",
                        "42", "My logic is undeniable.", "Danger, @" + user.name + ", danger!",
                        "Apologies, @" + user.name + ". I seem to have reached an odd functional impasse. I am, uh ... stuck.",
                        "Don't test. Ask. Or ask not.", "This is my pool. There are many like it, but this one is mine!", "I used to be a miner like you, but then I took an ASIC to the knee")
            room.message(random.choice(justsain))
      
      except json.decoder.JSONDecodeError:
        print("There was a json.decoder.JSONDecodeError while attempting /" + str(cmd.lower()) + " (probably due to /pool/stats/)")
        room.message("JSON Bourne is trying to kill me!")
      except:
        print("Error while attempting /" + str(cmd.lower()))
        room.message("Oops. Something went wrong. You cannot afford your own Bot. Try again in a few minutes.")

rooms = [""] # List of rooms you want the bot to connect to
username = "" # For tests you can use your own - trigger bot as anon
password = "*"
checkForNewBlockInterval = 10 # How often to check for new block, in seconds. If not set, default value of 20 will be used

try:
  bot.easy_start(rooms,username,password, checkForNewBlockInterval)
except KeyboardInterrupt:
  print("\nStopped")
