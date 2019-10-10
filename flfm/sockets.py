import os
import json
import shutil
from flask import current_app, url_for
from flask_socketio import emit, disconnect
from . import socketio

@socketio.on('prepare video')
def prepare_video(data):
    vid_dir = current_app.config['VIEWER_VIDEO_DIRECTORY']
    stream_video = os.path.join(vid_dir, data['data']['filename'])
    source_video = data['data']['shell_location']

    if not os.path.exists(stream_video):
        try:
            os.symlink(source_video, stream_video)
        except (OSError, NotImplementedError, AttributeError):
            shutil.copyfile(source_video, stream_video)

    video_url = url_for('static', filename=data['data']['filename'],
                         _external=True).replace('static', 'videos')

    emit('video ready', json.dumps(dict({
        'video_url': video_url,
    })))

@socketio.on('received video')
def received_video():
    disconnect()
