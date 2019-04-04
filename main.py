import tempfile
import cv2
from flask import Flask, jsonify, abort
from google.cloud import storage
import pymysql
from google.cloud import videointelligence


pymysql.install_as_MySQLdb()
# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)


@app.route('/shots/<video_id>', methods=['GET'])
def get_shots(video_id):
    storage_client = storage.Client.from_service_account_json('keys.json')
    bucket_name = 'galeata_magica_123'
    bucket = storage_client.get_bucket(bucket_name)

    blobs = bucket.list_blobs(prefix=video_id + "/")
    counter = 0
    for blob in blobs:
        counter += 1
    if counter != 0:
        return jsonify({"Counter": counter})

    blob = bucket.blob(video_id + '.mp4')

    with tempfile.NamedTemporaryFile() as temp_video:
        blob.download_to_file(temp_video)
        if not blob.exists():
            abort(404)
            return

        shots = analyze_shots(video_id + '.mp4')

        temp_video.seek(0)
        cam = cv2.VideoCapture(temp_video.name)

        currentframe = 0
        uploaded_image_counter = 0

        storage_client = storage.Client.from_service_account_json('keys.json')
        bucket_name = 'galeata_magica_123'
        bucket = storage_client.get_bucket(bucket_name)

        frames_per_second = cam.get(cv2.CAP_PROP_FPS)
        needed_frames = get_frames_number(shots, frames_per_second)

        while True:
            ret, frame = cam.read()
            if ret:
                if currentframe in needed_frames:
                    with tempfile.NamedTemporaryFile() as temporary_image:
                        path_temp_image = "".join([str(temporary_image.name), ".jpg"])
                        cv2.imwrite(path_temp_image, frame)
                        image_blob = bucket.blob(video_id + '/' + str(uploaded_image_counter) + '.jpg')
                        image_blob.upload_from_filename(path_temp_image)
                    uploaded_image_counter += 1
                currentframe += 1
            else:
                break
        cam.release()
        cv2.destroyAllWindows()

    return jsonify({"Counter": uploaded_image_counter})


def analyze_shots(path):
    """ Detects camera shot changes. """
    video_client = videointelligence.VideoIntelligenceServiceClient.from_service_account_json("keys.json")
    features = [videointelligence.enums.Feature.SHOT_CHANGE_DETECTION]
    operation = video_client.annotate_video('gs://galeata_magica_123/' + path, features=features)
    print('\nProcessing video for shot change annotations:')

    result = operation.result(timeout=120)
    print('\nFinished processing.')

    splitted_shots = list()
    for i, shot in enumerate(result.annotation_results[0].shot_annotations):
        start_time = (shot.start_time_offset.seconds +
                      shot.start_time_offset.nanos / 1e9)
        end_time = (shot.end_time_offset.seconds +
                    shot.end_time_offset.nanos / 1e9)
        new_tuple = (start_time, end_time)
        splitted_shots.append(new_tuple)
        print('\tShot {}: {} to {}'.format(i, start_time, end_time))
    return splitted_shots


@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    return response


def get_frames_number(shots, fps):
    frames = list()
    for pair in shots:
        frames.append(int((pair[0] + pair[1])/2))
    for i in range(0, len(frames)):
        frames[i] = int(frames[i] * fps)
    return frames


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
