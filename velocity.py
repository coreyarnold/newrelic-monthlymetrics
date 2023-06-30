#!/usr/bin/env python3

import os
import requests
import json
import pandas
import operator
from pprint import pprint
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Your GitHub personal access token
TOKEN = 'YOUR_PERSONAL_ACCESS_TOKEN'
TOKEN = os.getenv('GITHUB_TOKEN', '...')

# The name of the organization
ORGANIZATIONS = {}
ORGANIZATIONS['newrelic'] = 'O_kgDNe_s'
start_date = '2022-07-01'
end_date = '2023-03-31'

def getPullRequestsBySearch(repo, org_name, start, end):
	QUERY = """
	query ($after: String){
		search(
				query: "repo:%s/%s is:pr merged:%s..%s"
			type: ISSUE
			first: 100
			after: $after
		) {
			pageInfo {
				hasNextPage
				endCursor
			}
			edges {
				node {
					... on PullRequest {
						url
						mergedAt
						commits(first: 12) {
							totalCount
						}
						additions
						deletions
						merged
						repository {
							name
						}
						files {
							totalCount
						}
					}
				}
			}
		}
	}
	"""

	full_query = QUERY % (org_name, repo, start, end)
#	print(full_query)
	
	has_next_page = True
	after_cursor = None
	
	TotalPRCount = 0
	while has_next_page:
		# Construct the variables for the GraphQL query
		variables = {}
		if after_cursor:
			variables['after'] = after_cursor
		# Send the GraphQL request to the GitHub API
		response = requests.post('https://api.github.com/graphql', headers={
				'Authorization': f'Bearer {TOKEN}',
				'Content-Type': 'application/json'
		}, json={'query': full_query, 'variables': variables})
		
		# Check for errors in the response
		if response.status_code != 200:
				raise ValueError(f'Request failed with status code {response.status_code}: {response.text}')
			
		# Parse the response JSON
		response_json = json.loads(response.text)
		
		TotalPRCount += len(response_json['data']['search']['edges'])
#		print("%s %s: %s" % (repo, end, len(response_json['data']['search']['edges'])))
#		for e in response_json['data']['search']['edges']:
#			repository = e['node']['repository']['name']
#	#		merge_date = datetime.strptime(e['node']['mergedAt'], '%Y-%m-%dT%H:%M:%SZ')
#			commits = e['node']['commits']['totalCount']
#			additions = e['node']['additions']
#			deletions = e['node']['deletions']
#			files = e['node']['files']['totalCount']
#			cursor = e['node'].get('cursor')
		
		has_next_page = response_json['data']['search']['pageInfo']['hasNextPage']
		after_cursor = response_json['data']['search']['pageInfo']['endCursor']
	
	
#	print(f'{username}: PRs:' + str({user[username]['pullRequestCount']}))
#	if user[username].get('repos'):
#		df = pandas.DataFrame(user[username]['repos'])
#		df_pivot = df.pivot_table(user[username]['repos'].keys()
#	, columns=['pullRequestCount', 'commits', 'files', 'additions', 'deletions'], aggfunc='sum', fill_value=0)
#		print(df_pivot)
#
#	return user
	return TotalPRCount

def readConfigJson():
	# JSON file
	f = open ('teams.json', "r")
	
	# Reading from file
	data = json.loads(f.read())
	
	# Closing file
	f.close()
	return data

def getTeamMembers(team):
	memberlist = []
	query_url = "https://api.github.com/orgs/newrelic/teams"
	params = {
		"per_page": 100,
	}
	headers = {'Authorization': f'token {TOKEN}'}
	r = requests.get(query_url, headers=headers, params=params)
	for i in r.json():
		if i['slug'] == team['team-slug']:
			query_url = i['members_url'].replace('{/member}','')
			teammembers = requests.get(query_url, headers=headers, params=params)
			for m in teammembers.json():
				memberlist.append(m['login'])
				
	return memberlist


def getPullRequestsByTeam(team_obj):
	print("pull requests for " + team_obj['name'])
	now = datetime.today()
	since = datetime(2023, 6, 5, 0, 0, 0)
	until = since + relativedelta(days=+7)
	while (until < now):
		TeamPRCount = 0
		for repo in team_obj['repos']:
			TeamPRCount += getPullRequestsBySearch(repo, 'newrelic', since.strftime("%Y-%m-%d"), until.strftime("%Y-%m-%d"))
#			TeamPRCount += getPullRequestsBySearch(repo, 'newrelic', "2023-06-05", "2023-06-12")
		print("%s %s: %s" % (team_obj['name'], until.strftime("%Y/%m/%d"), TeamPRCount))
		
		since = since + relativedelta(days=+7)
		until = since + relativedelta(days=+7)
	
def getReleasesByTeam(team_obj):
	print("deploys for " + team_obj['name'])
	repos = team_obj['repos']
	print('Gathering Release Counts')
	#gets the number of releases across all team repos for the current and previous month
	#GET /repos/{owner}/{repo}/releases
	lastmonthreleasecount = 0
	thismonthreleasecount = 0
	totalreleasecount = 0
	now = datetime.today()
	since = datetime(2023, 6, 5, 0, 0, 0)
	until = since + relativedelta(days=+7)
	
	while (until < now):
	
		for repo in repos:
			reporeleasecount = 0
			query_url = f"https://api.github.com/repos/newrelic/{repo}/releases"
			params = {
				"state": "open",
			}
			headers = {'Authorization': f'token {TOKEN}'}
			r = requests.get(query_url, headers=headers, params=params)
			releases = r.json()
			#Remove any unpublished releases since can't sort them when 'published_at' is None
			for release in releases:
				if release['published_at'] == None:
					releases.remove(release)
					
			releases.sort(key=operator.itemgetter('published_at'),reverse=False)
			
			for release in releases:
				releasepublishedat = datetime.strptime(release['published_at'], '%Y-%m-%dT%H:%M:%SZ')
				if (releasepublishedat >= since and releasepublishedat <= until):
#					print(" Release %s published (%s) in %s" % (release.get("name"), releasepublishedat, repo))
					reporeleasecount += 1
					
			totalreleasecount += reporeleasecount
		print("%s - Total Release Count: %s" % (until.strftime("%m/%d/%Y, %H:%M:%S"), totalreleasecount))
		
		since = since + relativedelta(days=+7)
		until = since + relativedelta(days=+7)

# The list of usernames to retrieve pull request reviews for
#USERS = ['newrelic-node-agent-team']

teams = readConfigJson()

for team in teams['team']:
	print(team['name'])
	getPullRequestsByTeam(team)
	getReleasesByTeam(team)
		