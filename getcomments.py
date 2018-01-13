#!/usr/bin/python

# Usage example:
# python comments.py --videoid='<video_id>' --text='<text>'

import httplib2
import os
import sys
import pandas as pd
import warnings

from apiclient.discovery import build_from_document
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow
from oauth2client.client import OAuth2WebServerFlow

import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

from documents import Documents

import sqlite3

class Articles(Documents):
    def __init__(self, fname):
        super().__init__(
            fname=fname, 
            tabname='articles', 
            columns='id integer primary key autoincrement, type string, parentid string, commentid string, videoid string, authname string, authurl string, content string, publishdat datetime, updatedat datetime, numlikes integer, nextpagetoken string',
            
            #src string, date timestamp, num integer, fname string, text string, doc blob',
            addorder = 'type,parentid,commentid,videoid,authname,authurl,content,publishdat,updatedat,numlikes,nextpagetoken',
        )
        #self.c.execute("create index if not exists idx1 on articles(date)")
        #self.c.execute("create index if not exists idx2 on articles(date,src)")
        #self.c.execute("create index if not exists idx4 on articles(src)")
        #self.c.execute("create index if not exists idx5 on articles(fname)")
        # https://sqlite.org/queryplanner.html
        
    def getsents(self, where=None):
        for row in self.getdocs(sel='doc', where=where):
            for s in row[0]:
                yield(s)

'''
cdata = dict()
comment = item["snippet"]["topLevelComment"]
cdata['commentid'] = comment['id']
cdata['videoid'] = comment["snippet"]['videoId']
cdata['authname'] = comment["snippet"]["authorDisplayName"]
cdata['authurl'] = comment["snippet"]["authorChannelUrl"]
cdata['text'] = comment["snippet"]["textDisplay"]
cdata['publishdat'] = comment["snippet"]["publishedAt"]
cdata['updatedat'] = comment["snippet"]["updatedAt"]
cdata['numlikes'] = comment["snippet"]["likeCount"]
cdata['nextpagetoken'] = results['nextPageToken']
'''





# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains

# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
YOUTUBE_READ_WRITE_SSL_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
CLIENT_SECRETS_FILE = "client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:
    %s
with information from the APIs Console
https://console.developers.google.com

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__), CLIENT_SECRETS_FILE))

# Authorize the request and store authorization credentials.
def get_authenticated_service(args):
    #flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_READ_WRITE_SSL_SCOPE, message=MISSING_CLIENT_SECRETS_MESSAGE)
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    #credentials = flow.run_console()

    #storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    # Trusted testers can download this discovery document from the developers page
    # and it should be in the same directory with the code.
    with open("youtube-v3-discoverydocument.json", "r") as f:
        doc = f.read()
        return build_from_document(doc, http=credentials.authorize(httplib2.Http()))


def get_authenticated_service2():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_console()
    
    return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)


# Call the API's commentThreads.list method to list the existing comment threads.
def get_comment_threads(youtube, video_id, pagetoken=None):
    if pagetoken is None:
        results = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=100,
        ).execute()
    else:
        results = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=100,
            pageToken=pagetoken,
        ).execute()

    return results


# Call the API's comments.list method to list the existing comment replies.
def get_comments(youtube, parent_id):
    results = youtube.comments().list(
        part="snippet",
        parentId=parent_id,
        textFormat="plainText"
    ).execute()
    
    return results

def parsecomment(comment, nptoken, typ='comment'):
    return (
        typ,
        comment["snippet"]['parentId'] if typ=='comment' else '',
        comment['id'],
        comment["snippet"]['videoId'] if typ!='comment' else '',
        comment["snippet"]["authorDisplayName"],
        comment["snippet"]["authorChannelUrl"],
        comment["snippet"]["textDisplay"],
        comment["snippet"]["publishedAt"],
        comment["snippet"]["updatedAt"],
        comment["snippet"]["likeCount"],
        nptoken,
    )



if __name__ == "__main__":
# The "videoid" option specifies the YouTube video ID that uniquely
# identifies the video for which the comment will be inserted.
    print('Wait, do you realize that I switched parentid and commentid? Make sure you take that into account!')
    exit()
    
    argparser.add_argument("--videoid",
        help="Required; ID for video for which the comment will be inserted.")

    args = argparser.parse_args()
    if not args.videoid:
        exit("Please specify videoid using the --videoid= parameter.")

    youtube = get_authenticated_service2()
    
    # storage databse object
    commdb = Articles('comments/comments.db')
    
    nptoken = None
    ids = [d[0] for d in commdb.getdocs(sel='id')]
    if len(ids) > 0:
        i = max(ids)
        nptoken = list(commdb.getdocs(sel='nextpagetoken', where='id == '+str(i)))[0][0]
        print('starting with prvious token', nptoken)
    
    results = get_comment_threads(youtube, args.videoid, nptoken)
    
    j = 0
    while True:
        #print(results['nextPageToken'])
        for item in results["items"]:
            #addorder = 'type,commentid,videoid,authname,authurl,content,publishdat,updatedat,numlikes,nextpagetoken',
            
            # https://developers.google.com/youtube/v3/docs/commentThreads#resource
            tlcomment = item["snippet"]["topLevelComment"]
            commdb.add(parsecomment(tlcomment,results['nextPageToken'],typ='commentThread'))
            
            # https://developers.google.com/youtube/v3/docs/comments#resource
            cresults = get_comments(youtube, tlcomment['id'])
            for item in cresults["items"]:
                commdb.add(parsecomment(item,'',typ='comment'))


            if j % 10 == 0:
                print('=================')
                print('retreived {} comment threads.'.format(j))
                print('=================')
            j += 1
        results = get_comment_threads(youtube, args.videoid, results['nextPageToken'])
        

        
    #print('parent ids!======================')
    #parent_id = video_comment_threads[0]["id"]
    #print('comments!=============================')
    #video_comments = get_comments(youtube, parent_id)


