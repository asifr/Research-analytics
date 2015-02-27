#!/usr/bin/env python

import os
import json
from nltk import FreqDist, word_tokenize
import collections
import networkx as nx
from networkx.algorithms import bipartite

# Load all articles into pmdata
directory = '/Users/Asif/Sites/scholars/data/tacs/'
data_files = [os.path.abspath(directory + '/' + f) for f in os.listdir(directory) if f.endswith('.json')]
pmdata = []
for x in xrange(0,len(data_files)):
	d = open(data_files[x])
	data = json.load(d)
	pmdata = pmdata + data

# Load information about this dataset
d = open('/Users/Asif/Sites/scholars/data/tacs.json')
info = json.load(d)
term = info['term']
count = int(info['count'])

# Group items
years = []
journals = []
journalsByYear = {}
authorsByJournalYear = {}
authors = []
titles = []
for x in xrange(0,len(pmdata)):
	if pmdata[x]['year'] != '':
		years.append(int(pmdata[x]['year']))
	if pmdata[x]['journal'] != '':
		journals.append(pmdata[x]['journal'])
		if pmdata[x]['year'] != '':
			if not journalsByYear.get(pmdata[x]['journal']):
				journalsByYear[pmdata[x]['journal']] = []
			journalsByYear[pmdata[x]['journal']].append(int(pmdata[x]['year']))
	if pmdata[x]['authors'] != '':
		authors.append(pmdata[x]['authors'])
		for y in pmdata[x]['authors']:
			if pmdata[x]['journal'] != '' and pmdata[x]['year'] != '':
				if not authorsByJournalYear.get(y):
					authorsByJournalYear[y] = []
				authorsByJournalYear[y].append([pmdata[x]['journal'], int(pmdata[x]['year'])])
	if pmdata[x]['title'] != '':
		titles.append(pmdata[x]['title'])

# Years
yearsCounter = collections.Counter(years).items()
yearsX = []
yearsY = []
for x in xrange(0,len(yearsCounter)):
	yearsX.append(yearsCounter[x][0]) # year
	yearsY.append(yearsCounter[x][1]) # count

# Authors
authorsList = []
for n in xrange(0,len(authors)):
	authorsList = authorsList + authors[n];
authorsCounter = collections.Counter(authorsList) # sorted in most to least publications

# Journals that have become more popular over the years as indiccated by the number of
# publications per year over 8 years.
# Authors who frequently publish in the same journal can indicate bias.

# Journals
journalsCounter = collections.Counter(journals).items()
journalX = []
journalY = []
for x in xrange(0,len(journalsCounter)):
	journalX.append(journalsCounter[x][0]) # name
	journalY.append(journalsCounter[x][1]) # count

# Journals by year
journalsTabulated = {} # dict of journal names and number of publications over last 8 years
journalsRelations = []
mostfreq = collections.Counter(journals).most_common(20)
mostFreqJournalNames = [x[0] for x in mostfreq]
yr = range(2005,2013)
for journalname in journalsByYear:
	if journalname in mostFreqJournalNames:
		y = journalsByYear[journalname]
		c = collections.Counter(y)
		ci = c.items()
		journalsTabulated[journalname] = range(1)*len(yr) # last 8 years
		journalsRelations.append({
			'journalName': journalname,
			'publicationsByYear': ci
		})
		for i in xrange(0,len(ci)):
			if ci[i][0] in yr: # within the last 8 years
				journalsTabulated[journalname][yr.index(ci[i][0])] = ci[i][1]

# dest = '/Users/asif/Sites/pmidx/journals.json'
# f = open(dest, 'w+')
# f.write(json.dumps(journalsRelations))
# f.close()

journalsCSV = "Journal" + ",".join([str(i) for i in yr]) + "\n"
for journalname in journalsTabulated:
	journalsCSV += journalname + "," + ",".join([str(i) for i in journalsTabulated[journalname]]) + "\n"

# dest = '/Users/asif/Sites/pmidx/journals.csv'
# f = open(dest, 'w+')
# f.write(journalsCSV)
# f.close()

# Tokenized titles
tokenized_titles = []
tokenized_titles = [word_tokenize(titles[x]) for x in xrange(0,len(titles))]
tkTitlesList = []
for n in xrange(0,len(tokenized_titles)):
	tkTitlesList = tkTitlesList + tokenized_titles[n]
