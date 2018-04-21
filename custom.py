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
        poolstats = requests.get(apiUrl + "pool/stats/pplns/").json()
        totalblocks = poolstats['pool_statistics']['totalBlocksFound']
        #print('total blocks found is ' + str(totalblocks))
        # totalblocks=2500
        totalblocks = int(totalblocks)
        NblocksNum = totalblocks // 100 * 100  # Integer floor division
        Nblocklist = requests.get(apiUrl + "pool/blocks/pplns/?limit=" + str(totalblocks)).json()
        # print(Nblocklist);
        Ntotalshares = 0
        Nvalids = 0
        Nlucks = []
        for i in reversed(range(totalblocks)):
            #if i == (totalblocks - NblocksNum - 1):
             #   break  # Ignore the last (totalblocks % NblocksNum) blocks (note the off-by-one offset)
            #print(str(Ntotalshares))
            #print(str(Nblocklist[i]['valid']))
            #break
            Ntotalshares += int(Nblocklist[i]['shares'])
            #print(str(Ntotalshares))
            #print(str(Nblocklist[i]['valid']))
            if str(Nblocklist[i]['valid']) == 'True':
                #print(str(Nblocklist[i]['valid']))
                Ndiff = int(Nblocklist[i]['diff'])
                Nlucks.append(Ntotalshares / Ndiff)
                Nvalids += 1
                Ntotalshares = 0
        NblocksAvg = sum(Nlucks) / Nvalids
        print("Effort for the first " + str(NblocksNum) + " blocks has been cached")
    except:
        print("Failed fetching the last N blocks - defaulting to 0")
        NblocksNum = 0
        NblocksAvg = 0
        Nvalids = 0

    def getLastFoundBlockNum(self):
        try:
            poolstats = requests.get(apiUrl + "pool/stats/pplns/").json()
            blockstats = requests.get(apiUrl + "pool/blocks/pplns/?limit=1").json()
            self._lastFoundBlockNum = int(poolstats['pool_statistics']['totalBlocksFound'])
            self._lastFoundBlockLuck = int(round(int(blockstats[0]['shares']) * 100 / int(int(blockstats[0]['diff']))))
            self._lastFoundBlockValue = str(round(int(blockstats[0]['value']) / 1000000000000, 5))
            self._lastFoundBlockTime = int(poolstats['pool_statistics']['lastBlockFoundTime'])
            #print (str(self._lastFoundBlockNum) + ' - ' + str(self._lastFoundBlockLuck) + ' - '+ str(self._lastFoundBlockValue) +' - ' + str(self._lastFoundBlockTime))
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
        if prevBlockNum == 0:  # Check for case we can't read the number
            return
        self.getLastFoundBlockNum()
        self._lastFoundBlockNum = int(self._lastFoundBlockNum)
        # if self._lastFoundBlockNum > prevBlockNum:
        # BlockTimeAgo = prettyTimeDelta(int(int(self._lastFoundBlockTime) - prevBlockTime))
        # room.message("*burger* #" + str(self._lastFoundBlockNum) + " | &#x26cf; " + str(self._lastFoundBlockLuck) + "% | &#x23F0; " + str(BlockTimeAgo)+ " | &#x1DAC; " + self._lastFoundBlockValue)

        # def onJoin(self, room, user):
        # print(user.name + " joined the chat!")
        # room.message("Hello "+user.name+", how are you)

        # def onLeave(self, room, user):
        # print(user.name + " have left the chat")
        # room.message(user.name+" has left the building.)

    def burger(hournum, timetocheck, blockstocheck, endblocksloop):
        #print('success')
        blockstocheckstr = str(blockstocheck)
        #print(blockstocheckstr)
        nowTS = time.time()
        lastBlock = requests.get(apiUrl + "pool/blocks/pplns/?limit=" + blockstocheckstr).json()
        lastBlockFoundTime = int(lastBlock[0]['ts'])
        timeAgo = prettyTimeDelta(int(int(nowTS) - int(lastBlockFoundTime) / 1000))
        timeAgoInt = int(int(nowTS) - int(lastBlockFoundTime) / 1000)
        timeArray = []
        blockCounter = 1
        timeArray.append(int(timeAgoInt))
        # print('success')
        while (int(timeAgoInt) <= (timetocheck)):
            lastBlockFoundTime = int(lastBlock[int(blockCounter)]['ts'])
            timeAgoInt = int(int(nowTS) - int(lastBlockFoundTime) / 1000)
            #print(str(timeAgoInt) + '-' + str(blockCounter) + '-' + str(timetocheck) + '-' + str(endblocksloop))
            blockCounter = blockCounter + 1
            timeArray.append(timeAgoInt)
            #print(str(timeAgoInt))
            #print(str(blockCounter) + '-' + str(endblocksloop))
            if blockCounter > endblocksloop:
                #room.message('test' + blockstocheckstr)
                #room.message("Blockcounter hitting loop-limit: " + blockstocheckstr + ". Exiting.")
                break
        #print('successmeta')
        timeDifferenceArray = []
        sharesArray = []
        diffArray = []
        timeDifferenceArrayLen = int(int(len(timeArray)) - 1)
        timeDifferenceArrayLoop = 1
        #print('successmeta')
        while (timeDifferenceArrayLoop <= timeDifferenceArrayLen):
            #print(str(lastBlock[int(timeDifferenceArrayLoop)]['valid']))
            #print('tested')
            if str(lastBlock[int(timeDifferenceArrayLoop)]['valid']) == 'True':
                timeDifference = abs(int(int(lastBlock[int(timeDifferenceArrayLoop)]['ts']) / 1000) - int(
                    int(int(lastBlock[int(timeDifferenceArrayLoop + 1)]['ts'])) / 1000))
                #print(timeDifference)
                diffVal = int(lastBlock[int(timeDifferenceArrayLoop)]['diff'])
                sharesVal = int(lastBlock[int(timeDifferenceArrayLoop)]['shares'])
                diffArray.append(diffVal)
                sharesArray.append(sharesVal)
                timeDifferenceArray.append(timeDifference)
                #print('time' + '-' + str(timeDifferenceArrayLoop))
            timeDifferenceArrayLoop = timeDifferenceArrayLoop + 1
            if int(timeDifferenceArrayLoop) >= int(endblocksloop):
                #room.message("timeDifferenceArrayLoop hitting loop-limit: " + str(blockstocheck) + ". Exiting.")
                break
        #print('pp')
        timeDifferenceArrayResult = int(sum(timeDifferenceArray) / int(timeDifferenceArrayLoop))
        validBlockLoop = 0
        print(str(lastBlock[validBlockLoop]['valid']))
        while (str(lastBlock[validBlockLoop]['valid']) == 'False'):
            #print('false')
            if validBlockLoop >= blockstocheck:
                room.message("lastValidBlockLoop hitting loop-limit: " + str(blockstocheck) + ". Exiting.")
                break
            validBlockLoop = validBlockLoop + 1
        lastValidBlock = int(lastBlock[validBlockLoop]['ts'])
        # print(str(prettyTimeDelta(abs(int(lastValidBlock/1000) - int(nowTS)))))
        # print(str(prettyTimeDelta(int(lastValidBlock/1000))))
        lastValidBlockDiff = abs(int(nowTS) - int(lastValidBlock / 1000))
        # print(str(prettyTimeDelta(timeDifferenceArrayResult)))
        # print(str(" . "))
        # print(str(prettyTimeDelta(lastValidBlockDiff)))
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
            if effortCalcLoop > endblocksloop:
                room.message("effortCalcLoop hitting loop-limit: " + str(blockstocheck) + ". Exiting.")
                break
        effort24Val = int(sum(effortCalcArray) / int(effortCalcLimit + 1))
        poolStats = requests.get(apiUrl + "pool/chart/hashrate/").json()
        poolStatsHashRate = []
        poolStatsHashRateLoop = 0
        poolStatsHashRateTime = int(poolStats[int(poolStatsHashRateLoop)]['ts'])
        poolStatsHashRateVal = int(poolStats[int(poolStatsHashRateLoop)]['hs'])
        timeAgoPoolstat = int(int(nowTS) - int(poolStatsHashRateTime) / 1000)
        poolStatsHashRateLoop = poolStatsHashRateLoop + 1
        while (timeAgoPoolstat <= timetocheck):
            poolStatsHashRateTime = int(poolStats[int(poolStatsHashRateLoop)]['ts'])
            poolStatsHashRateVal = int(poolStats[int(poolStatsHashRateLoop)]['hs'])
            poolStatsHashRate.append(poolStatsHashRateVal)
            timeAgoPoolstat = int(int(nowTS) - int(poolStatsHashRateTime) / 1000)
            poolStatsHashRateLoop = poolStatsHashRateLoop + 1
            if poolStatsHashRateLoop > endblocksloop:
                print("poolStatsHashRateLoop hitting loop-limit: " + str(blockstocheck) + ". Exiting.")
                break
        poolStatsAvgHashRate = float(int(sum(poolStatsHashRate) / poolStatsHashRateLoop + 1) / 1000000)
        poolStatsAvgHashRate = format(poolStatsAvgHashRate, ',.2f')
        return (blockCounter, timeDifferenceArrayResult, nextBlock, messageEst, messageEstSmiley, effort24Val,
                poolStatsAvgHashRate)

    def onMessage(self, room, user, message):

        global searchObjCmd
        if self.user == user: return

        try:
            # cmds = ['/help', '/effort', '/pooleffort', '/price', '/block',
            #        '/window', '/test'] # Update if new command
            # hlps = ['?pplns', '?register', '?RTFN', '?rtfn', '?help', '?bench', '?list'] # Update if new helper
            cmds = ['/list', '/test', '/scroll', '/goblin', '/mizzery', '/burger', '/motto', '/fuckduck', '/bentley',
                    '/nismo', '/fee', '/feefunction', '/help']
            hlps = ['?test', '?list', '?vega', '?daily', '?statsdiffer', '?mining', '?config', '?help', '?m5m400']
            hshs = ['#limerick', '#limerick2']
            searchObj = re.findall(r'(\/\w+)(\.\d+)?(\.\d+)?|(\?\w+)|(\#\w+)(\.\w+)?', message.body, re.I)
            searchObjCmd = []
            searchObjArg = []
            searchObjHlp = []
            searchObjHsh = []
            for i in range(len(searchObj)):
                for j in range(len(cmds)):
                    if searchObj[i][0] == cmds[j]:
                        searchObjCmd.append(searchObj[i][0])
                        searchObjArg.append(searchObj[i][1] + searchObj[i][2])
                        searchObjArg.append(searchObj[i][2])
                if searchObj[i][3]:
                    searchObjHlp.append(searchObj[i][3])
                for k in range(len(hshs)):
                    if searchObj[i][4] == hshs[k]:
                        searchObjHsh.append(searchObj[i][4])
                        searchObjArg.append(searchObj[i][5])
            command = searchObjCmd
            argument = searchObjArg
            helper = searchObjHlp
            hash = searchObjHsh
        except:
            room.message("I'm sorry @{}, I might have misunderstood what you wrote... Could you repeat please?".format(
                user.name))

        for i in range(len(helper)):
            hlp = helper[i]
            if hlp in hlps:
                hlp = hlp[1:]

                if hlp.lower() == "test":
                    room.message("Custom bot/slave. Thanks! https://github.com/miziel/poolbot")

                if hlp.lower() == "help":
                    room.message("try it with list")

                if hlp.lower() == "list":
                    room.message(
                        "Available commands (use: ?command): trite, list, vega, statsdiffer, daily, statsdiffer, mining, config, m5m400")  # Update if new helper

                if hlp.lower() == "daily":
                    room.message("https://goo.gl/c1TQgc")

                if hlp.lower() == "statsdiffer":
                    room.message(
                        "Your computer does the following while mining:\n\nThe pool gives you a search-job, then your miner starts calculating hashes until it finds one that matches the requirements (difficulty). The miner sends the pool the result if it exceeds the difficulty.\n\nThe pool does not see how often you perform the hash calculations. It only knows when your miner submits a hash that exceeds the difficulty.\n\nThe pool then uses the law of probability to estimate the number of hashes it took to make the share result you found. This is ONLY AN ESTIMATE. That is why you see the fluctuating numbers.\n\nYou do not get paid based on your hashrate, but by a combination of the difficulty of AND the number of shares submitted to the pool.\n\nIn very basic terms:Shares*Difficulty=MuhMoneez\n\n(credits to TheJerichoJones)")

                if hlp.lower() == "vega":
                    room.message("http://vega.miningguides.com/?m=0")
					
                if hlp.lower() == "mining":
                    room.message("mining is like throwing dice actually. Every hash is a throw. Only... if the network diff is 50 billion, the dice have about 50 billion sides. And only an ace is good. So statistically, with all the network hashing power, someone should throw an ace every two minutes. If it happens faster, diff goes up. If it slows down, diff goes down. Like with normal dice, statistically you throw an ace 1 out of six throws. But sometimes it takes longer. If it is nine throws, the effort would be 9/6 = 150%.")

                if hlp.lower() == "config":
                    room.message("https://supportxmr.com/#/help/config_generator")

                if hlp.lower() == "m5m400":
                    room.message("You can mail me at support@supportxmr.com. I'll answer when I'm not trying to sell my Clio, polishing my new m135i, changing my nick to M55, opening my envelope wallet to buy a lambo, counting my savings for my Bentley, talking to my gf or sleeping at work.")

        for i in range(len(hash)):
            hsh = hash[i]
            arg = argument[i]
            hsh = hsh[1:]
            arg = arg[1:]
            try:

                if hsh.lower() == "limerick":
                    if arg.lower() == "":
                        justsain = (
                                "'Polish' them vegas, make 'm shiny as hell\n\nA Pole would use wodka, and worship the smell.\n\nBut not for mizzy,\n\nHe starts to feel dizzy\n\nAnd thinks 'if I use plum wine, would that work as well? '\n\n.\n\nby BenVerXmr",
                                "There once sailed a pirate far from Carribean\n\nHis looks and manners quite simple, plebeian.\n\nAnd it was not the character\n\nNor the hook to atract her...\n\nAll about his hard wood she would sing her sweat peaen.\n\n.\n\nby Miziel0",
                                "There once was a young guy in Vienna\n\nwho had a huge wi-fi antenna\n\nGirls loved it so big\n\nbut there was a trick:\n\nTo get it up was two hours gehenna.\n\n.\n\nby Miziel0",
                                "Once a guy went on vacations to Crete\n\nwith a girl, oh, so perfect and sweet.\n\nHe bluntly avowed\n\nto make her come loud\n\nbut her moan 'err, oh!' stayed very discrete.\n\n.\n\nby Miziel0",
                                "He's into Vegas, this bass playing miner,\n\nHe's staff, a wine maker and rhymer\n\nOur Goblin thought he's\n\nJust a kid on his knees\n\nBut he's the damn pool ui front designer..\n\n.\n\nby BenVerXmr",
                                "Upon problems they used to call Houston,\n\nThe city were solutions got produced in,\n\nOne guy wrote them all,\n\nNow in Vegas he stands tall\n\nAnd that is why our pool is so boostin’ !\n\n.\n\nby BenVerXmr",
                                "There lived handsome guy somewhere in Warsaw\n\nWho had a huge nose and the other thing also\n\nAnd when he snorted coke\n\nGirls would sigh to this bloke:\n\nNice pole for a Pole! Show your torso!\n\n.\n\nby Miziel0",
                                "There was young, hasty boy in Belfast\n\nWho wanted his blocks found real fast\n\nBe patient, young lad\n\nUsed to calm him his dad:\n\nIn long term we'll all turn to dust\n\n.\n\nby Miziel0",
                                "There once lived a goddes of a name Tyche\n\nShe drunk lots of wine, had moods and been spikey\n\nWe think she is so cool\n\nWhen she visits our pool...\n\nBut we curse her when her head is achy...\n\n.\n\nby Miziel0",
                                "There once was a guy on the planet of Endor\n\nWho wanted to be a big Monero vendor\n\nHe mined like a crazy\n\nBut the future was hazy -\n\nWould he fail or get glory and splendor?\n\n.\n\nby Miziel0",
                                "Although women come so far from Venus\n\nI satisfy all of them - after Guinnes.\n\nWhen we go down to sub,\n\nI have my gear all up.\n\nThey come like a train - every two minutes.\n\n.\n\nby Miziel0",
								"A pool-owner who was Viennese,\n\nwas having coffee and a sandwich with cheese\n\nHe saw the panic that hyped\n\namongst the anons, and typed:\n\n'Scroll up a few lines, will ya, Djeez' !\n\n.\n\nby BenVerXmr",
                                "little luck did we get\n\nwhich made the anons upset\n\nthey nagged all day\n\nand we could only say\n\nany other pool is no safer bet\n\n.\n\nby SolderGirl",
                                "there once was a block\n\nwe all watched in shock\n\nbecause the effort we spent\n\nwas over a thousand percent\n\nthat day, it felt like chewing on rock\n\n.\n\nby SolderGirl"
                            )

                        room.message(random.choice(justsain))

                    if arg.lower() == "m5m400":
                        justsain = (
                           "There once was a young guy in Vienna\n\nwho had a huge wi-fi antenna\n\nGirls loved it so big\n\nbut there was a trick:\n\nTo get it up was two hours gehenna.\n\n.\n\nby Miziel0",
						   "A pool-owner who was Viennese,\n\nwas having coffee and a sandwich with cheese\n\nHe saw the panic that hyped\n\namongst the anons, and typed:\n\n'Scroll up a few lines, will ya, Djeez' !\n\n.\n\nby BenVerXmr"

                        )
                        room.message(random.choice(justsain))

                    if arg.lower() == "soldergirl":
                        justsain = (
                           "little luck did we get\n\nwhich made the anons upset\n\nthey nagged all day\n\nand we could only say\n\nany other pool is no safer bet\n\n.\n\nby SolderGirl",
                           "there once was a block\n\nwe all watched in shock\n\nbecause the effort we spent\n\nwas over a thousand percent\n\nthat day, it felt like chewing on rock\n\n.\n\nby SolderGirl"

                        )
                        room.message(random.choice(justsain))

                    if arg.lower() == "endor":
                        justsain = (
                    "There once was a guy on the planet of Endor\n\nWho wanted to be a big Monero vendor\n\nHe mined like a crazy\n\nBut the future was hazy -\n\nWould he fail or get glory and splendor?\n\n.\n\nby Miziel0",
                        )
                        room.message(random.choice(justsain))

                    if arg.lower() == "snipa22":
                        justsain = (
                            "Upon problems they used to call Houston,\n\nThe city were solutions got produced in,\n\nOne guy wrote them all,\n\nNow in Vegas he stands tall\n\nAnd that is why our pool is so boostin’ !\n\n.\n\nby BenVerXmr",

                        )
                        room.message(random.choice(justsain))
                    if arg.lower() == "miziel0":
                        justsain = (
                            "'Polish' them vegas, make 'm shiny as hell\n\nA Pole would use wodka, and worship the smell.\n\nBut not for mizzy,\n\nHe starts to feel dizzy\n\nAnd thinks 'if I use plum wine, would that work as well? '\n\n.\n\nby BenVerXmr",


                        )
                        room.message(random.choice(justsain))

            except json.decoder.JSONDecodeError:
                print("There was a json.decoder.JSONDecodeError while attempting /" + str(
                    hsh.lower()) + " (probably due to /pool/stats/)")
                room.message("JSON Bourne is trying to kill me!")
            except:
                print("Error while attempting /" + str(hsh.lower()))
                room.message("Now I asked the API a polite question regarding your command, @" + user.name + ", but I'm afraid the API was awfully rude to me. Even when saying I won't repeat what it told me, my Bot cheeks are blushing... Can't help you right now.")

        for i in range(len(command)):
            cmd = command[i]
            arg = argument[i]
            cmd = cmd[1:]
            arg = arg[1:]

            try:

                if cmd.lower() == "list":
                    room.message(
                        "Available commands (use: /command): test, list, scroll, goblin, burger, mizzery, motto, fuckduck, bentley, nismo, fee, feefunction. \n\nYou can add the number of hours to check burgers by typing burger.x where x is the number of hours. \n\nIf you want to know how much xmr will be deducted from your payment for an amount of XMR use the command fee with the amount of XMR behind it, like \n\nfee.0.3\n\nInformational help is in helpcommands, try ? list")  # Update if new command

                if cmd.lower() == "help":
                    room.message("try list")

                if cmd.lower() == "burger":
                    if not arg.isdigit():
                        hournum = 24
                    if arg.isdigit():
                        hournum = int(arg)
                    timetocheck = 3600 * hournum
                    blockstocheck = int(round(timetocheck / 3600 / 24 * 150))
                    endblocksloop = blockstocheck - 1
                    if hournum == 0:
                        room.message(
                            "How many burgers do you think we found in _zero_hours ? Your fine for testing my whit is... 0.3 XMR to be deducted from your total due within 0 hrs...")
                    if hournum > 0:
                        (blockCounter, timeDifferenceArrayResult, nextBlock, messageEst, messageEstSmiley, effort24Val,
                         poolStatsAvgHashRate) = bot.burger(hournum, timetocheck, blockstocheck, endblocksloop)
                        print("blockcount is : " + str(blockCounter) + " for " + str(hournum) + " hours.")
                        room.message("\n\n\n*burger*" + " Total within " + str(hournum) + " hours: " + str(
                            blockCounter) + "\nAverage effort: " + str(
                            effort24Val) + "%" + ". \nAverage time between: " + str(
                            prettyTimeDelta(timeDifferenceArrayResult)) + "\n" + messageEst + str(
                            prettyTimeDelta(nextBlock)) + messageEstSmiley + " \nWith average pool hashrate: " + str(
                            poolStatsAvgHashRate) + " MH/s")

                if cmd.lower() == "scroll":
                    room.message("Scroll up a few lines will ya, Djeez")

                if cmd.lower() == "goblin":
                    room.message("please stop writing faster than people can read. \nHave a bowl.")

                if cmd.lower() == "motto":
                    room.message("\nI used to be processing drugs. \nNow I'm drugging processors.")

                if cmd.lower() == "fuckduck":
                    room.message("\nI'm afraid @" + user.name + " wants you to go fuck a duck...")


                if cmd.lower() == "feefunction":
                    room.message(
                        "\nThere is zero Transaction fee for withdraw of 4 XMR or more, there is a max .005 XMR transaction cost when the minimum .1 XMR setting is used. \n\nThe transaction fee is linear in between. \n\nYou can calculate the exact fee yourself: \n\nfee = (-0.005*payout/3.9)+(0.005*4/3.9)")

                if cmd.lower() == "mizzery":
                    room.message("that puzzles me")
                    time.sleep(6)


                if cmd.lower() == "fee":
                    try:
                        float(arg)
                    except ValueError:
                        if arg == "":
                            room.message("Pleas add an amount of xmr like fee.0.9 behind the slash.")
                            break
                        room.message("Comedians are funny. You are not.")
                        break
                    amount = float(arg)
                    transfercosts = 0
                    if amount < 0.1:
                        room.message("The amount you want transferred from supportXMR to your wallet is: " + str(
                            amount) + " XMR. \n\nThat will never happen as the minimum payout threshold is 0.1 XMR.")
                    if amount >= 4:
                        room.message("The amount you want transferred from supportXMR to your wallet is: " + str(
                            amount) + " XMR. \n\nFor amounts above 4 XMR the pool waives the fee. The full amount of " + str(
                            amount) + " XMR will arrive in your wallet.")
                    if (amount < 4 and amount >= 0.1):
                        costs = (-0.005 * amount / 3.9) + (0.005 * 4 / 3.9)
                        costsf = format(costs, ',.4f')
                        remainder = amount - costs
                        remainderf = format(remainder, ',.4f')
                        room.message("The amount you want transferred from supportXMR to your wallet is: " + str(
                            amount) + " XMR. \n\nThe transaction costs for that amount would be " + str(
                            costsf) + " XMR. The amount of " + str(remainderf) + " XMR will arrive in your wallet.")

                if cmd.lower() == "bentley":
                    kraken = requests.get("https://api.kraken.com/0/public/Ticker?pair=XMREUR").json()
                    EUR_XMR_krak = kraken['result']['XXMRZEUR']['c'][0]
                    poolstatss = requests.get(apiUrl + "pool/stats/").json()
                    totalblockss = poolstatss['pool_statistics']['totalBlocksFound']
                    # savings = (6/10*int(totalblocks)*int(EUR_XMR_krak))
                    savings = int(totalblockss)
                    blocknum = str(savings)
                    monerorate = str(EUR_XMR_krak)
                    saveuro = float(EUR_XMR_krak)
                    savings = savings * saveuro * 6 / 10 / 100 * 5
                    blades = 84 * saveuro
                    bladesformat = format(blades, ',.2f')
                    savingsafterblades = savings - blades
                    # krak = ast.literal_eval(EUR_XMR_krak)
                    savv = format(savings, ',.2f')
                    savvafter = format(savingsafterblades, ',.2f')
                    # savv = str(savings)
                    moretosave = 200000 - savings
                    moretosaveafterblades = 200000 - savingsafterblades
                    more = format(moretosave, ',.2f')
                    moreafterblades = format(moretosaveafterblades, ',.2f')
                    room.message(
                        "A Bentley with some options easily costs about 200.000 euro.\n Our pool found " + blocknum + " blocks since its conception. \nCurrent reward is slightly above 5 XMR, \ncurrent value of XMR on Kraken is " + monerorate + " euro. \nAt 0.6 % pool fee, total income of M5M400 would be (slightly, depending on past rewards) more than " + savv + " euro.\nThat means he still had to save " + more + " euro. \n\n He bought some blade servers though, so he's down 84 XMR again, or " + bladesformat + "euro. \n\nThat leaves him with " + savvafter + "euro or now he has to save " + moreafterblades + "euro again.")

                if cmd.lower() == "nismo":
                    kraken = requests.get("https://api.kraken.com/0/public/Ticker?pair=XMRUSD").json()
                    EUR_XMR_krak = kraken['result']['XXMRZUSD']['c'][0]
                    poolstatss = requests.get(apiUrl + "pool/stats/").json()
                    totalblockss = poolstatss['pool_statistics']['totalBlocksFound']
                    # savings = (6/10*int(totalblocks)*int(EUR_XMR_krak))
                    savings = int(totalblockss)
                    blocknum = str(savings)
                    monerorate = str(EUR_XMR_krak)
                    saveuro = float(EUR_XMR_krak)
                    savings = savings * saveuro * 6 / 10 / 100 * 5
                    # krak = ast.literal_eval(EUR_XMR_krak)
                    savv = format(savings, ',.2f')
                    # savv = str(savings)
                    moretosave = 176585 - savings
                    more = format(moretosave, ',.2f')
                    room.message(
                        "A Nismo starts From 176,585.00 usd.\n Our pool found " + blocknum + " blocks since its conception. \nCurrent reward is slightly above 5 XMR, \ncurrent value of XMR on Kraken is " + monerorate + " usd. \nAt 0.6 % pool fee, total pool income would be (slightly, depending on past rewards) more than " + savv + " usd.\n If M5M400 paid Snipa22 what he would like to get paid, Snipa still had to save " + more + " usd. \n\n As we know nothing about the income flows from M5M400 to Snipa, \n\n(and M5M400 states the same thing)... \n\n We're afraid Snipa will have to come up with 176,585.00 usd to get his car...")

                if cmd.lower() == "test":
                    justsain = (
                    "Attention. Emergency. All personnel must evacuate immediately. \nYou now have 15 minutes to reach minimum safe distance.",
                    "I'm sorry @" + user.name + ", I'm afraid I can't do that.",
                    "@" + user.name + ", you are fined one credit for violation of the verbal morality statute.",
                    "42", "My logic is undeniable.", "Danger, @" + user.name + ", danger!",
                    "Apologies, @" + user.name + ". I seem to have reached an odd functional impasse. I am, uh ... stuck.",
                    "Don't test. Ask. Or ask not.", "This is my pool. There are many like it, but this one is mine!",
                    "I used to be a miner like you, but then I took an ASIC to the knee",
                    "M5M400 misses Goblin...")
                    room.message(random.choice(justsain))

            except json.decoder.JSONDecodeError:
                print("There was a json.decoder.JSONDecodeError while attempting /" + str(
                    cmd.lower()) + " (probably due to /pool/stats/)")
                room.message("JSON Bourne is trying to kill me!")
            except:
                print("Error while attempting /" + str(cmd.lower()))
                room.message("Now I asked the API a polite question regarding your command, @" + user.name + ", but I'm afraid the API was awfully rude to me. Even when saying I won't repeat what it told me, my Bot cheeks are blushing... Can't help you right now.")


rooms = [""]  # List of rooms you want the bot to connect to
username = ""  # For tests you can use your own - trigger bot as anon
password = ""
checkForNewBlockInterval = 10  # How often to check for new block, in seconds. If not set, default value of 20 will be used

try:
    bot.easy_start(rooms, username, password, checkForNewBlockInterval)
except KeyboardInterrupt:
    print("\nStopped")
