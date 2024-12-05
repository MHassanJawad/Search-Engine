lexicon = {}
    for word, word_data in lexicon_dict.items():
        word_obj = Word(word_data["word_id"])
        word_obj.frequency = word_data["frequency"]
        word_obj.doc_freq = word_data["doc_freq"]
        word_obj.documents = word_data["documents"]
        lexicon[word] = word_obj