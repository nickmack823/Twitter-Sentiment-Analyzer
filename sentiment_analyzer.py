import nltk
import pandas
import statistics
import random
import pickle
import json
from os.path import exists
from pathlib import Path
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import opinion_lexicon
from sklearn.naive_bayes import (BernoulliNB, ComplementNB, MultinomialNB,)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.svm import LinearSVC
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis

# NLTK pre-trained analyzer: VADER
# Best suited for social media language (short sentences with slang y abbreviations)
sia = SentimentIntensityAnalyzer()
topic = 'abortion'
df = pandas.read_csv(f'{topic}.csv')
tweets_col = df.loc[:, 'tweet']

# Check tweet positivity with VADER
def is_tweet_positive(tweet):
    """Returns true if tweet has a positive compound sentiment, otherwise False."""
    return sia.polarity_scores(tweet)["compound"] > 0


# Liu and Hu Opinion Lexicon word lists (cast to set for faster lookup)
positive_words = set(opinion_lexicon.positive())
negative_words = set(opinion_lexicon.negative())


def extract_features(text):
    """Finds features that indicate positivity in given text"""
    features = {}
    pos_wordcount, neg_wordcount = 0, 0
    compound_scores = []
    positive_scores, negative_scores = [], []

    # Go through each sentence in text
    for sentence in nltk.sent_tokenize(text):
        # Go through each word
        for word in nltk.word_tokenize(sentence):
            # Check if word is in the above list of positive words
            if word.lower() in positive_words:
                pos_wordcount += 1
            if word.lower() in negative_words:
                neg_wordcount += 1

        # Use VADER to determine scores for the sentence
        polarity_scores = sia.polarity_scores(sentence)
        compound_scores.append(polarity_scores["compound"])
        positive_scores.append(polarity_scores["pos"])
        negative_scores.append(polarity_scores["neg"])

    # Creates three features: mean_compound, mean_positive, mean_negative, pos_wordcount, and neg_wordcount

    # Adding 1 to the final compound score to always have positive numbers
    # since some classifiers don't work with negative numbers.
    # Negative features omitted, testing suggests highest accuracy without them.
    features["mean_compound"] = statistics.mean(compound_scores) + 1
    features["mean_positive"] = statistics.mean(positive_scores)
    # features["mean_negative"] = statistics.mean(negative_scores)
    features["pos_wordcount"] = pos_wordcount
    # features["neg_wordcount"] = neg_wordcount

    return features


# 1. Using VADER to get a list of positive and negative tweets
# pos_tweets = [tweet for tweet in tweets_col if is_tweet_positive(tweet)]
# neg_tweets = [tweet for tweet in tweets_col if not is_tweet_positive(tweet)]

# 2. Using Sentiment140 training data consisting of 1,600,000 tweets categorized as negative (0), neutral (2), or
# positive (4)

# Paths for pickled files
root = Path('.')  # Get root file path with pathlib
pickle_dir = 'pickled_files'
positive_tweets_path = root / pickle_dir / 'positive_tweets.pickle'
negative_tweets_path = root / pickle_dir / 'negative_tweets.pickle'
positive_features_path = root / pickle_dir / 'positive_tweet_features.pickle'
negative_features_path = root / pickle_dir / 'negative_tweet_features.pickle'
naive_bayes_classifier_path = root / pickle_dir / 'naive_bayes_classifier.pickle'


def get_pickled_data(file_path):
    print(f'Getting pickled data from {file_path}')
    f = open(file_path, 'rb')
    data = pickle.load(f)
    f.close()
    return data


def store_pickled_data(file_path, obj):
    print(f'Pickling and storing to {file_path}')
    with open(file_path, 'wb') as f:
        pickle.dump(obj, f)


def get_sentiment140_training_tweets():
    print('Getting sentiment140 data')
    sentiment140_df = pandas.read_csv('sentiment140_training_data_tweets.csv', encoding='ISO-8859-1')

    # Isolate sentiment values and tweet texts
    for i in range(4):
        sentiment140_df.drop(sentiment140_df.columns[1], axis=1, inplace=True)

    # Add headers to dataframe and create more workable version of training data file
    print('Creating modified CSV file of data')
    headers = ['sentiment', 'tweet']
    sentiment140_df.to_csv('sentiment140_training_data_modified.csv', header=headers, index=False)
    training_data = pandas.read_csv('sentiment140_training_data_modified.csv')

    # Get positive- and negative-tagged tweets
    print('Getting pos/neg tweets from training data')
    positive_tweet_data = training_data.loc[training_data['sentiment'] == 4]
    negative_tweet_data = training_data.loc[training_data['sentiment'] == 0]
    pos_tweets = positive_tweet_data['tweet'].tolist()
    neg_tweets = negative_tweet_data['tweet'].tolist()

    return pos_tweets, neg_tweets


