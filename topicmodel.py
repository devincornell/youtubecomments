
import nltk
import sys

import semanticanalysis as sa
import pandas as pd

outdir = 'topicmodels_65k/'

df = pd.read_excel('comments/comments65k_3tmd-ClpJxA.xlsx')
ids = [str(c) for c in list(df['commentid'])]
texts = [str(t) for t in list(df['text'])]

bows = sa.tokenize_bow(texts)

cbows = sa.removewords(bows)

for Nt in range(10, 150, 10):
	
	# perform topic mdoel
	tm = sa.nmf(cbows, Nt, verbose=True)
	outfile = outdir+'nmf_'+str(Nt)+'.xlsx'
	tm.save_report(outfile, docnames=ids)
	print(outfile, 'saved.')
	
	tm = sa.lda(cbows, Nt, verbose=True)
	outfile = outdir+'lda_'+str(Nt)+'.xlsx'
	tm.save_report(outfile, docnames=ids)
	print(outfile, 'saved.')

