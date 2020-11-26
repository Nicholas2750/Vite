# SQL Queries

'''Get Requests'''
get_all_rides   = """
                SELECT ActivityId, ActivityName
                FROM Ride NATURAL JOIN Athlete NATURAL JOIN Auth
                WHERE ActivityName LIKE '%{query}%' AND Username='{username}';
                """

get_ride        = """
                SELECT ActivityId, ActivityName
                FROM Ride NATURAL JOIN Athlete NATURAL JOIN Auth
                WHERE ActivityId = {activity_id} AND Username='{username}';
                """

get_data_point  = """
                SELECT * 
                FROM (
                        SELECT @row := @row + 1 AS rownum, TimeStamp, ActivityID, Elevation, Power, Temperature, Cadence, Latitude, Longitude, Heartrate 
                        FROM ( SELECT @row:=0) r, DataPoint
                     ) ranked 
                WHERE rownum % {interval} = 1 AND ActivityID = {activity_id};
                """

get_lat_long    = """
                SELECT Latitude, Longitude
                FROM (
                        SELECT @row := @row + 1 AS rownum, ActivityID, Latitude, Longitude 
                        FROM ( SELECT @row:=0) r, DataPoint
                     ) ranked 
                WHERE rownum % {interval} = 1 AND ActivityID={activity_id};"""


'''Post Requests'''
add_ride        = """
                INSERT INTO Ride (AthleteID, ActivityName, Time) 
                VALUES ((
                        SELECT AthleteID FROM Auth WHERE Username='{username}'
                        ), '{activity_name}', '{time}');
                """

add_data_point  = """
                INSERT INTO DataPoint (TimeStamp, ActivityID, Elevation, Power, Temperature, Cadence, Latitude, Longitude, Heartrate)
                VALUES('{time_stamp}', {activity_id}, {elevation}, {power}, {temperature}, {cadence}, {latitude}, {longitude}, {heartrate});
                """

update_ride     = """
                UPDATE Ride SET ActivityName = '{activity_name}'
                WHERE ActivityId = {activity_id};
                """

register_user   = """
                INSERT INTO Auth (Username, Salt, Hash, AthleteID)
                VALUES ('{username}', '{salt}', '{hashed_password}', {athlete_id})
                """

get_salt        = """
                SELECT Salt From Auth
                WHERE Username = '{username}'
                """

login           = """
                SELECT COUNT(1) 
                FROM Auth 
                WHERE Username = '{username}' AND Hash = '{hashed_password}'
                """

add_athlete     = """
                INSERT INTO Athlete VALUES()
                """


'''Delete Requests'''
delete_ride     = """
                DELETE FROM Ride 
                WHERE ActivityId = {activity_id};
                """


'''Calorie Calculation'''
calculate_calories  = """
                    SELECT ((SUM(Power) / 1000 * 4.184) * {efficiency_value})
                    FROM DataPoint
                    WHERE ActivityId={activity_id};
                    """

'''Utils'''
get_row_count       = """
                    SELECT COUNT(TimeStamp)
                    FROM {Table}
                    WHERE ActivityID = {activity_id};
                    """

get_elapsed_time    = """
                    (SELECT TimeStamp FROM DataPoint WHERE ActivityID = (SELECT AthleteID FROM Auth WHERE Username='{username}') LIMIT 1)
                    UNION
                    (SELECT TimeStamp FROM DataPoint WHERE ActivityID={activity_id} LIMIT {row_count},1);
                    """

get_last_insert_id  = "SELECT LAST_INSERT_ID();"
