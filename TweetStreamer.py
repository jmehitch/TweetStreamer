#! python3
# TweetStreamer - streams and collects live tweet data for a certain keyword and stores the data in an SQLite database.

import tweepy
import re
import textblob
import sqlite3
import os


class TweetListener(tweepy.StreamListener):
    """Initialises Twitter Stream API object that will obtain live tweets and relevant tweet info."""

    def __init__(self, api=''):

        # Initialise parameters for use in class
        self.api = api
        self.tweet_count = 0
        self.collected_tweet_list = []
        self.tweet = []
        print("Collecting live tweets...\n")

    def on_status(self, status):
        """Obtains a list of all tweet data and appends to tweet list every time a tweet is collected."""

        # Collect relevant tweet data for each tweet
        self.tweet.append(status.id)
        self.tweet.append(status.text)
        self.tweet.append(str(status.created_at))
        self.tweet.append(str(status.user.location))
        self.tweet.append(str(status.coordinates))
        self.tweet.append(status.user.followers_count)
        self.tweet.append(status.user.friends_count)
        self.collected_tweet_list.append(self.tweet)
        self.tweet = []
        self.tweet_count += 1
        # Specify number of tweets to collect
        if self.tweet_count > 10:
            return False


# Initialise empty lists to store data for use in following functions
tweets_to_analyse = []
sentiment_score_list = []


def clean_tweets(tweet_list):
    """
    Removes special characters from tweet text and returns list of clean strings for sentiment analysis.

    Args:
        tweet_list: list of tweets generated by the TweetListener

    Returns:
        List of tweets with no special characters in the text of the tweets.
    """

    # Remove special characters from text of each tweet using a regular expression
    for i in range(len(tweet_list)):
        tweet = " ".join(re.sub("(@[A-Za-z0-9]+)|(\w+:\/\/\S+)|([^A-Za-z0-9 \t])", " ", tweet_list[i][1]).split())
        tweets_to_analyse.append(tweet)
    return tweets_to_analyse


def sentiment_analysis(tweet_list):
    """
    Analyses sentiment of tweets and returns sentiment polarity to 2dp.

    Args:
        tweet_list: list of tweets to analyse the sentiment of

    Returns:
        List of sentiment scores for each tweet in order of tweets.
    """

    # Analyse sentiment of each tweet by iterating through clean tweets
    for i in tweet_list:
        statement = textblob.TextBlob(i)
        sentiment_score = round(statement.sentiment.polarity, 2)
        sentiment_score_list.append(sentiment_score)
    return sentiment_score_list


def add_score_to_list(score_list, tweet_list):
    """
    Adds sentiment score of tweets to the list of tweets.

    Args:
        score_list: list of values of sentiment in same order of corresponding tweet
        tweet_list: list of tweet data obtained by TweetStreamer

    Returns:
        Completed list of tweet data with sentiment score appended.
    """

    # Add sentiment score to the main list of tweet data by iterating
    for i in range(len(score_list)):
        tweet_list[i].append(score_list[i])
    return tweet_list


def create_sql_table(db_file):
    """
    Creates SQLite table if not already created.

    Args:
        db_file: filename of SQLite database to be created

    Returns:
        SQLite database generated with corresponding column headings.
    """

    # See if database already exists
    need_to_create = not os.path.exists(db_file)

    # If database does not exist, create 'tweets' table with relevant headings
    if need_to_create:
        sql_create_tb_tweets = "CREATE TABLE tweets" \
                               "(tweet_id INTEGER NOT NULL," \
                               "tweet_text TEXT NOT NULL," \
                               "created_at TEXT NOT NULL," \
                               "location TEXT NOT NULL," \
                               "geo_coordinates TEXT NOT NULL," \
                               "no_of_followers INTEGER NOT NULL," \
                               "no_of_friends INTEGER NOT NULL," \
                               "sentiment REAL NOT NULL)"
        db = sqlite3.connect(db_file)
        cursor = db.cursor()
        cursor.execute(sql_create_tb_tweets)
        db.commit()
        cursor.close()
    else:
        db = sqlite3.connect(db_file)
    return db


def add_tweets_to_db(tweet_list, db_file):
    """
    Adds tweets and tweet data using the tweet list to SQLite database previously created.

    Args:
        tweet_list: completed nested list of tweets containing all tweet data collected
        db_file: filename of SQLite database created by create_sql_table

    Returns:
        Updated SQLite database, containing all tweet data collected.
    """

    # Connect to database created previously
    db = sqlite3.connect(db_file)
    cursor = db.cursor()

    # Insert tweet data into database into corresponding columns using data from tweet list
    for i in range(len(tweet_list)):
        cursor.executemany("INSERT INTO tweets VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (tweet_list[i],))
        db.commit()
    return db


def main():
    """Main code block to run the above functions."""

    # User credentials for access to Twitter API
    consumer_key = "i2fASXlUYmybSD7P3X7yMoLEr"
    consumer_secret_key = "kjLQ513FNjqmMHzEondlm7Pd7EabEiAEGN8PkMvydQ2nDazxxO"
    access_token = "57310039-hFzgsQKn564Xyrb1ok1rrYs36n5uTgm1FAQnEW1ml"
    access_token_secret = "esn9nDK0bwiRfvoemOLn9uLmuGTwoscDbAGWKFqfZPtkT"

    # Twitter API authorisation
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret_key)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    # Collect tweets from Twitter Stream API
    stream_listener = TweetListener()
    stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
    stream.filter(track=[tweet_keyword])

    # Analyse sentiment of tweets
    clean_tweets(stream_listener.collected_tweet_list)
    sentiment_analysis(tweets_to_analyse)
    add_score_to_list(sentiment_score_list, stream_listener.collected_tweet_list)

    # Store tweets & tweet data in database
    create_sql_table(db_filename)
    add_tweets_to_db(stream_listener.collected_tweet_list, db_filename)
    print("Tweets successfully collected and stored in database: " + db_filename)


if __name__ == "__main__":

    # Set keyword to stream tweets with and set filename of SQLite database
    tweet_keyword = input("Type your chosen keyword: ")
    db_filename = "collected_tweets.db"
    main()
