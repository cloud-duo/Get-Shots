import cv2
import os


def extract(video_id, frames):
    # Read the video from specified path
    cam = cv2.VideoCapture(os.path.join('Bucket', video_id + '.mp4'))
    try:
        if not os.path.exists(os.path.join('Bucket', video_id)):
            os.makedirs(os.path.join('Bucket', video_id))
    except OSError:
        print('Error: Creating directory of data')

    # frame
    currentframe = 0
    needed_frames = get_frames_number(frames)
    counter = 0
    while True:
        # reading from frame
        ret, frame = cam.read()
        # print('---------- ', ret, frame)
        if ret:
            if currentframe in needed_frames:
                # if video is still left continue creating images
                name = os.path.join('Bucket', video_id, str(counter) + '.jpg')
                counter += 1
                print('Creating...' + name)
                # writing the extracted images
                cv2.imwrite(name, frame)
                # increasing counter so that it will
                # show how many frames are created
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
