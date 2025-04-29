from __future__ import print_function

import os.path

import json 

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.apps import chat_v1 as google_chat
from google.protobuf.json_format import MessageToJson, MessageToDict


# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/chat.spaces.readonly',
    'https://www.googleapis.com/auth/chat.messages.readonly',
    ]


class ChatExtractor():
    def __init__(self):
        self.client: google_chat.ChatServiceClient
        self.space_ids = []
        self.creds = None
        self._init_oauth()


    def _init_oauth(self):
        """
        Initializes the OAuth2 client to authenticate with the Chat API.
        """
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=8080)
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        
        self.client = google_chat.ChatServiceClient(
            credentials = self.creds,
            client_options = {
                "scopes" : SCOPES
            }
        )     
        

    def list_spaces(self) -> list[dict]:
        # Initialize request argument(s)
        request = google_chat.ListSpacesRequest(
            # Filter spaces by space type (SPACE or GROUP_CHAT or DIRECT_MESSAGE)
            filter = 'space_type = "SPACE"'
        )

        # Make the request
        page_result = self.client.list_spaces(request)


        spaces = [ MessageToDict(space._pb) for space in page_result ]

        return spaces


    def list_messages(self, space_id: str) -> list[dict]:
        request = google_chat.ListMessagesRequest(
            parent=space_id
        )
        results = self.client.list_messages(request)

        # Convert each protobuf message to a dict properly
        messages = [ MessageToDict(message._pb) for message in results ]

        return messages

    def dump_json(self, content, output_file :str) -> None:
        with open(output_file, 'w') as f:
            json.dump(content, f, indent=4)


# ONE - Q&A on System Activity pipeline
target_space = 'spaces/AAAAocwPEic'

chatter = ChatExtractor()
chats = chatter.list_messages(target_space)
chatter.dump_json(chats,'tmp.json')
