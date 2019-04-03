import os

import flask
import sqlalchemy
from flask import Flask, request
from google.cloud import storage
import uuid
import pymysql
import argparse
import images
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
    blob = bucket.blob(video_id + '.mp4')
    if not os.path.exists('Bucket'):
        os.mkdir('Bucket')
    destination_file_name = os.path.join('Bucket', video_id + '.mp4')
    blob.download_to_filename(destination_file_name)
    print('Blob {} downloaded to {}.'.format(
        bucket_name,
        destination_file_name))

    # parser = argparse.ArgumentParser(
    #     description=__doc__,
    #     formatter_class=argparse.RawDescriptionHelpFormatter)
    # parser.add_argument('path', help='GCS path for shot change detection.')
    # args = parser.parse_args()
    #
    # analyze_shots(args.path)
    shots = analyze_shots(video_id + '.mp4')
    images.extract(video_id, shots)

    dirs = os.listdir(os.path.join('Bucket', video_id))

    # This would print all the files and directories
    for file in dirs:
        image_blob = bucket.blob(video_id + '/' + file)
        image_blob.upload_from_filename(os.path.join('Bucket', video_id, file))

    resp = flask.Response("Foo bar baz")
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


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


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
