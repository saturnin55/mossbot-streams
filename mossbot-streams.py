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
   while not client.is_closed:

      try:
         r = http.request("GET", url)
         data = json.loads(r.data.decode('utf-8'))
      except http.exceptions.RequestException as e:
         mylog("ERR1: {0}".format(e))
         await asyncio.sleep(config["delay"])
         break;

      twitch = []
      for item in data:
         twitch.append(item["twitch"])

         if item["twitch"] not in streamers_config["streamers"]:
            streamers_config["streamers"][item["twitch"]] = item

            msg_title = "{0} is now streaming!".format(item["twitch"])

            embed=discord.Embed(title=item["url"], url=item["url"], color=0x6441a5)
            embed.set_author(name="{0} is spelunking!".format(item["username"]), url=item["url"])
            embed.set_thumbnail(url="{0}".format(item["logo"]))
            embed.add_field(name="Stream Title", value=item["status"], inline=False)
            embed.set_footer(text="@mossranking | https://mossranking.com", icon_url="https://i.imgur.com/2ZpHHKm.png")

            try:
               if config["debug"] > 0:
                  mylog("Add : {0}\n".format(item))
               msg = await client.send_message(discord.Object(id=config["channel"]), embed=embed)
            except Exception as e:
               mylog("ERR2: {0}".format(e))
               await asyncio.sleep(config["delay"])
               break;

            streamers_config["streamers"][item["twitch"]]["msgid"] = msg.id
            write_config(streamers_file, streamers_config)

            if config["debug"] == 2:
               try:
                  await client.send_message(discord.Object(id=config["channel"]), "DEBUG: {0} started streaming".format(item["twitch"]))
               except Exception as e:
                  mylog("ERR3: {0}".format(e))
                  await asyncio.sleep(config["delay"])
                  break;

         elif item["twitch"] in streamers_config["streamers"] and item["status"] != streamers_config["streamers"][item["twitch"]]["status"]:

            # stream status changed
            msgid = streamers_config["streamers"][item["twitch"]]["msgid"]

            streamers_config["streamers"][item["twitch"]] = item

            msg_title = "{0} is now streaming!".format(item["twitch"])

            embed=discord.Embed(title=item["url"], url=item["url"], color=0x6441a5)
            embed.set_author(name="{0} is spelunking!".format(item["username"]), url=item["url"])
            embed.set_thumbnail(url="{0}".format(item["logo"]))
            embed.add_field(name="Stream Title", value=item["status"], inline=False)
            embed.set_footer(text="@mossranking | https://mossranking.com", icon_url="https://i.imgur.com/2ZpHHKm.png")

            try:
               msg = await client.get_message(discord.Object(id=config["channel"]), msgid)
               msg = await client.edit_message(msg, embed=embed)
            except Exception as e:
               mylog("ERR4: {0}".format(e))
               await asyncio.sleep(config["delay"])
               break;

            streamers_config["streamers"][item["twitch"]]["msgid"] = msg.id
            write_config(streamers_file, streamers_config)

            if config["debug"] > 0:
               mylog("Edited : {0} => {1}\n".format(item["twitch"], item["status"]))

            if config["debug"] == 2:
               try:
                  await client.send_message(discord.Object(id=config["channel"]), "DEBUG: edited {0}".format(item["twitch"]))
               except Exception as e:
                  mylog("ERR5: {0}".format(e))
                  await asyncio.sleep(config["delay"])
                  break;

      for item in list(streamers_config["streamers"]):
         if item not in twitch:
            msgid = streamers_config["streamers"][item]["msgid"]

            if config["debug"] > 0:
               mylog("Remove : {0}\n".format(item))
               mylog("msgid : {0}\n".format(msgid))

            try:
               msg = await client.get_message(discord.Object(id=config["channel"]), msgid)
               await client.delete_message(msg)
            except Exception as e:
                  mylog("ERR6: {0}".format(e))
                  await asyncio.sleep(config["delay"])
                  break;

            if config["debug"] == 2:
               try:
                  await client.send_message(discord.Object(id=config["channel"]), "DEBUG: {0} stopped streaming".format(item))
               except Exception as e:
                  mylog("ERR7: {0}".format(e))
                  await asyncio.sleep(config["delay"])
                  break;

            streamers_config["streamers"].pop(item, None)
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
