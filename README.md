# mossbot-streams
Bot that announces a subset of streamers of a specific game into a discord channel



documentation :

- https://cog-creators.github.io/discord-embed-sandbox/
- https://discordpy.readthedocs.io/en/latest/api.html#embed
- https://anidiots.guide/first-bot/using-embeds-in-messages

The url that is called returns a json array of the current streamers. streamers has the field "username", "twitch" (channel), "twitchid", "twitch_logo", "twitch_url" and "twitch_status" (stream title) defined.

I have another program running at an interval that poll the twitch api for active Spelunky streamers that met specific criterias (must be members of the mossranking.com website) and write that info to a database. the url called check the database for that info.
