import streamlit as st
import pandas as pd
import glob

def recompute_ub_ranking(arena_df):
    # From https://github.com/lm-sys/FastChat/blob/e208d5677c6837d590b81cb03847c0b9de100765/fastchat/serve/monitor/monitor.py#L51
    ranking = {}
    for i, model_a in enumerate(arena_df.index):
        ranking[model_a] = 1
        for j, model_b in enumerate(arena_df.index):
            if i == j:
                continue
            if (
                arena_df.loc[model_b]["lower"]
                > arena_df.loc[model_a]["upper"]
            ):
                ranking[model_a] += 1
    return ranking

def process_leaderboard(filepath):
    leaderboard = pd.read_csv(filepath)

    # Round scores to integers
    leaderboard['score'] = leaderboard['score'].round().astype(int)
    leaderboard['upper'] = leaderboard['upper'].round().astype(int)
    leaderboard['lower'] = leaderboard['lower'].round().astype(int)

    # Calculate the difference for upper and lower bounds
    leaderboard['upper_diff'] = leaderboard['upper'] - leaderboard['score']
    leaderboard['lower_diff'] = leaderboard['score'] - leaderboard['lower']

    # Combine the differences into a single column with +/- format
    leaderboard['confidence_interval'] = '+' + leaderboard['upper_diff'].astype(str) + ' / -' + leaderboard['lower_diff'].astype(str)

    rankings_ub = recompute_ub_ranking(leaderboard)
    leaderboard.insert(loc=0, column="Rank* (UB)", value=rankings_ub)
    leaderboard['Rank'] = leaderboard['score'].rank(ascending=False).astype(int)

    # Sort the leaderboard by rank and then by score
    leaderboard = leaderboard.sort_values(by=['Rank'], ascending=[True])
    
    return leaderboard

def process_user_leaderboard(filepath):
    NUM_SHOW_USERS = 14

    leaderboard = pd.read_csv(filepath)

    # Sort the leaderboard by votes
    leaderboard = leaderboard.sort_values(by=['count'], ascending=[False])

    return leaderboard.head(NUM_SHOW_USERS), len(leaderboard)

def build_leaderboard(leaderboard_table_file, user_leaderboard_table_file):
    st.title("Copilot Arena Leaderboard")
    st.write("Welcome to Copilot Arena leaderboard! 🏆")
    col1, col2 = st.columns(2)

    with col1:
        # Display leaderboard
        dataFrame = process_leaderboard(leaderboard_table_file)
        dataFrame = dataFrame.rename(
            columns= {
                "name": "Model",
                "confidence_interval": "Confidence Interval",
                "score": "Arena Score",
                "organization": "Organization",
                "wins": "Votes",
            }
        )

        column_order = ["Rank", "Rank* (UB)", "Model", "Arena Score", "Confidence Interval", "Votes", "Organization"]
        dataFrame = dataFrame[column_order]
        num_models = len(dataFrame) 
        total_votes = int(dataFrame['Votes'].sum())

        st.subheader("Model Leaderboard")
        st.write(f"This is the leaderboard of all {num_models} models, and their relative performance in Copilot Arena.")
        st.dataframe(dataFrame, hide_index=True)

    with col2:
        # Display user leaderboard
        dataFrame, num_users = process_user_leaderboard(user_leaderboard_table_file)
        dataFrame = dataFrame.rename(
            columns= {
                "userId": "User ID",
                "count": "Votes"
            }
        )
        column_order = ["User ID", "Votes"]
        dataFrame = dataFrame[column_order]

        st.subheader("User Leaderboard")
        st.write(f"This is the leaderboard of all the users. There are {num_users} users and a total of {total_votes} votes.")
        st.dataframe(dataFrame, hide_index=True)

    st.markdown("""
        ***Rank (UB)**: model's ranking (upper-bound), defined by one + the number of models that are statistically better than the target model.
        Model A is statistically better than model B when A's lower-bound score is greater than B's upper-bound score (in 95% confidence interval). \n
        **Confidence Interval**: represents the range of uncertainty around the Arena Score. It's displayed as +X / -Y, where X is the difference between the upper bound and the score, and Y is the difference between the score and the lower bound.
    """)

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    leaderboard_table_files = glob.glob("backend/leaderboard.csv")
    leaderboard_table_file = leaderboard_table_files[-1]

    user_leaderboard_table_files = glob.glob("backend/user_leaderboard.csv")
    user_leaderboard_table_file = user_leaderboard_table_files[-1]

    build_leaderboard(leaderboard_table_file, user_leaderboard_table_file)