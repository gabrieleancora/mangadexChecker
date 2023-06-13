# MangadexChecker plugin for [personalAlerter](https://github.com/gabrieleancora/personalAlerter)  

This is the very plugin that pushed me to create personalAlert.  
It allows you to be notified using Telegram when a new chapter of your favourite manga is published.

Currently supports only english and excudes porn by default, I'll look into making the config file a bit more complex 
to also support them. Feel free to edit the lines containing the filters if you don't want to wait for an update (both 
parameters are on [line 52!](https://github.com/gabrieleancora/mangadexChecker/blob/6a84b7e7ae21f2da03e99748b3c219309065f9a2/__init__.py#LL52C57-L52C57)).

Also, for now you have to fill at least the username and the password (and the ID of a specific Mangadex List) that you 
have access to, if you want to not be notified for each manga you follow.  
In the future I'll add a way to do anonymous queries usign a public list, so you won't have to insert the username and 
the password, if you feel unsure.  

Obviously it works using the [official Mangadex APIs](https://api.mangadex.org/docs/). 
