#!/usr/bin/python3.6
from pprint import pprint
import discord
import asyncio
import json
import urllib3
import datetime

def write_config(file, data):
   try:
      outfile = open(file, "w")
      outfile.write(json.dumps(data, indent=4, sort_keys=True))
      outfile.close()
   except Exception as e:
      mylog("ERR(write_config): {0}".format(e))


def read_config(file):
   try:
      with open(file) as infile:
         data = json.load(infile)
   except Exception as e:
      mylog("ERR(read_config): {0}".format(e))

   return(data)

def mylog(s):
   try:
      now = datetime.datetime.now()
      dt = '{0}'.format(now.strftime("%Y-%m-%d %H:%M:%S"))
      f = open("mossbot.log","a+")
      f.write("{0} {1}\n".format(dt, s))
      f.close()
   except Exception as e:
      print("ERR(read_config): {0}".format(e))

urllib3.disable_warnings()

config_file = "config.json"
streamers_file = "streamers.json"

config = read_config(config_file)
streamers_config = read_config(streamers_file)

KEY = config["mrkey"]

client = discord.Client();

@client.event
async def on_ready():
    mylog("Logged in as {0} ({1})".format(client.user.name, client.user.id))
    mylog('------')

async def background_task():

   await client.wait_until_ready()
   http = urllib3.PoolManager()

   url = "https://mossranking.com/api/gettwitchstreamers.php?key={0}".format(KEY)
   
   while not client.is_closed():
      try:
         if config["debug"] > 0:
            mylog("Fetching {0}".format(url))

         r = http.request("GET", url)
         data = json.loads(r.data.decode('utf-8'))
      except http.exceptions.RequestException as e:
         mylog("ERR: can't fetch {0} : {1}".format(url, e))
         await asyncio.sleep(config["delay"])
         continue;

      channel = client.get_channel(int(config["channel"]));
      twitch = []
      for item in data:
         if config["debug"] > 0:
            mylog("Processing {0}".format(item["twitch"]))

         twitch.append(item["twitch"])

         if item["twitch"] not in streamers_config["streamers"]:
            if config["debug"] > 0:
               mylog("==> {0} not in streamers.json".format(item["twitch"]))

            msg_title = "{0} is now streaming!".format(item["twitch"])

            embed=discord.Embed(title=item["url"], url=item["url"], color=0x6441a5)
            embed.set_author(name="{0} is spelunking!".format(item["username"]), url=item["url"])
            embed.set_thumbnail(url="{0}".format(item["logo"]))
            embed.add_field(name="Stream Title", value=item["status"], inline=False)
            embed.set_footer(text="@mossranking | https://mossranking.com", icon_url="https://i.imgur.com/2ZpHHKm.png")

            try:
               mylog("{0} started streaming\n".format(item["twitch"]))
               msg = await channel.send(embed=embed)
            except Exception as e:
               mylog("ERR: cant send start of stream discord msg : {0}".format(e))
               continue

            streamers_config["streamers"][item["twitch"]] = item
            streamers_config["streamers"][item["twitch"]]["msgid"] = msg.id
            streamers_config["streamers"][item["twitch"]]["delerr"] = 0

            write_config(streamers_file, streamers_config)

            if config["debug"] == 2:
               try:
                  await channel.send("DEBUG: {0} started streaming".format(item["twitch"]))
               except Exception as e:
                  mylog("ERR: can't send start of stream discord debug message: {0}".format(e))
                  continue

         elif item["twitch"] in streamers_config["streamers"] and item["status"] != streamers_config["streamers"][item["twitch"]]["status"]:
            # stream status changed

            if "msgid" in streamers_config["streamers"][item["twitch"]]:
               msgid = streamers_config["streamers"][item["twitch"]]["msgid"]

               streamers_config["streamers"][item["twitch"]] = item

               msg_title = "{0} is now streaming!".format(item["twitch"])

               embed=discord.Embed(title=item["url"], url=item["url"], color=0x6441a5)
               embed.set_author(name="{0} is spelunking!".format(item["username"]), url=item["url"])
               embed.set_thumbnail(url="{0}".format(item["logo"]))
               embed.add_field(name="Stream Title", value=item["status"], inline=False)
               embed.set_footer(text="@mossranking | https://mossranking.com", icon_url="https://i.imgur.com/2ZpHHKm.png")

               try:
                  msg = await channel.fetch_message(int(msgid))
                  msg.edit(embed=embed)
               except Exception as e:
                  mylog("ERR: can't retrieve or edit msgid {0} for {1}: {2}".format(msgid, item["twitch"], e))
                  continue

               mylog("==> {0} status changed : |{1}|".format(item["twitch"], item["status"]))

               streamers_config["streamers"][item["twitch"]]["msgid"] = msg.id
               streamers_config["streamers"][item["twitch"]]["delerr"] = 0
               write_config(streamers_file, streamers_config)

               if config["debug"] > 0:
                  mylog("Edited : {0} => {1}\n".format(item["twitch"], item["status"]))

               if config["debug"] == 2:
                  try:
                     await channel.send("DEBUG: edited {0}".format(item["twitch"]))
                  except Exception as e:
                     mylog("ERR: sending debug msg edited {0}".format(e))
                     continue
            else:
               #FIXME ?
               mylog("ERR: no msgid key for {0}: {1}".format(item["twitch"], e))
               continue

      mrstreamers = list(streamers_config["streamers"])

      for streamer in mrstreamers:
         if streamer not in twitch:
            if "msgid" in streamers_config["streamers"][streamer]:
               msgid = streamers_config["streamers"][streamer]["msgid"]

               if "delerr" not in streamers_config["streamers"][streamer]:
                  streamers_config["streamers"][streamer]["delerr"] = 0

               if config["debug"] > 0:
                  mylog("Remove : {0}, msgid {1}, delerr {2}".format(streamer, msgid, streamers_config["streamers"][streamer]["delerr"]))

               if streamers_config["streamers"][streamer]["delerr"] < 5:
                  try:
                     msg = await channel.fetch_message(int(msgid))
                     await msg.delete()
                  except Exception as e:
                        mylog("Cant retreive or delete message {0} for {1}: {2}".format(msgid, streamer, e))
                        streamers_config["streamers"][streamer]["delerr"] += 1
                        write_config(streamers_file, streamers_config)
                        continue

                  if config["debug"] == 2:
                     try:
                        await channel.send("DEBUG: {0} stopped streaming".format(streamer))
                     except Exception as e:
                        mylog("Can't send debug message to delete {0} {1}".format(streamer, e))
                        continue
               else:
                  mylog("Too many tries deleting msgid {0} for {1}".format(msgid, streamer))


            del streamers_config["streamers"][streamer]
            mylog("==> {0} stopped streaming|".format(item["twitch"]))

         write_config(streamers_file, streamers_config)


      await asyncio.sleep(config["delay"])

try:
   mylog("Starting background_task()")
   task = client.loop.create_task(background_task())
   client.run(config["login_token"])
except Exception as e:
   mylog("ERR8: {0}".format(e))
   client.loop.run_until_complete(client.close())
   client.loop.close()
