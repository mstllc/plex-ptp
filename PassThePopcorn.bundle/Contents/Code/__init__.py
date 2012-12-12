#########################################################
#														#
#			PassThePopcorn Browser for PLEX				#
#														#
#########################################################

ART = 'art-default.jpg'
ICON = 'icon-default.png'

PTP_URL = 'http://passthepopcorn.me/'

#########################################################
def Start():
	Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')
	Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
	
	ObjectContainer.art = R(ART)
	ObjectContainer.title1 = L('Title')
	DirectoryObject.thumb = R(ICON)
	
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_2) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.97 Safari/537.11'
	
#########################################################
@handler('/video/ptp', 'Pass The Popcorn', thumb=ICON, art=ART)
def MainMenu():

	oc = ObjectContainer(
		view_group = 'List',
		objects = [
			DirectoryObject(
				key = Callback(PtpBrowse, title=L('Browse'), page=1),
				title = L('Browse')
			),
			DirectoryObject(
				key = Callback(PtpAccount, title=L('My Account')),
				title = L('My Account')
			),
			
			PrefsObject(
				title = L('Preferences'),
				thumb = R('icon-default.png')
			)
		]
	)
	
	return oc
	
#########################################################
def PtpBrowse(title, page):
	if not PtpLoggedIn():
		Log('Not Logged In')
		if not Prefs['username'] or not Prefs['password']:
			Log('Prefs Not Set')
			return ObjectContainer(header=L('Log-in Error'), message=L('Enter your username and password in the preferences section.'))
			
		PtpLogIn()
		
		if not PtpLoggedIn():
			Log('Log In Error')
			return ObjectContainer(header=L('Log-in Error'), message=L('Error logging in. Please check your username and password in the preferences section.'))
	
	html = HTML.ElementFromURL(PTP_URL + 'torrents.php?page=' + str(page))
	
	oc = ObjectContainer(view_group='InfoList', title2=title)
	
	for group in html.xpath('//table[@id="torrent_table"]/tr[@class="group"]'):
		
		tid = group.xpath('.//td[@class="small"]/a')[0].get('href')
		tid = (tid.split('id='))[1]
		
		fs = []
		for f in html.xpath('//table[@id="torrent_table"]//tr[@class="group_torrent groupid_' + tid + '"]'):
			if f.xpath('.//td/a'):
				fs.append({
					"name": f.xpath('.//td/a')[0].text, 
					"url": f.xpath('.//td/span/a')[0].get('href'),
					"added": f.xpath('.//td[2]/span')[0].text,
					"size": f.xpath('.//td')[2].text,
					"snatches": f.xpath('.//td')[3].text,
					"seeders": f.xpath('.//td')[4].text,
					"leechers": f.xpath('.//td')[5].text,
					"thumb": group.xpath('.//td[@class="small"]/a/img')[0].get('src')
				})
				
		obj = DirectoryObject(
			key = Callback(PtpSelectTorrent, formats=fs),
			title = group.xpath('.//td/a[@class="l_movie"]')[0].text + ' (' + group.xpath('.//td[2]/text()')[1][2:6] + ')',
			thumb = group.xpath('.//td[@class="small"]/a/img')[0].get('src')
		)
		
		oc.add(obj)
	
	oc.add(DirectoryObject(key=Callback(PtpBrowse, title=L('Browse'), page=(page+1)), title=L('Next Page')))
	
	return oc
	
#########################################################
def PtpSelectTorrent(formats):
	Log('------- SELECT TORRENT ---------')
	Log(formats)
	
	oc = ObjectContainer(view_group='InfoList', title2='View Torrent')
	
	for f in formats:
		obj = PopupDirectoryObject(
			key = Callback(PtpSelectFormat, format=f),
			title = f['name'],
			summary = 'ADDED: ' + f['added'] + ' / SIZE: ' + f['size'] + '\nSNATCHES: ' + f['snatches'] + ' / SEEDERS: ' + f['seeders'] + ' / LEECHERS: ' + f['leechers'],
			thumb = f['thumb']
		)
		
		oc.add(obj)
	
	return oc
	
#########################################################
def PtpSelectFormat(format):
	
	oc = ObjectContainer(
		view_group='List',
		objects = [
			DirectoryObject(
				key = Callback(PtpDownloadFormat, url=format['url']),
				title = L('Download')
			),
			DirectoryObject(
				key = Callback(PtpDownloadFormat, url=format['url']),
				title = L('Cancel')
			)
		]
	)
	
	return oc

#########################################################
def PtpDownloadFormat(url):
	return None


#########################################################
def PtpAccount(title):
	
	if not PtpLoggedIn():
		Log('Not Logged In')
		if not Prefs['username'] or not Prefs['password']:
			Log('Prefs Not Set')
			return ObjectContainer(header=L('Log-in Error'), message=L('Enter your username and password in the preferences section.'))
			
		PtpLogIn()
		
		if not PtpLoggedIn():
			Log('Log In Error')
			return ObjectContainer(header=L('Log-in Error'), message=L('Error logging in. Please check your username and password in the preferences section.'))
	
	html = HTML.ElementFromURL(PTP_URL, cacheTime=0)
	
	return ObjectContainer(header=L('Logged In'), message=L('Logged In!'))
	
#########################################################
def PtpLoggedIn():
	
	html = HTML.ElementFromURL(PTP_URL, cacheTime=0)
	
	print(html.xpath('//li[@id="nav_logout"]'))
	
	if len(html.xpath('//li[@id="nav_logout"]')) > 0:
		Log('Found at least one!')
		return True
		
	return False
	
#########################################################
def PtpLogIn():

	Log('<----- Attempting to log in ----->')
	
	post = {
		'username': Prefs['username'],
		'password': Prefs['password']
	}
	
	login = HTTP.Request(PTP_URL + 'ajax.php?action=login', post).content