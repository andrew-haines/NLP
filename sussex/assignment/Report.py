'''
Created on Nov 5, 2013

@author: haines
'''

import numpy as np
import matplotlib.pyplot as plt
class Report(object):

    def __init__(self, classifiedDatasets, supervisedClassifierFactories):
        
        if (len(classifiedDatasets) < 2):
            raise Exception('We need at least 2 classified datasets to train with');
        
        currentMaxSize = classifiedDatasets[0].getNumBuckets();
        
        for dataset in classifiedDatasets:
            if currentMaxSize != dataset.getNumBuckets():
                raise Exception('all datasets need to be constructed with the same ratio %s vs %s' %(currentMaxSize, dataset.getNumBuckets()));
        
        self._datasets = classifiedDatasets;
        self._numTests = currentMaxSize;
        self._supervisedClassifierFactories = supervisedClassifierFactories;
        
    def getReport(self):
        
        classifierAverageReport = {};
        
        for classifier in self._supervisedClassifierFactories:
            classifierAverageReport[classifier.getName()] = AggregatedReportStatistics(classifier.getName());
        
        for runNum in range(0, self._numTests):
            
            datasetChunk = [dataset.getChunk(runNum) for dataset in self._datasets];
            
            allTestDocuments = map(lambda dataset: dataset.getTestingDocuments(), datasetChunk)
            allTrainingDocuments = map(lambda dataset: dataset.getTrainingDocuments(), datasetChunk)
            
            print "run %s using %s training documents and %s test documents" % (runNum, Report.getDocSize(allTrainingDocuments), Report.getDocSize(allTestDocuments));
            
            for supervisedClassifierFactory in self._supervisedClassifierFactories:
                classifier = supervisedClassifierFactory.train(allTrainingDocuments);
                
                [results, testWords] = classifier.batch_classify(allTestDocuments);
                
                stats = ReportStatistics(results, testWords, classifier.getName()); 
                classifierAverageReport[classifier.getName()].addReport(stats);
                
        return classifierAverageReport;
    
    @staticmethod
    def getDocSize(documents):
        totalSize = 0;
        for document in documents:
            totalSize += len(document.getDocuments());
            
        return totalSize;
    
    
    @staticmethod
    def printReport(reportStats):
        nameWidth = max([len(label) for label in reportStats.keys()]) + 4;
        valueWidth = 14;
        
        headerFormatter = "|{0:<{col1}}|{1:>{col2}}|{2:>{col2}}|{3:>{col2}}|{4:>{col2}}|";
        formatter = "|{0:<{col1}}|{1:>{col2}}|{2:>{col2}}|{3:>{col2}}|{4:>{col2}}|";
        precisionFormater = "{0:.4f}";
        border = "_{0:_<{col1}}_{0:_<{col2}}_{0:_<{col2}}_{0:_<{col2}}_{0:_<{col2}}_".format('', col1=nameWidth, col2=valueWidth);
        
        print border;
        print headerFormatter.format("Classifier Name", "Accuracy", "Precision", "Recall", "FMeasure", col1=nameWidth, col2=valueWidth);
        print border;
        for reportStatName in reportStats:
    
            reportStat = reportStats[reportStatName];
            
            print formatter.format(reportStat.getClassifierName(), precisionFormater.format(reportStat.getAccuracy()), precisionFormater.format(reportStat.getPrecision()), precisionFormater.format(reportStat.getRecall()), precisionFormater.format(reportStat.getFMeasure()), col1=nameWidth, col2=valueWidth)

            print border;
    
    @staticmethod
    def showGraph(reportStats, reportName):
        
        ind = np.arange(len(reportStats))
        width = 0.4
        plt.bar(ind,[reportStat.getAccuracy() for reportStat in reportStats.values()],width,color="#1AADA4")
        plt.ylabel('Accuracy')
        plt.ylim(ymax=1)
        plt.xticks(ind+width/2.0,[reportStat for reportStat in reportStats])
        plt.title(reportName)
        plt.show()
        
                
from nltk.metrics.scores import accuracy 
from nltk.metrics.scores import recall
from nltk.metrics.scores import precision
from nltk.metrics.scores import f_measure
from collections import defaultdict

class ReportStatistics(object):
    
    def __init__(self, classifiedResults, actualResults, classifierName):
        
        self._classifiedResults = classifiedResults;
        
        self._actualResults = [document[1] for document in actualResults] if actualResults is not None else None;
        
        refsets = defaultdict(set)
        testsets = defaultdict(set)
        if (actualResults is not None):
            for i, (label) in enumerate(self._actualResults):
                refsets[label].add(i)
                observed = self._classifiedResults[i];
                testsets[observed].add(i)
            
        self._refsets = refsets;
        self._testsets = testsets;
        self._classifiedName = classifierName;
        
    def getAccuracy(self):
        return accuracy(self._classifiedResults, self._actualResults);
    
    def getRecall(self):
        return recall(self._refsets['POS'], self._testsets['POS'])
    
    def getPrecision(self):
        return precision(self._refsets['POS'], self._testsets['POS'])
    
    def getFMeasure(self):
        return f_measure(self._refsets['POS'], self._testsets['POS']);
    
    def getClassifierName(self):
        return self._classifiedName;
    
class AggregatedReportStatistics(ReportStatistics):
    
    def __init__(self, classifierName):
        ReportStatistics.__init__(self, None, None, classifierName)
        self._reports = list();
    
    def addReport(self, report):
        self._reports.append(report);
        
    def getAccuracy(self):        
        
        return self.getAverage(lambda report: report.getAccuracy());
    
    def getRecall(self):
       
        return self.getAverage(lambda report: report.getRecall());      
    
    def getPrecision(self):        
        
        return self.getAverage(lambda report: report.getPrecision());      
    
    def getFMeasure(self):
        
        return self.getAverage(lambda report: report.getFMeasure());  
    
    def getAverage(self, valueGetter):
        total = reduce(lambda accumulatedAccuracy,report: accumulatedAccuracy + valueGetter(report), self._reports, 0)
        
        return total / len(self._reports)    