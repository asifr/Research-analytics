#!/usr/bin/env python

import os
import json
from nltk import FreqDist, word_tokenize
import collections
import networkx as nx
from networkx.algorithms import bipartite
from unidecode import unidecode
from sys import exit

def save_json(name, data):
	dest = os.path.join(directory, name+".json")
	f = open(dest, 'w+')
	f.write(json.dumps(data))
	f.close()

# Load all articles into pmdata
directory = '/Users/asif/Sites/scholars/data/tdcs/'
data_files = [os.path.abspath(directory + '/' + f) for f in os.listdir(directory) if f.endswith('.json')]
pmdata = []
for x in xrange(0,len(data_files)):
	d = open(data_files[x])
	data = json.load(d)
	pmdata = pmdata + data

# Load information about this dataset
d = open('/Users/asif/Sites/scholars/data/tdcs.json')
info = json.load(d)
term = info['term']
count = int(info['count'])

# Group items
years = []
journals = []
journalsByYear = {}
authorsByJournalYear = {}
keywordsByJournalYear = {}
authors = []
keywords = []
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
	if pmdata[x]['keywords'] != '':
		if pmdata[x]['keywords']:
			keywords.append(pmdata[x]['keywords'])
			for y in pmdata[x]['keywords']:
				if pmdata[x]['journal'] != '' and pmdata[x]['year'] != '':
					if not keywordsByJournalYear.get(y):
						keywordsByJournalYear[y] = []
					keywordsByJournalYear[y].append([pmdata[x]['journal'], int(pmdata[x]['year'])])
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
authorsCounter = collections.Counter(authorsList) # sorted from most to least publications

# Keywords
keywordsList = []
for n in xrange(0,len(keywords)):
	keywordsList = keywordsList + keywords[n];
keywordsCounter = collections.Counter(keywordsList) # sorted from most to least publications

###########################################################
# Publications per year
###########################################################

# Save publications per year
dest = '/Users/asif/Sites/scholars/data/tdcs_years.json'
f = open(dest, 'w+')
f.write(json.dumps(yearsCounter))
f.close()

###########################################################
# Co-occurrences
###########################################################

# Returns collaborators as a dictionary matrix
# first argument groups is either authors or keywords
def collaborators_matrix(groups):
	coll = {}
	for x in xrange(0,len(groups)):
		if groups[x]:
			for y in xrange(0,len(groups[x])):
				for z in xrange(0,len(groups[x])):
					if groups[x][y] != groups[x][z]:
						if groups[x][y] in coll.keys(): # first author
							if groups[x][z] not in coll[groups[x][y]].keys():
								coll[groups[x][y]][groups[x][z]] = 0
							coll[groups[x][y]][groups[x][z]] += 1
						else:
							coll[groups[x][y]] = {}
							coll[groups[x][y]][groups[x][z]] = 1
	return coll

# Co-occurrence links
def cooccurrence_links(authorsCounter, collaborators):
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

G = nx.Graph()
topAuthorNames = [a[0] for a in authorsCounter.most_common(50)] # top 40 authors
G.add_nodes_from(topAuthorNames) # assign nodes, edges are assigned in cooccurrence_links()
collaborators = collaborators_matrix(authors)
cooccurrences = {'nodes':[], 'links':[]}
cooccurrences['links'] = cooccurrence_links(authorsCounter, collaborators)
communities=list(nx.k_clique_communities(G,3)) # detect communities and than assign groups
cooccurrences['nodes'] = cooccurrence_nodes(authorsCounter, 50, communities)

dest = '/Users/asif/Sites/scholars/data/tdcs-cooccurrences.json'
f = open(dest, 'w+')
f.write(json.dumps(cooccurrences))
f.close()

###########################################################
# Edge-bindings collaborators
###########################################################

# Edge bindings
def collaborators_bindings(groupCounters, collaborators):
	mostfreq = [x[0] for x in groupCounters.most_common(50)]
	collaborators_bindings = []
	for name in mostfreq:
		collabGroup = []
		size = 0 # size is the total coauthorship count
		for (collabName, count) in collaborators[name].items():
			if collabName in mostfreq:
				size += count
				collabGroup.append(collabName)
		if size > 0:
			collaborators_bindings.append({
				'name':name,
				'size':size,
				'collaborators':collabGroup
			})
	return collaborators_bindings

