#!/usr/bin/python3
import pygame
from math import sin, cos, pi#, acos
from opensimplex import OpenSimplex
from itertools import repeat
import random
import numpy as np
from multiprocessing.dummy import Pool as ThreadPool
from Cell import Cell
from Quadrant import Quadrant
import sys


class Map:
	def __init__(self, depth):
		self.depth = depth
		self.N = 2**self.depth
		self.M = 2*self.N
		self.d_lat, self.d_lon = 180.0/self.N, 360.0/self.M
		self.cells = []
		self.base_elev = 1000
		

	# Run through the steps to make a map
	def make(self, mode=""):
		self.create_cells()
		self.quad_set()
		self.add_noise()
		self.elev_stats()
		if mode == "gradiant":
			self.grad_color_set()
		else:
			self.color_set()
	

	# Create a cells to cover the map
	# returns the cells
	def create_cells(self):
		for n in range(self.N):
			for m in range(self.M):
				lon = (360.*m)/self.M
				lat = 180.*n/self.N 
				cell = Cell(lon, lat, self.base_elev)
				cell.d_lon = self.d_lon
				cell.d_lat = self.d_lat
				self.cells.append(cell)


	# Recursively find neighbors between quadrants while finding the
	# ends of the tree
	def get_leaves(self, leaves):
		added_to_leaves = False
		for leaf in frozenset(leaves):
			leaf.find_neighbors()
			if len(leaf.children) != 0:
				for child in leaf.children:
					leaves.add(child)

				leaves.remove(leaf)
				added_to_leaves = True
		
		if added_to_leaves:
			self.get_leaves(leaves)


	# Recursively make a tree to help find neighbors
	def quad_set(self):
		#  Quadrant(inp,  base depth, max depth, long_distance, lat_distance)
		q = Quadrant(self.cells, 0, self.depth, self.d_lon, self.d_lat)
		leaves = set([q])
		self.get_leaves(leaves)
		del leaves


	# Convert from spherical to cartesian and add noise to elev
	# based off of the cartesian coordinates
	def elev_noise(self, cell, noise, freq, amp):
		x = freq*sin(cell.lat*pi/180.)*cos(cell.lon*pi/180.)
		y = freq*sin(cell.lat*pi/180.)*sin(cell.lon*pi/180.)
		z = freq*cos(cell.lat*pi/180.)
		cell.elev += amp*noise.noise3d(x, y, z)


	# Run through scales and parallelize the process
	# of adding the noise to create "land" features on the map
	# returns the updated cells
	def add_noise(self):
		scales = np.array(list(range(1, 100, 2)))/3
		amplitude = 0.5
		lacurnity = 2.0
		for scl in scales:
			seed = random.randint(0, 1000)
			noise = OpenSimplex(seed)
			freq = lacurnity**scl
			amp = amplitude**scl

			pool = ThreadPool(16)
			pool.starmap(self.elev_noise, zip(self.cells, repeat(noise), 
				repeat(freq), repeat(amp)))
			pool.close()
			pool.join()


	# Get the elevations from all of the cells
	def get_elevs(self, cell):
		cell.find_neighbors()
		return cell.elev


	# Multithread finding statistical information from the 
	# elevation distributions
	def elev_stats(self):
		pool = ThreadPool(16)
		self.elevations = pool.map(self.get_elevs, self.cells)	
		pool.close()
		pool.join()

		# Find the elevation limits
		self.min_elev = min(self.elevations)
		self.max_elev = max(self.elevations)
		self.std_dev = np.std(self.elevations)
		self.mean = np.mean(self.elevations)


	# Have the cells assign its color
	def assign_colors(self, cell):
		cell.get_color(self.mean, self.std_dev)

	# Multithread the color assignment process
	def color_set(self):
		pool = ThreadPool(16)
		pool.starmap(self.assign_colors, zip(self.cells))
		pool.close()
		pool.join()


	# Have the cell find its color based on local gradiant
	def assign_grad_colors(self, cell):
		cell.get_grad_color()


	# parallelize finding the gradiant color 
	def grad_color_set(self):
		pool = ThreadPool(16)
		pool.map(self.assign_grad_colors, self.cells)
		pool.close()
		pool.join()

if __name__ == "__main__":
	# Create the map
	example = Map(int(sys.argv[1]))
	example.make()
	scale = int(sys.argv[2])

	#initialize pygame window
	pygame.init()
	win = pygame.display.set_mode((scale*example.M, scale*example.N))

	# Display the results
	run = True
	while run:
		win.fill(( 0,0,0 ))


		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False

		for cell in example.cells:
			cell.draw(win, scale)

		pygame.display.update()

	pygame.quit()