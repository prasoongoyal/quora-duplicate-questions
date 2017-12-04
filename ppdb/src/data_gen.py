# data_gen.py

from utils import *
import re
import numpy as np
import csv
import random

# Wraps a sequence of word indices with a 0-1 label (0 = negative, 1 = positive)
class QuestionPair:
    def __init__(self, indexed_q1, indexed_q2, label, dataset):
        self.indexed_q1 = indexed_q1
        self.indexed_q2 = indexed_q2
        self.label = label
        self.dataset = dataset

    def __repr__(self):
        return repr(self.indexed_q1) + "\t" + repr(self.indexed_q2) + "\t" + "; label=" + repr(self.label)

    def get_indexed_words_reversed(self):
        #returns a tuple of lists of reversed questions
        return ([self.indexed_q1[len(self.indexed_q1) - 1 - i] for i in xrange(0, len (self.indexed_q1))], 
                    [self.indexed_q2[len(self.indexed_q2) - 1 - i] for i in xrange(0, len (self.indexed_q2))])


# Reads sentiment examples in the format [0 or 1]<TAB>[raw sentence]; tokenizes and indexes the sentence according
# to the vocabulary in indexer. If add_to_indexer is False, replaces unseen words with UNK, otherwise grows the
# indexer. word_counter optionally keeps a tally of how many times each word is seen (mostly for logging purposes).
def read_and_index(infile, indexer, add_to_indexer=False, word_counter=None):
    exs = []
    maxi  = 0
    with open(infile) as tsvfile:
        tsvreader = csv.reader(tsvfile, delimiter="\t")
        col_names = next(tsvreader)
        for line in tsvreader:
            fields = line
            label = int(fields[-1])
            q1 = fields[-3]
            q2 = fields[-2]

            token_clean_q1 = filter(lambda x: x != '', clean_str(q1).rstrip().split(" "))
            token_clean_q2 = filter(lambda x: x != '', clean_str(q2).rstrip().split(" "))

            if word_counter is not None:
                for word in token_clean_q1:
                    word_counter.increment_count(word, 1.0)
                for word in token_clean_q2:
                    word_counter.increment_count(word, 1.0)
            
            indexed_q1 = [indexer.get_index(word) if indexer.contains(word) or add_to_indexer else indexer.get_index("UNK")
                for word in token_clean_q1]
            indexed_q2 = [indexer.get_index(word) if indexer.contains(word) or add_to_indexer else indexer.get_index("UNK")
                for word in token_clean_q2]

            if len(indexed_q1) > maxi:
                maxi = len(indexed_q1)
            if len(indexed_q2) > maxi:
                maxi = len(indexed_q2) 
            
            exs.append(QuestionPair(indexed_q1, indexed_q2, label, 'quora'))
    print maxi
    return exs


def read_and_index_ppdb(infile, indexer, add_to_indexer=False, word_counter=None):
    exs = []
    with open(infile) as tsvfile:
        tsvreader = csv.reader(tsvfile, delimiter="\t", quoting=csv.QUOTE_NONE)
        for line in tsvreader:
            try:
                #print line
                fields = line
                label = 1
                s1 = fields[0]
                s2 = fields[1]

                token_clean_s1 = filter(lambda x: x != '', clean_str(s1).rstrip().split())
                token_clean_s2 = filter(lambda x: x != '', clean_str(s2).rstrip().split())

                if word_counter is not None:
                    for word in token_clean_s1:
                        word_counter.increment_count(word, 1.0)
                    for word in token_clean_s2:
                        word_counter.increment_count(word, 1.0)
                indexed_s1 = [indexer.get_index(word) if indexer.contains(word) or add_to_indexer else indexer.get_index("UNK") for word in token_clean_s1]
                indexed_s2 = [indexer.get_index(word) if indexer.contains(word) or add_to_indexer else indexer.get_index("UNK") for word in token_clean_s2]
                
                if len(indexed_s1) > 0 and len(indexed_s2) > 0:
                    exs.append(QuestionPair(indexed_s1, indexed_s2, 1, 'ppdb'))
            except:
                pass

    # add random negative examples
    n_neg_exs = len(exs)
    for i in xrange(0, n_neg_exs):
        indexed_s1 = []
        indexed_s2 = []
        while len(indexed_s1) == 0 or len(indexed_s2) == 0:
            idx1 = np.random.randint(n_neg_exs)
            idx2 = np.random.randint(n_neg_exs)
            r1 = np.random.random()
            r2 = np.random.random()
            indexed_s1 = exs[idx1].indexed_q1 if r1<0.5 else exs[idx1].indexed_q2
            indexed_s2 = exs[idx2].indexed_q1 if r2<0.5 else exs[idx2].indexed_q2
        exs.append((QuestionPair(indexed_s1, indexed_s2, 0, 'ppdb')))

    random.shuffle(exs)
    return exs

# Writes sentiment examples to an output file in the same format they are read in. However, note that what gets written
# out is tokenized and contains UNKs, so this will not exactly match the input file.
def write_question_pairs(exs, outfile, indexer):
    o = open(outfile, 'w')
    for ex in exs:
        o.write(repr(ex.label) + "\t" + " ".join([indexer.get_object(idx) for idx in ex.indexed_words]) + "\n")
    o.close()


