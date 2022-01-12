import cv2
import mediapipe as mp
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils
from mediapipe.framework.formats import location_data_pb2
import time

from djitellopy import Tello

import face_tracking

TELLO_STATE = 2

TELLO_ON = True
TAKEOFF = True

cap_width = 720
cap_height = 480

pid = [0.3, 0.5, 0]

tello = Tello()

def main():
	pError = 0

	if TELLO_ON:

		print('Starting')

		tello = Tello()
		tello.connect()

		if tello.get_battery() < 20:
			return

		tello.streamon()

		if TAKEOFF == True:
			
			tello.takeoff()
			print('Takeoff')
			tello.send_rc_control(0, 0, 30, 0)
			time.sleep(0.5)

		while(True) :
			if tello.get_battery() < 20:
				tello.land()
				break

			img = tello.get_frame_read().frame
			img = cv2.resize(img, (cap_width, cap_height))

			key = cv2.waitKey(10)
			if key == 27:
				tello.land()
				break
			elif key == ord('1'): #stay
				TELLO_STATE = 1
			elif key == ord('2'): #keyboard
				TELLO_STATE = 2
			elif key == ord('3'): #facetracking
				TELLO_STATE = 3
			elif key == ord('4'):
				TELLO_STATE = 4

			if TELLO_STATE == 1: #stay
				continue 
			if TELLO_STATE == 2: #keyboard
				if key == ord('w'):
					tello.move_forward(30)
				elif key == ord('s'):
					tello.move_back(30)
				elif key == ord('a'):
					tello.move_left(30)
				elif key == ord('d'):
					tello.move_right(30)
				elif key == ord('e'):
					tello.rotate_clockwise(30)
				elif key == ord('q'):
					tello.rotate_counter_clockwise(30)
				elif key == ord('r'):
					tello.move_up(30)
				elif key == ord('f'):
					tello.move_down(30)
			if TELLO_STATE == 3:
				img, center, area = face_tracking.finwdNearestFaces(img)
				pError, fb, yaw = face_tracking.trackFace(1, center, area, cap_width, pid, pError, TAKEOFF=TAKEOFF) 

				if TAKEOFF == True: tello.send_rc_control(0, fb, 0, yaw)
			if TELLO_STATE == 4:
				continue    

			cv2.imshow("Tello",img)

	
	if not TELLO_ON:
		# For webcam input:
		# Camera preparation ###############################################################
		cap = cv2.VideoCapture(0)
		cap.set(cv2.CAP_PROP_FRAME_WIDTH, cap_width)
		cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cap_height)

		while cap.isOpened():
			success, img = cap.read()
			if not success:
				print("Ignoring empty camera frame.")
				# If loading a video, use 'break' instead of 'continue'.
				continue
			
			img, center, area = face_tracking.findNearestFaces(img)
			print(area)
			pError, fb, yaw = face_tracking.trackFace(1, center, area, cap_width, pid, pError, TAKEOFF=TAKEOFF) 

			if TAKEOFF == True: tello.send_rc_control(0, fb, 0, yaw)

			cv2.imshow('MediaPipe Face Detection', img)
			if cv2.waitKey(5) & 0xFF == 27:
				break
		cap.release()


	

if __name__ == "__main__":
	main()