from sussex_nltk.parse import load_parsed_dvd_sentences, load_parsed_example_sentences
from OpinionExtractor import opinionExtractor
from os import getcwd
from os.path import dirname;
 
query = "dialogue"   # Set this to the query token you're interested in
save_file_path = dirname(dirname(dirname(getcwd())))+"results"    # Set this to the location of the file you wish to create/overwrite with the saved output.
 
# Tracking these numbers will allow us to see what proportion of sentences we discovered features in
sentences_with_discovered_features = 0  # Number of sentences we discovered features in
total_sentences = 0  # Total number of sentences 
 
# This is a "with statement", it invokes a context manager, which handles the opening and closing of resources (like files)
with open(save_file_path, "w") as save_file:  # The 'w' says that we want to write to the file
    
    # Iterate over all the parsed sentences
    for parsed_sentence in load_parsed_dvd_sentences(query):   # Change "load_parsed_dvd_sentences(query)" to "load_parsed_example_sentences()" to get the example sentences from section 8 instead of DVD sentences.
        
        total_sentences += 1  # We've seen another sentence
        
        opinions = [] # Make a list for holding any opinions we extract in this sentence
 
        # Iterate over each of the query tokens in the sentences (in case there is more than one)
        for query_token in parsed_sentence.get_query_tokens(query):
            
            # Call your opinion extractor
            opinions += opinionExtractor(query_token, parsed_sentence)
        
        # If we found any opinions, write to the output file what we know.
        if opinions: 
            # Currently, the sentence will only be printed if opinions were found. But if you want to know what you're missing, you could move the sentence printing outside the if-statement
            
            # Print a separator and the raw unparsed sentence
            save_file.write("--- Sentence: %s ---\n" % parsed_sentence.raw())  # "\n" starts a new line
            # Print the parsed sentence
            save_file.write("%s\n" % parsed_sentence) 
            # Print opinions extracted
            save_file.write("Opinions: %s\n" % opinions)
            
            sentences_with_discovered_features += 1  # We've found features in another sentence
            
print "%s sentences out of %s contained features" % (sentences_with_discovered_features, total_sentences)