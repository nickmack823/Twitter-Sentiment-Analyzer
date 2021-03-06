import os
import nltk
import pandas
import statistics
import random
import pickle
import joblib
from os.path import exists
from pathlib import Path
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.corpus import opinion_lexicon
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression

# Paths for pickled files
root_path = Path('.')  # Get root file path with pathlib
pickle_dir = 'pickled_files'
joblib_dir = 'joblib_files'
accuracies_path = root_path / pickle_dir / 'classifier_accuracies.pickle'

if not os.path.exists(pickle_dir):
    os.mkdir(pickle_dir)
if not os.path.exists(joblib_dir):
    os.mkdir(joblib_dir)

# NLTK pre-trained analyzer: VADER
# Best suited for social media language (short sentences with slang y abbreviations)
sia = SentimentIntensityAnalyzer()

# Liu and Hu Opinion Lexicon word lists (cast to set for faster lookup)
positive_words = set(opinion_lexicon.positive())
negative_words = set(opinion_lexicon.negative())


def extract_features(text):
    """Finds features that indicate positive sentiment in given text string using VADER and the Opinion Lexicon."""
    features = {}
    pos_wordcount = 0
    neg_wordcount = 0
    compound_scores = []
    positive_scores = []
    negative_scores = []

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
    # 5 features included, testing suggests higher accuracy with 5
    features["mean_compound"] = statistics.mean(compound_scores) + 1
    features["mean_positive"] = statistics.mean(positive_scores)
    features["mean_negative"] = statistics.mean(negative_scores)
    features["pos_wordcount"] = pos_wordcount
    features["neg_wordcount"] = neg_wordcount

    return features


def store_data(file_path, obj, compress=3):
    """Stores input 'obj' data to the given file path."""
    print(f'Storing data to {file_path}')
    str_path = str(file_path)
    if str_path.endswith('.pickle'):
        with open(file_path, 'wb') as f:
            pickle.dump(obj, f)
    elif str_path.endswith('.joblib'):
        joblib.dump(obj, file_path, compress=compress)


def get_data(file_path):
    """Retrieves data from the given file path."""
    print(f'Getting data from {file_path}')
    data = None
    str_path = str(file_path)
    if str_path.endswith('.pickle'):
        f = open(file_path, 'rb')
        data = pickle.load(f)
        f.close()
    elif str_path.endswith('.joblib'):
        data = joblib.load(file_path)

    return data


def get_sentiment140_training_tweets():
    """Gets positive and negative tweet data from Sentiment140 training tweets."""
    print('Getting sentiment140 data')
    # sentiment140_df = pandas.read_csv('sentiment140_training_data_tweets.csv', encoding='ISO-8859-1')

    # Isolate sentiment values and tweet texts by dropping unneeded columns
    # for i in range(4):
    #     sentiment140_df.drop(sentiment140_df.columns[1], axis=1, inplace=True)

    # Add headers to dataframe and create more workable version of training data file
    # print('Creating modified CSV file of data')
    # headers = ['sentiment', 'tweet']
    # sentiment140_df.to_csv('sentiment140_training_data_modified.csv', header=headers, index=False)
    training_data = pandas.read_csv('sentiment140_training_data_modified.csv')

    # Get positive- and negative-tagged tweets
    print('Getting pos/neg tweets from training data')
    positive_tweet_data = training_data.loc[training_data['sentiment'] == 4]
    negative_tweet_data = training_data.loc[training_data['sentiment'] == 0]
    positive_tweets = positive_tweet_data['tweet'].tolist()
    negative_tweets = negative_tweet_data['tweet'].tolist()

    return positive_tweets, negative_tweets


def get_features_from_tweets(positive_tweets, negative_tweets):
    """Gets features from input positive and negative tweets."""
    print("Getting features from tweets...")
    pos_features, neg_features = [], []

    # Getting positive features
    for t in positive_tweets:
        pos_features.append((extract_features(t), "pos"))

    # Getting negative features
    for t in negative_tweets:
        neg_features.append((extract_features(t), "neg"))

    print('Features acquired.')
    return pos_features, neg_features


