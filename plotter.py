import pathlib
import plotly.express as px
import pandas as pd


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
                     hover_data=hover_data, height=500, title="All Data " + f"(#{self.hashtag})", color=colors,
                     labels={"date": "Date", "total_score": "Total Engagement Score"})
        plot.update_layout(legend_title_text='Majority')
        plot.for_each_trace(lambda t: t.update(name={"blue": "positive", "red": "negative", '': ''}[t.name]))

        # Prevent bars becoming difficult to see as time range increases
        plot.update_layout(bargap=0.1, bargroupgap = 0,)
        plot.update_traces(marker_line_width=0, selector=dict(type="bar"))

        file_name = f'{self.hashtag}_all_data.html'
        html_path = "templates/" + file_name
        plot.write_html(html_path)
        return file_name

    def plot_month(self, month, year):
        month_df = self.df.copy()
        month_df = month_df.loc[(month_df['month'] == month) & (month_df['year'] == year)]

        # If no data found, return
        if len(month_df) == 0:
            return None

        plot = px.bar(month_df, x="day", y=["positive_score", "negative_score"],
                      title=f"{month} {year} Data " + f"(#{self.hashtag})",
                      hover_data=hover_data,
                      labels={"day": "Day", "value": "Engagement Score"})
        plot.update_layout(legend_title_text='Value', xaxis={'tickmode': 'linear', 'dtick': 1})

        file_name = f'{self.hashtag}_{month}-{year}.html'
        html_path = "templates/" + file_name
        plot.write_html(html_path)

        return file_name

    def plot_year(self, year):
        # Now, let's zoom out to consider a whole year at once (weighted)
        year_df = self.df.copy()
        year_df = year_df.loc[(year_df['year'] == year)]

        # If no data found, return
        if len(year_df) == 0:
            print(f"NO DATA FOR {year}")
            return None

        year_df.reindex(columns=['date', 'month', 'day', 'year', 'positive_tweets', 'negative_tweets', 'total_tweets'])
        year_df = year_df.groupby(['month'], as_index=False).sum()

        # Sort by month for easier reading and drop unnecessary columns
        months_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                        'November', 'December']
        year_df['month'] = pd.Categorical(year_df['month'], categories=months_order, ordered=True)
        year_df.sort_values(by='month', inplace=True)

        plot = px.bar(year_df, x="month", y=["positive_score", "negative_score"],
                      title=f"{year} Data " + f"(#{self.hashtag})",
                      hover_data=hover_data,
                      labels={"month": "Month", "value": "Engagement Score"})
        plot.update_layout(legend_title_text='Value')

        file_name = f'{self.hashtag}_{year}.html'
        html_path = "templates/" + file_name
        plot.write_html(html_path)
        return file_name
