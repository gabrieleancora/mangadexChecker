# MangadexChecker plugin for [personalAlerter](https://github.com/gabrieleancora/personalAlerter)  

This is the very plugin that pushed me to create personalAlert.  
It allows you to be notified using Telegram when a new chapter of your favourite manga is published.

Currently supports only english and excudes porn by default, I'll look into making the config file a bit more complex to also support them. Feel free to edit the lines containing the filters if you don't want to wait for an update (both parameters are on line 94!).

Also, for now you have to fill at least the username and the API token (you can obtain it here: https://mangadex.org/settings in the section "API Clients")  and the ID of a specific Mangadex List that you have access to, if you want to specify one, if you want to not be notified for each manga you follow.  
In the future I'll add a way to do anonymous queries usign a public list, so you won't have to insert the username and the login token, if you feel unsure.  

Obviously it works using the [official Mangadex APIs](https://api.mangadex.org/docs/). 
