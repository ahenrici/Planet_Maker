import pygame
from MapMaker import Map


planet = Map(6)
planet.make(mode="gradiant")
scale = 7
pygame.init()
win = pygame.display.set_mode((scale*planet.M, scale*planet.N))

index = 0
run = True
while run:
	win.fill((0,0,0))

	pygame.time.delay(100)

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			run = False

	
	for cell in planet.cells:
		cell.draw(win, scale)

	pygame.display.update()

pygame.quit()