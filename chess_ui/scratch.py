import pandas as pd

puzzles_df = pd.read_csv("C:\\Users\\wei0c\\Desktop\\school\\7-1\\CS-6320-NLP\\lichess_db_puzzle.csv")

fen = puzzles_df.iloc[0]['FEN']
moves = puzzles_df.iloc[0]['Moves']


print(moves)
print(type(moves))
