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

def getUnreviewedBugCounts(team):
	repos = team['repos']
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
		bugs = r.json()
		if (len(bugs) > 0):
			for b in bugs:
				labels = b.get('labels')
				bug_check = False
				triage_check = False
				for label in labels:
					if label.get('name') == 'needs-triage':
						triage_check = True
					if label.get('name') == 'bug':
						bug_check = True
				if (triage_check and bug_check):
					print(' found unreviewed bug %s in %s' % (b.get('number'), repo))
					openBugCount += 1
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
		prs.sort(key=operator.itemgetter('created_at'),reverse=False)
		for pr in prs:
			if pr['user']['login'] not in teammembers :
				print(' found external pr in %s from: %s opened %s' % (repo, pr['user']['login'], datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')))
				prcount += 1
#			else:
#				print(' found pr for a team member: ', pr['user']['login'])
	print("Open External PRs: ", prcount)

def get_month_day_range(date):
	first_day = datetime.combine(date.replace(day = 1), datetime.min.time())
	last_day = datetime.combine(date.replace(day = calendar.monthrange(date.year, date.month)[1]), datetime.max.time())
	return first_day, last_day

def getReleaseNumbers(repos):
	print('Gathering Release Counts')
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
		#Remove any unpublished releases since can't sort them when 'published_at' is None
		for release in releases:
			if release['published_at'] == None:
				releases.remove(release)

		releases.sort(key=operator.itemgetter('published_at'),reverse=False)

		for release in releases:
			releasepublishedat = datetime.strptime(release['published_at'], '%Y-%m-%dT%H:%M:%SZ')
			if(releasepublishedat > lastmonth[0] and releasepublishedat < lastmonth[1]):
				print(" Release %s last month (%s) in %s" % (release.get("name"), releasepublishedat, repo))
				reporeleasecount_lastmonth += 1
			elif(releasepublishedat > thismonth[0] and releasepublishedat < thismonth[1]):
				print(" Release %s this month (%s) in %s" % (release.get("name"), releasepublishedat, repo))
				reporeleasecount_thismonth += 1

		lastmonthreleasecount += reporeleasecount_lastmonth
		thismonthreleasecount += reporeleasecount_thismonth
	print("Total Release Count Last Month: ", lastmonthreleasecount)
	print("Total Release Count This Month: ", thismonthreleasecount)
	
def getOpenBugs(team):
	repos = team['repos']
	openBugCount = 0
	for repo in repos:
		query_url = f"https://api.github.com/repos/newrelic/{repo}/issues"
		params = {
			"status": "open",
			"labels": "bug",
		}
		headers = {'Authorization': f'token {token}'}
		r = requests.get(query_url, headers=headers, params=params)
		bugs = r.json()
		if (len(bugs) > 0):
			openBugCount += len(bugs)
		else:
			openBugCount += 0
	return openBugCount


teams = readConfigJson()
aggregatebugs = 0
for team in teams['team']:
	aggregatebugs += getOpenBugs(team)
print('Total Open Bugs: ',aggregatebugs)

for team in teams['team']:
	print(team['name'].upper())
	getUnreviewedBugCounts(team)
	getExternalPRCounts(team['repos'], team['team-slug'])
	getReleaseNumbers(team['repos'])
	print()	
