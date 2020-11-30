'''
Note:
docs are in section headers, read all the comments

if calling functions in app.py, MongoClient is already created there as variable "mongo", so literally 
call any function here exactly like the function definition

ex: (in app.py) mongoqueries.get_global_miles(mongo)
this returns a single number: the total miles for all athletes combined
'''

import math
import pymongo
from bson.code import Code
from datetime import datetime, timedelta
    
    
'''
this section: underscore beginning denotes private helper functions, don't use
'''
def _get_miles(mongo, query):
    mapper = Code("""
               function () {
                  var key = this.ActivityID;
                  var value = {"latitude": this.Latitude, "longitude": this.Longitude};
                  emit(key, value);
               }
               """)
    reducer = Code("""
                function (key, values) {
                    var dist = 0;
                    const R = 3959; // miles
                    
                    for (var i = 1; i < values.length; i++) {
                        const lat1 = values[i]["latitude"];
                        const lon1 = values[i]["longitude"];
                        const lat2 = values[i - 1]["latitude"];
                        const lon2 = values[i - 1]["longitude"];
                            
                        const φ1 = lat1 * Math.PI/180; // φ, λ in radians
                        const φ2 = lat2 * Math.PI/180;
                        const Δφ = (lat2-lat1) * Math.PI/180;
                        const Δλ = (lon2-lon1) * Math.PI/180;

                        const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                                  Math.cos(φ1) * Math.cos(φ2) *
                                  Math.sin(Δλ/2) * Math.sin(Δλ/2);
                        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

                        const d = R * c; // in miles
                        
                        dist += d;
                    }
                    return dist;
                }
                """)
    result = mongo.db.DataPoint.map_reduce(mapper, reducer, "tmp", query=query)
    result = list(result.find({}))
    ret = 0;
    for x in result:
        ret += x['value']
    return ret;
    
    
def _get_hours(mongo, query):
    q = mongo.db.DataPoint.aggregate( 
        [
            {"$match": query},
            {"$group": { 
                "_id": "$ActivityID",
                "a": {"$min": "$TimeStamp"},
                "b": {"$max": "$TimeStamp"},
            }},
            {"$project": {"_id": 0, 
                          "time": {"$subtract": ["$b", "$a"]}
            }},
        ]
    )
    
    ret = 0
    for x in q:
        ret += x['time']
        
    return ret / (1000 * 60 * 60)
    
    
def _get_calories(mongo, query):
    q = mongo.db.DataPoint.aggregate( 
        [
            {"$match": query},
            {"$group": { 
                "_id": None,
                "sum" : { "$sum": "$Power" }
            }},
            {"$project": {"_id": 0, 
                          "sum": 1
            }},
        ]
    )

    try:
      return (list(q)[0]['sum'] / 1000) * 4.184 * 0.22
    except:
      return 0
    

def _get_field_max(mongo, field):
    q = mongo.db.DataPoint.find_one({field: {"$ne": None}}, sort=[(field, pymongo.DESCENDING)])
    ride_id, val = q["ActivityID"], q[field]
    athlete_id = mongo.db.Ride.find_one({"ActivityID": ride_id})["AthleteID"]
    username = mongo.db.Auth.find_one({"AthleteID": athlete_id})["Username"]
    return [username, val]

def _get_field_min(mongo, field):
    q = mongo.db.DataPoint.find_one({field: {"$ne": None}}, sort=[(field, pymongo.ASCENDING)])
    ride_id, val = q["ActivityID"], q[field]
    athlete_id = mongo.db.Ride.find_one({"ActivityID": ride_id})["AthleteID"]
    username = mongo.db.Auth.find_one({"AthleteID": athlete_id})["Username"]
    return [username, val]
    
    
    
'''
all functions in this section return a single number
'''    
def get_global_miles(mongo):
    return _get_miles(mongo, query={})


def get_global_miles_last_week(mongo):
    return _get_miles(mongo, query={"TimeStamp": {"$gte": datetime.now() - timedelta(days=7)}})
    
    
def get_global_miles_last_month(mongo):
    return _get_miles(mongo, query={"TimeStamp": {"$gte": datetime.now() - timedelta(days=31)}})
    
    
