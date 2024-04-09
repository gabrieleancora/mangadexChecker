import datetime
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

    if os.path.isfile(mangadexConfigPath):
        try:
            sessionToken = ''
            config = configparser.ConfigParser(interpolation=None)
            config.read(mangadexConfigPath)
            mangadexConfig = config['Mangadex']
            refreshToken = mangadexConfig.get('REFRESH', None)
            mdList = mangadexConfig.get('MDLIST', None)

            # If more than 29 days or the refresh token value is empty, do a new login using username / psw and then
            # saves the refresh token to the config file to avoid new logins. The session token will be used only for
            # the current loop.

            if nowTime - lastRuntimeLinux > 2505600 or refreshToken is None or refreshToken == "":
                MANGADEX_USERNAME = mangadexConfig['USERNAME']
                MANGADEX_PASSWORD = mangadexConfig['PASSWORD']
                loginReq = requests.post(f'{base_url}/auth/login', json={"username": MANGADEX_USERNAME, "password": MANGADEX_PASSWORD})
                loginJson = loginReq.json()
                sessionToken = loginJson["token"]["session"]
                refreshToken = loginJson["token"]["refresh"]
                config['Mangadex']['REFRESH'] = refreshToken
            else:
                refreshReq = requests.post(f'{base_url}/auth/refresh', json={"token": refreshToken})
                loginJson = refreshReq.json()
                if loginJson["result"] == "ok":
                    sessionToken = loginJson["token"]["session"]
                    refreshToken = loginJson["token"]["refresh"]
                    config['Mangadex']['REFRESH'] = refreshToken
                # If I get error 401 I can refresh the token from scratch and it should work.
                elif loginJson["result"] == "error" and loginJson["errors"][0]["status"] == 401:
                    MANGADEX_USERNAME = mangadexConfig['USERNAME']
                    MANGADEX_PASSWORD = mangadexConfig['PASSWORD']
                    loginReqNew = requests.post(f'{base_url}/auth/login', json={"username": MANGADEX_USERNAME, "password": MANGADEX_PASSWORD})
                    loginJsonNew = loginReqNew.json()
                    sessionToken = loginJsonNew["token"]["session"]
                    refreshToken = loginJsonNew["token"]["refresh"]
                    config['Mangadex']['REFRESH'] = refreshToken
                else:
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
            updateRequest = requests.get(followedUrl, headers={"Authorization": f"Bearer {sessionToken}"}, params=parametersList)
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
