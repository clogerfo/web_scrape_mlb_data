from bs4 import BeautifulSoup as soup
from urllib.request import urlopen as uReq
import datetime as dt
import re
import csv


#good to write a function similar to this for use in all webscraping projects
def bs_Read(url):
	working_url = url
	working_client = uReq(working_url)
	working_html = working_client.read()
	working_soup = soup(working_html, "html.parser")
	return working_soup

with open("2017_FA.csv", "w") as f:
	headers = ("FA_year", "name", "team", "position", "contractValue", 
		"contractDuration", "avg_war", "avg_games", "avg_pa/ip", "avg_k", "avg_b", "avg_babip",
		"OPS/FIP", "age", "BirthPlace", "experience", "college")

	output = csv.writer(f, delimiter=",")
	output.writerow(headers)


	"""
	my_url is starting URL, must be ESPN's MLB free agent list. Preferabally sorted in Dollar order
	This script scrapes one year of free agents at a time. the url format is as follows : 
	http://www.espn.com/mlb/freeagents/_/year/*ENTER-DESIRED-YEAR*/type/dollars
	"""
	my_url = "http://www.espn.com/mlb/freeagents/_/year/2017/type/dollars"



	#bs_Read returns soup object
	table = bs_Read(my_url).find('table',{'class':'tablehead'})
	trs = table.findAll('tr')	
	tds = trs[1].findAll('td')

	currentYear = int(dt.date.today().strftime("%Y"))

	faYear = tds[4].text.split(" ")
	faYear = int(faYear[0])

	year_diff = currentYear - faYear

	#avoided using tr in trs
	i = 2
	for tr in range(i, len(trs) - 1):
		validRow = True
		data = trs[tr].findAll('td')
		numA = data[0].findAll('a')

		if len(data) <= 1:
			validRow = False
		if len(numA) < 1:
			validRow = False

		if validRow == True:
			data = trs[tr].findAll('td')
			if len( data) > 1:
				name = data[0].text
				print( "{} : {}".format("current player being scraped", name) )

				position = data[1].text
				if position.find('P') > -1:
					position = "P"
				if position.find('F') > -1:
					position = "OF"


				#Scrape general contract info. 
				age = int(data[2].text) - year_diff
				newTeam = data[5].text
				years = data[6].text
				val = data[8].text

				#Scrape given player's personal profile.
				player_url = data[0].a['href']
				print(player_url)

				player_data = bs_Read(player_url).find('ul',{'class':'player-metadata floatleft'})
				try:
					lis = player_data.findAll('li')
				except Exception as e:
					print("{} : {}".format("Invalid player URL", e))
					string_to_add = "stats/_/"
					store_url = player_url.split('_/')
					new_url = store_url[0] + string_to_add + store_url[1]
					print("{} : {}".format("updated URL", new_url))
					player_data = bs_Read(new_url).find('ul',{'class':'player-metadata'})
					lis = player_data.findAll('li')

				"""
				Parse unique information for each player.
				birth place, years of experience (at time of contract), college
				"""
				birthPlace = lis[1].text
				birthPlace = birthPlace.replace('Birthplace', '')

				experience = lis[2].text
				experience = experience.replace('Experience', '')
				experience = int(experience.replace('years', '')) - year_diff

				college = lis[3].text
				college = college.replace('College', '')

				#store for future use before parsing name string
				testName = name

				#parse name string
				names = name.split(" ")
				firstName = names[0]

				#This parse will provide us a unique key (first 2 letters of the player's last name)
				#that is used to transfer from the player's ESPN page to their FanGraphs page
				lastName = names[1]#
				letters = lastName[:2]

				fgURL = "https://www.fangraphs.com/players.aspx"
				content = bs_Read(fgURL).find("div", {"id": "content"})

				aArray = content.findAll('a')
				key = letters

				for x in range(0,len(aArray)):
					if(key == aArray[x].text):
						playerlistURL = "https://www.fangraphs.com/" + aArray[x]['href']

				newContent = bs_Read(playerlistURL).find('div', {'id':'content'})
				allA = newContent.findAll('a')

				for x in range(0, len(allA)):
					if(testName == allA[x].text):
						if allA[x]['href'].find(position) > -1:
							newUrl = "https://www.fangraphs.com/" + allA[x]['href']			

				statTable = bs_Read(newUrl).findAll('table',{'class':'rgMasterTable'})

				if len(statTable[0].findAll('tr')) > 3:
					rows = statTable[0].findAll('tr')
				else :
					rows = statTable[1].findAll('tr')

				lowerSeason = faYear - 2
				validYears = lessValidYear = 0
				warSum = gamesSum = paSum = inningsSum =  0
				rate_BB = rate_K = babip = fip = ops = 0
				

				if(position != "P"):
					for r in rows:
						data = r.findAll('td')
						if len(data) == 21 and data[20].text != '\xa0':
							try:	
								currentSeason = int(data[0].text)
								currentTeam = data[1].text
							except Exception as e:
								print(e)

							if currentSeason <= faYear and currentSeason >= lowerSeason:
								if currentTeam.find('2') > -1:
									#player played for 2 teams this year
									lessValidYear += 1
								if currentTeam.find('3') > -1:
									#player played for 3 teams this year
									lessValidYear += 2

								"""
								scrape statistics : 
								WAR, games, plate appearances, innings pitched, babip
								walk rate, strikeout rate, fip, ops
								"""
								if currentTeam.find('2') == -1 and currentTeam.find('3') == -1:
									#cumulative sum war
									warSum = warSum + float(data[20].text)

									#cumulative sum games and plate appearances 
									gamesSum = gamesSum + float(data[2].text)
									paSum = paSum + float(data[3].text)
									
									#cumulative sum ops
									ops =  ops + (float(data[13].text) + float(data[14].text))

									#cumulative sum babip
									babip = babip + float(data[11].text)

									bb_string = k_string = None
									bb_num = k_num = 0

									#strip/parse walk and strikeout rates
									bb_string = data[8].text
									bb_num = float( re.sub('%','',bb_string))
									k_string = data[9].text
									k_num = float( re.sub('%','',k_string))

									#cumulative sum BB and K
									rate_BB = rate_BB + bb_num
									rate_K = rate_K + k_num

									#udpate the number of years we are averaging over
									validYears += 1	

					cumsumYears = validYears
					percentageYears = validYears

					"""
					Update the number of years we are averaging over. 
					If player played for multiple teams 1 year, this if-statement
					is needed to account for that when calculating average totals
					"""
					if lessValidYear > 0:
						cumsumYears = validYears - lessValidYear
					elif validYears == 0:
						#we've run into an error I cannot figure out. Make war high rather than skip player
						#so that we can see which players are incorrect in the final data set
						warSum = 9999
						validYears = 1
						cumsumYears = 1
						percentageYears = 1


					averageWar = round(warSum/cumsumYears,1)
					averageGame = round(gamesSum/cumsumYears,1)
					averagePA_IN = round(paSum/cumsumYears,1)
					averageOPS_FIP = round(ops/percentageYears,1)
					averageBABIP = round(babip/percentageYears,1)
					rate_K = round(rate_K/percentageYears,1)
					rate_BB = round(rate_BB/percentageYears,1)



				else:
					for r in rows:
						data = r.findAll('td')
						if len(data) == 19 and data[18].text != '\xa0':
							try:	
								currentSeason = float(data[0].text)
								currentTeam = data[1].text
							except Exception as e:
								print(e)
							
							#test if the row contains data from a season in our 3 year range
							if currentSeason <= faYear and currentSeason >= lowerSeason:
								if currentTeam.find('2') > -1:
									#player played for 2 teams this year
									lessValidYear += 1
								if currentTeam.find('3') > -1:
									#player played for 3 teams this year
									lessValidYear += 2
								if currentTeam.find('2') == -1 and currentTeam.find('3') == -1: 
									warSum = warSum + float(data[18].text)
									gamesSum = gamesSum + float(data[5].text)
									inningsSum = inningsSum + float(data[7].text)

									fip = fip + float(data[16].text)

									#cumulative sum babip
									babip = babip + float(data[11].text)

									bb_string = k_string = None
									bb_num = k_num = 0

									#strip/parse walk and strikeout rates
									bb_string = data[9].text
									bb_num = float( re.sub('%','',bb_string))
									k_string = data[8].text
									k_num = float( re.sub('%','',k_string))

									#cumulative sum BB and K
									rate_BB = rate_BB + bb_num
									rate_K = rate_K + k_num

									validYears += 1	

					cumsumYears = validYears
					percentageYears = validYears

					if lessValidYear > 0:
						totalYears = validYears
						cumsumYears = validYears - lessValidYear
					if validYears == 0:
						#we've run into an error I cannot figure out. Make war high rather than skip player
						#so that we can see which players are incorrect in the final data set
						warSum = 99999
						validYears = 1	
						cumsumYears = 1
						percentageYears = 1	

					averageWar = round(warSum/cumsumYears,1)
					averageGame = round(gamesSum/cumsumYears,1)
					averagePA_IN = round(inningsSum/cumsumYears,1)
					averageOPS_FIP = round(fip/percentageYears,1)
					averageBABIP = round(babip/percentageYears,1)
					rate_K = round(rate_K/percentageYears,1)
					rate_BB = round(rate_BB/percentageYears,1)

				output.writerow([
					faYear, name, newTeam, position, val, years, averageWar, 
					averageGame, averagePA_IN, rate_K, rate_BB, averageBABIP, 
					averageOPS_FIP, age, birthPlace, experience, college])