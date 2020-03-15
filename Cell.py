import pygame
from scipy import stats
from math import sin, cos, acos, pi

class Cell:
	def __init__(self, lon, lat, elev):
		self.lon = lon
		self.lat = lat
		self.elev = elev
		self.lat_neighbors = set([])
		self.lon_neighbors = set([])
		self.local_gradiant = [0,0]
		self.quadrant = None
		self.color = (0,0,0)
		self.d_lon = 0
		self.d_lat = 0
		self.per = 0

	# How the cell appears when you call it
	def __repr__(self):
		return "Cell({}, {})".format(self.lon, self.lat)

	# Calculate what percentile the cell belongs to, assuming a 
	# uniform distribution
	# def percentile(self, min_elev, max_elev):
	# 		return (self.elev-min_elev)/(max_elev-min_elev)*100.

	# Calculate what percentile of the elevations the cells belongs to
	# based off of a cumulative distribution function, assuming it
	# is a normal distribution
	def percentile(self, mean, std_dev):
		return 100*stats.norm.cdf(self.elev, loc=mean, scale=std_dev)


	# Calculate the RGB values based off of interpolating between two colors
	def interpolate(self, a_elev, b_elev, a_color, b_color):
		new_color = [0,0,0]
		frac = (self.per - b_elev)/(a_elev - b_elev)
		for i in range(3):
			new_color[i] = (a_color[i] - b_color[i])*frac**1 + b_color[i]
		self.color = tuple(new_color)

	# Find the angular distance between the two points
	def distance(self, a, b):
		sins = sin(a.lon*pi/180.0)*sin(b.lon*pi/180.0)
		coss = cos(a.lon*pi/180.0)*cos(b.lon*pi/180.0)*sin((a.lat-b.lat)*pi/180.0)
		dist = acos(sins-coss)
		if dist != 0:
			return dist
		else:
			return 1e-9

	# Find the local gradient of the cell based off of its neighbors
	def get_grad(self):
		try:
			a_lon, b_lon = self.lon_neighbors
		except:
			print(self.lon, self.lat, "bad lon neighbors")
			a_lon = list(self.lon_neighbors)[0]
			b_lon = self
		d_elev_lon = a_lon.elev - b_lon.elev
		dist_lon = self.distance(a_lon, b_lon)

		try:
			a_lat, b_lat = self.lat_neighbors
		except:
			print(self.lon, self.lat, "bad lat neighbors")
			a_lat = list(self.lat_neighbors)[0]
			b_lat = self
		d_elev_lat = a_lat.elev - b_lat.elev
		dist_lat = self.distance(a_lat, b_lat)

		return [d_elev_lon/dist_lon, d_elev_lat/dist_lat]

	# Use the local gradient to calculate the color to be displayed
	# by the cell when drawn
	def get_grad_color(self):
		self.local_gradiant = self.get_grad()

		dx = self.local_gradiant[1]
		if dx >= 0:
			self.color = (0, int(100*dx), 0)
		else:
			self.color = (int(-100*dx), 0, 0)

	# Use the topographic information to calculate the color to
	# be displayed by the cell when drawn
	def get_color(self, mean, std_dev):
		self.per = self.percentile(mean, std_dev) 

		# Initialize the colors for each elevation
		snow = (204, 204, 204)	# rgb:(204, 204, 204)	hsv:(0, 0, 80)
		mountain = (50, 50, 50)	# rgb:(50, 50, 50)		hsv:(0, 0, 20)
		forest = (0, 50, 10)	# rgb:(0, 50, 10)		hsv:(132, 100, 20)
		grass =  (0, 180, 0)	# rgb:(0, 180, 0)		hsv:(120, 100, 71)
		sand = (255, 244, 102)	# rgb:(255, 244, 102)	hsv:(56, 60, 100)
		shore = (61, 226, 255)	# rgb:(61, 226, 255)	hsv:(189, 76, 100)
		ocean = (0, 0, 180)		# rgb:(0, 0, 180)		hsv:(240, 100, 70)
		abyss = (0, 0, 30)		# rgb:(0, 0, 30)		hsv:(0, 0, 12)	

		# Organize the elevations for comparison
		elevations = [0, 55, 65, 70, 71, 97, 99, 100]
		colors = [abyss, ocean, shore, sand, grass, forest, mountain, snow]
		
		# Interpolate the color based off of the closest two elevations
		for i in range(8):
			if self.per > elevations[i]:
				if self.per <= elevations[i+1]:
					color_a = colors[i]
					color_b = colors[i+1]
					self.interpolate(elevations[i],elevations[i+1], color_a, color_b)


	# Draw the cell on the display
	def draw(self, display, scale):
		W, H = pygame.display.Info().current_w, pygame.display.Info().current_h
		x = W*self.lon/360.
		y = H*self.lat/180.

		# Draw the cells
		try:
			pygame.draw.rect(display, self.color, (x, y, scale, scale))

		except:
			pygame.draw.rect(display, (0,0,0), (x, y, scale, scale))


	# Find the neighbors of the cell
	def find_neighbors(self):
		cells_to_check = self.quadrant.cells
		quadrants = self.quadrant.lon_neighbors.union(self.quadrant.lat_neighbors)
		for quadrant in quadrants:
			cells_to_check += quadrant.cells

		for cell in cells_to_check:
			self.check_neighbor(cell)

	# Check if the given cell is the right distance away to be considered a neighbor
	def check_neighbor(self, cell):
		#Longitudinal Neighbors
		if self.lat == 0.0 and cell.lat == 0.0:
			if self.lon == (cell.lon + 180.0)%360.0:
				self.lon_neighbors.add(cell)
				cell.lon_neighbors.add(self)
		
		elif self.lat == 180.0 - self.d_lat and cell.lat == 180.0 - self.d_lat:
			if self.lon == (cell.lon + 180.0)%360.0:
				self.lon_neighbors.add(cell)
				cell.lon_neighbors.add(self)
		
		elif self.lon == cell.lon:
			if abs(self.lat - cell.lat) == self.d_lat:
				self.lon_neighbors.add(cell)
				cell.lon_neighbors.add(self)
		
		# Latitudinal Neighbors
		if self.lat == cell.lat:
			if abs(self.lon - cell.lon) == self.d_lon :
				self.lat_neighbors.add(cell)
				cell.lon_neighbors.add(self)
		
			elif abs(self.lon - cell.lon) == 360.0 - self.d_lon:
				self.lat_neighbors.add(cell)
				cell.lon_neighbors.add(self)