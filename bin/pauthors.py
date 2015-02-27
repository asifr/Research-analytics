#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from nltk import FreqDist, word_tokenize
import collections
import networkx as nx
from networkx.algorithms import bipartite
from unidecode import unidecode
from sys import exit
from operator import itemgetter

# Load all articles into pmdata
directory = '/Users/asif/Sites/scholars/data/'

def save_json(name, data):
	dest = os.path.join(directory, name+".json")
	f = open(dest, 'w+')
	f.write(json.dumps(data))
	f.close()

def load_dataset(term):
	# Load all articles into pmdata
	directory = '/Users/asif/Sites/scholars/data/%s/' % term
	data_files = [os.path.abspath(directory + '/' + f) for f in os.listdir(directory) if f.endswith('.json')]
	pmdata = []
	for x in xrange(0,len(data_files)):
		d = open(data_files[x])
		data = json.load(d)
		pmdata = pmdata + data
	return pmdata

tdcs = load_dataset('tdcs')
tacs = load_dataset('tacs')
tms = load_dataset('tms')
tes = load_dataset('tes')

Speakers=['Alonso-Alonso, M','Barrett, AM','Bestmann, S','Bikson, M','Carmel, J','Clark, V','Cortes, M','Coslett, HB','DaSilva, AF','Edwards, D','Fregni, F','Gillick, B','Ikonomidouni, C','Javitt, DC','Kappenman, ES','Kessler, SK','Kirton, A','Knotkova, H','Krekelberg, B','Martin, JH','McKinley, RA','Nitsche, MA','Parra, LC','Paulus, W','Reato, D','Richardson, JD','Rotenberg, A','Schlaug, G','Walsh, V','Woods, AJ']

totalPublications = 0
IntersectingPublications = {}
titles = []

for article in tdcs:
	if article['title'] != '':
		titles.append(article['title'])
		inters = list(set(Speakers).intersection(set(article['authors'])))
		if len(inters) > 0:
			IntersectingPublications[article['title']] = inters

for article in tacs:
	if article['title'] != '':
		titles.append(article['title'])
		inters = list(set(Speakers).intersection(set(article['authors'])))
		if len(inters) > 0:
			IntersectingPublications[article['title']] = inters

# for article in tes:
# 	if article['title'] != '':
# 		titles.append(article['title'])
# 		inters = list(set(Speakers).intersection(set(article['authors'])))
# 		if len(inters) > 0:
# 			IntersectingPublications[article['title']] = inters

# for article in tms:
# 	titles.append(article['title'])
# 	inters = list(set(Speakers).intersection(set(article['authors'])))
# 	if len(inters) > 0:
# 		IntersectingPublications[article['title']] = inters

uniqueTitles = list(set(titles))
print (len(IntersectingPublications),len(uniqueTitles))

# save_json("intersecting_speakers_publications",IntersectingPublications)

IntersectingTitles = IntersectingPublications.keys()
articles = []
for title in IntersectingTitles:
	try:
		articles.append(tdcs[map(itemgetter('title'),tdcs).index(title)])
	except Exception, e:
		continue
	try:
		articles.append(tacs[map(itemgetter('title'),tacs).index(title)])
	except Exception, e:
		continue
	try:
		articles.append(tes[map(itemgetter('title'),tes).index(title)])
	except Exception, e:
		continue

# dest = '/Users/asif/Sites/scholars/neuromodulation/intersecting_titles.json'
# f = open(dest, 'w+')
# f.write(json.dumps(IntersectingTitles))
# f.close()

# Group items
years = []
journals = []
journalsByYear = {}
authorsByJournalYear = {}
keywordsByJournalYear = {}
authors = []
keywords = []
titles = []
for x in xrange(0,len(articles)):
	if articles[x]['year'] != '':
		years.append(int(articles[x]['year']))
	if articles[x]['journal'] != '':
		journals.append(articles[x]['journal'])
		if articles[x]['year'] != '':
			if not journalsByYear.get(articles[x]['journal']):
				journalsByYear[articles[x]['journal']] = []
			journalsByYear[articles[x]['journal']].append(int(articles[x]['year']))
	if articles[x]['authors'] != '':
		authors.append(articles[x]['authors'])
		for y in articles[x]['authors']:
			if articles[x]['journal'] != '' and articles[x]['year'] != '':
				if not authorsByJournalYear.get(y):
					authorsByJournalYear[y] = []
				authorsByJournalYear[y].append([articles[x]['journal'], int(articles[x]['year'])])
	if 'keywords' in articles[x].keys() and articles[x]['keywords'] != '':
		if articles[x]['keywords']:
			keywords.append(articles[x]['keywords'])
			for y in articles[x]['keywords']:
				if articles[x]['journal'] != '' and articles[x]['year'] != '':
					if not keywordsByJournalYear.get(y):
						keywordsByJournalYear[y] = []
					keywordsByJournalYear[y].append([articles[x]['journal'], int(articles[x]['year'])])
	if articles[x]['title'] != '':
		titles.append(articles[x]['title'])

# Years
yearsCounter = collections.Counter(years).items()
yearsX = []
yearsY = []
for x in xrange(0,len(yearsCounter)):
	yearsX.append(yearsCounter[x][0]) # year
	yearsY.append(yearsCounter[x][1]) # count

# Authors
# authorsList = []
# for n in xrange(0,len(authors)):
# 	authorsList = authorsList + authors[n];
authorsList = Speakers
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
# dest = '/Users/asif/Sites/scholars/neuromodulation/years.json'
# f = open(dest, 'w+')
# f.write(json.dumps(yearsCounter))
# f.close()


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
		if sourceName in collaborators.keys():
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

# dest = '/Users/asif/Sites/scholars/neuromodulation/cooccurrences.json'
# f = open(dest, 'w+')
# f.write(json.dumps(cooccurrences))
# f.close()

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
		if name in collaborators.keys():
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

# dest = '/Users/asif/Sites/scholars/neuromodulation/collaborators_speakers.json'
# f = open(dest, 'w+')
# f.write(json.dumps(collab_bindings))
# f.close()

###########################################################
# Edge-bindings keywords
###########################################################

keyword_collaborators = collaborators_matrix(keywords)
collab_bindings = collaborators_bindings(keywordsCounter, keyword_collaborators)

# dest = '/Users/asif/Sites/scholars/neuromodulation/keyword_collaborators.json'
# f = open(dest, 'w+')
# f.write(json.dumps(collab_bindings))
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

# dest = '/Users/asif/Sites/scholars/neuromodulation/journals_yearly.json'
# f = open(dest, 'w+')
# f.write(json.dumps(j.yearly()))
# f.close()