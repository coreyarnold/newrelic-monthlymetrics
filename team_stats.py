#!/usr/bin/env python3

import os
import requests
import json

# Your GitHub personal access token
TOKEN = 'YOUR_PERSONAL_ACCESS_TOKEN'
TOKEN = os.getenv('GITHUB_TOKEN', '...')

# The name of the organization
ORGANIZATIONS = {}
ORGANIZATIONS['newrelic'] = 'O_kgDNe_s'
start_date = '2022-07-01'
end_date = '2023-03-31'

def getReviews(username,org_id):
	
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
	print(response_json)

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
	print(response_json)

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
	print(response_json)


# The list of usernames to retrieve pull request reviews for
USERS = ['coreyarnold']

for team_mamber in USERS:
	ORGANIZATION_ID = ORGANIZATIONS['newrelic']
	getPullRequests(team_mamber, ORGANIZATION_ID, start_date, end_date)
	getReviews(team_mamber, ORGANIZATION_ID)
	getPullRequestsBySearch(team_mamber, list(ORGANIZATIONS.keys())[0], start_date, end_date)