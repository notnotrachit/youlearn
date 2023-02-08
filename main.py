from flask import Flask, request, jsonify, render_template, redirect
from deta import Deta
import requests

deta = Deta() 
app = Flask(__name__,
            static_url_path='/static', 
            static_folder='static')


invidious_base_url = 'https://inv.riverside.rocks'

def get_invidious_url():
    inv_api="https://api.invidious.io/instances.json?pretty=1&sort_by=api,health"
    r = requests.get(inv_api)
    data = r.json()
    return(data[0][1]['uri'])

@app.route('/')
def index():
    courses = deta.Base('courses').fetch().items
    invidious_base_url = get_invidious_url()
    for i in courses:
        i['complete_percentage'] = round((len(i['watched'])/i['videoCount'])*100)
    return render_template('dashboard.html', courses=courses)


@app.route('/create_course', methods=['GET'])
def create_course():
    return render_template('new_course.html')

@app.route('/new_course', methods=['POST'])
def new_course():
        url = request.form['url']
        if url.startswith('https://www.youtube.com/playlist?')==False:
            return jsonify({'success': False, 'error': 'Please enter a valid YouTube playlist URL'})
        else:
            playlist_id= url.split('=')[1]
            invidious_base_url = get_invidious_url()
            invidious_url = f'{invidious_base_url}/api/v1/playlists/{playlist_id}'
            r = requests.get(invidious_url)
            data = r.json()
            watched = {'watched': []}
            data.update(watched)
            data['playlistThumbnail'] = data['playlistThumbnail'].replace('hqdefault', 'maxresdefault')
            base = deta.Base('courses')
            base.put(data)
            return jsonify({'success': True})

@app.route('/course/<id>', methods=['GET'])
def course(id):
    invidious_base_url = get_invidious_url()
    course = deta.Base('courses').fetch({'key': id}).items[0]
    all_videos = course['videos']
    watched = course['watched']
    unwatched = [i for i in all_videos if i not in watched]
    current_video = unwatched[0]
    try:
        next_video = unwatched[1]
    except:
        next_video = None
    try:
        previous_video = watched[-1]
    except:
        previous_video = None
    complete_percentage = round((len(watched)/course['videoCount'])*100)
    return render_template('course.html', course=course, current_video=current_video, next=next_video, prev=previous_video, complete_percentage=complete_percentage)

@app.route('/course/<id>/watched', methods=['POST'])
def watched(id):
    base = deta.Base('courses')
    course = base.fetch({'key': id}).items[0]
    watched = course['watched']
    watched.append(request.form['video'])
    base.update({'watched': watched}, id)
    return jsonify({'success': True})

@app.route('/course/<id>/unwatched', methods=['POST'])
def unwatched(id):
    base = deta.Base('courses')
    course = base.fetch({'key': id}).items[0]
    watched = course['watched']
    watched.remove(request.form['video'])
    base.update({'watched': watched}, id)
    return jsonify({'success': True})

@app.route('/course/<id>/video/<video_id>', methods=['GET'])
def video(id, video_id):
    invidious_base_url = get_invidious_url()
    course = deta.Base('courses').fetch({'key': id}).items[0]
    all_videos = course['videos']
    video = [i for i in all_videos if i['videoId'] == video_id][0]
    video_api_url = f'{invidious_base_url}/api/v1/videos/{video_id}'
    r = requests.get(video_api_url)
    video_data = r.json()
    description = video_data['description'].replace('\n', '<br>')
    return render_template('vid.html', course=course, video=video, inv_url=invidious_base_url, description=description, all_videos=all_videos)

@app.route('/course/<id>/notes', methods=['POST'])
def notes(id):
    updated_notes = request.form['textarea']
    base = deta.Base('courses')
    base.update({'notes': updated_notes}, id)
    return jsonify({'success': True})


@app.route('/course/notes/<id>', methods=['GET'])
def get_notes(id):
    course = deta.Base('courses').fetch({'key': id}).items[0]
    notes = course['notes']
    return render_template('course_notes.html', course=course, notes=notes)


@app.route('/__space/v0/actions', methods=['POST'])
def actions():
    action = request.json
    if action['event']['id'] == 'update_playlists':
        all_courses = deta.Base('courses').fetch().items
        for i in all_courses:
            playslist_id = i['playlistId']
            invidious_base_url = get_invidious_url()
            invidious_url = f'{invidious_base_url}/api/v1/playlists/{playlist_id}'
            r = requests.get(invidious_url)
            data = r.json()
            videos = data['videos']
            video_count = data['videoCount']
            base = deta.Base('courses')
            base.update({'videos': videos, 'videoCount': video_count}, i['key'])
        return jsonify({'success': True})