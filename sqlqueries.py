# SQL Queries

'''Get Requests'''
get_ride = "SQL HERE"
get_race = "SQL HERE"
get_athlete = "SQL HERE"
get_data_point = "SQL HERE"

'''Post Requests'''
add_ride = "INSERT INTO Ride (AthleteID, ActivityName, Time) VALUES ({athlete_id}, '{activity_name}', '{time}');"
get_last_insert_id = "SELECT LAST_INSERT_ID();"
add_data_point = "INSERT INTO DataPoint (TimeStamp, ActivityID, Elevation, Power, Temperature, Cadence, Latitude, Longitude, Heartrate) VALUES('{time_stamp}', {activity_id}, {elevation}, {power}, {temperature}, {cadence}, {latitude}, {longitude}, {heartrate});"
add_race = "SQL HERE"
add_athlete = "SQL HERE"

'''Put Requests'''
modify_ride = "SQL HERE" # only activity name should be able to change
modify_race = "SQL HERE" # type, race_name, and date can change
modify_athlete = "SQL HERE" # only age, name can change

'''Delete Requests'''
delete_ride = "SQL HERE"
delete_athlete = "SQL HERE"


