import pathlib

import plotly.express as px
import pandas as pd

#
# # Zoom in an a particular month
# weighted_percentage_df_april2022 = weighted_percentage_df.loc[(weighted_percentage_df['month'] == 'April')
#                                                               & (weighted_percentage_df['year'] == 2022)]
# weighted_percentage_df_april2022
#
# # Plot month's weighted data
# plt.figure(figsize=(10,8))
# plt.xticks(rotation=90)
# plt.ylim(0, 1)
# plt.yticks(numpy.arange(0, 1.1, 0.1))
# plt.xticks(range(1, weighted_percentage_df_april2022['day'].iloc[-1] + 1, 1))
# plt.xlabel('Day', size=14)
# plt.ylabel('Percentage of Tweets', size=14)
# plt.title(f'Abortion Twitter Sentiment (April 2022, Weighted)', size=16)
# plt.plot(weighted_percentage_df_april2022['day'], weighted_percentage_df_april2022['pos_score_percentage'],
#          linewidth=1, label='positive', color='green')
# plt.plot(weighted_percentage_df_april2022['day'], weighted_percentage_df_april2022['neg_score_percentage'],
#          linewidth=1, label='negative', color='red')
# plt.legend(title='Tweet Sentiment')
# plt.show()

# df_2021_weighted.drop({'positive_tweets', 'positive_likes', 'positive_retweets', 'negative_tweets',
#                        'negative_likes', 'negative_retweets', 'day', 'year', 'total_tweets'}, axis='columns', inplace=True)
# df_2021_weighted
#
# # Get percentages as before
# df_2021_percentages_weighted = df_2021_weighted.copy()
# df_2021_percentages_weighted['pos_percentage'] = round(df_2021_percentages_weighted['positive_score'] / df_2021_percentages_weighted['total_score'], 2)
# df_2021_percentages_weighted['neg_percentage'] = round(df_2021_percentages_weighted['negative_score'] / df_2021_percentages_weighted['total_score'], 2)
# df_2021_percentages_weighted.drop({'positive_score', 'negative_score'}, axis='columns', inplace=True)
# df_2021_percentages_weighted
#
# # Plot year's data (in terms of weighted percentages)
# plt.figure(figsize=(10,8))
# plt.xticks(rotation=90)
# plt.ylim(0, 1)
# plt.yticks(numpy.arange(0, 1.1, 0.1))
# plt.xticks(range(0, 12, 1))
# plt.xlabel('Month', size=14)
# plt.ylabel('Percentage of Tweets', size=14)
# plt.title('Abortion Twitter Sentiment (2021, Percentages, Weighted)', size=16)
# plt.plot(df_2021_percentages_weighted['month'], df_2021_percentages_weighted['pos_percentage'], linewidth=1, label='positive', color='green')
# plt.plot(df_2021_percentages_weighted['month'], df_2021_percentages_weighted['neg_percentage'], linewidth=1, label='negative', color='red')
#
# # axis2 = plt.gca().twinx()
# # axis2.plot(df_2021_percentages['month'], df_2021_percentages['total_tweets'], linewidth=1, label='total')
#
# plt.legend(title='Tweet Sentiment')

# df = px.data.tips()
# fig = px.bar(df, x="total_bill", y="day", orientation='h')
# fig.show()

