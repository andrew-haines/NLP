'''
Created on Dec 2, 2013

@author: haines
'''

def getRelationshipDependency(queryToken, otherToken, parsedSentence):
    for dependant in parsedSentence.get_dependants(otherToken):
        
        if dependant == queryToken:
            return dependant.deprel;
    
    return '';
    
class Opinion(object):
    
    def getForm(self):
        raise NotImplementedError();
    
    def getRootToken(self):
        raise NotImplementedError();
    
class BaseOpinion(Opinion):
    
    def __init__(self, adjective):
        self._adjective = adjective;
        
    def getForm(self):
        return self._adjective.form;
    
    def getRootToken(self):
        return self._adjective;
    
class PrepositionalModifiedOpinion(Opinion):
    
    def __init__(self, preposition, opinion):
        self._preposition = preposition;
        self._opinion = opinion;
        
    def getForm(self):
        return self._opinion.getForm()+'-'+self._preposition.form;
    
    def getRootToken(self):
        return self._opinion.getRootToken();

class PrepositionalObjectModifiedOpinion(Opinion):
    def __init__(self, prepositionalObject, opinion):
        self._prepositionalObject = prepositionalObject;
        self._opinion = opinion;
        
    def getForm(self):
        return self._opinion.getForm()+'-'+self._prepositionalObject.form;
    
    def getRootToken(self):
        return self._opinion.getRootToken();

class AdverbialModifiedOpinion(Opinion):
    
    def __init__(self, adverbial, opinion):
        self._adverbial = adverbial;
        self._opinion = opinion;
        
    def getForm(self):
        return self._adverbial.form + "-" +self._opinion.getForm();
    
    def getRootToken(self):
        return self._opinion.getRootToken();

class NegatedOpinion(Opinion):
    
    def __init__(self, opinion):
        self._opinion = opinion;
        
    def getForm(self):
        return 'not-'+self._opinion.getForm();
    
    def getRootToken(self):
        return self._opinion.getRootToken();

def getPrepositionalModifiers(parsedSentence, opinion, token = None):
    
    if (token == None):
        token = opinion.getRootToken();
    
    for dependency in parsedSentence.get_dependants(token):
        if (dependency.deprel == 'prep'):
            # we have found a preposition dependency. Trace through the preps until we find the prepositional object and apply both adverbial and negation modifiers to it
            
            opinion = PrepositionalModifiedOpinion(dependency, opinion);
            opinion = getPrepositionalModifiers(parsedSentence, opinion, dependency);
            
        elif (dependency.deprel == 'pobj'):
            opinion = getPrepositionalModifiers(parsedSentence, PrepositionalObjectModifiedOpinion(dependency, opinion), dependency)
    return opinion
  
def getAdjectiveOpinions(queryToken, parsedSentence):
    
    adjectives = [BaseOpinion(dependant) for dependant in parsedSentence.get_dependants(queryToken) if dependant.deprel == 'amod'];
    head = parsedSentence.get_head(queryToken)
    if (head.pos.startswith('JJ') or head.pos.startswith('VBG')):
        if (getRelationshipDependency(queryToken, head, parsedSentence) == 'nsubj'):
            adjectives += [BaseOpinion(head)];
    
    adjectives = [getPrepositionalModifiers(parsedSentence, adjective) for adjective in adjectives]; # look to see if this is a propositionally modified adjective      
    return adjectives;

def getAdverbialModifiedOpinions(opinions, parsedSentence):

    for index in range(0, len(opinions)):
        # see if we have any adverbial modifiers to our adjectives
        advmods = [];
        for adjectiveDependency in parsedSentence.get_dependants(opinions[index].getRootToken()):
            if(adjectiveDependency.deprel == 'advmod'):
                advmods += [adjectiveDependency];
        if (len(advmods) > 0):
            orginalOpinions = opinions.pop(index);
            for advmod in advmods:
                opinions.insert(index, AdverbialModifiedOpinion(advmod, orginalOpinions));
    return opinions;


def negateAdjectiveOpinions(adjectiveOpinion, parsedSentence):
    
    for dependant in parsedSentence.get_dependants(adjectiveOpinion.getRootToken()):
        if dependant.deprel == 'neg':
            adjectiveOpinion = NegatedOpinion(adjectiveOpinion);
    return adjectiveOpinion;

def negateOpinions(queryToken, parsedSentence, opinions):
    negateOpinions = ([dependant for dependant in parsedSentence.get_dependants(queryToken) if dependant.deprel == 'neg'])
    for index in range(0, len(opinions)):
        if (negateOpinions): # if there is a negated dependency on the query token then negate all opinions
            opinions[index] = NegatedOpinion(opinions[index])
        else:  # otherwise if there are any negations to the adjective of this opinion, then also negate the opinion
            opinions[index] = negateAdjectiveOpinions(opinions[index], parsedSentence);
                    
    return opinions;