collab_bindings = collaborators_bindings(authorsCounter, collaborators)

dest = '/Users/asif/Sites/scholars/tdcs/collaborators.json'
f = open(dest, 'w+')
f.write(json.dumps(collab_bindings))
f.close()

###########################################################
# Edge-bindings keywords
###########################################################

keyword_collaborators = collaborators_matrix(keywords)
collab_bindings = collaborators_bindings(keywordsCounter, keyword_collaborators)

dest = '/Users/asif/Sites/scholars/tdcs/keyword_collaborators.json'
f = open(dest, 'w+')
f.write(json.dumps(collab_bindings))
f.close()

###########################################################
# Journals over time
###########################################################

journalsCounter = collections.Counter(journals).items()
journalX = []
journalY = []
for x in xrange(0,len(journalsCounter)):
	journalX.append(journalsCounter[x][0]) # name
	journalY.append(journalsCounter[x][1]) # count

# Journals by year
journalsTabulatedScatter = [] 
journalsTabulatedDonut = {} # dict of journal names and number of publications over last 8 years
journalsRelations = []
mostfreq = collections.Counter(journals).most_common(40)
mostFreqJournalNames = [x[0] for x in mostfreq]
yr = range(min(years),max(years))
for journalname in journalsByYear:
	if journalname in mostFreqJournalNames:
		y = journalsByYear[journalname]
		c = collections.Counter(y)
		ci = c.items()
		for i in xrange(0,len(ci)):
			journalsTabulatedScatter.append({
				'journal': journalname,
				'year': ci[i][0],
				'articles': ci[i][1]
			})
		children = []
		for i in xrange(0,len(ci)):
			children.append({
				'name': ci[i][0],
				'size': ci[i][1]
			})
		journalsRelations.append({
			'name': journalname,
			'chidlren': children
		})
		# journalsTabulatedDonut[journalname] = range(1)*len(yr) # last 8 years
		# for i in xrange(0,len(ci)):
		# 	if ci[i][0] in yr: # within the last n years
		# 		journalsTabulatedDonut[journalname][yr.index(ci[i][0])] = ci[i][1]

# dest = '/Users/asif/Sites/scholars/data/tdcs-journals-years-scatter.json'
# f = open(dest, 'w+')
# f.write(json.dumps(journalsTabulatedScatter))
# f.close()

# dest = '/Users/asif/Sites/scholars/data/tdcs-journals-years-relations.json'
# f = open(dest, 'w+')
# f.write(json.dumps(journalsRelations))
# f.close()

# exit(0)

# journalsCSV = "Journal," + ",".join([str(i) for i in yr]) + "\n"
# for journalname in journalsTabulatedDonut:
# 	journalsCSV += unidecode(journalname) + "," + ",".join([str(i) for i in journalsTabulatedDonut[journalname]]) + "\n"
# dest = '/Users/asif/Sites/scholars/data/tacs-journals-years-donut.json'
# f = open(dest, 'w+')
# f.write(journalsCSV)
# f.close()

###########################################################
# Journals over time
###########################################################
class Journals(object):
	limit = 30

	def __init__(self, journals, journalsByYear):
		super(Journals, self).__init__()
		self.journals = journals
		self.journalsByYear = journalsByYear

	def yearly(self):
		yearly = []
		mostfreq = collections.Counter(self.journals).most_common(self.limit)
		mostFreqJournalNames = [x[0] for x in mostfreq]
		idx=0
		for journalName in mostFreqJournalNames:
			c = collections.Counter(self.journalsByYear[journalName])
			ci = c.items()
			yearly.append({
				'name': journalName,
				'articles': ci,
				'total': mostfreq[idx][1]
			})
			idx+=1
		return yearly

j = Journals(journals, journalsByYear)
save_json("journals_tdcs",j.yearly())