def create_df_from_csv(file_path):
    df = pd.read_csv(file_path)

    df['date'] = pd.to_datetime(df['date'])
    df.sort_values(by='date', inplace=True)
    df.groupby('date').count()

    # Get number of positive tweets for each date
    pos = df[df['sentiment'] == 'positive']
    pos_tweets = pos.groupby(['date', 'sentiment'], as_index=False).size()  # as_index creates relevant columns in a DF
    pos_tweets.rename({'size': 'positive_tweets'}, inplace=True, axis='columns')
    pos_tweets.drop({'sentiment'}, axis='columns')
    pos_likes_retweets = pos.groupby(['date'], as_index=False).sum()

    pos_final = pos_likes_retweets.copy()
    pos_final['positive_tweets'] = pos_tweets['positive_tweets']

    # Get number of negative tweets for each date
    neg = df[df['sentiment'] == 'negative']
    neg_tweets = neg.groupby(['date', 'sentiment'], as_index=False).size()  # as_index creates relevant columns in a DF
    neg_tweets.rename({'size': 'negative_tweets'}, inplace=True, axis='columns')
    neg_tweets.drop({'sentiment'}, axis='columns')
    neg_likes_retweets = neg.groupby(['date'], as_index=False).sum()

    neg_final = neg_likes_retweets.copy()
    neg_final['negative_tweets'] = neg_tweets['negative_tweets']

    # Create new DataFrame with date, positive_tweets, negative_tweets, engagements, and date breakdowns
    final_df = pos_final[['date', 'positive_tweets']]
    final_df['positive_retweets'] = pos_final['retweets']
    final_df['positive_likes'] = pos_final['likes']

    final_df['negative_tweets'] = neg_final['negative_tweets']
    final_df['negative_likes'] = neg_final['likes']
    final_df['negative_retweets'] = neg_final['retweets']

    final_df['total_tweets'] = final_df['positive_tweets'] + final_df['negative_tweets']
    final_df['day'] = pd.DatetimeIndex(final_df['date']).day
    final_df['month'] = final_df['date'].dt.month_name()
    final_df['year'] = pd.DatetimeIndex(final_df['date']).year
    final_df['positive_score'] = final_df['positive_tweets'] + final_df['positive_retweets'] + final_df[
        'positive_likes']
    final_df['negative_score'] = final_df['negative_tweets'] + final_df['negative_retweets'] + final_df[
        'negative_likes']
    final_df['total_score'] = final_df['positive_score'] + final_df['negative_score']

    return final_df


hover_data = ["positive_tweets", "negative_tweets", "positive_likes", "negative_likes", "positive_retweets",
              "negative_retweets", "total_score"]


class Plotter:

    def __init__(self, hashtag):
        self.hashtag = hashtag
        self.df = create_df_from_csv(pathlib.Path('.') / "data_files" / f"{hashtag}.csv")

    def plot_all_days(self):
        colors = []
        for positive_score, negative_score in zip(self.df['positive_score'], self.df['negative_score']):
            if positive_score > negative_score:
                colors.append('blue')
            elif positive_score < negative_score:
                colors.append('red')
            else:
                colors.append('')

        plot = px.bar(self.df, x="date", y="total_score",
                     hover_data=hover_data, height=500, title="Daily View", color=colors,
                     labels={"date": "Date", "total_score": "Total Engagement Score"})
        plot.update_layout(legend_title_text='Majority')
        plot.for_each_trace(lambda t: t.update(name={"blue": "positive", "red": "negative", '': ''}[t.name]))

        plot.write_html("templates/" + f'{self.hashtag}_all_days.html')

    def plot_month(self, month, year):
        month_df = self.df.copy()
        month_df = month_df.loc[(month_df['month'] == month) & (month_df['year'] == year)]
        plot = px.bar(month_df, x="day", y=["positive_score", "negative_score"], title=f"{month} {year} Data",
                      hover_data=hover_data,
                      labels={"day": "Day", "value": "Engagement Score"})
        plot.update_layout(legend_title_text='Value', xaxis={'tickmode': 'linear', 'dtick': 1})

        plot.write_html(f'{self.hashtag}_{month}-{year}.html')

    def plot_year(self, year):
        # Now, let's zoom out to consider a whole year at once (weighted)
        year_df = self.df.copy()
        year_df = year_df.loc[(year_df['year'] == year)]
        year_df.reindex(columns=['date', 'month', 'day', 'year', 'positive_tweets', 'negative_tweets', 'total_tweets'])
        year_df = year_df.groupby(['month'], as_index=False).sum()

        # Sort by month for easier reading and drop unnecessary columns
        months_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                        'November', 'December']
        year_df['month'] = pd.Categorical(year_df['month'], categories=months_order, ordered=True)
        year_df.sort_values(by='month', inplace=True)

        plot = px.bar(year_df, x="month", y=["positive_score", "negative_score"], title=f"{year} Data",
                      hover_data=hover_data,
                      labels={"month": "Month", "value": "Engagement Score"})
        plot.update_layout(legend_title_text='Value')

        plot.write_html(f'{self.hashtag}_{year}.html')