def getVerbs(queryToken, parsedSentence):
    head = parsedSentence.get_head(queryToken)
    if (head.pos.startswith('VB') and head.pos != 'VBZ'): # all verbs except third person singular presents (such as has)
        if (getRelationshipDependency(queryToken, head, parsedSentence) == 'dobj'):
            return [BaseOpinion(head)]
        
    return [];
    
def opinionExtractor(queryToken, parsedSentence):
    return [opinion.getForm() for opinion in hainesOpinionExtractor(queryToken, parsedSentence)];
    
def hainesOpinionExtractor(queryToken, parsedSentence):
    
    # first trace back through head conjunctions to see if this token has adjectives
    # linked to conjunction conjoined to this token.
    
    head = parsedSentence.get_head(queryToken);
    opinions = [];
    if (getRelationshipDependency(queryToken, head, parsedSentence) == 'conj'):
        opinions = hainesOpinionExtractor(head, parsedSentence); # recursively trace head conjunctions and add their opinions 
    
    tokenOpinions = getAdjectiveOpinions(queryToken, parsedSentence);
    tokenOpinions = getAdverbialModifiedOpinions(tokenOpinions, parsedSentence);
    tokenOpinions += getVerbs(queryToken, parsedSentence);
    
    tokenOpinions = negateOpinions(queryToken, parsedSentence, tokenOpinions);
    
    # now look for conjunctions 
    for index in range(0, len(tokenOpinions)):
        rootToken = tokenOpinions[index].getRootToken();
        conjunctions = [dependant for dependant in parsedSentence.get_dependants(rootToken) if (dependant.deprel == 'conj')];
        
        if (len(conjunctions) > 0):
            conjunctionOpinions = [BaseOpinion(conjunction) for conjunction in conjunctions];
            
            conjunctionOpinions = getAdverbialModifiedOpinions(conjunctionOpinions, parsedSentence);
            conjunctionOpinions = [negateAdjectiveOpinions(adjectiveOpinion, parsedSentence) for adjectiveOpinion in conjunctionOpinions];
            tokenOpinions += conjunctionOpinions;

    return opinions + tokenOpinions;

import unittest
from nltk import pos_tag
from sussex_nltk.parse import get_parser
from sussex_nltk.parse import parse
from nltk.tokenize import word_tokenize

PARSER = get_parser();

