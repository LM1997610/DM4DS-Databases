
import time
import pandas as pd

from tabulate import tabulate
from pymongo import MongoClient


# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['soccer_db']



pipeline = [

    {"$addFields": {"odds_diff": {"$abs": {"$subtract": [{"$ifNull": ["$B365H", 0]}, {"$ifNull": ["$B365A", 0]}]}}}     },

    {"$sort": {"odds_diff": -1}},
    {"$limit": 1},

    {"$lookup": {"from": "leagues",
                 "localField": "league_id",
                 "foreignField": "id",
                 "as": "league_info"}   },

    {"$unwind": "$league_info"},

    {"$lookup": {"from": "teams",
                 "localField": "home_team_api_id",
                 "foreignField": "team_api_id",
                 "as": "home_team_info"}    },

    {"$unwind": "$home_team_info"},

    {"$lookup": {"from": "teams",
                 "localField": "away_team_api_id",
                 "foreignField": "team_api_id",
                 "as": "away_team_info"}    },

    {"$unwind": "$away_team_info"},
    
    {"$project": {"_id": 0,
                  "league_id": "$league_info.name",
                  "season": 1,
                  "home_team": "$home_team_info.team_long_name",
                  "away_team": "$away_team_info.team_long_name",
                  "odds_diff": "$odds_diff"}   }   ]








start_time = time.time()

result = db.matches.aggregate(pipeline)

df = pd.DataFrame.from_records(result) 

print()
print(tabulate(df, headers='keys', tablefmt="github", numalign='center', stralign="center"))

print(f"\n Execution time: {time.time() - start_time:.3f} seconds")