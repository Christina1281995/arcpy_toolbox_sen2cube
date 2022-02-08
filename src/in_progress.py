import arcpy
import requests_oauthlib 
import oauthlib
import json
import os
from datetime import datetime
from oauthlib.oauth2 import InvalidGrantError, LegacyApplicationClient, OAuth2Token, \
  UnauthorizedClientError
from requests import Response
from requests_oauthlib import OAuth2Session
# envs
auth_token_url = "https://auth.sen2cube.at/realms/sen2cube-at/protocol/openid-connect/token"
auth_client_id = "iq-web-client"
output_scale_factor = 10
url_for_request = "https://api.sen2cube.at/v1/inference"

def fetch_token(username: str, password: str,
                auth_token_url: str,
                auth_client_id: str,
                ) -> OAuth2Token:
  """
  Get OAuth token from auth_token_url and store in config_path_tokenfile
  :return: OAuth2Token with session information or None if any error
  """
  try:
    client: Final[LegacyApplicationClient] = LegacyApplicationClient(client_id=auth_client_id)
    with OAuth2Session(client=client) as oauth_session:
      token: Final[OAuth2Token] = oauth_session.fetch_token(
        token_url=auth_token_url,
        client_id=auth_client_id,
        username=username,
        password=password
      )
      arcpy.AddMessage(f"Login successful. Got token: {token}")
      return token
    
  except UnauthorizedClientError:
    arcpy.AddErrorMessage(
      f"Authorisation failed for token url {auth_token_url} as client {auth_client_id}.",
      exc_info=True,
    )
  except InvalidGrantError as e:
    arcpy.AddErrorMessage(f"Login failed. Reason {str(e)}", exc_info=False)
  except Exception:
    arcpy.AddErrorMessage(
      f"Unknown error on authentication for token url {auth_token_url} as client {auth_client_id}.",
      exc_info=True,
    )
# This is used to execute code if the file was run but not imported
if __name__ == '__main__':
  
    # user login
    username = arcpy.GetParameterAsText(0)
    password = arcpy.GetParameterAsText(1)
    
    result = fetch_token(username, password, auth_token_url, auth_client_id)
    print(result)

    
    # factbase
    if arcpy.GetParameterAsText(2) == "Austria":
      factbase = 1
    # knowledgebase
    if arcpy.GetParameterAsText(3) == "modelnr_1":
      knowledgebase = 2150

    # hard coded AOI for now  
    area_of_interest = "{\"type\":\"FeatureCollection\",\"features\":[{\"type\":\"Feature\",\"properties\":{\"name\":\"Area-of-interest 00\"},\"geometry\":{\"type\":\"Polygon\",\"coordinates\":[[[14.07188,47.768556],[14.07188,47.865185],[14.237462,47.865185],[14.237462,47.768556],[14.07188,47.768556]]]}}]}"

    # hard coded date range for now
    temp_range_start = "2021-03-01T00:00:00+00:00"
    temp_range_end = "2021-07-31T23:59:59.999000+00:00"


    # create POST request
     url = url_for_request
     headers = {'Authorization': f"{token['token_type']} {token['access_token']}"}
     request_body = "data" {
      "inference": {
        "properties": {
          "owner": {
            "type": "string"
          },
          "timestamp_created": {
            "type": ["string", "null"]
          },
          "timestamp_started": {
            "type": ["string", "null"]
          },
          "timestamp_finished": {
            "type": ["string", "null"]
          },
          "status": {
            "type": ["string", "null"]
          },
          "status_message": {
            "type": ["string", "null"]
          },
          "temp_range_start": {
            "type": "string"
          },
          "temp_range_end": {
            "type": "string"
          },
          "area_of_interest": {
            "type": "string"
          },
          "qgis_project_location": {
            "type": ["string", "null"]
          },
          "output": {
            "type": "array",
            "items": {
              "type": "string"
            }
          },
          "comment": {
            "type": "string",
          },
          "output_scale_factor": {
            "type": "integer"
          },
          "favourite": {
            "type": "boolean"
          },
          'factbase': {'relation': 'to-one', 'resource': ['factbase']},
          'knowledgebase': {'relation': 'to-one', 'resource': ['knowledgebase']},

        }
      },
      "knowledgebase": {
        "properties": {
          "title": {
            "type": "string"
          },
        }
      },
      "factbase": {
        "properties": {
          "title": {
            "type": "string"
          },
        }
      }
    }