def get_global_miles_last_year(mongo):
    return _get_miles(mongo, query={"TimeStamp": {"$gte": datetime.now() - timedelta(days=365)}})

    
def get_global_hours(mongo):
    return _get_hours(mongo, query={})
    
    
def get_global_hours_last_week(mongo):
    return _get_hours(mongo, query={"TimeStamp": {"$gte": datetime.now() - timedelta(days=7)}})


def get_global_hours_last_month(mongo):
    return _get_hours(mongo, query={"TimeStamp": {"$gte": datetime.now() - timedelta(days=31)}})


def get_global_hours_last_year(mongo):
    return _get_hours(mongo, query={"TimeStamp": {"$gte": datetime.now() - timedelta(days=365)}})
    
    
def get_global_calories(mongo):
    return _get_calories(mongo, query={})
    
    
def get_global_calories_last_week(mongo):
    return _get_calories(mongo, query={"TimeStamp": {"$gte": datetime.now() - timedelta(days=7)}})


def get_global_calories_last_month(mongo):
    return _get_calories(mongo, query={"TimeStamp": {"$gte": datetime.now() - timedelta(days=31)}})


def get_global_calories_last_year(mongo):
    return _get_calories(mongo, query={"TimeStamp": {"$gte": datetime.now() - timedelta(days=365)}})
        
    
def get_global_activities(mongo):
    return mongo.db.Ride.count()
    
    
def get_global_activities_last_week(mongo):
    return mongo.db.Ride.count({"TimeStamp": {"$gte": datetime.now() - timedelta(days=7)}})


def get_global_activities_last_month(mongo):
    return mongo.db.Ride.count({"TimeStamp": {"$gte": datetime.now() - timedelta(days=31)}})


def get_global_activities_last_year(mongo):
    return mongo.db.Ride.count({"TimeStamp": {"$gte": datetime.now() - timedelta(days=365)}})



'''
get_leaderboard returns a dictionary

d["week"]: list of usernames of athletes ranked by miles for the past week
d["month"]: list of usernames of athletes ranked by miles for the past month
d["year"]: list of usernames of athletes ranked by miles for the past year
'''
def get_leaderboard(mongo):
    usernames = [x["Username"] for x in mongo.db.Auth.find({})]
    
    subtract_days = [7, 31, 365]
    hours = []
    
    for username in usernames:
        athlete_id = mongo.db.Auth.find({"Username": username})[0]["AthleteID"]
        ids = [x["ActivityID"] for x in mongo.db.Ride.find({"AthleteID": athlete_id})]

        tmp = [username]
        for s in subtract_days:
            q = mongo.db.DataPoint.aggregate( 
                [
                    {"$match": {"ActivityID": {"$in": ids}, "TimeStamp": {"$gte": datetime.now() - timedelta(days=s)}}},
                    {"$group": { 
                        "_id": "$ActivityID",
                        "a": {"$min": "$TimeStamp"},
                        "b": {"$max": "$TimeStamp"},
                    }},
                    {"$project": {"_id": 0, 
                                  "time": {"$subtract": ["$b", "$a"]}
                    }},
                ]
            )
            
            total = 0
            for x in q:
                total += x['time']
            tmp.append(total)
        hours.append(tmp)
    
    week_leaderboard = [x[0] for x in sorted(hours, key=lambda k: k[1], reverse=True)]
    month_leaderboard = [x[0] for x in sorted(hours, key=lambda k: k[2], reverse=True)]
    year_leaderboard = [x[0] for x in sorted(hours, key=lambda k: k[3], reverse=True)]
    
    return {'week': week_leaderboard, 'month': month_leaderboard, 'year': year_leaderboard}



'''
all functions in this section return a list with 2 elements
the first element is the username
the second element is a number
'''
def get_athlete_max_miles(mongo):
    q = mongo.db.Ride.aggregate( 
        [
            {"$group": { 
                "_id": "$AthleteID",
                "activities": {"$addToSet": "$ActivityID"},
            }},
            {"$project": {"_id": 1, "activities": 1}}
        ]
    )
    
    username = None
    max_miles = 0
    
    for x in q:
        athlete_id, activities = x['_id'], x['activities']
        miles = _get_miles(mongo, query={"ActivityID": {"$in": activities}})
        if (miles > max_miles):
            max_miles = miles
            username = mongo.db.Auth.find_one({"AthleteID": athlete_id})["Username"]
    return [username, max_miles]
    
    
