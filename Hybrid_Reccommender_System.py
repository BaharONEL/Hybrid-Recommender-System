import pandas as pd
pd.set_option('display.max_columns', 20)

### Data Preparation ###
def create_user_movie_df():
    movie = pd.read_csv(r"C:\Users\Oguz\Desktop\DCMLBC06\HAFTA04\dataset\movie_lens_dataset\movie.csv")
    rating = pd.read_csv (r"C:\Users\Oguz\Desktop\DCMLBC06\HAFTA04\dataset\movie_lens_dataset\rating.csv")
    df = movie.merge(rating, how ="left", on="movieId")
    comment_counts = pd.DataFrame(df["title"].value_counts())          # filmler ve yapılan yorumları df e atadım
    common_movies = df[~df["title"].isin(comment_counts[comment_counts["title"] <= 1000].index)]                 # 1000 den fazla yoruma sahip olan filmleri common_movies df e atadım
    user_movie_df = common_movies.pivot_table(index=["userId"], columns=["title"], values="rating")
    return user_movie_df

user_movie_df = create_user_movie_df()


### Movies watched by the user to be recommended to determine ###
random_user = int(pd.Series(user_movie_df.index).sample(1, random_state=45).values)
random_user_df = user_movie_df[user_movie_df.index == random_user]
movies_watched = random_user_df.columns[random_user_df.notna().any()].tolist()  # movies watched by the user to be recommended

len(movies_watched) #How many movies did the user watch?

### Other users watching the same movies access their data and Ids ###
### People who watch the same movies as random user ###
movies_watched_df = user_movie_df[movies_watched]
movies_watched_df.shape  # The number of people who watched at least 1 same movie with the user to be recommended
user_movie_count =(movies_watched_df.T.notnull().sum()).reset_index()
user_movie_count.columns = ["userId", "movie_count"]
perc = len(movies_watched) * 50/100
users_same_movies = user_movie_count[user_movie_count["movie_count"] > perc]["userId"]   # id of users who have at least ½50 joint views with random user


### Most similar to the user to be suggested identify users ###
### Users with the same like structure as random user ###
final_df = pd.concat([movies_watched_df[movies_watched_df.index.isin(users_same_movies)],
                      random_user_df[movies_watched]])  # Merged random user and other users

corr_df = final_df.T.corr().unstack().sort_values().drop_duplicates()
corr_df = pd.DataFrame(corr_df, columns=["corr"])
corr_df.index.names = ['user_id_1', 'user_id_2']
corr_df = corr_df.reset_index()

## Bringing users with a correlation of ½65 and above with random user ##
top_users = corr_df[(corr_df["user_id_1"] == random_user) & (corr_df["corr"] >= 0.65)][
    ["user_id_2", "corr"]].reset_index(drop=True).sort_values(by="corr", ascending = False)
top_users.rename(columns={"user_id_2": "userId"}, inplace=True)

top_users   # Users with similar likes to random user

### Weighted Average Recommendation Score Calculate and keep the first 5 movies. ###

rating = pd.read_csv ("rating.csv")
top_users_ratings = top_users.merge(rating[["userId", "movieId", "rating"]], how='inner')

top_users_ratings = top_users_ratings[top_users_ratings["userId"] != random_user]

top_users_ratings['weighted_rating'] = top_users_ratings['corr'] * top_users_ratings['rating']

recommendation_df = top_users_ratings.groupby('movieId').agg({"weighted_rating": "mean"}).reset_index()

recommendation_df[recommendation_df["weighted_rating"] > 3.5]
movies_to_be_recommend = recommendation_df[recommendation_df["weighted_rating"] > 3.5].sort_values("weighted_rating", ascending=False)


## User's most recent highest rated movies watched
## Make an item-based suggestion based on the name of the movie.
# 5 recommendations user-based
# 5 suggestions item-based     # Make 10 suggestions. ##

movie = pd.read_csv("movie.csv")
rating = pd.read_csv ("rating.csv")
# Getting the id of the movie with the most up-to-date score from the movies that the user to be suggested gives 5 points #
movie_id = rating[(rating["userId"] == random_user) & (rating["rating"] ==5.0)].sort_values(by="timestamp", ascending=False)["movieId"][0:1].values[0]


movie_name = movie[movie['movieId'] == movie_id]['title'].values[0]
movie_name = user_movie_df[movie_name]

user_based_recommend_top5 = movies_to_be_recommend.merge(movie[["movieId","title"]]).loc[0:5,"title"]
movies_from_item_based =user_movie_df.corrwith(movie_name).sort_values(ascending=False).reset_index()['title'][1:6].tolist()