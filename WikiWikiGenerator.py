import requests
import re
from datetime import date

verticalToHub = {
	0: 8, # Other
	1: 2, # TV
	2: 6, # Games
	3: 5, # Books
	4: 1, # Comics
	5: 7, # Lifestyle
	6: 4, # Music
	7: 3, # Movies
	8: 9, # Anime
}

while True:
	url = input('Input wiki: ')
	if not url: break

	data = requests.get('https://%s.fandom.com/api.php?format=json&action=query&meta=siteinfo&siprop=general|statistics|variables' % url).json()['query']

	cityId = next((x for x in data['variables'] if x['id'] == 'wgCityId'), None)['*']

	dw = requests.get('https://community.fandom.com/wikia.php?controller=DWDimensionApi&method=getWikis&limit=1&after_wiki_id=%d' % (cityId - 1)).json()[0]

	infobox = {
		'name': data['general']['sitename'],
		'URL': data['general']['servername'].split('.')[0], # community.fandom.com
		'dbname': data['general']['logo'].split('/')[3], # https://images.wikia.com/central/images/b/bc/Wiki.png
		'language':  data['general']['lang'],
		'articles': data['statistics']['articles'],
		'founded': dw['created_at'],
		'founder': requests.get('https://community.fandom.com/api.php?format=json&action=query&list=users&ususerids=' + dw['founding_user_id']).json()['query']['users'][0]['name'],
		'adopted': None,
		'adopter': None,
		'id': cityId,
		'hub': verticalToHub[int(dw['vertical_id'])],
		'checked': date.today().strftime("%Y-%m-%d")
	}

	for attempt in requests.get('https://community.fandom.com/api.php?format=json&action=query&list=allpages&apdir=descending&apnamespace=118&apprefix=' + infobox['name']).json()['query']['allpages']:
		req = requests.get('https://community.fandom.com/api.php?format=json&formatversion=2&action=query&prop=revisions&rvlimit=1&rvprop=content|user&rvdir=newer&titles=' + attempt['title']).json()['query']['pages'][0]['revisions'][0]
		if re.search('https?:\/\/' + infobox['URL'] + '\.(fandom|wikia)\.(com|org)', req['content']): # this wiki was mentioned
			user = req['user']
			log = requests.get(data['general']['server'] + data['general']['scriptpath'] + '/api.php?format=json&action=query&list=logevents&leaction=rights/rights&letitle=User:' + user).json()['query']['logevents']
			if not log:
				# they didn't adopt it, try the next page
				continue
			if 'bureaucrat' in log[0]['params']['newgroups']:
				# they are still a bcrat, find when it was added
				action = next((x for x in reversed(log) if next((y for y in x['params']['newmetadata'] if y['group'] == 'bureaucrat'), None)), None)
				
				infobox['adopted'] = action['timestamp'].replace('T', ' ').replace('Z', '')
				infobox['adopter'] = user
				break

	template = '{{Infobox wiki\n'
	for key, value in infobox.items():
		if value != None:
			template += f'|{key} = {value}\n'
	template += '}}'

	print(template)