def get_athlete_max_hours(mongo):
    q = mongo.db.Ride.aggregate( 
        [
            {"$group": { 
                "_id": "$AthleteID",
                "activities": {"$addToSet": "$ActivityID"},
            }},
            {"$project": {"_id": 1, "activities": 1}}
        ]
    )
    
    username = None
    max_hours = 0
    
    for x in q:
        athlete_id, activities = x['_id'], x['activities']
        hours = _get_hours(mongo, query={"ActivityID": {"$in": activities}})
        if (hours > max_hours):
            max_hours = hours
            username = mongo.db.Auth.find_one({"AthleteID": athlete_id})["Username"]
    return [username, max_hours]
    
    
def get_athlete_max_elevation(mongo):
    return _get_field_max(mongo, "Elevation")

def get_athlete_max_cadence(mongo):
    return _get_field_max(mongo, "Cadence")


def get_athlete_max_power(mongo):
    return _get_field_max(mongo, "Power")


def get_athlete_max_temperature(mongo):
    return _get_field_max(mongo, "Temperature")


def get_athlete_max_latitude(mongo):
    return _get_field_max(mongo, "Latitude")


def get_athlete_max_longitude(mongo):
    return _get_field_max(mongo, "Longitude")


def get_athlete_max_heartrate(mongo):
    return _get_field_max(mongo, "Heartrate")


def get_athlete_min_elevation(mongo):
    return _get_field_min(mongo, "Elevation")


def get_athlete_min_temperature(mongo):
    return _get_field_min(mongo, "Temperature")


def get_athlete_min_latitude(mongo):
    return _get_field_min(mongo, "Latitude")


def get_athlete_min_longitude(mongo):
    return _get_field_min(mongo, "Longitude")


'''
get distance of ride
'''
def get_distance_of_ride(mongo, ride_id):
    return _get_miles(mongo, query={"ActivityID": ride_id})


'''
user analysis (ARCHIVED)
'''

def get_total_miles(mongo, username):
    athlete_id = mongo.db.Auth.find({"Username": username})[0]["AthleteID"]    
    ids = [x["ActivityID"] for x in list(mongo.db.Ride.find({"AthleteID": athlete_id}))]
    
    return _get_miles(mongo, query={"ActivityID": {"$in": ids}})

def get_total_hours(mongo, username):
    athlete_id = mongo.db.Auth.find({"Username": username})[0]["AthleteID"]
    ids = [x["ActivityID"] for x in mongo.db.Ride.find({"AthleteID": athlete_id})]

    q = mongo.db.DataPoint.aggregate( 
        [
            {"$match": {"ActivityID": {"$in": ids}}},
            {"$group": { 
                "_id": "$ActivityID",
                "a": {"$min": "$TimeStamp"},
                "b": {"$max": "$TimeStamp"},
            }},
            {"$project": {"_id": 0, 
                          "time": {"$subtract": ["$b", "$a"]}
            }},
        ]
    )
    
    ret = 0
    for x in q:
        ret += x['time']
        
    return ret / (1000 * 60 * 60)
    
def get_total_calories(mongo, username):
    athlete_id = mongo.db.Auth.find({"Username": username})[0]["AthleteID"]    
    ids = [x["ActivityID"] for x in list(mongo.db.Ride.find({"AthleteID": athlete_id}))]
        
    q = mongo.db.DataPoint.aggregate( 
        [
            {"$match": {"ActivityID": {"$in": ids}}},
            {"$group": { 
                "_id": None,
                "sum" : { "$sum": "$Power" }
            }},
            {"$project": {"_id": 0, 
                          "sum": 1
            }},
        ]
    )
    
    q = list(q)
    return (q[0]['sum'] / 1000) * 4.184 * 0.22
        
def get_total_activities(mongo, username):
    athlete_id = mongo.db.Auth.find({"Username": username})[0]["AthleteID"]
    ids = [x["ActivityID"] for x in mongo.db.Ride.find({"AthleteID": athlete_id})]
    return mongo.db.Ride.count_documents({"ActivityID": {"$in": ids}})

