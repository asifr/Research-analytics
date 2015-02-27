from time import sleep
import os, sys, requests, re, json
from bs4 import BeautifulSoup
import urllib

chars = {
	'\xc2\x82' : ',',        # High code comma
	'\xc2\x84' : ',,',       # High code double comma
	'\xc2\x85' : '...',      # Tripple dot
	'\xc2\x88' : '^',        # High carat
	'\xc2\x91' : '\x27',     # Forward single quote
	'\xc2\x92' : '\x27',     # Reverse single quote
	'\xc2\x93' : '\x22',     # Forward double quote
	'\xc2\x94' : '\x22',     # Reverse double quote
	'\xc2\x95' : ' ',
	'\xc2\x96' : '-',        # High hyphen
	'\xc2\x97' : '--',       # Double hyphen
	'\xc2\x99' : ' ',
	'\xc2\xa0' : ' ',
	'\xc2\xa6' : '|',        # Split vertical bar
	'\xc2\xab' : '<<',       # Double less than
	'\xc2\xbb' : '>>',       # Double greater than
	'\xc2\xbc' : '1/4',      # one quarter
	'\xc2\xbd' : '1/2',      # one half
	'\xc2\xbe' : '3/4',      # three quarters
	'\xca\xbf' : '\x27',     # c-single quote
	'\xcc\xa8' : '',         # modifier - under curve
	'\xcc\xb1' : ''          # modifier - under line
}
def replace_chars(match):
	char = match.group(0)
	return chars[char]

d = open('/Users/asif/Sites/scholars/data/intersecting_titles.json')
ititles = json.load(d)

x=53
for title in ititles:
	baseurl = "http://scholar.google.com/scholar?hl=en&q=%s&btnG=Search"
	r = requests.get(baseurl % urllib.quote_plus(title))

	html = re.sub('(' + '|'.join(chars.keys()) + ')', replace_chars, r.text)

	dest = '/Users/asif/Sites/scholars/data/nycneurocitations/results_%s.html' % x
	f = open(dest, 'w+')
	f.write(html.encode('utf8'))
	f.close()

	x=x+1
	sleep(60) # be kind

# f = open('/Users/Asif/Sites/scholars/data/results.html')
# html = re.sub('(' + '|'.join(chars.keys()) + ')', replace_chars, f.read())
# soup = BeautifulSoup(html, "lxml")

# titles = soup.find_all(class_="gs_rt")
# citations = soup.find_all(class_="gs_fl")

# title = titles[0].find('a').text
# citedby = int(re.sub('Cited by ','',citations[1].find('a').text))
