import datetime
import json

import requests
import pathlib
import os
import configparser


def pluginMain(parametersString : str, longReturnMessage : bool, lastRuntime : datetime.datetime):
    returnMsg = []

    # Converts last runtime and current time to check only new manga.
    lastRuntimeLinux = lastRuntime.timestamp()
    nowTime = datetime.datetime.now().timestamp()
    myPath = pathlib.Path(__file__).parent
    mangadexConfigPath = os.path.join(myPath, 'mangadexConfig.ini')
    base_url = 'https://api.mangadex.org'
    auth_url = 'https://auth.mangadex.org'

    if os.path.isfile(mangadexConfigPath):
        try:
            # TODO: if username | Password is empty
            #       Prova a leggere gli update della lista
            #       Se da errore di auth, tira un errore all'utente (graceful)
            #       se son compialti, invecce, vedi qua stotto...
            #       Mantieni possibilità di controllare lista if lista privata!!

            accessToken = ''
            config = configparser.ConfigParser(interpolation=None)
            config.read(mangadexConfigPath)
            mangadexConfig = config['Mangadex']
            mdList = mangadexConfig.get('MDLIST', None)
            refreshToken = mangadexConfig.get('REFRESH', None)


            # If more than 29 days or the refresh token value is empty, do a new login using username / psw and then
            # saves the refresh token to the config file to avoid new logins. The access token will be used only for
            # the current loop.

            if nowTime - lastRuntimeLinux > 2505600 or refreshToken is None or refreshToken == "":
                MANGADEX_USERNAME = mangadexConfig['USERNAME']
                MANGADEX_PASSWORD = mangadexConfig['PASSWORD']
                MANGADEX_CLIENT_ID = mangadexConfig['client_id']
                MANGADEX_CLIENT_SECRET = mangadexConfig['client_secret']
                if MANGADEX_CLIENT_SECRET is None or MANGADEX_PASSWORD is None or MANGADEX_CLIENT_ID is None or MANGADEX_CLIENT_SECRET is None:
                    returnMsg.append("Error while authenticating: one or more login tokens are missing.")
                    return returnMsg
                requestData = {"grant_type": "password", "username": MANGADEX_USERNAME, "password": MANGADEX_PASSWORD, "client_id": MANGADEX_CLIENT_ID, "client_secret": MANGADEX_CLIENT_SECRET}
                loginReq = requests.post(f'{auth_url}/realms/mangadex/protocol/openid-connect/token', data=requestData)
                try:
                    loginJson = loginReq.json()
                    accessToken = loginJson["access_token"]
                    refreshToken = loginJson["refresh_token"]
                    config['Mangadex']['REFRESH'] = refreshToken
                except json.decoder.JSONDecodeError:
                    returnMsg.append("Error while refreshing the token. Maybe mangadex is offline?")
                    return returnMsg
            else:
                MANGADEX_CLIENT_ID = mangadexConfig['client_id']
                MANGADEX_CLIENT_SECRET = mangadexConfig['client_secret']
                refreshData = {"grant_type": "refresh_token","refresh_token": refreshToken, "client_id": MANGADEX_CLIENT_ID, "client_secret": MANGADEX_CLIENT_SECRET}
                refreshReq = requests.post(f'{auth_url}/realms/mangadex/protocol/openid-connect/token', data=refreshData)
                try:
                    loginJson = refreshReq.json()
                    if refreshReq.status_code == 200:
                        accessToken = loginJson["access_token"]
                        refreshToken = loginJson["refresh_token"]
                        config['Mangadex']['REFRESH'] = refreshToken
                    elif refreshReq.status_code == 400:
                        MANGADEX_USERNAME = mangadexConfig['USERNAME']
                        MANGADEX_PASSWORD = mangadexConfig['PASSWORD']
                        MANGADEX_CLIENT_ID = mangadexConfig['client_id']
                        MANGADEX_CLIENT_SECRET = mangadexConfig['client_secret']
                        requestData = {"grant_type": "password", "username": MANGADEX_USERNAME, "password": MANGADEX_PASSWORD, "client_id": MANGADEX_CLIENT_ID, "client_secret": MANGADEX_CLIENT_SECRET}
                        loginReq = requests.post(f'{auth_url}/realms/mangadex/protocol/openid-connect/token', data=requestData)
                        loginJson = loginReq.json()
                        accessToken = loginJson["access_token"]
                        refreshToken = loginJson["refresh_token"]
                        config['Mangadex']['REFRESH'] = refreshToken
                    else:
                        returnMsg.append("Error while refreshing the token. Maybe mangadex is offline?")
                        return returnMsg
                except json.decoder.JSONDecodeError:
                    returnMsg.append("Error while refreshing the token. Maybe mangadex is offline?")
                    return returnMsg

            with open(mangadexConfigPath, 'w') as cfgWriter:
                config.write(cfgWriter)

            followedUrl = ''
            # Prepares the parameters for the Mangadex updates list request.
            lastRuntimeString = lastRuntime.strftime("%Y-%m-%dT%H:%M:%S")
            parametersList = { 'translatedLanguage[]': 'en', 'contentRating[]': ['safe', 'suggestive', 'erotica'], 'createdAtSince': lastRuntimeString,
                               'order[createdAt]': 'asc', 'order[updatedAt]': 'asc', 'order[publishAt]': 'asc', 'order[readableAt]': 'asc', 'order[volume]': 'asc', 'order[chapter]': 'asc', 'includes[]': 'manga' }
            if mdList is not None:
                followedUrl = base_url + f'/list/{mdList}/feed'
            else:
                followedUrl = base_url + '/user/follows/manga/feed'
            # Get updates list
            updateRequest = requests.get(followedUrl, headers={"Authorization": f"Bearer {accessToken}"}, params=parametersList)
            updatedMangaJson = updateRequest.json()
            if updatedMangaJson['result'] == 'ok':
                for chapter in updatedMangaJson['data']:
                    mangaTitle = ''
                    readUrl = f'https://mangadex.org/chapter/{chapter["id"]}'
                    if chapter['attributes']['externalUrl'] is not None:
                        readUrl = chapter['attributes']['externalUrl']

                    # I get the manga title
                    for relation in chapter['relationships']:
                        if relation['type'] == 'manga':
                            mangaID = relation['id']
                            mangaInfoRequest = requests.get(f'{base_url}/manga/{mangaID}')
                            mangaInfoJson = mangaInfoRequest.json()
                            if mangaInfoJson['result'] == 'ok':
                                # Checks the main title for en title and if not found checks the alt titles
                                if mangaInfoJson['data']['attributes']['title'].get('en') is not None:
                                    mangaTitle = relation['attributes']['title']['en']
                                elif mangaInfoJson['data']['attributes'].get('altTitles') is not None:
                                    altTitles = mangaInfoJson['data']['attributes']['altTitles']
                                    for altTitle in altTitles:
                                        if altTitle.get('en') is not None:
                                            mangaTitle = altTitle['en']
                                            break
                                        elif altTitle.get('ja') is not None:
                                            mangaTitle = altTitle['ja']
                                            break
                                        else:
                                            mangaTitle = 'No title found'
                                else:
                                    mangaTitle = 'No title found'
                    # With the hard earned info I prepare the message.
                    preparedString = f'New chapter for manga {mangaTitle}: {readUrl}'
                    returnMsg.append(preparedString)


        except requests.exceptions.RequestException as e:
            returnMsg.append(f"There was a connection error, retrying on the next loop")
            returnMsg.append(f"The exception was: {e}")
    else:
        returnMsg.append('Manga list not found! Did you delete the "mangalist.txt" file?')
    return returnMsg


# Stuff to display if directly run. The initial \033[93m and the final \033[0m are for coloring the string.
if __name__ == "__main__":
    print(f"\033[93mThis is a personalAlerter plugin! Please do not run it directly but import it in personalAlerter.\033[0m")
