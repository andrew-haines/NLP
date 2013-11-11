'''
Created on Nov 5, 2013

@author: haines
'''

from random import shuffle

class Dataset(object):

    def __init__(self, testRatio, trainingDocuments, testingDocuments=None):
        
        if testingDocuments is None: # The is no difference is the training and testing datasets are the same.
            testingDocuments = trainingDocuments;
            
        if (testRatio >= 1 and testRatio <=0):
            raise Exception('testRatio needs to be a value between 0-1 exclusive')
        #first shuffle
        
        shuffle(trainingDocuments);
        shuffle(testingDocuments);
        
        #now work out chuck/bucket size for each bucketed test/train combination
        self._trainSize = len(trainingDocuments);
        self._testSize = len(testingDocuments);
        self._testRatio = testRatio;
        
        bucketRatio = testRatio if testRatio <= 0.5 else 1 - testRatio; 
        
        self._trainBucketSize = (self._trainSize * bucketRatio);
        self._testBucketSize = (self._testSize * bucketRatio);
        self._trainDocuments = trainingDocuments;
        self._testDocuments = testingDocuments;
        
    def getChunk(self, chuckNum):
        trainBucketStart = int(round(self._trainBucketSize * chuckNum));
        trainBucketEnd = int(round(trainBucketStart + self._trainBucketSize));
        testBucketStart = int(round(self._testBucketSize * chuckNum));
        testBucketEnd = int(round(testBucketStart + self._testBucketSize));
        
        training = self._trainDocuments[trainBucketStart:trainBucketEnd];
        testing = self._testDocuments[testBucketStart:testBucketEnd];
        
        if self._testRatio > 0.5:
            testing = [doc for doc in self._testDocuments if doc not in testing];
        else : # if the ratio between train/test is greater then 0.5 then use the inverse
            training = [doc for doc in self._trainDocuments if doc not in training];
        
        return DatasetBucket(training, testing)
        
    def getNumBuckets(self):
        return int(round(self._trainSize / self._trainBucketSize))
    
class ClassifiedDataset(Dataset):
    
    def __init__(self, testRatio, classificationLabel, trainingDocuments, testingDocuments=None):
        Dataset.__init__(self, testRatio, trainingDocuments, testingDocuments);
        
        self.classificationLabel = classificationLabel;
        
    def getClassificationLabel(self):
        return self.classificationLabel;
    
    def getChunk(self, chuckNum):
        
        dataset = Dataset.getChunk(self, chuckNum);
        return ClassifiedDatasetBucket(dataset.getTrainingDocuments(),dataset.getTestingDocuments(), self.getClassificationLabel())

class DatasetBucket(object):
    
    def __init__(self, trainingDocuments, testingDocuments):
        self._trainingDocuments = trainingDocuments;
        self._testingDocuments = testingDocuments;
    
    def getTrainingDocuments(self):
        return self._trainingDocuments;
    
    def getTestingDocuments(self):
        return self._testingDocuments;
    
class ClassifiedDatasetBucket(DatasetBucket):
    
    def __init__(self, trainingDocuments, testingDocuments, classification):
        DatasetBucket.__init__(self, trainingDocuments, testingDocuments);
        
        self._classification = classification;
        
    def getClassification(self):
        return self._classification;
    
    def getTrainingDocuments(self):
        return ClassifiedDocument(self._trainingDocuments, self.getClassification());
    
    def getTestingDocuments(self):
        return ClassifiedDocument(self._testingDocuments, self.getClassification());


class ClassifiedDocument(object):
    
    def __init__(self, documents, classification):
        self._documents = documents;
        self._classification = classification;
        
    def getDocuments(self):
        return self._documents;
    
    def getClassification(self):
        return self._classification;
    
import unittest


