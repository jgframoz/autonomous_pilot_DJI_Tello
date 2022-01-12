import cv2
import mediapipe as mp
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils
from mediapipe.framework.formats import location_data_pb2
import numpy as np

face_detection = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)
fbRange = [6200, 6800]

def draw_simple_info_text(img, brect, info_text, color):
	cv2.rectangle(img, (brect[0], brect[1]), (brect[2], brect[1] - 22), color, -1)

	cv2.putText(img, info_text, (brect[0] + 5, brect[1] - 4),
			   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

def bbox_area(rect_start_point,rect_end_point):
	if rect_start_point != None and rect_end_point != None:
		x1, y1 = rect_start_point
		x2, y2 = rect_end_point
		w = x2-x1
		h = y2-y1
		cx = x1 + w // 2
		cy = y1 + h // 2
		area = w * h
		return cx, cy, area
	else:
		return 0,0,0


def process_face(img, face):
	if not face.location_data:
		return
	if img.shape[2] != 3: #RGB_CHANNELS
		raise ValueError('Input image must contain three channel rgb data.')
	
	image_rows, image_cols, _ = img.shape

	location = face.location_data
	if location.format != location_data_pb2.LocationData.RELATIVE_BOUNDING_BOX:
		raise ValueError('LocationData must be relative for this drawing funtion to work.')

	# Draws bounding box if exists.
	if not location.HasField('relative_bounding_box'):
		return

	relative_bounding_box = location.relative_bounding_box
	

	rect_start_point = mp_drawing._normalized_to_pixel_coordinates(\
		relative_bounding_box.xmin, relative_bounding_box.ymin, image_cols,\
		image_rows)

	rect_end_point = mp_drawing._normalized_to_pixel_coordinates(\
		relative_bounding_box.xmin + relative_bounding_box.width,\
		relative_bounding_box.ymin + +relative_bounding_box.height, image_cols,\
		image_rows)
	
	cx, cy, area = bbox_area(rect_start_point,rect_end_point)

	return img, [cx, cy], area, rect_start_point, rect_end_point


def findNearestFaces(img):

	faceListCenters = []
	faceListAreas = []

	# Flip the image horizontally for a later selfie-view display, and convert
	# the BGR image to RGB.
	img = cv2.cvtColor(cv2.flip(img, 1), cv2.COLOR_BGR2RGB)
	# To improve performance, optionally mark the image as not writeable to
	# pass by reference.
	img.flags.writeable = False
	results = face_detection.process(img)

	# Draw the face detection annotations on the image.
	img.flags.writeable = True
	img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
	if results.detections:
		for face in results.detections:
			img, center, area, rect_start_point, rect_end_point  = process_face(img, face)
			if rect_start_point != None and rect_end_point != None:
				draw_face(img, face, rect_start_point, rect_end_point, (50,205,50), 2) # refactor
				faceListCenters.append(center)
				faceListAreas.append(area)

		if len(faceListAreas) > 0:
			m = faceListAreas.index(max(faceListAreas))
			return img, faceListCenters[m], faceListAreas[m]
	else:
		return img, [0,0], 0
		
	return img, [0,0], 0

def draw_face(image, face, rect_start_point, rect_end_point, color, thickness):

	cv2.rectangle(image, rect_start_point, rect_end_point, color, thickness)
	cv2.putText(image, 'face detected', (rect_start_point[0], rect_start_point[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
	cv2.putText(image, 'score: %.2f'% face.score[0], (rect_start_point[0]+5, rect_start_point[1]+30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
	#cv2.putText(image, 'area: %.0f'% bbox_area(rect_start_point,rect_end_point), (rect_start_point[0], rect_start_point[1]-30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

def trackFace(tello, center, area, w, pid, pError) :
    fb = 0

    x,y = center[0], center[1]
    print(x,y)

    error = x - w//2 #how far it is from the center

    print(error)
    yaw = pid[0] * error + pid[1] * (error - pError)
    yaw = int(np.clip(yaw, -100,100))
    print(area)

    if area > fbRange[0] and area < fbRange[1]:
        fb = 0
    elif area > fbRange[1]:
        fb = -20
    elif area < fbRange[0] and area != 0:
        fb = 20
    if x == 0:
        yaw = 0
        error = 0

    return error, fb, yaw