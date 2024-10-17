from flask import Flask, render_template, request
from mapGenerator import MapCreator

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_map', methods=['POST'])
def generate_map():
    # Define cameras (Boschmolenplas)
    cameras = [
        {
            'latitude': 51.176858,
            'longitude': 5.882079,
            'direction': -60,
            'width': 94,
            'reach': 200,
            'name': 'camera 1 red',
            'video_source': 'https://www.youtube.com/embed/4qOxFyZLcl0?si=VO9YbHXW7mDSENHO',
            'cone_outline_color': 'red',
            'cone_fill_color': 'lightred',
            'camera_outline_color': 'blue',
            'camera_fill_color': 'lightblue'
        },
        {
            'latitude': 51.179512,
            'longitude': 5.878201,
            'direction': 180,
            'width': 94,
            'reach': 200,
            'name': 'camera 2 blue',
            'video_source': 'https://www.youtube.com/embed/4qOxFyZLcl0?si=VO9YbHXW7mDSENHO',
            'cone_outline_color': 'blue',
            'cone_fill_color': 'lightblue',
            'camera_outline_color': 'red',
            'camera_fill_color': 'lightred'
        },
        {
            'latitude': 51.184346,
            'longitude': 5.876827,
            'direction': 278,
            'width': 137,
            'reach': 800,
            'name': 'camera 3 green',
            'video_source': 'https://www.youtube.com/embed/lffpBLDQqqc?si=H6um6OemAf8UQc56',
            'cone_outline_color': 'green',
            'cone_fill_color': 'lightgreen',
            'camera_outline_color': 'purple',
            'camera_fill_color': 'lightpurple'
        }
    ]

    # Define passage points (Boschmolenplas)
    passage_points = [
        (51.184965, 5.884337),
        (51.179639, 5.894701),
        (51.175684, 5.876698),
        (51.178336, 5.872226),
        (51.180796, 5.883265)
    ]

    latitude = float(request.form['latitude'])
    longitude = float(request.form['longitude'])
    name = request.form['name']
    area = int(request.form['area'])
    map_creator = MapCreator(latitude, longitude, name, area, 150, 20, cameras=cameras, passage_points=passage_points)
    map_name = map_creator.create_detailed_map()
    print(map_name)
    return render_template('template_map.html', map_name=map_name)

if __name__ == '__main__':
    app.run(debug=False)