def get_features():
    """Gets and returns features acquired from training tweets."""
    positive_tweets, negative_tweets = get_sentiment140_training_tweets()
    positive_features, negative_features = get_features_from_tweets(positive_tweets, negative_tweets)

    all_features = positive_features + negative_features
    return all_features


def get_classifiers():
    """Initializes all classifiers."""
    print('Initializing classifiers...')
    classifiers_to_get = {
        "NaiveBayes": None,
        "MultinomialNB": MultinomialNB(),
        "KNeighborsClassifier": KNeighborsClassifier(),
        "DecisionTreeClassifier": DecisionTreeClassifier(),
        "LogisticRegression": LogisticRegression(),
    }
    need_features = False
    classifiers = {}

    # Check if sklearn classifier exists already
    for name in classifiers_to_get.keys():
        classifier_path = root_path / joblib_dir / f'{name}.joblib'
        if not exists(classifier_path):
            need_features = True
            break

    # One or more classifier pickled files not present, need to create them
    if need_features:
        # Get features
        tweet_features = get_features()
        train_count = int(len(tweet_features) * 0.7)
        random.shuffle(tweet_features)

        # Get each classifier, either by training or loading existing pickle data
        for name, classifier in classifiers_to_get.items():
            classifier_path = root_path / joblib_dir / f'{name}.joblib'
            if not exists(classifier_path):
                # Check for NaiveBayes, it requires different training call
                if name == 'NaiveBayes':
                    nb_classifier = nltk.NaiveBayesClassifier.train(tweet_features[:train_count])
                    classifiers['NaiveBayes'] = nb_classifier
                    store_data(classifier_path, nb_classifier)
                    continue

                classifier_ = nltk.classify.SklearnClassifier(classifier)
                classifier_.train(tweet_features[:train_count])
                classifiers[name] = classifier_
                store_data(classifier_path, classifier_)
            else:
                classifiers[name] = get_data(classifier_path)

    # Pickled files exist for all classifiers
    else:
        for name, classifier in classifiers_to_get.items():
            classifier_path = root_path / joblib_dir / f'{name}.joblib'
            classifiers[name] = get_data(classifier_path)

    print('Classifiers initialized.')
    return classifiers


def test_classifier_accuracy(name, classifier, features):
    """Tests classifier accuracy."""
    classifier_accuracy = {name: 0}
    test_count = int(len(features) * 0.3)

    print(f'Testing accuracy for {name}')
    # Test accuracy and add result
    accuracy = nltk.classify.accuracy(classifier, features[-test_count:])
    classifier_accuracy[name] = f'{(classifier_accuracy[name] + accuracy):.2%}'

    return classifier_accuracy


def test_classifiers(classifiers):
    """Tests each classifier in input dictionary."""
    features = get_features()
    accuracies = []
    test_count = int(len(features) * 0.3)
    random.shuffle(features)
    for name, classifier in classifiers.items():
        accuracy_data = test_classifier_accuracy(name, classifier, features)
        accuracies.append(accuracy_data)

    test_details = {'test tweet count (30% of training data)': test_count}
    accuracies.append(test_details)
    store_data(accuracies_path, accuracies)
    print(accuracies)
    return accuracies


def classify_tweets(tweets, classifiers):
    """Classifies a list of tweets using input classifiers."""
    print('Classifying tweets...')
    analysis_results = []

    n = 0
    for tweet in tweets:
        individual_results = []
        tweet_features = extract_features(tweet)
        for name, classifier in classifiers.items():
            sentiment = classifier.classify(tweet_features)
            individual_results.append((name, sentiment))

        analysis_results.append(individual_results)
        n += 1

    return analysis_results


def get_majority_sentiments(results):
    """Determines the majority sentiment of classification results for a tweet."""
    sentiments_list = []
    for result in results:
        positive_classifications = 0
        negative_classifications = 0
        for classification in result:
            if classification[1] == 'pos':
                positive_classifications += 1
            else:
                negative_classifications += 1

        if positive_classifications > negative_classifications:
            majority_sentiment = 'positive'
        else:
            majority_sentiment = 'negative'

        sentiments_list.append(majority_sentiment)

    return sentiments_list


def classify(tweets, classifiers):
    classifications = classify_tweets(tweets, classifiers)
    return get_majority_sentiments(classifications)
