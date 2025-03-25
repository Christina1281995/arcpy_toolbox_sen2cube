import requests
import json

FACTBASE_URL = 'https://api.sen2cube.at/v1/factbase'
KNOWLEDGEBASE_URL = 'https://api.sen2cube.at/v1/knowledgebase'


def get_available_factbases(access_token: str,
                            factbase_url = FACTBASE_URL):
    """
    Sends API request to get currently available Facebases

    Returns:
        (json): a json object of all the factbases currently available
    """

    headers = {'Authorization': f'Bearer {access_token}'}
    with requests.Session() as s:
        s.headers.update(headers)
        all_factbases = s.get(factbase_url).json()

    return all_factbases


def get_knowledgebases(access_token: str,
                        knowledgebase_url = KNOWLEDGEBASE_URL):
    """
    Sends API request to get user's save knowledgebase models. 

    Returns:
        (dict): a dictionary of all knowledgebase model titles and IDs
    """
    knowledgebase_infos = {}

    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {'page[size]': 0}
    with requests.Session() as s:
        s.headers.update(headers)
        knowledgebases = s.get(knowledgebase_url, params=payload).json()
        
    for j in range(len(knowledgebases['data'])):
        key = knowledgebases['data'][j]['attributes']['title']
        value = knowledgebases['data'][j]['id']
        knowledgebase_infos[key] = value

    return knowledgebase_infos
