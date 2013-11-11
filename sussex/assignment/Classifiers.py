'''
Created on Nov 5, 2013

@author: haines
'''
from nltk.classify import NaiveBayesClassifier
from random import random
from nltk.classify.api import ClassifierI

class SupervisedBinaryClassifierFactory(object):
    
    def __init__(self, name):
        self._name = name;
        
    def getName(self):
        return self._name;
    
    def train(self, positiveTrainingDocuments, negativeTrainingDocuments):
        raise NotImplementedError()
    

class Classifier(object):
    
    def __init__(self, name):
        self._name = name;
    
    def getName(self):
        return self._name;
    
    def classify(self, documents):
        raise NotImplementedError()
        
class NltkIClassifierClassifierFactory(SupervisedBinaryClassifierFactory):
    
    def __init__(self, name, featureSetExtractor):
        SupervisedBinaryClassifierFactory.__init__(self, "%s@%s" % (name,featureSetExtractor.getDescription() if featureSetExtractor is not None else ''))
        self._featureSetExtractor = featureSetExtractor;
        
    def train(self, trainingDocuments):
        
        features = self._formatData(trainingDocuments);
        
        return self.trainOnFeatures(features);
        
    def trainOnFeatures(self, features):
        raise NotImplementedError()
    
    def _formatData(self, classifiedDocuments):
        
        data = [];
        for classifiedDocument in classifiedDocuments:
            label = classifiedDocument.getClassification();
            if self._featureSetExtractor is None: #If a feature extraction function is not provided, use simply the words of the review as features
                data += [(dict([(feature, True) for feature in review.words()]), label) for review in classifiedDocument.getDocuments()] 
            else:
                data += [(dict([(feature, True) for feature in self._featureSetExtractor.extract(review.words())]), label) for review in classifiedDocument.getDocuments()]
                
        return data
    
class NltkNaiveBayesClassifierFactory(NltkIClassifierClassifierFactory):
    
    def __init__(self, featureSetExtractor):
        
        NltkIClassifierClassifierFactory.__init__(self, 'NaiveBayes', featureSetExtractor)
        
    def trainOnFeatures(self, features):
        
        return NltkClassifierTransformer(NaiveBayesClassifier.train(features), self);
    
class NltkClassifierTransformer(ClassifierI):
    
    def __init__(self, delegate, nltkIClassifierClassifierFactory):
        self._delegate = delegate;
        self._nltkIClassifierClassifierFactory = nltkIClassifierClassifierFactory;
        self._name = nltkIClassifierClassifierFactory.getName();
        
    def batch_classify(self, documents):
        words = self._nltkIClassifierClassifierFactory._formatData(documents);
        
        return [self._delegate.batch_classify([fs for (fs,l) in words]), words];
        
    def getName(self):
        return self._name;
        
class SimpleWordCountClassifierFactory(NltkIClassifierClassifierFactory):
    
    def __init__(self, featureSetExtractor, positiveLabel, negativeLabel, simpleWordTrainingFilter):
        NltkIClassifierClassifierFactory.__init__(self, 'SimpleCountClassifier['+simpleWordTrainingFilter.__class__.__name__+']', featureSetExtractor)
        self._positiveLabel = positiveLabel;
        self._negativeLabel = negativeLabel;
        self._simpleWordTrainingFilter = simpleWordTrainingFilter;
   
    def trainOnFeatures(self, features):
        
        return NltkClassifierTransformer(SimpleWordCountClassifier.train(features, self._positiveLabel, self._negativeLabel, self._simpleWordTrainingFilter, self._featureSetExtractor), self)

class SimpleWordCountClassifier(ClassifierI): 
 
    @staticmethod
    def train(labeledFeaturesets, positiveLabel, negativeLabel, simpleWordTrainingFilter, featureSetExtractor):
        
        positiveWords = [word for word,label in labeledFeaturesets if label == positiveLabel];
        negativeWords = [word for word,label in labeledFeaturesets if label == negativeLabel];
        
        positiveWords = simpleWordTrainingFilter.getPositiveWordsToTrain(positiveWords);
        negativeWords = simpleWordTrainingFilter.getNegativeWordsToTrain(negativeWords);
        
        return SimpleWordCountClassifier(positiveWords, negativeWords, featureSetExtractor);
    
    def __init__(self, pos, neg, featureSetExtractor): 
        self._pos = pos 
        self._neg = neg
        self._featureSetExtractor = featureSetExtractor;
 
    def classify(self, words): 
        score = 0 
        
        words = words.keys();
        if (self._featureSetExtractor is not None):
            words = self._featureSetExtractor.extract(words);
            
        for pos_word in self._pos: 
            score += words.count(pos_word) 
        for neg_word in self._neg: 
            score -= words.count(neg_word) 
        if score == 0:
            score = random() - 0.5
        return "NEG" if score < 0 else "POS" 
 
    def batch_classify(self, docs): 
        return [self.classify(doc) for doc in docs] 
 
    def labels(self): 
        return ("POS", "NEG")
    
class StaticWordListTrainingFeatureFilter(object):
    
    def __init__(self, positiveWords, negativeWords):
        self._positiveWords = positiveWords;
        self._negativeWords = negativeWords;
        
    def getPositiveWordsToTrain(self, positiveWords):
        return self._positiveWords;
    
    def getNegativeWordsToTrain(self, negativeWords):
        return self._negativeWords;

def get_all_words(words):
    return reduce(lambda words,review: words + list(word.lower() for word in words), words, [])

from nltk.probability import FreqDist

class TopRankedNWordsTrainingFeatureFilter():
    
    def __init__(self, n):
        self._n = n;
    
    def getPositiveWordsToTrain(self, positiveWords):
        pos_book_freqdist = FreqDist(get_all_words(positiveWords))
        
        return pos_book_freqdist.keys()[:self._n];
    
    def getNegativeWordsToTrain(self, negativeWords):
        neg_book_freqdist = FreqDist(get_all_words(negativeWords))
        
        return neg_book_freqdist.keys()[:self._n];
        
        
class TopFrequencyWordTrainingFeatureFilter():
    
    def __init__(self, n):
        self.n = n;
        
    def getPositiveWordsToTrain(self, positiveWords):
        pos_book_freqdist = FreqDist(get_all_words(positiveWords))
        
        return [word for word,count in pos_book_freqdist.iteritems() if count > self.n]
    
    def getNegativeWordsToTrain(self, negativeWords):
        neg_book_freqdist = FreqDist(get_all_words(negativeWords))
        
        return [word for word,count in neg_book_freqdist.iteritems() if count > self.n]
    
class NltkStemmerFeatureExtractor():
    
    def __init__(self, stemmer, stopList):
        self._stemmer = stemmer;
        self._stopList = [stemmer.stem(word) for word in stopList];
        
    def extract(self, words):
        return [self._stemmer.stem(word) for word in words if self._stemmer.stem(word) not in self._stopList];
    
    def getDescription(self):
        return 'nltk<%s>' % self._stemmer.__class__.__name__;
    
class SimpleFeatureExtractor():

    def __init__(self, stopList):
        self._stopList = [];
        self._stopList = self.extract(stopList);
        
    def extract(self, words):
        return ["NUM" if word.isdigit() else word.lower() for word in words if word not in self._stopList and word.isalpha()];
    
    def getDescription(self):
        return 'SimpleExtractor';