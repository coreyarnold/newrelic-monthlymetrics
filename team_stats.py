#!/usr/bin/env python3

import os
import requests
import json
import pandas
from pprint import pprint
from datetime import datetime

# Your GitHub personal access token
TOKEN = 'YOUR_PERSONAL_ACCESS_TOKEN'
TOKEN = os.getenv('GITHUB_TOKEN', '...')

# The name of the organization
ORGANIZATIONS = {}
ORGANIZATIONS['newrelic'] = 'O_kgDNe_s'
start_date = '2022-07-01'
end_date = '2023-03-31'

def getReviews(username,org_id, start_date, end_date):
	
	# The GraphQL query to retrieve the reviews
	QUERY = """
	query {
		user(login: "%s") {
			contributionsCollection(organizationID: "%s") {
				totalPullRequestReviewContributions
				pullRequestReviewContributionsByRepository {
					contributions(first: 100) {
						nodes {
							repository {
								name
							}
							occurredAt
							pullRequest {
								author {
									login
								}
							}
						}
						edges {
							cursor
						}
					}
				}
			}
		}
	}
	"""
	
	full_query = QUERY % (username, org_id)
	
	user = {}
	user[username] = {'reviewCount': 0, 'authors': {}, 'repos': {}}
	#{'username': 'reviewCount': 0, 'authors': {'author1': 0, 'author2': 0}, 'repos': {'repo1': 0, 'repo2: 0}}
	has_next_page = True
	after_cursor = None
	
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
		
		for e in response_json['data']['user']['contributionsCollection']['pullRequestReviewContributionsByRepository']:
			for node in e['contributions']['nodes']:
				occurredAt = datetime.strptime(node['occurredAt'], '%Y-%m-%dT%H:%M:%SZ')
				if datetime.strptime(start_date, '%Y-%m-%d') <= occurredAt <= datetime.strptime(end_date, '%Y-%m-%d'):
					user[username]['reviewCount'] += 1
					repo = node['repository']['name']
					author = node['pullRequest']['author']['login']
					if user[username]['authors'].get(author):
						user[username]['authors'][author] = user[username]['authors'][author] + 1
					else:
						user[username]['authors'][author] = 1
					
					if user[username]['repos'].get(repo):
						user[username]['repos'][repo] = user[username]['repos'][repo] + 1
					else:
						user[username]['repos'][repo] = 1
					
			cursor = e['contributions']['edges'][0]['cursor']
		has_next_page = False
#		has_next_page = response_json['data']['search']['pageInfo']['hasNextPage']
#		after_cursor = response_json
	print(user)
#
#		if username in user and user.get(username).get('repos'):
#			stats = user[username]['repos']
#			
#		if repository in stats:
#			s = stats[repository]
#			s['pullRequestCount'] += 1
#			s['commits'] += commits
#			s['files'] += files
#			s['additions'] += additions
#			s['deletions'] += deletions
#			stats[repository] = s
#		else:
#			stats[repository] = 	{'pullRequestCount': 1, 'commits':commits,'files':files,'additions':additions,'deletions':deletions}
#			
	
	return response_json

def getPullRequests(username, org_id, start, end):
	# The GraphQL query to retrieve the pull requests
	QUERY = """
	query {
		user(login: "%s") {
			contributionsCollection(organizationID: "%s") {
				totalPullRequestContributions
				pullRequestContributions(orderBy: {direction: DESC}, first: 1) {
					pageInfo {
						hasNextPage
						endCursor
					}
					edges {
						node {
							pullRequest {
								author {
									login
								}
								changedFiles
								deletions
								additions
								repository {
									name
								}
							}
							occurredAt
						}
					}
				}
			}
		}
	}
	"""
	
	full_query = QUERY % (username, org_id)
	
	# Send the GraphQL request to the GitHub API
	response = requests.post('https://api.github.com/graphql', headers={
			'Authorization': f'Bearer {TOKEN}',
			'Content-Type': 'application/json'
	}, json={'query': full_query})
	
	# Check for errors in the response
	if response.status_code != 200:
			raise ValueError(f'Request failed with status code {response.status_code}: {response.text}')
		
	# Parse the response JSON
	response_json = json.loads(response.text)
#	if datetime.strptime(start, '%Y-%m-%d') <= merge_date <= datetime.strptime(end, '%Y-%m-%d'):
#		print('yep')
#	else:
#		print('nope')
	
	return response_json

def getPullRequestsBySearch(username, org_name, start, end):
	QUERY = """
	query ($after: String){
		search(
				query: "author:%s org:%s is:pr merged:%s..%s"
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

	full_query = QUERY % (username, org_name, start, end)
	
	user = {}
	user[username] = {'pullRequestCount': 0, 'additions': 0, 'deletions': 0, 'files': 0, 'commits': 0}
	
	has_next_page = True
	after_cursor = None
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
		
		stats = {}
		for e in response_json['data']['search']['edges']:
			repository = e['node']['repository']['name']
	#		merge_date = datetime.strptime(e['node']['mergedAt'], '%Y-%m-%dT%H:%M:%SZ')
			commits = e['node']['commits']['totalCount']
			additions = e['node']['additions']
			deletions = e['node']['deletions']
			files = e['node']['files']['totalCount']
			cursor = e['node'].get('cursor')
			
			if username in user and user.get(username).get('repos'):
				stats = user[username]['repos']
	
			if repository in stats:
				s = stats[repository]
				s['pullRequestCount'] += 1
				s['commits'] += commits
				s['files'] += files
				s['additions'] += additions
				s['deletions'] += deletions
				stats[repository] = s
			else:
				stats[repository] = 	{'pullRequestCount': 1, 'commits':commits,'files':files,'additions':additions,'deletions':deletions}
			
			if username in user:
				u = user[username]
				u['pullRequestCount'] += 1
				u['additions'] += additions
				u['deletions'] += deletions
				u['files'] += files
				u['commits'] += commits
				u['repos'] = stats
			else:
				user[username] = {'pullRequestCount': 1, 'additions': additions, 'deletions': deletions, 'files': files, 'commits': commits, 'repos': stats}
		
				#		print(response_json)
		has_next_page = response_json['data']['search']['pageInfo']['hasNextPage']
		after_cursor = response_json['data']['search']['pageInfo']['endCursor']
		#"Y3Vyc29yOjEwMA=="#response_json['data']['search']['pageInfo']['endCursor']
		#{'data': {'search': {'pageInfo': {'hasNextPage': False, 'endCursor': 'Y3Vyc29yOjUy'}		
	
	
	print(f'{username}: PRs:' + str({user[username]['pullRequestCount']}))
	if user[username].get('repos'):
		df = pandas.DataFrame(user[username]['repos'])
		df_pivot = df.pivot_table(user[username]['repos'].keys()
	, columns=['pullRequestCount', 'commits', 'files', 'additions', 'deletions'], aggfunc='sum', fill_value=0)
		print(df_pivot)

	return user

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

# The list of usernames to retrieve pull request reviews for
USERS = ['newrelic-node-agent-team']

teams = readConfigJson()

for team in teams['team']:
	print(team['name'])
	teammembers = getTeamMembers(team)
	for team_member in teammembers:
		getPullRequestsBySearch(team_member, list(ORGANIZATIONS.keys())[0], start_date, end_date)			
		getReviews(team_member, ORGANIZATIONS['newrelic'], start_date, end_date)
#getPullRequestsBySearch('coreyarnold', 'newrelic', start_date, end_date)
#getReviews('bizob2828', ORGANIZATIONS['newrelic'], start_date, end_date)
