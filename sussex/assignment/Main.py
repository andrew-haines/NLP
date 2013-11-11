'''
Created on Nov 5, 2013

@author: haines
'''

from Classifiers import NltkNaiveBayesClassifierFactory;
from Classifiers import SimpleWordCountClassifierFactory;
from Classifiers import StaticWordListTrainingFeatureFilter;
from Classifiers import TopRankedNWordsTrainingFeatureFilter;
from Classifiers import TopFrequencyWordTrainingFeatureFilter;
from Classifiers import SimpleFeatureExtractor;
from Classifiers import NltkStemmerFeatureExtractor;
from Dataset import ClassifiedDataset;
from Report import Report
from sussex_nltk.corpus_readers import AmazonReviewCorpusReader
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer;
from nltk.stem import LancasterStemmer;

staticPositiveWords = ["happy","splendid","resplendent","splendiferous", "great", "excellent", "brilliant", "best", "super", "fantastic", "incredible", "amazing", "awesome", "amazing", "good", "spectacular", "fabulous", "marvelous", "wonderful"]
staticNegativeWords = ["mediocre","paltry","inconsequential", "awful", "rubbish", "terrible", "appalling", "worst", "crap", "bad", "nonsense", "unhappy", "nightmare", "dreadful", "redundant", "obsolete", "trash"];
stopList = stopwords.words('english') + ["book", "books", "the", ".", ",", "``"];

# first create our classifier factories

factories = [
            NltkNaiveBayesClassifierFactory(None),
            NltkNaiveBayesClassifierFactory(NltkStemmerFeatureExtractor(PorterStemmer(), stopList)),
            NltkNaiveBayesClassifierFactory(NltkStemmerFeatureExtractor(LancasterStemmer(), stopList)),
            NltkNaiveBayesClassifierFactory(SimpleFeatureExtractor(stopList)),
            SimpleWordCountClassifierFactory(None, 'POS', 'NEG', StaticWordListTrainingFeatureFilter(staticPositiveWords, staticNegativeWords)),
            SimpleWordCountClassifierFactory(NltkStemmerFeatureExtractor(PorterStemmer(), stopList), 'POS', 'NEG', StaticWordListTrainingFeatureFilter(staticPositiveWords, staticNegativeWords)),
            SimpleWordCountClassifierFactory(NltkStemmerFeatureExtractor(LancasterStemmer(), stopList), 'POS', 'NEG', StaticWordListTrainingFeatureFilter(staticPositiveWords, staticNegativeWords)),
            SimpleWordCountClassifierFactory(SimpleFeatureExtractor(stopList), 'POS', 'NEG', StaticWordListTrainingFeatureFilter(staticPositiveWords, staticNegativeWords)),
            SimpleWordCountClassifierFactory(None, 'POS', 'NEG', TopRankedNWordsTrainingFeatureFilter(500)),
            SimpleWordCountClassifierFactory(NltkStemmerFeatureExtractor(PorterStemmer(), stopList), 'POS', 'NEG', TopRankedNWordsTrainingFeatureFilter(500)),
            SimpleWordCountClassifierFactory(NltkStemmerFeatureExtractor(LancasterStemmer(), stopList), 'POS', 'NEG', TopRankedNWordsTrainingFeatureFilter(500)),
            SimpleWordCountClassifierFactory(SimpleFeatureExtractor(stopList), 'POS', 'NEG', TopRankedNWordsTrainingFeatureFilter(500)),
            SimpleWordCountClassifierFactory(None, 'POS', 'NEG', TopFrequencyWordTrainingFeatureFilter(30)),
            SimpleWordCountClassifierFactory(NltkStemmerFeatureExtractor(PorterStemmer(), stopList), 'POS', 'NEG', TopFrequencyWordTrainingFeatureFilter(30)),
            SimpleWordCountClassifierFactory(NltkStemmerFeatureExtractor(LancasterStemmer(), stopList), 'POS', 'NEG', TopFrequencyWordTrainingFeatureFilter(30)),
            SimpleWordCountClassifierFactory(SimpleFeatureExtractor(stopList), 'POS', 'NEG', TopFrequencyWordTrainingFeatureFilter(30))
             ]

def getAllClassifiedReviews(reader, category):
    
    generator = reader.category(category);
    positiveReviews = generator.positive().documents();
    negativeReviews = generator.negative().documents();
    unlabeledReviews = generator.unlabeled().documents();
    
    return (list(positiveReviews) + list([r for r in unlabeledReviews if r.rating() > 4.9 ]),
            list(negativeReviews) + list([r for r in unlabeledReviews if r.rating() < 1.1 ]));
            
def runTestsAndPrintReport(trainingCategories, testingCategories):
    
    allPositiveTrainingReviews = list();
    allNegativeTrainingReviews = list();
    allPositiveTestingReviews = list();
    allNegativeTestingReviews = list();
    
    for category in trainingCategories:
        (allPositiveTrainingReviewsTmp, allNegativeTrainingReviewsTmp) = getAllClassifiedReviews(AmazonReviewCorpusReader(), category)
        allPositiveTrainingReviews += allPositiveTrainingReviewsTmp;
        allNegativeTrainingReviews += allNegativeTrainingReviewsTmp;
    
    for category in testingCategories:
        (allPositiveTestingReviewsTmp, allNegativeTestingReviewsTmp) = getAllClassifiedReviews(AmazonReviewCorpusReader(), category)
        allPositiveTestingReviews += allPositiveTestingReviewsTmp;
        allNegativeTestingReviews += allNegativeTestingReviewsTmp;
    
    datasets = [ClassifiedDataset(0.1, 'POS', allPositiveTrainingReviews, allPositiveTestingReviews),
            ClassifiedDataset(0.1, 'NEG', allNegativeTrainingReviews, allNegativeTestingReviews)
            ]
    
    print 'training: %s vs testing: %s' % (trainingCategories, testingCategories);

    report = Report(datasets, factories)
    
    reportStats = report.getReport();
    
    Report.printReport(reportStats);
    
    #Report.showGraph(reportStats, "train %s vs test %s"%(trainingCategories, testingCategories));


book_reader = AmazonReviewCorpusReader()

runTestsAndPrintReport(['book'], ['book']);
runTestsAndPrintReport(['book', 'electronics'], ['book']);
runTestsAndPrintReport(['book', 'electronics', 'kitchen'], ['book']);
runTestsAndPrintReport(['book', 'electronics', 'kitchen', 'dvd'], ['book']);

runTestsAndPrintReport(['electronics'], ['book']);
runTestsAndPrintReport(['kitchen'], ['book']);
runTestsAndPrintReport(['dvd'], ['book']);

runTestsAndPrintReport(['book', 'electronics', 'kitchen', 'dvd'], ['book', 'electronics', 'kitchen', 'dvd']);