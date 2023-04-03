import datetime
import requests
import os
import json
from pprint import pprint
from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta

token = os.getenv('GITHUB_TOKEN', '...')

start_date = datetime(2022, 1, 1)
end_date = datetime(2023, 3, 31)

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

def getTeamStats(team,start,end):
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
							if merge_date >= start and merge_date < end:
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
		getTeamStats(team,start_date,end_date)
		print()	