def get_all_features():
    print('Getting all features')
    pos_features, neg_features = [], []
    n1, n2 = 0, 0
    l1, l2 = len(positive_tweets), len(negative_tweets)
    print('Getting negative features')
    for t in positive_tweets:
        pos_features.append((extract_features(t), "pos"))
        n1 += 1
        print(f'{n1}/{l1} complete')
    print('Getting negative features')
    for t in negative_tweets:
        neg_features.append((extract_features(t), "neg"))
        n2 += 1
        print(f'{n2}/{l2} complete')

    return pos_features, neg_features


# If positive and negative tweet data is already pickled, retrieve it. If not, get and pickle it
if exists(positive_tweets_path) and exists(negative_tweets_path):
    positive_tweets = get_pickled_data(positive_tweets_path)
    negative_tweets = get_pickled_data(negative_tweets_path)
else:
    print('Pos/neg tweets file does not exist, getting data and storing')
    modified_data = get_sentiment140_training_tweets()
    positive_tweets, negative_tweets = modified_data[0], modified_data[1]
    store_pickled_data(positive_tweets_path, positive_tweets)
    store_pickled_data(negative_tweets_path, negative_tweets)

# Check if positive features have already been collected for the training data
if exists(positive_features_path) and exists(negative_features_path):
    positive_features = get_pickled_data(positive_features_path)
    negative_features = get_pickled_data(negative_features_path)
# If not, collect the features and store them to a pickled file
else:
    positive_features, negative_features = get_all_features()
    store_pickled_data(positive_features_path, positive_features)
    store_pickled_data(negative_features_path, negative_features)

# Consolidate all features into one list
tweet_features = positive_features + negative_features
train_count = len(tweet_features) // 4

# Get classifier if it exists
if exists(naive_bayes_classifier_path):
    nb_classifier = get_pickled_data(naive_bayes_classifier_path)
# Create classifier considering features up to the train_count index
else:
    print('Training Naive Bayes Classifier')
    # Train classifier
    random.shuffle(tweet_features)
    nb_classifier = nltk.NaiveBayesClassifier.train(tweet_features[:train_count])
    store_pickled_data(naive_bayes_classifier_path, nb_classifier)

# nb_classifier.show_most_informative_features(10)

# Additional classifiers used for testing
# classifiers = {
#     "BernoulliNB": BernoulliNB(),
#     "ComplementNB": ComplementNB(),
#     "MultinomialNB": MultinomialNB(),
#     "KNeighborsClassifier": KNeighborsClassifier(),
#     "DecisionTreeClassifier": DecisionTreeClassifier(),
#     "RandomForestClassifier": RandomForestClassifier(),
#     "LogisticRegression": LogisticRegression(),
#     "MLPClassifier": MLPClassifier(max_iter=1000),
#     "AdaBoostClassifier": AdaBoostClassifier(),
# }


def test_classifiers(classifiers):
    classifier_accuracies = {classifier: '' for classifier in classifiers.keys()}
    nb_accuracy = nltk.classify.accuracy(nb_classifier, tweet_features[train_count:])
    classifier_accuracies['NaiveBayes'] = nb_accuracy
    random.shuffle(tweet_features)
    for name, sklearn_classifier in classifiers.items():
        # Create classifier
        classifier = nltk.classify.SklearnClassifier(sklearn_classifier)
        # Train
        classifier.train(tweet_features[:train_count])
        # Test accuracy
        accuracy = nltk.classify.accuracy(classifier, tweet_features[train_count:])
        classifier_accuracies[name] = accuracy

    return classifier_accuracies


# Run 50 accuracy tests and find the average accuracies for each classifier
# accuracies = test_classifiers()
# for n in range(49):
#     print(f'{n+1}/50 accuracy tests completed.')
#     test_results = test_classifiers()
#     for key in test_results.keys():
#         current_value = accuracies[key]
#         this_value = test_results[key]
#         accuracies[key] = current_value + this_value

# # Get accuracy average after 50 tests for each
# for key in accuracies.keys():
#     accuracies[key] = f'{accuracies[key]/50:.2%}'

# with open('classifier_accuracies.json', 'w') as f:
#     json.dump(accuracies, f)
#
# print(accuracies)

# TODO: Classify new incoming tweets