class Test(unittest.TestCase):


    def testGetBuckets(self):
        
        documents = range(0,20)
        self.assertEqual(len(documents), 20);

        dataset = Dataset(0.1, documents)
        
        self.assertEqual(dataset.getNumBuckets(), 10);

        for bucket in range(0, dataset.getNumBuckets()):
            print dataset.getChunk(bucket).getTrainingDocuments();
            print dataset.getChunk(bucket).getTestingDocuments();
            
            self.assertEqual(len(dataset.getChunk(bucket).getTrainingDocuments()), 18);
            self.assertEqual(len(dataset.getChunk(bucket).getTestingDocuments()), 2);
            
        pass
    
    def testNonIntegerSplit2(self):
        
        documents = range(0,22)

        dataset = Dataset(0.1, documents)
        
        self.assertEqual(dataset.getNumBuckets(), 10);

        for bucket in range(0, dataset.getNumBuckets()):
            print dataset.getChunk(bucket).getTrainingDocuments();
            print dataset.getChunk(bucket).getTestingDocuments();
            
            self.assertEqual(len(dataset.getChunk(bucket).getTrainingDocuments()), 20);
            self.assertEqual(len(dataset.getChunk(bucket).getTestingDocuments()), 2);
            
        pass
    
    def testNonIntegerSplit(self):
        
        documents = range(0,21)

        dataset = Dataset(0.1, documents)
        
        self.assertEqual(dataset.getNumBuckets(), 10);

        for bucket in range(0, dataset.getNumBuckets()):
            print dataset.getChunk(bucket).getTrainingDocuments();
            print dataset.getChunk(bucket).getTestingDocuments();
            
            self.assertEqual(len(dataset.getChunk(bucket).getTrainingDocuments()), 19);
            self.assertEqual(len(dataset.getChunk(bucket).getTestingDocuments()), 2);
            
        pass
    def testGetBucketsWithGreaterThan50PercentSplit(self):
        
        documents = range(0,20)
        self.assertEqual(len(documents), 20);

        dataset = Dataset(0.9, documents)
        
        self.assertEqual(dataset.getNumBuckets(), 10);

        for bucket in range(0, dataset.getNumBuckets()):
            print dataset.getChunk(bucket).getTrainingDocuments();
            print dataset.getChunk(bucket).getTestingDocuments();
            
            self.assertEqual(len(dataset.getChunk(bucket).getTrainingDocuments()), 2);
            self.assertEqual(len(dataset.getChunk(bucket).getTestingDocuments()), 18);
            
        pass
    
    def testGetBucketsWithMultipleTrainingAndTestSetsGreaterThan50PercentSplit(self):
        
        trainDocuments = range(0,20)
        testDocuments = range(100, 120)
        self.assertEqual(len(trainDocuments), 20);

        dataset = Dataset(0.1, trainDocuments, testDocuments)
        
        self.assertEqual(dataset.getNumBuckets(), 10);

        for bucket in range(0, dataset.getNumBuckets()):
            print dataset.getChunk(bucket).getTrainingDocuments();
            print dataset.getChunk(bucket).getTestingDocuments();
            
            self.assertEqual(len(dataset.getChunk(bucket).getTrainingDocuments()), 18);
            self.assertEqual(len(dataset.getChunk(bucket).getTestingDocuments()), 2);
            
            self.assertEqual(len(set(dataset.getChunk(bucket).getTrainingDocuments()) & set(trainDocuments)), len(dataset.getChunk(bucket).getTrainingDocuments()));
            self.assertEqual(len(set(dataset.getChunk(bucket).getTestingDocuments()) & set(testDocuments)), len(dataset.getChunk(bucket).getTestingDocuments()));

        pass
    
    def testGetBucketsWithMultipleDifferentSizedTrainingAndTestSetsGreaterThan50PercentSplit(self):
        
        trainDocuments = range(0,20)
        testDocuments = range(100, 135)
        self.assertEqual(len(trainDocuments), 20);

        dataset = Dataset(0.1, trainDocuments, testDocuments)
        
        self.assertEqual(dataset.getNumBuckets(), 10);

        for bucket in range(0, dataset.getNumBuckets()):
            print dataset.getChunk(bucket).getTrainingDocuments();
            print dataset.getChunk(bucket).getTestingDocuments();
            
            self.assertEqual(len(dataset.getChunk(bucket).getTrainingDocuments()), 18);
            if (bucket == 9): # last bucket is 3 entries big
                self.assertEqual(len(dataset.getChunk(bucket).getTestingDocuments()), 3);
            else :
                self.assertEqual(len(dataset.getChunk(bucket).getTestingDocuments()), 4);
            
            self.assertEqual(len(set(dataset.getChunk(bucket).getTrainingDocuments()) & set(trainDocuments)), len(dataset.getChunk(bucket).getTrainingDocuments()));
            self.assertEqual(len(set(dataset.getChunk(bucket).getTestingDocuments()) & set(testDocuments)), len(dataset.getChunk(bucket).getTestingDocuments()));
        pass

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    