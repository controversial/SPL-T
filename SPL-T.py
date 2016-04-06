"""An in-progress implementation of the iOS game SPL-T. http://simogo.com/work/spl-t/"""

from PIL import Image, ImageDraw



#TILE CLASS



class Tile:
	"""
	A tile in the SPL-T game. Tiles are contained within games.
	A tile can be either standard, or a point block. Point
	blocks cannot be split.
	"""
	def __init__(self, frame, game, tiletype=1, pointCount=None):
		"""
		BLOCK TYPES:
		1: standard block type
		2: point blocks
		"""
		self.frame=[int(d) for d in frame]
		x,y,w,h=self.frame
		self.x,self.y,self.w,self.h=x,y,w,h

		self.game=game

		self.type=tiletype
		self.pointBlockValue=pointCount

		self.originFrame=None

	@property
	def coordsEncompassed(self):
		x,y,w,h=self.frame
		return sum([[(x+xv,y+yv) for xv in range(w)] for yv in range(h)],[])

	@property
	def xs(self):
		return list(zip(*self.coordsEncompassed))[0]

	@property
	def ys(self):
		return zip(*self.coordsEncompassed)[0]

	def fall(self):
		"""Called recursively to make tiles fall down."""
		#Check if the space one row down is empty.
		xValuesEncompassed=range(self.x,self.x+self.w)
		#The spaces that must be empty for falling one space
		spacesNeeded=[(x,self.y+self.h) for x in xValuesEncompassed]
		#All the spaces that are needed to fall are avaliable, the tile can fall
		if all([space in self.game.blankSpaces for space in spacesNeeded]):
			x,y,w,h=self.frame
			#Record original falling position
			if self.originFrame is None:
				self.originFrame=self.frame
			#Fall one space down
			self.updateFrame((x,y+1,w,h))
			#Recur
			self.fall()
		#In this case, the block has fallen, and is now finished falling.
		elif self.originFrame is not None:
			self.originFrame=None
			#Cut the value in half if it's a point block
			if self.type==2:
				self.pointBlockValue -= 1
		#The tile has not, and can not fall
		else:
			return False


	def updateFrame(self,frame):
		"""Change the frame of the current block"""
		x,y,w,h=frame
		self.frame=[int(d) for d in frame]
		self.x,self.y,self.w,self.h=x,y,w,h

	def split(self, silent=1):
		"""Replace this tile with two tiles of half size. Tile is split
		according to the current split direction of the parent game."""
		if self.type != 1:
			if not silent:
				print("Only standard type blocks can be split!")
			return False

		x,y,w,h=self.x,self.y,self.w,self.h

		index=self.game.index(self)
		#Remove old tile from list
		popped=self.game.tiles.pop(index)
		#Create frames of new tiles
		if self.game.splitHorizon:
			subTiles = [Tile((x,y,w,h/2.0),self.game),
			Tile((x,y+h/2.0,w,h/2.0),self.game)]
		else:
			subTiles = [Tile((x,y,w/2.0,h),self.game),
			Tile((x+w/2.0,y,w/2.0,h),self.game)]

		#Make sure tiles are not too small to be split
		tooSmall=0
		for t in subTiles:
			if t.w<1 or t.h<1:
				tooSmall=1

		if tooSmall:
			#Put popped tile back
			self.game.tiles.insert(index, popped)

			if not silent:
				print(popped, 'was too small to be split!')
				self.game.show()
			#Report failure
			return False

		else:
			self.game.addTiles(subTiles)
			self.game.splitHorizon = not self.game.splitHorizon
			#Update the game state.
			self.game.update()
			#Add a point (one point awarded for each split)
			self.game.score += 1
			#One more split has been made.
			self.game.splitsCount+=1
			#Debug info
			if not silent:
				print('Splitting',popped,'into',[str(t) for t in subTiles])
				print('Current points:',self.game.score)
				self.game.show()

			#Report success
			return True

	def __str__(self):
		"""String representation of a tile"""
		return 'tile: ' + str(self.frame)



#GAME CLASS



