import os
import tempfile

import cv2
import flask
from flask import Flask
from google.cloud import storage
import pymysql
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

    # destination_file_name = os.path.join('Bucket', video_id + '.mp4')
    # blob.download_to_file()


    #fd, path = tempfile.mkstemp()
    with tempfile.NamedTemporaryFile() as temp_video:
        blob.download_to_file(temp_video)

        shots = analyze_shots(video_id + '.mp4')
        #images.extract(video_id, shots, temp_video)

####################################################################################################
        # temp_filename = os.path.join(tempfile.gettempdir(), temp_video.name)
        # local_temp_file = open(temp_filename, mode='w')
        # temp_video.seek(0)
        # local_temp_file.write(temp_video.read())
        # local_temp_file.close()
        temp_video.seek(0)
        cam = cv2.VideoCapture(temp_video.name)
        currentframe = 0
        needed_frames = images.get_frames_number(shots)
        counter = 0
        print('Needed frames: ', needed_frames)
        storage_client = storage.Client.from_service_account_json('keys.json')
        bucket_name = 'galeata_magica_123'
        bucket = storage_client.get_bucket(bucket_name)

        frames_per_second = cam.get(cv2.CAP_PROP_FPS)

        for i in range(0, len(needed_frames)):
            needed_frames[i] = int(needed_frames[i] * frames_per_second)

        while True:
            # reading from frame
            ret, frame = cam.read()
            # print('---------- ', ret, frame)
            if ret:
                if currentframe in needed_frames:
                    with tempfile.NamedTemporaryFile() as gcs_image:
                        iName = "".join([str(gcs_image.name), ".jpg"])
                        # save image to temp file
                        cv2.imwrite(iName, frame)
                        # frame.tofile(gcs_image)
                        # gcs_image.seek(0)
                        # data = cv2.imencode('.jpg', gcs_image)[1].tostring()
                        image_blob = bucket.blob(video_id + '/' + str(counter) + '.jpg')
                        image_blob.upload_from_filename(iName)

                        # with NamedTemporaryFile() as temp:
                        #     # Extract name to the temp file
                        #     iName = "".join([str(temp.name), ".jpg"])
                        #     # save image to temp file
                        #     cv2.imwrite(iName, duplicate_image)


                    # increasing counter so that it will
                    # show how many frames are created
                    print('Counter: ', counter)
                    counter += 1
                print('Counter: ', currentframe)
                currentframe += 1

            else:
                break
        # Release all space and windows once done
        cam.release()
        cv2.destroyAllWindows()
####################################################################################################
    #os.remove(path)

    resp = flask.Response("200")
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


@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    return response


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
