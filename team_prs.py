import calendar
import datetime
import operator
import requests
import os
import json
from pprint import pprint
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta

token = os.getenv('GITHUB_TOKEN', '...')

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
	headers = {'Authorization': f'token {token}'}
	r = requests.get(query_url, headers=headers, params=params)
	for i in r.json():
		if i['slug'] == team['team-slug']:
			query_url = i['members_url'].replace('{/member}','')
			teammembers = requests.get(query_url, headers=headers, params=params)
			for m in teammembers.json():
				memberlist.append(m['login'])

	return memberlist

def getPRsForTeam(team,start_date, end_date):
	repos = team['repos']
	print(f"Gathering Team PR Counts for {team['name']}")
	prcount = 0
	teammembers = getTeamMembers(team)
	for repo in repos:
		
		query_url = f"https://api.github.com/repos/newrelic/{repo}/pulls"
#is:pr is:closed reason:completed closed:2022-04-01..2023-04-01 
		page_num = 1
		while page_num != 0:
			params = {
				"state": "closed",
				"page": page_num
			}
			headers = {'Authorization': f'token {token}'}
			r = requests.get(query_url, headers=headers, params=params)
			#this has all pull requests. need to filter out ones where the author is on the team
			prs = r.json()

			# Check the Link header to see if there are more pages of results
			if 'Link' in r.headers:
				links = r.headers['Link'].split(', ')
				for link in links:
					if 'rel="next"' in link:
						page_num += 1
						# Set the next page URL
#						next_page_url = link.split(';')[0][1:-1]
						break
					else:
						page_num = 0
			else:
				page_num = 0
			#are there more pages?
			print(r.headers['Link'])
			if True:
				page_num += 1
			prs.sort(key=operator.itemgetter('created_at'),reverse=False)
			for pr in prs:
				if pr['user']['login'] in teammembers :
					print(' found pr in %s from: %s opened %s' % (repo, pr['user']['login'], datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')))
					prcount += 1
				
	#			else:
	#				print(' found pr for a team member: ', pr['user']['login'])
	print("Open External PRs: ", prcount)

def getTeamStats(team,start_date,end_date):
	repos = team['repos']
	print(f"Gathering Team PR Counts for {team['name']}")
	prcount = 0
	teammembers = getTeamMembers(team)

	pr_counts = {}

	for repo in repos:
		
		url = f"https://api.github.com/repos/newrelic/{repo}/pulls?state=closed"
		
		#	url = 'https://api.github.com/repos/newrelic/{repo}/pulls?state=closed'
	
		# Set the headers to include the access token
		headers = {
			'Authorization': f'token {token}',
			'Accept': 'application/vnd.github.v3+json'
		}
		
		# Create a dictionary to keep track of the count of pull requests per contributor
		
		# Keep track of the next page URL
		next_page_url = url
		
		# Loop through all the pages of results
		while next_page_url:
			# Make a GET request to the API
			response = requests.get(next_page_url, headers=headers)
			
			# Check the response status code
			if response.status_code == 200:
				# Get the JSON response from the API
				json_data = response.json()
				
				# Loop through the list of pull requests and count the number of pull requests per contributor
				for pr in json_data:
					if pr['user']['login'] in teammembers :
						merge_date_str = pr['merged_at']
						if merge_date_str:
							merge_date = datetime.strptime(merge_date_str, '%Y-%m-%dT%H:%M:%SZ')
							if merge_date >= datetime(2022, 4, 1) and merge_date < datetime(2023, 4, 1):
								contributor = pr['user']['login']
								if contributor in pr_counts:
									pr_counts[contributor] += 1
								else:
									pr_counts[contributor] = 1
								
				# Check the Link header to see if there are more pages of results
				if 'Link' in response.headers:
					links = response.headers['Link'].split(', ')
					for link in links:
						if 'rel="next"' in link:
							# Set the next page URL
							next_page_url = link.split(';')[0][1:-1]
							break
						else:
							next_page_url = None
				else:
					next_page_url = None
			else:
				print(f'Response status code: {response.status_code}')
			
	# Print the count of pull requests per contributor
	print(pr_counts)
	


teams = readConfigJson()

for team in teams['team']:
	if (team['name'].upper() != 'ELIXIR'):
		print(team['name'].upper())
#		print(team)
#		getPRsForTeam(team,'2022-01-01','2022-01-01')
		getTeamStats(team,'2022-01-01','2022-01-01')
		print()	