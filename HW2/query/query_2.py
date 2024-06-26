
import time
import pandas as pd

from tabulate import tabulate
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['soccer_db']
season = "2009/2010"


## 2) Find the Champion of each league in a specific season 

pipeline = [
    
    {
        "$match": {
            "season": season,
            "$expr": {"$eq": ["$home_team_goal", "$away_team_goal"]}
        }
    },
    {
        
        "$facet": {
            "home_draws": [
                {
                    "$group": {
                        "_id": {"league_id": "$league_id", "team_id": "$home_team_api_id"},
                        "num_draws": {"$sum": 1}
                    }
                }
            ],
            "away_draws": [
                {
                    "$group": {
                        "_id": {"league_id": "$league_id", "team_id": "$away_team_api_id"},
                        "num_draws": {"$sum": 1}
                    }
                }
            ]
        }
    },
    {
        
        "$project": {
            "all_draws": {
                "$concatArrays": ["$home_draws", "$away_draws"]
            }
        }
    },
    {
        
        "$unwind": "$all_draws"
    },
    {
        
        "$replaceRoot": {
            "newRoot": "$all_draws"
        }
    },
    {
        "$group": {
            "_id": {"league_id": "$_id.league_id", "team_id": "$_id.team_id"},
            "num_draws": {"$sum": "$num_draws"}
        }
    },

    
    {
        
        "$unionWith": {
            "coll": "matches",
            "pipeline": [
                {
                    "$match": {
                        "season": season,
                        "$expr": {"$gt": ["$home_team_goal", "$away_team_goal"]}
                    }
                },
                {
                    "$group": {
                        "_id": {"league_id": "$league_id", "team_id": "$home_team_api_id"},
                        "num_wins": {"$sum": 1}
                    }
                }
            ]
        }
    },
    {
        
        "$unionWith": {
            "coll": "matches",
            "pipeline": [
                {
                    "$match": {
                        "season": season,
                        "$expr": {"$gt": ["$away_team_goal", "$home_team_goal"]}
                    }
                },
                {
                    "$group": {
                        "_id": {"league_id": "$league_id", "team_id": "$away_team_api_id"},
                        "num_wins": {"$sum": 1}
                    }
                }
            ]
        }
    },
    {
        "$group": {
            "_id": {"league_id": "$_id.league_id", "team_id": "$_id.team_id"},
            "num_draws": {"$first": "$num_draws"},
            "num_wins": {"$sum": "$num_wins"}
        }
    },

    
    
    {
        "$project": {
            "draws": "$num_draws",
            "wins": "$num_wins"
        }
    },

    
    {
        "$lookup": {
            "from": "teams",
            "localField": "_id.team_id",
            "foreignField": "team_api_id",
            "as": "team"
        }
    },
    
    {
        "$unwind": "$team"
    },
    
    {
        "$project": {
            "league_id": "$_id.league_id",
            "team_long_name": "$team.team_long_name",
            "wins": 1,
            "draws": 1
        }
    },

    
    {
        "$project": {
            "league_id": 1,
            "team_long_name": 1,
            "points": {"$add": [{"$multiply": ["$wins", 3]}, "$draws"]}
        }
    },
    
    {
        "$sort": {"league_id": 1, "points": -1}
    },

    {
        "$group": {
            "_id": "$league_id",
            "team": {"$first": "$team_long_name"},
            "points": {"$first": "$points"}
        }
    },

    
    {
        "$lookup": {
            "from": "leagues",
            "localField": "_id",
            "foreignField": "id",
            "as": "league"
        }
    },
    
    {
        "$unwind": "$league"
    },

    {
        "$project": {
            "league_name": "$league.name",
            "team": 1,
            "points": 1
        }
    }
]

start_time = time.time()

result = list(db.matches.aggregate(pipeline))

df = pd.DataFrame.from_records(result) 

print()
print(tabulate(df, headers='keys', tablefmt="github", numalign='center', stralign="center"))

print(f"\n Execution time: {time.time() - start_time:.3f} seconds")
