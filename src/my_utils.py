import pandas as pd


##### Visualizzazione di un documento tramite doc_id
def stampa_info_doc(documents, triples, doc_id, text = False): 
	'''
	Dato il doc_id, visualizza i campi: one_sentence summary, Categoria, Range di Date 
	Poi visualizza le relazioni semantiche estrapolate dall'AI sul documento. 
	Se il documento è 'HOUSE_OVERSIGHT_013343', allora non stampa il testo 
	'''
	my_triples = triples[triples['doc_id'] == doc_id]
	my_document = documents[documents['doc_id'] == doc_id]
	print(25*'-' + f'{doc_id}' + 25*'-' + '\n')
	print(30*'*' + 'One Sentence Summary' + 30* '*')
	print(my_document['one_sentence_summary'].iloc[0])
	print(80*'*' + '\n\n')
	print(250*'*' + ' Information ' + 25*'*')
	print(f"Category: {my_document['category'].iloc[0]}")
	print(f"Data Range: From {my_document['date_range_earliest'].iloc[0]} to {my_document['date_range_latest'].iloc[0]}")
	print(80*'*' + '\n\n')
	print(25*'-' + 'Parsed Relations' + 25*'-' +'\n')
	print(f'We have found {len(my_triples)} semantic relations of the kind A did B to C\nWe are going to list them:')
	for i, triple in enumerate(my_triples.itertuples(index = False), start = 1):
		print('\n'+ 80*'*')
		print(25*'*' + f'The {i}-th Semantic Relation' + 25*'*')
		print(80*'*' + '\n')
		print(f'*The \033[1m actor\033[0m {triple.actor} \033[1m did \033[0m {triple.action} \033[1m to \033[0m {triple.target}')
		print(f'*Location: {triple.location}')
		print(f'*The tags are: {triple.triple_tags}')
		print('\n*The explicit topic is: \n')
		print(triple.explicit_topic)
		print('\n*The implicit topic is: \n')
		print(triple.implicit_topic)
	if (text): 
		print('\n' + 30*'-' + 'Full Text' + 30* '-')
		print(90*'*')
		print(my_document['full_text'].iloc[0])
	print(80*'*' + '\n' + 80*'*' + '\n'+  80*'*')

