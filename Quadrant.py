# Recursively divide the map into quadrants that make the 
# search for neighboring cells easier and faster

class Quadrant:
	def __init__(self, cells, current_depth, 
				final_depth, d_lon, d_lat, 
				parent=None):

		self.cells = cells
		self.current_depth = current_depth
		self.final_depth = final_depth
		self.parent = parent
		self.mid_height, self.mid_width = 0, 0
		self.children = set()
		self.lon_neighbors = set()
		self.lat_neighbors = set()
		self.d_lon = d_lon
		self.d_lat = d_lat


		self.lon, self.lat = self.find_midpoint()
		self.check_depth()


	# Check if at final depth otherwise divide
	def check_depth(self):
		if self.current_depth < self.final_depth:
			if self.current_depth == 0:
				self.children = list(self.bisect())

				# Connect children as longitudinal neighbors
				self.children[0].lon_neighbors.add(self.children[1])
				self.children[1].lon_neighbors.add(self.children[0])

				# Connect children as latitudinal neighbors
				self.children[0].lat_neighbors.add(self.children[1])
				self.children[1].lat_neighbors.add(self.children[0])

			else:
				self.children = list(self.divide())

		else:
			for cell in self.cells:
				cell.quadrant = self


	# Find the midpoint of the quadrant
	def find_midpoint(self):
		# get lists of all the longitudes and latitudes
		longitudes = [cell.lon for cell in self.cells]
		latitudes = [cell.lat for cell in self.cells]

		if len(longitudes) != 0 and len(latitudes) != 0:
			# find midpoint of quadrant
			self.mid_width = round((max(longitudes) - min(longitudes) + self.d_lon)/2.0, 7) + min(longitudes)
			self.mid_height = round((max(latitudes) - min(latitudes) + self.d_lat)/2.0, 7) + min(latitudes)
			
		else:
			self.mid_width, self.mid_height = self.parent.lon, self.parent.lat

		return [self.mid_width, self.mid_height]


	# Divide the quadrant into two new quadrants
	def bisect(self):
		_q1, _q2 = [], []

		for cell in self.cells:
			if cell.lon < self.mid_width:
				_q1.append(cell)
				
			elif cell.lon >= self.mid_width:
				_q2.append(cell)

		# create quadrant
		q1 = Quadrant(_q1, self.current_depth+1, self.final_depth, self.d_lon, self.d_lat, self)
		q2 = Quadrant(_q2, self.current_depth+1, self.final_depth, self.d_lon, self.d_lat, self)

		return [q1, q2] 


	# Divide the quadrant into four new quadrants
	def divide(self):
		_q1, _q2, _q3, _q4 = [], [], [], []

		for cell in self.cells:
			if cell.lon < self.mid_width:
				if cell.lat >= self.mid_height:
					_q1.append(cell)
	
				elif cell.lat < self.mid_height:
					_q4.append(cell)
		
			elif cell.lon >= self.mid_width:
				if cell.lat >= self.mid_height:
					_q2.append(cell)

				elif cell.lat < self.mid_height:
					_q3.append(cell)

		#print(self.current_depth, len(_q1), len(_q2), len(_q3), len(_q4))
		q1 = Quadrant(_q1, self.current_depth+1, self.final_depth, self.d_lon, self.d_lat, self)
		q2 = Quadrant(_q2, self.current_depth+1, self.final_depth, self.d_lon, self.d_lat, self)
		q3 = Quadrant(_q3, self.current_depth+1, self.final_depth, self.d_lon, self.d_lat, self)
		q4 = Quadrant(_q4, self.current_depth+1, self.final_depth, self.d_lon, self.d_lat, self)

		return [q1, q2, q3, q4]


	# Find any neighbors of the quadrant
	def find_neighbors(self):
		if self.current_depth > 1:
			dlat = 180 / (2**(self.current_depth-1))
			dlon = 360 / 2**(self.current_depth)

			neighbors = self.parent.lon_neighbors.union(self.parent.lat_neighbors)

			for quad in neighbors:
				for child in quad.children:
					if quad != self:

						#Longitudinal Neighbors
						if self.lat == dlat/2 and child.lat == dlat/2:
							if self.lon == (child.lon + 180.0 + dlon/2)%360.0:
								self.lon_neighbors.add(child)
								child.lon_neighbors.add(self)

						elif self.lat == 180.0 - dlat/2 and child.lat == 180.0 - dlat/2:
							if self.lon == (child.lon + 180.0 + dlon/2)%360.0:
								self.lon_neighbors.add(child)
								child.lon_neighbors.add(self)

						elif self.lon == child.lon:
							if abs(self.lat - child.lat) == dlat:
								self.lon_neighbors.add(child)
								child.lon_neighbors.add(self)

						# Latitudinal Neighbors
						if self.lat == child.lat:
							if abs(self.lon - child.lon) == dlon:
								self.lat_neighbors.add(child)
								child.lat_neighbors.add(self)

							elif abs(self.lon - child.lon) == 360.0 - dlon:
								self.lat_neighbors.add(child)
								child.lat_neighbors.add(self)


	# How to represent the quadrant
	def __repr__(self):
		return "Quadrant({}, {}; {}, {})".format(self.lat, self.lon, self.current_depth, len(self.cells))