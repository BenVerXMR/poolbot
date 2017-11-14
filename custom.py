#!/usr/local/bin/python3
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
    #if self._lastFoundBlockNum > prevBlockNum:
      #BlockTimeAgo = prettyTimeDelta(int(int(self._lastFoundBlockTime) - prevBlockTime))
      #room.message("*burger* #" + str(self._lastFoundBlockNum) + " | &#x26cf; " + str(self._lastFoundBlockLuck) + "% | &#x23F0; " + str(BlockTimeAgo)+ " | &#x1DAC; " + self._lastFoundBlockValue)

   # def onJoin(self, room, user):
     # print(user.name + " joined the chat!")
     # room.message("Hello "+user.name+", how are you)

   # def onLeave(self, room, user):
     # print(user.name + " have left the chat")
     # room.message(user.name+" has left the building.)

  def burger():
      nowTS = time.time()
      lastBlock = requests.get(apiUrl + "pool/blocks/pplns?limit=80").json()
      lastBlockFoundTime = lastBlock[0]['ts']
      timeAgo = prettyTimeDelta(int(int(nowTS) - int(lastBlockFoundTime) / 1000))
      timeAgoInt = int(int(nowTS) - int(lastBlockFoundTime) / 1000)
      timeArray = []
      blockCounter = 1
      timeArray.append(int(timeAgoInt))
      while (int(timeAgoInt) <= 86400):
          lastBlockFoundTime = lastBlock[int(blockCounter)]['ts']
          timeAgoInt = int(int(nowTS) - int(lastBlockFoundTime) / 1000)
          blockCounter = blockCounter + 1
          timeArray.append(timeAgoInt)
          if blockCounter > 79:
              room.message("Blockcounter hitting loop-limit: 80. Exiting.")
              break
      timeDifferenceArray = []
      sharesArray = []
      diffArray = []
      timeDifferenceArrayLen = int(int(len(timeArray)) - 1)
      timeDifferenceArrayLoop = 1
      while (timeDifferenceArrayLoop <= timeDifferenceArrayLen):
          if lastBlock[int(timeDifferenceArrayLoop)]['valid'] == 1:
              timeDifference = abs(int(lastBlock[int(timeDifferenceArrayLoop)]['ts'] / 1000) - int(lastBlock[int(timeDifferenceArrayLoop + 1)]['ts'] / 1000))
              diffVal = int(lastBlock[int(timeDifferenceArrayLoop)]['diff'])
              sharesVal = int(lastBlock[int(timeDifferenceArrayLoop)]['shares'])
              diffArray.append(diffVal)
              sharesArray.append(sharesVal)
              timeDifferenceArray.append(timeDifference)
          timeDifferenceArrayLoop = timeDifferenceArrayLoop + 1
          if timeDifferenceArrayLoop > 79:
              room.message("timeDifferenceArrayLoop hitting loop-limit: 80. Exiting.")
              break
      timeDifferenceArrayResult = int(sum(timeDifferenceArray) / int(timeDifferenceArrayLoop))
      validBlockLoop = 0
      while (lastBlock[validBlockLoop]['valid'] == 0):
          if validBlockLoop >= 80:
              room.message("lastValidBlockLoop hitting loop-limit: 80. Exiting.")
              break
          validBlockLoop = validBlockLoop + 1
      lastValidBlock = lastBlock[validBlockLoop]['ts']
      #print(str(prettyTimeDelta(abs(int(lastValidBlock/1000) - int(nowTS)))))
      #print(str(prettyTimeDelta(int(lastValidBlock/1000))))
      lastValidBlockDiff = abs(int(nowTS) - int(lastValidBlock/1000))
      #print(str(prettyTimeDelta(timeDifferenceArrayResult)))
      #print(str(" . "))
      #print(str(prettyTimeDelta(lastValidBlockDiff)))
      if timeDifferenceArrayResult < lastValidBlockDiff:
          messageEst = str(" Burger is late! ")
          messageEstSmiley = str("  :( ")
      else:
          messageEst = str(" Burger is on time!  ")
          messageEstSmiley = str(" :) ")
      nextBlock = abs(timeDifferenceArrayResult - lastValidBlockDiff)
      effortCalcLoop = 0
      effortCalcArray = []
      effortCalcLimit = int(len(diffArray) - 1)
      while (effortCalcLoop <= effortCalcLimit):
          diffVal = diffArray[int(effortCalcLoop)]
          sharesVal = sharesArray[int(effortCalcLoop)]
          sumVal = int(round(100 * int(sharesVal) / int(diffVal)))
          effortCalcArray.append(sumVal)
          effortCalcLoop = effortCalcLoop + 1
          if effortCalcLoop > 79:
              room.message("effortCalcLoop hitting loop-limit: 80. Exiting.")
              break
      effort24Val = int(sum(effortCalcArray) / int(effortCalcLimit + 1))
      poolStats = requests.get(apiUrl + "pool/chart/hashrate/").json()
      poolStatsHashRate = []
      poolStatsHashRateLoop = 0
      poolStatsHashRateTime = poolStats[int(poolStatsHashRateLoop)]['ts']
      poolStatsHashRateVal = poolStats[int(poolStatsHashRateLoop)]['hs']
      timeAgoPoolstat = int(int(nowTS) - int(poolStatsHashRateTime) / 1000)
      poolStatsHashRateLoop = poolStatsHashRateLoop + 1
      while (timeAgoPoolstat <= 86400):
          poolStatsHashRateTime = poolStats[int(poolStatsHashRateLoop)]['ts']
          poolStatsHashRateVal = poolStats[int(poolStatsHashRateLoop)]['hs']
          poolStatsHashRate.append(poolStatsHashRateVal)
          timeAgoPoolstat = int(int(nowTS) - int(poolStatsHashRateTime) / 1000)
          poolStatsHashRateLoop = poolStatsHashRateLoop + 1
          if poolStatsHashRateLoop > 79:
              print("poolStatsHashRateLoop hitting loop-limit: 80. Exiting.")
              break
      poolStatsAvgHashRate = float(int(sum(poolStatsHashRate)/poolStatsHashRateLoop + 1)/1000000)
      return (blockCounter, timeDifferenceArrayResult, nextBlock, messageEst, messageEstSmiley, effort24Val, poolStatsAvgHashRate)

  def onMessage(self, room, user, message):

    if self.user == user: return

    try: 
      #cmds = ['/help', '/effort', '/pooleffort', '/price', '/block',
      #        '/window', '/test'] # Update if new command
      #hlps = ['?pplns', '?register', '?RTFN', '?rtfn', '?help', '?bench', '?list'] # Update if new helper
      cmds = ['/help', '/trite', '/scroll', '/goblin', '/mizzery', '/burger', '/motto', '/fuckduck', '/bentley', '/nismo']
      hlps = ['?trite', '?help', '?vega', '?daily', '?statsdiffer']
      searchObj = re.findall(r'(\/\w+)(\.\d+)?|(\?\w+)', message.body, re.I)
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

        if hlp.lower() == "trite":
            room.message("Custom bot/slave. Thanks! https://github.com/miziel/poolbot")

        if hlp.lower() == "help":
            room.message("Available commands (use: ?command): help, trite, vega, statsdiffer, daily") # Update if new helper

        if hlp.lower() == "daily":
            room.message("https://goo.gl/c1TQgc")
			
        if hlp.lower() == "statsdiffer":
            room.message("Your computer does the following while mining:\n\nThe pool gives you a search-job, then your miner starts calculating hashes until it finds one that matches the requirements (difficulty). The miner sends the pool the result if it exceeds the difficulty.\n\nThe pool does not see how often you perform the hash calculations. It only knows when your miner submits a hash that exceeds the difficulty.\n\nThe pool then uses the law of probability to estimate the number of hashes it took to make the share result you found. This is ONLY AN ESTIMATE. That is why you see the fluctuating numbers.\n\nYou do not get paid based on your hashrate, but by a combination of the difficulty of AND the number of shares submitted to the pool.\n\nIn very basic terms:Shares*Difficulty=MuhMoneez\n\n(credits to TheJerichoJones)")
			
        if hlp.lower() == "vega":
            room.message("https://vegamining.blogspot.com/")
            

    for i in range(len(command)):
      cmd = command[i]
      arg = argument[i]
      cmd = cmd[1:]
      arg = arg[1:]
      
      try:
        
        if cmd.lower() == "help":
            room.message("Available commands (use: /command): trite, help, scroll, goblin, burger, mizzery, motto, fuckduck, bentley, nismo. Help is in helpcommands, try ?help") # Update if new command

        if cmd.lower() == "burger":
            (blockCounter, timeDifferenceArrayResult, nextBlock, messageEst, messageEstSmiley, effort24Val, poolStatsAvgHashRate) = bot.burger()
            room.message("\n\n\n*burger*" + " Total within 24 hours: " + str(blockCounter) + " |. " + "\nAverage effort: " + str(effort24Val) + "%" + " |" + ". \nAverage time between: " + str(prettyTimeDelta(timeDifferenceArrayResult)) + " |.\n" + messageEst + str(prettyTimeDelta(nextBlock)) + messageEstSmiley + " |. " + " \nWith average pool hashrate: " + str(poolStatsAvgHashRate) + "MH/s")

        if cmd.lower() == "scroll":
            room.message("Scroll up a few lines will ya, Djeez")

        if cmd.lower() == "goblin":
            room.message("please stop writing faster than people can read. \nHave a bowl.")

        if cmd.lower() == "motto":
            room.message("\nI used to be processing drugs. \nNow I'm drugging processors.")

        if cmd.lower() == "fuckduck":
            room.message("\nI'm afraid @" + user.name + " wants you to go fuck a duck...")

        if cmd.lower() == "mizzery":
            room.message("that puzzles me")
            time.sleep(6)
			
        if cmd.lower() == "bentley":
            kraken = requests.get("https://api.kraken.com/0/public/Ticker?pair=XMREUR").json()
            EUR_XMR_krak = kraken['result']['XXMRZEUR']['c'][0]
            poolstatss = requests.get(apiUrl + "pool/stats/").json()
            totalblockss = poolstatss['pool_statistics']['totalBlocksFound']
            #savings = (6/10*int(totalblocks)*int(EUR_XMR_krak))
            savings = int(totalblockss)
            blocknum = str(savings)
            monerorate = str(EUR_XMR_krak)
            saveuro = float(EUR_XMR_krak)
            savings = savings * saveuro * 6 / 10 / 100 * 6
            blades = 95 * saveuro
            bladesformat = format(blades, ',.2f')
            savingsafterblades = savings - blades
            #krak = ast.literal_eval(EUR_XMR_krak)
            savv = format(savings, ',.2f')
            savvafter = format(savingsafterblades, ',.2f')
            #savv = str(savings)
            moretosave = 200000 - savings
            moretosaveafterblades = 200000 - savingsafterblades
            more = format(moretosave, ',.2f')
            moreafterblades = format(moretosaveafterblades, ',.2f')
            room.message("A Bentley with some options easily costs about 200.000 euro.\n Our pool found " + blocknum + " blocks since its conception. \nCurrent reward is slightly above 6 XMR, \ncurrent value of XMR on Kraken is " + monerorate + " euro. \nAt 0.6 % pool fee, total income of M5M400 would be (slightly, depending on past rewards) more than " + savv + " euro.\nThat means he still had to save " + more + " euro. \n\n He bought some blade servers though, so he's down 95 XMR again, or " + bladesformat + "euro. \n\nThat leaves him with " + savvafter + "euro or now he has to save " + moreafterblades + "euro again.")
			
        if cmd.lower() == "nismo":
            kraken = requests.get("https://api.kraken.com/0/public/Ticker?pair=XMRUSD").json()
            EUR_XMR_krak = kraken['result']['XXMRZUSD']['c'][0]
            poolstatss = requests.get(apiUrl + "pool/stats/").json()
            totalblockss = poolstatss['pool_statistics']['totalBlocksFound']
            #savings = (6/10*int(totalblocks)*int(EUR_XMR_krak))
            savings = int(totalblockss)
            blocknum = str(savings)
            monerorate = str(EUR_XMR_krak)
            saveuro = float(EUR_XMR_krak)
            savings = savings * saveuro * 6 / 10 / 100 * 6
            #krak = ast.literal_eval(EUR_XMR_krak)
            savv = format(savings, ',.2f')
            #savv = str(savings)
            moretosave = 184950 - savings
            more = format(moretosave, ',.2f')
            room.message("A Nismo starts From 176,585.00 usd.\n Our pool found " + blocknum + " blocks since its conception. \nCurrent reward is slightly above 6 XMR, \ncurrent value of XMR on Kraken is " + monerorate + " usd. \nAt 0.6 % pool fee, total pool income would be (slightly, depending on past rewards) more than " + savv + " usd.\n If M5M400 paid Snipa22 what he would like to get paid, Snipa still had to save " + more + " usd. \n\n As we know nothing about the income flows from M5M400 to Snipa, \n\n(and M5M400 states the same thing)... \n\n We're afraid Snipa will have to come up with 176,585.00 usd to get his car...")
			
        if cmd.lower() == "trite":
            justsain = ("Attention. Emergency. All personnel must evacuate immediately. \nYou now have 15 minutes to reach minimum safe distance.",
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
        room.message("Main Cmd/Msg Function Except.")
        


rooms = [""] # List of rooms you want the bot to connect to
username = "" # For tests you can use your own - trigger bot as anon
password = ""
checkForNewBlockInterval = 10 # How often to check for new block, in seconds. If not set, default value of 20 will be used

try:
  bot.easy_start(rooms,username,password, checkForNewBlockInterval)
except KeyboardInterrupt:
  print("\nStopped")
