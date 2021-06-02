import requests
import os
import json
from pprint import pprint

token = os.getenv('GITHUB_TOKEN', '...')

def readConfigJson():
	# JSON file
	f = open ('teams.json', "r")
	
	# Reading from file
	data = json.loads(f.read())
	
	# Closing file
	f.close()
	return data
	
def getReposFromProject():
	return node

def getTeamMembers(team_slug):
	memberlist = []
	query_url = "https://api.github.com/orgs/newrelic/teams"
	params = {
		"per_page": 100,
	}
	headers = {'Authorization': f'token {token}'}
	r = requests.get(query_url, headers=headers, params=params)
	for i in r.json():
		if i['slug'] == team_slug:
			query_url = i['members_url'].replace('{/member}','')
			teammembers = requests.get(query_url, headers=headers, params=params)
			for m in teammembers.json():
				memberlist.append(m['login'])

	return memberlist


def getBugCounts(repos):
	openBugCount = 0
	print("Gathering Unreviewed Bug Counts")
	for repo in repos:
		query_url = f"https://api.github.com/repos/newrelic/{repo}/issues"
		params = {
			"status": "open",
			"labels": "bug",
			"labels": "needs-triage",
		}
		headers = {'Authorization': f'token {token}'}
		r = requests.get(query_url, headers=headers, params=params)
		openBugCount += len(r.json())
	print("Open Bugs: ", openBugCount)

def getExternalPRCounts(repos,team):
	print("Gathering Open External PR Counts")
	prcount = 0
	teammembers = getTeamMembers(team)
	for repo in repos:

		query_url = f"https://api.github.com/repos/newrelic/{repo}/pulls"
		params = {
			"state": "open",
		}
		headers = {'Authorization': f'token {token}'}
		r = requests.get(query_url, headers=headers, params=params)
		#this has all pull requests. need to filter out ones where the author is on the team
		prs = r.json()
		for pr in prs:
			if pr['user']['login'] not in teammembers :
				print(' found external pr from:', pr['user']['login'])
				prcount += 1
			else:
				print(' found pr for a team member: ', pr['user']['login'])
	print("Open External PRs: ", prcount)

teams = readConfigJson()
for team in teams['team']:
	print(team['name'].upper())
	getBugCounts(team['repos'])
	getExternalPRCounts(team['repos'], team['team-slug'])
	print()	