# Tokenizes and cleans a string: contractions are broken off from their base words, punctuation is broken out
# into its own token, junk characters are removed, etc.
def clean_str(string):
    # string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)
    string = re.sub(r"[^A-Za-z0-9(),.!?\'\`\-]", " ", string)
    string = re.sub(r"\'s", " \'s", string)
    string = re.sub(r"\'ve", " \'ve", string)
    string = re.sub(r"n\'t", " n\'t", string)
    string = re.sub(r"\'re", " \'re", string)
    string = re.sub(r"\'d", " \'d", string)
    string = re.sub(r"\'ll", " \'ll", string)
    string = re.sub(r",", " , ", string)
    string = re.sub(r"!", " ! ", string)
    string = re.sub(r"\(", " ( ", string)
    string = re.sub(r"\)", " ) ", string)
    string = re.sub(r"\?", " ? ", string)
    string = re.sub(r"\-", " - ", string)
    # We may have introduced double spaces, so collapse these down
    string = re.sub(r"\s{2,}", " ", string)
    return string


# Wraps an Indexer and a list of 1-D numpy arrays where each position in the list is the vector for the corresponding
# word in the indexer. The 0 vector is returned if an unknown word is queried.
class WordEmbeddings:
    def __init__(self, word_indexer, vectors):
        self.word_indexer = word_indexer
        self.vectors = vectors

    def get_embedding(self, word):
        word_idx = self.word_indexer.get_index(word)
        word_idx = int(word_idx)
        if word_idx != -1:
            return self.vectors[word_idx]
        else:
            return self.vectors[self.word_indexer.get_index("UNK")]

    def get_embedding_byidx(self, word_idx):
        #word_idx = self.word_indexer.get_index(word)
        word_idx = int(word_idx)
        if word_idx != -1:
            return self.vectors[word_idx]
        else:
            return self.vectors[self.word_indexer.get_index("UNK")]




# Loads the given embeddings (ASCII-formatted) into a WordEmbeddings object. Augments this with an UNK embedding
# that is the 0 vector. Reads in all embeddings with no filtering -- you should only use this for relativized
# word embedding files.
def read_word_embeddings(embeddings_file):
    f = open(embeddings_file)
    word_indexer = Indexer()
    vectors = []
    for line in f:
        if line.strip() != "":
            space_idx = line.find(' ')
            word = line[:space_idx]
            numbers = line[space_idx+1:]
            float_numbers = [float(number_str) for number_str in numbers.split()]
            #print repr(float_numbers)
            vector = np.array(float_numbers)
            word_indexer.get_index(word)
            vectors.append(vector)
            #print repr(word) + " : " + repr(vector)
    f.close()
    print "Read in " + repr(len(word_indexer)) + " vectors of size " + repr(vectors[0].shape[0])
    # Add an UNK token at the end
    word_indexer.get_index("UNK")
    vectors.append(np.zeros(vectors[0].shape[0]))
    # Turn vectors into a 2-D numpy array
    return WordEmbeddings(word_indexer, np.array(vectors))


#################
# You probably don't need to interact with this code unles you want to relativize other sets of embeddings
# to this data. Relativization = restrict the embeddings to only have words we actually need in order to save memory
# (but this requires looking at the data in advance).

# Relativize the word vectors to the training set
def relativize(file, outfile, indexer, word_counter):
    f = open(file)
    o = open(outfile, 'w')
    voc = []
    for line in f:
        word = line[:line.find(' ')]
        if indexer.contains(word):
            print "Keeping word vector for " + word
            voc.append(word)
            o.write(line)
    for word in indexer.objs_to_ints.keys():
        if word not in voc:
            print "Missing " + word + " with count " + repr(word_counter.get_count(word))
    f.close()
    o.close()


# Relativizes word embeddings to the datasets
if __name__ == '__main__':
    word_indexer = Indexer()
    # The counter is just to see what the counts of missed words are so we can evaluate our tokenization (whether
    # it's mismatched with the word vector vocabulary)
    data_path = "/Volumes/anikesh_hdd/"
    word_counter = Counter()
    read_and_index(data_path + "train.tsv",word_indexer, add_to_indexer=True, word_counter=word_counter)
    read_and_index(data_path + "test.tsv",word_indexer, add_to_indexer=True, word_counter=word_counter)
    
    #read_and_index_sentiment_examples("data/train.txt", word_indexer, add_to_indexer=True, word_counter=word_counter)
    #read_and_index_sentiment_examples("data/dev.txt", word_indexer, add_to_indexer=True, word_counter=word_counter)
    #read_and_index_sentiment_examples("data/test.txt", word_indexer, add_to_indexer=True, word_counter=word_counter)
    # Uncomment these to relativize vectors to the dataset
    #relativize("data/glove.6B/glove.6B.50d.txt", "data/glove.6B.50d-relativized2.txt", word_indexer, word_counter)
    #relativize("data/glove.6B/glove.6B.300d.txt", "data/glove.6B.300d-relativized.txt", word_indexer, word_counter)
