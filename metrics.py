import calendar
import datetime
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

def get_month_day_range(date):
	first_day = datetime.combine(date.replace(day = 1), datetime.min.time())
	last_day = datetime.combine(date.replace(day = calendar.monthrange(date.year, date.month)[1]), datetime.max.time())
	return first_day, last_day

def getReleaseNumbers(repos):
	#gets the number of releases across all team repos for the current and previous month
	#GET /repos/{owner}/{repo}/releases
	lastmonthreleasecount = 0
	thismonthreleasecount = 0
	now = date.today()
	thismonth = get_month_day_range(now)
	lastmonth = get_month_day_range(now + relativedelta(months=-1))

	for repo in repos:
		reporeleasecount_lastmonth = 0
		reporeleasecount_thismonth = 0
		query_url = f"https://api.github.com/repos/newrelic/{repo}/releases"
		params = {
			"state": "open",
		}
		headers = {'Authorization': f'token {token}'}
		r = requests.get(query_url, headers=headers, params=params)
		#this has all pull requests. need to filter out ones where the author is on the team
		releases = r.json()

		for release in releases:
			releasepublishedat = datetime.strptime(release['published_at'], '%Y-%m-%dT%H:%M:%SZ')
			if(releasepublishedat > lastmonth[0] and releasepublishedat < lastmonth[1]):
				print("Release last month in ", repo)
				reporeleasecount_lastmonth += 1
			elif(releasepublishedat > thismonth[0] and releasepublishedat < thismonth[1]):
				print("Release this month in ", repo)
				reporeleasecount_thismonth += 1

		lastmonthreleasecount += reporeleasecount_lastmonth
		thismonthreleasecount += reporeleasecount_thismonth
	print("Total Release Count Last Month: ", lastmonthreleasecount)
	print("Total Release Count This Month: ", thismonthreleasecount)
	

teams = readConfigJson()
for team in teams['team']:
	print(team['name'].upper())
	getBugCounts(team['repos'])
	getExternalPRCounts(team['repos'], team['team-slug'])
	getReleaseNumbers(team['repos'])
	print()	
