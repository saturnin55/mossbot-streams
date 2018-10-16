import discord
import asyncio
import json
import urllib3

def write_config(file):
   outfile = open(config_file, "w")
   outfile.write(json.dumps(config, indent=4, sort_keys=True))
   outfile.close()

def read_config(file):
   with open(file) as infile:
      config = json.load(infile)

   return(config)

urllib3.disable_warnings()

config_file = "config.json"

config = read_config(config_file)

KEY = config["mrkey"]

client = discord.Client();

@client.event
async def on_ready():
    print("Logged in as {0} ({1})".format(client.user.name, client.user.id))
    print('------')

async def background_task():
   await client.wait_until_ready()

   http = urllib3.PoolManager()

   url = "https://mossranking.com/api/gettwitchstreamers.php?key={0}".format(KEY)
   while not client.is_closed:

      r = http.request("GET", url)
      data = json.loads(r.data.decode('utf-8'))

      twitch = []
      for item in data:
          twitch.append(item["twitch"])

client = discord.Client();

@client.event
async def on_ready():
    print("Logged in as {0} ({1})".format(client.user.name, client.user.id))
    print('------')

async def background_task():
   await client.wait_until_ready()

   http = urllib3.PoolManager()

   url = "https://mossranking.com/api/gettwitchstreamers.php?key={0}".format(KEY)
   while not client.is_closed:

      r = http.request("GET", url)
      data = json.loads(r.data.decode('utf-8'))

      twitch = []
      for item in data:
          twitch.append(item["twitch"])

          if item["twitch"] not in config["streamers"]:
             config["streamers"][item["twitch"]] = item

             msg_title = "{0} is now streaming!".format(item["twitch"])

             embed=discord.Embed(title=item["url"], url=item["url"], color=0x6441a5)
             embed.set_author(name="{0} is spelunking!".format(item["twitch"]), url=item["url"])
             embed.set_thumbnail(url="{0}".format(item["logo"]))
             embed.add_field(name="Stream Title", value=item["status"], inline=False)
             embed.set_footer(text="@mossranking", icon_url="https://i.imgur.com/2ZpHHKm.png")
             msg = await client.send_message(discord.Object(id=config["channel"]), embed=embed)

             config["streamers"][item["twitch"]]["msgid"] = msg.id
             write_config(config)

             if config["debug"] == 1:
                await client.send_message(discord.Object(id=config["channel"]), "DEBUG: {0} started streaming".format(item["twitch"]))

      for item in list(config["streamers"]):
         if item not in twitch:
            msgid = config["streamers"][item]["msgid"]

            if config["debug"] == 1:
               print("Remove : {0}\n".format(item))
               print("msgid : {0}\n".format(msgid))

            msg = await client.get_message(discord.Object(id=config["channel"]), msgid)
            await client.delete_message(msg)

            if config["debug"] == 1:
               await client.send_message(discord.Object(id=config["channel"]), "DEBUG: {0} stopped streaming".format(item))
               
            config["streamers"].pop(item, None)
            write_config(config)

      await asyncio.sleep(config["delay"])

client.loop.create_task(background_task())
client.run(config["login_token"])
