# SQL Queries

'''Get Requests'''
get_all_rides = "SELECT ActivityId, ActivityName FROM Ride;"
get_ride = "SELECT ActivityId, ActivityName FROM Ride WHERE ActivityId = {activity_id};"
get_race = "SQL HERE"
get_athlete = "SQL HERE"
get_data_point = "SELECT * FROM DataPoint WHERE ActivityID = {activity_id};"

'''Post Requests'''
add_ride = "INSERT INTO Ride (AthleteID, ActivityName, Time) VALUES ({athlete_id}, '{activity_name}', '{time}');"
get_last_insert_id = "SELECT LAST_INSERT_ID();"
add_data_point = "INSERT INTO DataPoint (TimeStamp, ActivityID, Elevation, Power, Temperature, Cadence, Latitude, Longitude, Heartrate) VALUES('{time_stamp}', {activity_id}, {elevation}, {power}, {temperature}, {cadence}, {latitude}, {longitude}, {heartrate});"
add_race = "SQL HERE"
add_athlete = "SQL HERE"
update_ride = "UPDATE Ride SET ActivityName = '{activity_name}' WHERE ActivityId = {activity_id};"

'''Put Requests'''
modify_ride = "SQL HERE" # only activity name should be able to change
modify_race = "SQL HERE" # type, race_name, and date can change
modify_athlete = "SQL HERE" # only age, name can change

'''Delete Requests'''
delete_ride = "DELETE FROM Ride WHERE ActivityId = {activity_id};"
delete_athlete = "SQL HERE"


