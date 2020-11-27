import gpxpy

# Parses the content of a GPX file for a ride and returns a dictionary containing
# all of its relevant data.
def parse_ride(file_content):
  gpx = gpxpy.parse(file_content)
  data = {}

  data['name'] = gpx.name
  data['time'] = gpx.time
  data['datapoints'] = []

  for track in gpx.tracks:
    for segment in track.segments:
      for point in segment.points:
        datapoint = {}
        datapoint['longitude'] = point.longitude
        datapoint['latitude'] = point.latitude
        datapoint['elevation'] = point.elevation
        datapoint['time'] = point.time

        for extension in point.extensions:
          if extension.tag in ['heartrate', 'cadence', 'power']:
            if extension.text != 'null':
                datapoint[extension.tag] = float(extension.text)

          # Strava's temperature data point in the GPX is misformatted.
          if 'Temperature' in extension.tag:
            if extension.text != 'null':
                datapoint['temperature'] = float(extension.text)

        data['datapoints'].append(datapoint)

  return data
