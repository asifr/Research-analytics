#!/usr/bin/env python

import requests
from xml.dom import minidom
import json
import time
from sys import exit

term = 'transcranial electrical stimulation'

email = 'asiftr@gmail.com'
tool = 'pmidx'
database = 'pubmed'
retmax = 10
retmode = 'xml'
retstart = 0

def parse_xml(elm, idx, default):
	try:
		if idx != None:
			elm = elm[idx]
		elm = elm.childNodes[0].data
		return elm
	except Exception:
		elm = default
		return elm
		pass
	else:
		elm = default
		return elm

def text_output(xml,count):
	"""makes a simple text output from the XML retured from efetch"""
	xmldoc = minidom.parseString(xml.encode('utf-8').strip())

	jsonout = []
	for i in range(count):
		title = ''
		title = xmldoc.getElementsByTagName('ArticleTitle')
		title = parse_xml(title, i, '')

		pmid = ''
		pmid = xmldoc.getElementsByTagName('PMID')
		pmid = parse_xml(pmid, i, '')

		abstract = ''
		abstract = xmldoc.getElementsByTagName('AbstractText')
		abstract = parse_xml(abstract, i, '')

		try:
			authors = xmldoc.getElementsByTagName('AuthorList')
			authors = authors[i].getElementsByTagName('Author')

			authorlist = []
			for author in authors:
				LastName = author.getElementsByTagName('LastName')
				LastName = parse_xml(LastName, 0, '')
				Initials = author.getElementsByTagName('Initials')
				Initials = parse_xml(Initials, 0, '')
				if LastName != '' and Initials != '':
					author = '%s, %s' % (LastName, Initials)
				else:
					author = ''
				authorlist.append(author)
		except Exception:
			authorlist = []
			pass

		try:
			keywords = xmldoc.getElementsByTagName('KeywordList')
			keywords = keywords[i].getElementsByTagName('Keyword')

			keywordList = []
			for keyword in keywords:
				word = parse_xml(keyword, None, '')
				keywordList.append(word)
		except Exception:
			keywordList = []
			pass

		try:
			journalinfo = xmldoc.getElementsByTagName('Journal')[i]
			journalIssue = journalinfo.getElementsByTagName('JournalIssue')[0]
		except Exception:
			journalinfo = None
			journalIssue = None
			pass

		journal = ''
		year = ''
		volume = ''
		issue = ''
		pages = ''
		if journalinfo != None:
			journal = parse_xml(journalinfo.getElementsByTagName('Title'), 0, '')

			year = journalIssue.getElementsByTagName('Year')
			year = parse_xml(year, 0, '')
			volume = journalIssue.getElementsByTagName('Volume')
			volume = parse_xml(volume, 0, '')
			issue = journalIssue.getElementsByTagName('Issue')
			issue = parse_xml(issue, 0, '')
			pages = xmldoc.getElementsByTagName('MedlinePgn')
			pages = parse_xml(pages, 0, '')

		jsonout.append({
					'pmid':pmid,
					'title':title,
					'authors':authorlist,
					'keywords':keywordList,
					'journal':journal,
					'year':year,
					'volume':volume,
					'issue':issue,
					'pages':pages,
					'abstract':abstract
				})
	return json.dumps(jsonout)

utilsparams = {
	'db':database,
	'tool':tool,
	'email':email,
	'term':term,
	'usehistory':'y',
	'retmax':retmax,
	'retstart':retstart
}

url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'
r = requests.get(url, params = utilsparams)
data = r.text
xmldoc = minidom.parseString(data)
ids = xmldoc.getElementsByTagName('Id')

if len(ids) == 0:
	print 'QueryNotFound'
	exit()

count = xmldoc.getElementsByTagName('Count')[0].childNodes[0].data
itr = int(count)/retmax

dest = '/Users/Asif/Sites/scholars/data/tes.json'
f = open(dest, 'w+')
f.write(json.dumps({'term':term,'count':count,'mtime':int(time.time())}))
f.close()

for x in xrange(0,itr+1):
	retstart = x*10

	utilsparams['retstart'] = retstart

	url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?'
	r = requests.get(url, params = utilsparams)
	data = r.text
	xmldoc = minidom.parseString(data)
	ids = xmldoc.getElementsByTagName('Id')

	id = []
	for i in ids:
		id.append(i.childNodes[0].data)

	fetchparams = {
		'db':database,
		'tool':tool,
		'email':email,
		'id':','.join(id),
		'retmode':retmode
	}

	url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'
	r = requests.get(url, params = fetchparams)
	data = r.text

	s = text_output(data,retmax)
	dest = '/Users/Asif/Sites/scholars/data/tes/query_results_%i.json' % retstart
	f = open(dest, 'w+')
	f.write(s)
	f.close()