class Game:
	def __init__(self):
		self.tiles=[Tile((0,0,8,16),self)]
		self.spaces = []
		self.splitsCount=0
		self.splitHorizon=True
		self.pointBlocks=[]
		self.score=0

	@property
	def fullSpaces(self):
		"""All coordinates full in the game"""
		spaces=list(set(sum([t.coordsEncompassed for t in self.tiles],[])))
		return sorted(spaces)

	@property
	def blankSpaces(self):
		"""All coordinates blank in the game"""
		allSpaces = sum([[(x, y) for x in range(8)] for y in range(16)], [])
		return [space for space in allSpaces if space not in self.fullSpaces]

	def index(self, item):
		"""Get the tile at the specified index position."""
		return self.tiles.index(item)

	def addTiles(self, tiles):
		"""Add tiles to the game"""
		self.tiles.extend(tiles)

	def update(self):
		"""Handle the global actions that need to be triggered every move"""
		self.updatePointBlocks() #Count down *before* falling.
		if self.blankSpaces: #Only fall if there are blank spaces in the game
			self.fallBlocks()
		self.newPointBlocks()#Form new point blocks after falling

	def updatePointBlocks(self):
		"""Handle count down and removal of existing point blocks"""
		#list of tiles to be kept
		keep = []
		for i, block in enumerate(self.pointBlocks):
			#Block counts down
			block.pointBlockValue -= 1
			#Add a point for the point block counting down
			self.score += 1
			#Remove the block if it has counted down to 0
			if block.pointBlockValue <= 0:
				try:
					self.tiles.pop(self.tiles.index(block))
				except:
					pass
			else:
				keep.append(block)
		self.pointBlocks = keep

	def newPointBlocks(self):
		"""Scan through all the blocks in the game to find the ones that should
		be made into point blocks."""
		#Find adjacent groups of blocks of equal size
		frames = [t.frame for t in self.tiles if t.type==1]
		#Sort by size
		frames.sort(key=lambda x:x[2:])

		#Will hold groupings of connected same-size blocks
		blockGroups = []
		#Dict will pair a frame with existing adjacent same-size frames
		neighbors = {}
		#Populare neighbors dict with values from board
		for f in frames:
			x,y,w,h=f
			#Possible 4-connectivity same-size neighbors
			potentialNeighbors = [
			[x+w,y,w,h], #w,h are kept constant, same size
			[x,y+h,w,h],
			[x-w,y,w,h],
			[x,y-h,w,h]]
			#Which of the potential neighbors actually exist on the board
			neighbors[tuple(f)]=[n for n in potentialNeighbors if list(n) in frames]

		#bfs (non-recursive) to explore groups of identically sized tiles
		for f in neighbors.keys():
			queue = [f]
			visited = [f]
			while queue:
				current=queue.pop(0)
				ns = neighbors[tuple(current)]
				for neigh in ns:
					if tuple(neigh) not in visited:
						visited.append(tuple(neigh))
						queue.append(tuple(neigh))
			blockGroups.append(visited)

		#Make sure identical groups in list are in same order
		blockGroups = [tuple(sorted(g)) for g in blockGroups]
		#Remove duplicates
		blockGroups = [list(g) for g in list(set(blockGroups))]
		#At this point, we have a list of all groups of same-size blocks
		#Will hold the blocks to be converted
		pointBlocks=[]
		#Check shape of block groups
		for bg in blockGroups:
			#List of all x, y, w, h values
			xs, ys, ws, hs = zip(*bg)
			#Width and height of all blocks
			w,h=ws[0],hs[0]
			#Blocks must be at least 2x2
			if (max(xs)+w-min(xs))/w >= 2 and (max(ys)+h-min(ys))/h >= 2:
				#Move an imaginary 2x2 blockgroup around the board and see if
				#there's any place that it "fits." It fits if all 4 of its tiles
				#exist. Groups of blocks with sizes like 2x3 and 3x3 will be
				#covered by multiple overlapping 2x2 blocks, so this method is
				#accurate and reliable.

				#Move the imaginary block around and check for matches
				for x in range(min(xs),max(xs),w):
					for y in range(min(ys),max(ys),h):
						#Move the imaginary blockgroup
						pseudoBlock=[(x,y,w,h),(x+w,y,w,h),(x+w,y+h,w,h),(x,y+h,w,h)]
						#Check whether all tiles in the imaginary blockgroup
						#exist in actuality. If so, mark them to be converted to
						#pointblocks
						matches=[b for b in pseudoBlock if b in bg]
						if len(matches)==4:
							pointBlocks.extend(matches)

						#Change type of identified blocks
						for frame in pointBlocks:
							#Iterate through all tiles' frames to find the one
							#that matches the frame to be converted
							for tile in self.tiles:
								if tuple(tile.frame) == frame:
									tile.type=2
									tile.pointBlockValue = self.splitsCount
									self.pointBlocks.append(tile)
									break
		#Remove any accidental duplicates
		self.pointBlocks=list(set(self.pointBlocks))

	def fallBlocks(self):
		"""Make blocks fall."""
		#Sort tiles such that farther-down tiles appear sooner. This will
		#ensure that bottom tiles have a chance to fall first.
		tiles=sorted(self.tiles,key=lambda t:t.y,reverse=True)
		#Only tiles with X positions intersecting blank xs need try to fall
		xs,ys = zip(*self.blankSpaces) #Blank xs and ys
		potentialFallers=[t for t in tiles if any([x in xs for x in t.xs])]
		#Have tiles fall
		for t in potentialFallers:
			t.fall()
		#Have new tiles fall in to fill gaps.
		self.fillNewTiles()
		
	def fillNewTiles(self):
		"""Fill in new tiles from the top."""
		#First find all the spaces that border on the top
		topSpaces=[s for s in self.blankSpaces if s[1]==0]
		
	def __getitem__(self, index):
		"""Support for indexing like Game[n]"""
		return self.tiles[index]

	def __iter__(self):
		"""Support for directly iterating through a game: 'for tile in Game' """
		return iter(self.tiles)

	def __str__(self):
		"""String representation of a game object"""
		tileStrings = [str(tile.frame) for tile in self.tiles]
		return str(tileStrings)

	@property
	def img(self):
		"""Return a PIL image for a graphical representation of the game. Useful
		for easily visualizing a game state while debugging."""
		im = Image.new("RGB", (160, 320))
		d=ImageDraw.Draw(im)
		for tile in self.tiles:
			if tile.type == 1:
				color=(0,0,0)
			else:
				color=(100,100,100)
			coords=tile.x*20,tile.y*20,(tile.x+tile.w-1)*22,(tile.y+tile.h-1)*21
			d.rectangle(coords, fill=color, outline=(255,255,255))
			if tile.type == 2:
				tileCoords = coords[:2]
				textCoords = tileCoords[0]+4, tileCoords[1]+3
				
				d.text(tileCoords, str(tile.pointBlockValue))
		return im

	def show(self):
		self.img.show()



#HELPER FUNCTIONS



def connectTiles(tiles):
	"""Given a list of tiles, return multiple lists of connected tiles"""
	pass

if __name__ == "__main__":
	g=Game()
	#Set of splits to be made
	for i in list(range(7))+[-4,-5,-8,-6,0,4,0,-1,-6,-1,-1,-1]:
		g[i].split(silent=0)
