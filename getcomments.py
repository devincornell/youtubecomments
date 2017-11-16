#!/usr/bin/python

# Usage example:
# python comments.py --videoid='<video_id>' --text='<text>'

import httplib2
import os
import sys
import pandas as pd

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

	for item in results["items"]:
		author = item["snippet"]["authorDisplayName"]
		text = item["snippet"]["textDisplay"]
		print("Comment by %s: %s" % (author, text))

	return results["items"]


if __name__ == "__main__":
# The "videoid" option specifies the YouTube video ID that uniquely
# identifies the video for which the comment will be inserted.

	cfolder = 'comments/'

	argparser.add_argument("--videoid",
		help="Required; ID for video for which the comment will be inserted.")

	args = argparser.parse_args()
	if not args.videoid:
		exit("Please specify videoid using the --videoid= parameter.")

	youtube = get_authenticated_service2()
	# All the available methods are used in sequence just for the sake of an example.

	fname = cfolder + 'comments_'+args.videoid+'.xlsx'
	if os.path.isfile(fname):
		df = pd.read_excel(fname)
		ind = max(df.index)
		nptoken = df.loc[ind,'nextpagetoken']
		results = get_comment_threads(youtube, args.videoid, nptoken)
	else:
		df = pd.DataFrame(columns=['videoid','commentid','authname','authurl','text','publishdat','updatedat','numlikes', 'nextpagetoken'])
		results = get_comment_threads(youtube, args.videoid)
	
	i = 0
	while True:
		#print(results['nextPageToken'])
		for item in results["items"]:
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
			
			df = df.append( pd.DataFrame([cdata,], index=[i,]) )
			i += 1
			
		try:
			results = get_comment_threads(youtube, args.videoid, results['nextPageToken'])
		except:
			break
	
		#with pd.ExcelWriter(fname, engine='xlsxwriter', {'strings_to_urls':False}) as writer:
		#	df.to_excel(writer)
		df.to_excel(fname)
		print('=================')
		print('retrieved', i, 'comments;', max(df.index)+1, 'in total; saved to file.')
		print('=================')
		
	#print('parent ids!======================')
	#parent_id = video_comment_threads[0]["id"]
	#print('comments!=============================')
	#video_comments = get_comments(youtube, parent_id)