class Test(unittest.TestCase):
    
    
    @staticmethod
    def parseSentence(sentence):
        
        taggedSentence = [(pos_tag(word_tokenize(sentence)))];
        
        parsedSentence = parse(PARSER, taggedSentence);
        print parsedSentence[0];
        return parsedSentence[0];

    TEST_SENTENCE_1 = parseSentence.__func__("It has an exciting fresh plot");
    TEST_SENTENCE_2 = parseSentence.__func__("The plot was dull");
    TEST_SENTENCE_3 = parseSentence.__func__("It has an excessively dull plot");
    TEST_SENTENCE_4 = parseSentence.__func__("The plot was excessively dull");
    TEST_SENTENCE_5 = parseSentence.__func__("The plot wasn't dull");
    TEST_SENTENCE_6 = parseSentence.__func__("It wasn't an exciting fresh plot");
    TEST_SENTENCE_7 = parseSentence.__func__("The plot wasn't excessively dull");
    TEST_SENTENCE_8 = parseSentence.__func__("The plot was cheesy, but fun and inspiring");
    TEST_SENTENCE_9 = parseSentence.__func__("The plot was really cheesy, and not particularly special");

    EXTENSION_SENTENCE_1 = parseSentence.__func__("The script and plot are utterly excellent");
    EXTENSION_SENTENCE_2 = parseSentence.__func__("The script and plot were unoriginal and boring");
    EXTENSION_SENTENCE_3 = parseSentence.__func__("The plot wasn't lacking");
    EXTENSION_SENTENCE_4 = parseSentence.__func__("The plot is full of holes");
    EXTENSION_SENTENCE_5 = parseSentence.__func__("There was no logical plot to this story");
    EXTENSION_SENTENCE_6 = parseSentence.__func__("I loved the plot");
    EXTENSION_SENTENCE_7 = parseSentence.__func__("I didn't mind the plot");
    
    def testAdjectivalModification(self):
        
        opinions = hainesOpinionExtractor(Test.TEST_SENTENCE_1.get_query_tokens('plot')[0], Test.TEST_SENTENCE_1);
        
        self.assertEqual(opinions[0].getForm(), 'exciting');
        self.assertEqual(opinions[1].getForm(), 'fresh');
        self.assertEqual(len(opinions), 2);
        
    def testAdjectivesLinkedByCopulae(self):
        
        opinions = hainesOpinionExtractor(Test.TEST_SENTENCE_2.get_query_tokens('plot')[0], Test.TEST_SENTENCE_2);
        
        self.assertEqual(opinions[0].getForm(), 'dull');
        self.assertEqual(len(opinions), 1);
        
    def testAdverbialModifiers1(self):
        
        opinions = hainesOpinionExtractor(Test.TEST_SENTENCE_3.get_query_tokens('plot')[0], Test.TEST_SENTENCE_3);
        
        self.assertEqual(opinions[0].getForm(), 'excessively-dull');
        self.assertEqual(len(opinions), 1);
        
    def testAdverbialModifiers2(self):
        
        opinions = hainesOpinionExtractor(Test.TEST_SENTENCE_4.get_query_tokens('plot')[0], Test.TEST_SENTENCE_4);
        
        self.assertEqual(opinions[0].getForm(), 'excessively-dull');
        self.assertEqual(len(opinions), 1);
        
    def testNegationModifiers1(self):
        
        opinions = hainesOpinionExtractor(Test.TEST_SENTENCE_5.get_query_tokens('plot')[0], Test.TEST_SENTENCE_5);
        
        self.assertEqual(opinions[0].getForm(), 'not-dull');
        self.assertEqual(len(opinions), 1);
        
    def testNegationModifiers2(self):
        
        opinions = hainesOpinionExtractor(Test.TEST_SENTENCE_6.get_query_tokens('plot')[0], Test.TEST_SENTENCE_6);
        
        self.assertEqual(opinions[0].getForm(), 'not-exciting');
        self.assertEqual(opinions[1].getForm(), 'not-fresh');
        self.assertEqual(len(opinions), 2);
        
    def testNegationModifiers3(self):
        
        opinions = hainesOpinionExtractor(Test.TEST_SENTENCE_7.get_query_tokens('plot')[0], Test.TEST_SENTENCE_7);
        
        self.assertEqual(opinions[0].getForm(), 'not-excessively-dull');
        self.assertEqual(len(opinions), 1);
        
    def testConjunctionModifiers1(self):
        
        opinions = hainesOpinionExtractor(Test.TEST_SENTENCE_8.get_query_tokens('plot')[0], Test.TEST_SENTENCE_8);
            
        self.assertEqual(opinions[0].getForm(), 'cheesy');
        self.assertEqual(opinions[1].getForm(), 'fun');
        self.assertEqual(opinions[2].getForm(), 'inspiring');
        self.assertEqual(len(opinions), 3);
        
    def testConjunctionModifiers2(self):
        
        opinions = hainesOpinionExtractor(Test.TEST_SENTENCE_9.get_query_tokens('plot')[0], Test.TEST_SENTENCE_9);
            
        self.assertEqual(opinions[0].getForm(), 'really-cheesy');
        self.assertEqual(opinions[1].getForm(), 'not-particularly-special');
        self.assertEqual(len(opinions), 2);
        
    def testExtension1(self):
        opinions = hainesOpinionExtractor(Test.EXTENSION_SENTENCE_1.get_query_tokens('plot')[0], Test.EXTENSION_SENTENCE_1);
            
        self.assertEqual(opinions[0].getForm(), 'utterly-excellent');
        self.assertEqual(len(opinions), 1);
        
    def testExtension2(self):
        opinions = hainesOpinionExtractor(Test.EXTENSION_SENTENCE_2.get_query_tokens('plot')[0], Test.EXTENSION_SENTENCE_2);
            
        self.assertEqual(opinions[0].getForm(), 'unoriginal');
        self.assertEqual(opinions[1].getForm(), 'boring');
        self.assertEqual(len(opinions), 2);
        
    def testExtension3(self):
        opinions = hainesOpinionExtractor(Test.EXTENSION_SENTENCE_3.get_query_tokens('plot')[0], Test.EXTENSION_SENTENCE_3);
            
        self.assertEqual(opinions[0].getForm(), 'not-lacking');
        self.assertEqual(len(opinions), 1);
        
    def testExtension4(self):
        opinions = hainesOpinionExtractor(Test.EXTENSION_SENTENCE_4.get_query_tokens('plot')[0], Test.EXTENSION_SENTENCE_4);
            
        self.assertEqual(opinions[0].getForm(), 'full-of-holes');
        self.assertEqual(len(opinions), 1);
    
    def testExtension5(self): # parser doesn't tag no as a negation
        opinions = hainesOpinionExtractor(Test.EXTENSION_SENTENCE_5.get_query_tokens('plot')[0], Test.EXTENSION_SENTENCE_5);
            
        self.assertEqual(opinions[0].getForm(), 'logical');
        self.assertEqual(len(opinions), 1);
        
    def testExtension6(self):
        opinions = hainesOpinionExtractor(Test.EXTENSION_SENTENCE_6.get_query_tokens('plot')[0], Test.EXTENSION_SENTENCE_6);
            
        self.assertEqual(opinions[0].getForm(), 'loved');
        self.assertEqual(len(opinions), 1);
        
    def testExtension7(self):
        opinions = hainesOpinionExtractor(Test.EXTENSION_SENTENCE_7.get_query_tokens('plot')[0], Test.EXTENSION_SENTENCE_7);
            
        self.assertEqual(opinions[0].getForm(), 'not-mind');
        self.assertEqual(len(opinions), 1);