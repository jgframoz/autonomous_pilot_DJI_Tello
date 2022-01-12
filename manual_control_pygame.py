from djitellopy import Tello
import cv2
import pygame
import numpy as np
import time

import face_tracking

# Speed of the drone
S = 60
# Frames per second of the pygame window display
# A low number also results in input lag, as input information is processed once per frame.
FPS = 120


class FrontEnd(object):
	""" Maintains the Tello display and moves it through the keyboard keys.
		Press escape key to quit.
		The controls are:
			- T: Takeoff
			- L: Land
			- Arrow keys: Forward, backward, left and right.
			- A and D: Counter clockwise and clockwise rotations (yaw)
			- W and S: Up and down.
	"""

	def __init__(self):
		# Init pygame
		pygame.init()

		self.cap_width = 960
		self.cap_height = 720

		# Creat pygame window
		pygame.display.set_caption("Tello video stream")
		self.screen = pygame.display.set_mode([self.cap_width, self.cap_height])

		# Init Tello object that interacts with the Tello drone
		self.tello = Tello()

		# Drone velocities between -100~100
		self.for_back_velocity = 0
		self.left_right_velocity = 0
		self.up_down_velocity = 0
		self.yaw_velocity = 0
		self.speed = 10
		self.state = 1
		self.pid = pid = [0.3, 0.5, 0]

		self.send_rc_control = False

		# create update timer
		pygame.time.set_timer(pygame.USEREVENT + 1, 1000 // FPS)

	def run(self):

		self.tello.connect()

		if self.tello.get_battery() < 20:
			print("No Battery") 
			return

		self.tello.set_speed(self.speed)

		# In case streaming is on. This happens when we quit this program without the escape key.
		self.tello.streamoff()
		self.tello.streamon()

		frame_read = self.tello.get_frame_read()

		should_stop = False
		while not should_stop:
			if self.tello.get_battery() < 20:
				print("No Battery")
				self.tello.land()

			for event in pygame.event.get():
				if event.type == pygame.USEREVENT + 1:
					self.update()
				elif event.type == pygame.QUIT:
					should_stop = True
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						should_stop = True
					else:
						self.keydown(event.key)
				elif event.type == pygame.KEYUP:
					self.keyup(event.key)

				if self.state == 3:
					frame, center, area = face_tracking.findNearestFaces(frame)
					pError, fb, yaw = face_tracking.trackFace(1, center, area, self.cap_width, self.pid, pError) 
					self.tello.send_rc_control(0, fb, 0, yaw)

			if frame_read.stopped:
				break

			self.screen.fill([0, 0, 0])

			frame = frame_read.frame

			frame = self.info_bottom_text(frame)
			
			frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
			frame = np.rot90(frame)
			frame = np.flipud(frame)

			frame = pygame.surfarray.make_surface(frame)
			self.screen.blit(frame, (0, 0))
			pygame.display.update()

			time.sleep(1 / FPS)

		# Call it always before finishing. To deallocate resources.
		self.tello.end()

	def keydown(self, key):
		""" Update velocities based on key pressed
		Arguments:
			key: pygame key
		"""
		if key == pygame.K_UP:  # set forward velocity
			self.for_back_velocity = S
		elif key == pygame.K_DOWN:  # set backward velocity
			self.for_back_velocity = -S
		elif key == pygame.K_LEFT:  # set left velocity
			self.left_right_velocity = -S
		elif key == pygame.K_RIGHT:  # set right velocity
			self.left_right_velocity = S
		elif key == pygame.K_w:  # set up velocity
			self.up_down_velocity = S
		elif key == pygame.K_s:  # set down velocity
			self.up_down_velocity = -S
		elif key == pygame.K_a:  # set yaw counter clockwise velocity
			self.yaw_velocity = -S
		elif key == pygame.K_d:  # set yaw clockwise velocity
			self.yaw_velocity = S
		elif key == pygame.K_1:  # change state for 1
			self.state = 1
		elif key == pygame.K_2:  # change state for 2
			self.state = 2
		elif key == pygame.K_3:  # change state for 3
			self.state = 3
		elif key == pygame.K_4:  # change state for 4
			self.state = 4
		elif key == pygame.K_5:  # change state for 5
			self.state = 5

	def keyup(self, key):
		""" Update velocities based on key released
		Arguments:
			key: pygame key
		"""
		if key == pygame.K_UP or key == pygame.K_DOWN:  # set zero forward/backward velocity
			self.for_back_velocity = 0
		elif key == pygame.K_LEFT or key == pygame.K_RIGHT:  # set zero left/right velocity
			self.left_right_velocity = 0
		elif key == pygame.K_w or key == pygame.K_s:  # set zero up/down velocity
			self.up_down_velocity = 0
		elif key == pygame.K_a or key == pygame.K_d:  # set zero yaw velocity
			self.yaw_velocity = 0
		elif key == pygame.K_t:  # takeoff
			self.tello.takeoff()
			self.send_rc_control = True
		elif key == pygame.K_l:  # land
			not self.tello.land()
			self.send_rc_control = False

	def update(self):
		""" Update routine. Send velocities to Tello."""
		if self.send_rc_control:
			self.tello.send_rc_control(self.left_right_velocity, self.for_back_velocity,
				self.up_down_velocity, self.yaw_velocity)
	
	def info_bottom_text(self, frame):
		state_dic = {1:'stay', 2:'keyboard control', 3:'facetracking', 4:'hand gesture control', 5:'voice control'}
		battery_text = "Battery: {}%".format(self.tello.get_battery())
		cv2.putText(frame, battery_text, (5, self.cap_height - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
		state_text = "State: {}".format(state_dic[self.state])
		cv2.putText(frame, state_text, (5, self.cap_height - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
		return frame



def main():
	frontend = FrontEnd()

	# run frontend
	frontend.run()


if __name__ == '__main__':
	main()