stops=['a','the','had','.','(',')','and','of',':',',','in','[',']','for','by','--','?','an','\'','\'s','to','on','is','as','from','-','at','can','does','or','but','use','its','with','using','during']
tokenizedTitles = [token.lower() for token in tkTitlesList if token.lower() not in stops]
fdist = FreqDist(tokenizedTitles)
sortedTitleWords = fdist.keys()
sortedTitleProb = [fdist.freq(token) for token in sortedTitleWords]
sortedTitleN = fdist.N()
sortedTitleCounts = [int(prob*sortedTitleN) for prob in sortedTitleProb]
titlesCounter = {}
for x in xrange(0,60):
	titlesCounter[sortedTitleWords[x]] = sortedTitleCounts[x]

# Returns collaborators as a dictionary matrix
def collaborators_matrix(authors):
	coll = {}
	for x in xrange(0,len(authors)):
		if authors[x]:
			for y in xrange(0,len(authors[x])):
				for z in xrange(0,len(authors[x])):
					if authors[x][y] != authors[x][z]:
						if authors[x][y] in coll.keys(): # first author
							if authors[x][z] not in coll[authors[x][y]].keys():
								coll[authors[x][y]][authors[x][z]] = 0
							coll[authors[x][y]][authors[x][z]] += 1
						else:
							coll[authors[x][y]] = {}
							coll[authors[x][y]][authors[x][z]] = 1
	return coll

# Edge bindings
def collaborators_bindings(authorsCounter, collaborators):
	mostfreq = [x[0] for x in authorsCounter.most_common(50)]
	collaborators_bindings = []
	for name in mostfreq:
		collabAuthors = []
		size = 0 # size is the total coauthorship count
		for (collabName, count) in collaborators[name].items():
			if collabName in mostfreq:
				size += count
				collabAuthors.append(collabName)
		if size > 0:
			collaborators_bindings.append({
				'name':name,
				'size':size,
				'collaborators':collabAuthors
			})
	return collaborators_bindings

# Co-occurrence matrix
def cooccurrence_links(authorsCounter, collaborators, maxAuthors):
	links = []
	for sourceName in topAuthorNames:
		collab = collaborators[sourceName]
		for (collabName, count) in collab.items():
			if  collabName in topAuthorNames:
				G.add_edge(sourceName, collabName, weight=count) # assign edges and weights
				links.append({
					'source':topAuthorNames.index(sourceName),
					'target':topAuthorNames.index(collabName),
					'value':count
				})
	return links

def cooccurrence_nodes(authorsCounter, maxAuthors, communities = []):
	nodes = []
	for name in topAuthorNames:
		g = 0
		for c in communities:
			if name in c:
				nodes.append({
					'name':name,
					'group':g
				})
			g = g + 1
	return nodes

# collaborators = collaborators_matrix(authors)
# collaborators_bindings = collaborators_bindings(authorsCounter, collaborators)

# dest = '/Users/Asif/Sites/pmidx/collaborators.json'
# f = open(dest, 'w+')
# f.write(json.dumps(collaborators_bindings))
# f.close()

# G = nx.Graph()
# topAuthorNames = [a[0] for a in authorsCounter.most_common(40)] # top 40 authors
# G.add_nodes_from(topAuthorNames) # assign nodes, edges are assigned in cooccurrence_links()

# cooccurrences = {'nodes':[], 'links':[]}
# cooccurrences['links'] = cooccurrence_links(authorsCounter, collaborators, 40)

# communities=list(nx.k_clique_communities(G,3)) # detect communities and than assign groups
# cooccurrences['nodes'] = cooccurrence_nodes(authorsCounter, 40, communities)

# dest = '/Users/Asif/Sites/pmidx/miserables.json'
# f = open(dest, 'w+')
# f.write(json.dumps(cooccurrences))
# f.close()


title_cooccurrences = {'nodes':[], 'links':[]}
# title_cooccurrences['links'] = title_cooccurrence_links(authorsCounter, collaborators, 40)

# dest = '/Users/Asif/Sites/pmidx/miserables_titles.json'
# f = open(dest, 'w+')
# f.write(json.dumps(title_cooccurrences))
# f.close()

# Results
# out = {
# 	'term':term,
# 	'numResults':count,
# 	'authorsDict':authorsCounter,
# 	'journalNames':journalX,
# 	'journalCounts':journalY,
# 	'years':yearsX,
# 	'yearsCounts':yearsY,
# 	'titles':titles,
# 	'sortedTokenizedTitleWords':sortedTitleWords,
# 	'sortedTokenizedTitleProb':sortedTitleProb,
# 	'sortedTitleN':sortedTitleN,
# 	'sortedTitleCounts':sortedTitleCounts
# }
# dest = '/Users/Asif/Sites/pmidx/results.json'
# f = open(dest, 'w+')
# f.write(json.dumps(out))
# f.close()