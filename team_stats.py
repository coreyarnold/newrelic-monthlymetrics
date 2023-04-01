#!/usr/bin/env python3

import os
import requests
import json
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
					contributions(first: 1) {
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
	query {
		search(
				query: "author:%s org:%s is:pr merged:%s..%s"
			type: ISSUE
			first: 100
		) {
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
				cursor
			}
		}
	}
	"""

	full_query = QUERY % (username, org_name, start, end)
	
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
	
	#stats[userame] = {'pullRequestCount':'<count>', commits, additions, deletions, files}
	
	user = {}
	stats = {}
	for e in response_json['data']['search']['edges']:
		repository = e['node']['repository']['name']
#		merge_date = datetime.strptime(e['node']['mergedAt'], '%Y-%m-%dT%H:%M:%SZ')
		commits = e['node']['commits']['totalCount']
		additions = e['node']['additions']
		deletions = e['node']['deletions']
		files = e['node']['files']['totalCount']
		cursor = e['node'].get('cursor')

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
			
	
	print(f'{username}: PRs:' + str({user[username]['pullRequestCount']}))
	return user

#{'url': 'https://github.com/newrelic/docs-website/pull/8941', 'mergedAt': '2022-08-22T15:48:28Z', 'commits': {'totalCount': 1}, 'additions': 14, 'deletions': 14, 'merged': True, 'repository': {'name': 'docs-website'}, 'files': {'totalCount': 1}}




# The list of usernames to retrieve pull request reviews for
USERS = ['coreyarnold']

for team_member in USERS:
	ORGANIZATION_ID = ORGANIZATIONS['newrelic']
	getPullRequests(team_member, ORGANIZATION_ID, start_date, end_date)
	getReviews(team_member, ORGANIZATION_ID, start_date, end_date)
	getPullRequestsBySearch(team_member, list(ORGANIZATIONS.keys())[0], start_date, end_date)