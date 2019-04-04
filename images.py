import tempfile
from tempfile import TemporaryFile

import cv2
import os

from google.cloud import storage


def extract(video_id, frames, tmp):
    # Read the video from specified path
    #cam = cv2.VideoCapture(os.path.join('Bucket', video_id + '.mp4'))
    #cam = cv2.VideoCapture(tmp.name)
    temp_filename = os.path.join(tempfile.gettempdir(), tmp.name)
    local_temp_file = open(temp_filename, "w+")
    tmp.seek(0)
    local_temp_file.write(tmp.read())
    local_temp_file.close()

    cam = cv2.VideoCapture(local_temp_file.name)

    # try:
    #     if not os.path.exists(os.path.join('Bucket', video_id)):
    #         os.makedirs(os.path.join('Bucket', video_id))
    # except OSError:
    #     print('Error: Creating directory of data')

    # frame
    currentframe = 0
    needed_frames = get_frames_number(frames)
    counter = 0

    storage_client = storage.Client.from_service_account_json('keys.json')
    bucket_name = 'galeata_magica_123'
    bucket = storage_client.get_bucket(bucket_name)


    while True:
        # reading from frame
        ret, frame = cam.read()
        # print('---------- ', ret, frame)
        if ret:
            if currentframe in needed_frames:
                # if video is still left continue creating images
                #name = os.path.join('Bucket', video_id, str(counter) + '.jpg')

                #print('Creating...' + name)
                # writing the extracted images

                #cv2.imwrite(name, frame)
                with TemporaryFile() as gcs_image:
                    frame.tofile(gcs_image)
                    gcs_image.seek(0)
                    #data = cv2.imencode('.jpg', frame)[1].tostring()
                    image_blob = bucket.blob(video_id + '/' + str(counter) + '.jpg')
                    image_blob.upload_from_file(gcs_image)
                # increasing counter so that it will
                # show how many frames are created
                counter += 1
            currentframe += 1

        else:
            break
    # Release all space and windows once done
    cam.release()
    cv2.destroyAllWindows()


def get_frames_number(shots):
    frames = list()
    for pair in shots:
        frames.append(int((pair[0] + pair[1])/2))
    return frames
