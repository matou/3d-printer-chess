import numpy as np
import cv2
from collections import defaultdict
import math


class MoveDetector:

    '''
    Initializes the MoveDetector by estimating:
        the positions of the the squares
        the general noise level ofthe stream
    Needs the url of the stream as parameter
    '''
    def __init__(self,path):
        self.path = path
        cap = cv2.VideoCapture(self.path)

        #input resolution is adjusted so that width is 320 px
        self.resize = 320/cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)*self.resize)
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)*self.resize)

        self.abc= ['h', 'g', 'f', 'e', 'd','c','b','a']
        
        self.fieldPositions = self.detectSquares()
        self.avgNoise = self.estimateNoise()

    '''
    Estimates the potitions of the sqaures
    '''
    def detectSquares(self):
        cap = cv2.VideoCapture(self.path)
        _, frame = cap.read()

        #find edges in input image
        editedFrame = cv2.resize(frame,(0,0),fx=self.resize, fy=self.resize)
        gray = cv2.cvtColor(editedFrame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 150,200)

        #find vertical and horizontal lines
        #assumption: chess board is more or less aligned to the camera
        vertLines = np.vstack((cv2.HoughLines(edges, 1, np.pi / 180, 70, None, 0, 0,0,0.05*np.pi),cv2.HoughLines(edges, 1, np.pi / 180, 70, None, 0, 0,0.95*np.pi,np.pi)))
        horLines = cv2.HoughLines(edges, 1, np.pi / 180, 70, None, 0, 0,0.45*np.pi, 0.55*np.pi)

        #transform polar coordinates of lines to cartesian coordinates of start and end point
        vertLines = self.getCoords(vertLines)
        horLines = self.getCoords(horLines)

        #find outermost lines that describe the chess bord's position
        #assumption: chess board takes up most of the image
        maxY = 0
        upperLine = None
        minY = 2*self.height
        lowerLine = None
        for line in horLines:
            avgY = line[0][1]+line[1][1]
            if avgY > maxY:
                maxY = avgY
                lowerLine = line
            if avgY < minY:
                minY = avgY
                upperLine = line

        maxX = 0
        leftLine = None
        minX = 2*self.width
        rightLine = None
        for line in vertLines:
            avgX = line[0][0]+line[1][0]
            if avgX> maxX:
                maxX = avgX
                rightLine = line
            if avgX < minX:
                minX = avgX
                leftLine = line

        #find corners of the chess board
        intersect1 = self.getIntersection(upperLine, rightLine)
        intersect2 = self.getIntersection(upperLine, leftLine)
        intersect3 = self.getIntersection(lowerLine, rightLine)
        intersect4 = self.getIntersection(lowerLine, leftLine)

        #calculate positions of the squares from the corners of the chess board
        fieldPositions = dict()

        stepLeft, offsetLeft = self.calcStep((intersect2,intersect4),8)
        stepRight, offsetRight = self.calcStep((intersect1, intersect3),8)
        for i in range(8):
            start = np.array(intersect2)+offsetLeft + i*stepLeft
            stop = np.array(intersect1)+offsetRight + i*stepRight

            step, offset = self.calcStep((start,stop), 8)
            for j in range(8):
                fieldPositions[self.abc[j]+str(i+1)] = (start+offset+j*step).astype(int)

        
        cap.release()        
        return fieldPositions

    '''
    Estimates the average noise of the video stream without motion
    '''
    def estimateNoise(self, noiseSpan=10):
        noise = []
        
        cap = cv2.VideoCapture(self.path)
        ref,prevFrame = cap.read()
        prevFrame = cv2.resize(prevFrame,(0,0),fx=self.resize, fy=self.resize)

        #collect difference pictures
        for i in range(noiseSpan):
            ref, frame = cap.read()
            frame = cv2.resize(frame,(0,0),fx=self.resize, fy=self.resize)
            
            noise.append(cv2.absdiff(frame,prevFrame))
                
            prevFrame = frame
            
        cap.release()

        #return mean difference
        return np.mean(noise)

    '''
    Waits for movement in the video stream, then compares the positions before and after the movement.
    Returns the move that was made.
    '''
    def getMove(self):

        #variables used to track movement and stillness
        stillCounter = 0
        hasMoved = False
        
        cap = cv2.VideoCapture(self.path)
        ref,prevFrame = cap.read()
        prevFrame = cv2.resize(prevFrame,(0,0),fx=self.resize, fy=self.resize)

        #save the starting position
        lastPosition = {key:self.getBox(prevFrame,point) for (key,point) in self.fieldPositions.items()}

        while(ref):
            
            ref, frame = cap.read()
            frame = cv2.resize(frame,(0,0),fx=self.resize, fy=self.resize)

            #calculate current noise level
            crntNoise = np.mean(cv2.absdiff(frame,prevFrame))

            #check if movement is occuring and update accordingly
            #   whether or not movement has already occured
            #   for how many frames is has stopped
            if np.absolute(crntNoise-self.avgNoise) < 0.5:
                stillCounter += 1
            else:
                stillCounter = 0
                hasMoved = True
        
            #if there has been movement and it has stopped long enough, the new positions have been established
            #compares the starting positions with the current ones to get the move
            if stillCounter > 30 and hasMoved:
                #save current position
                crntPosition = {key:self.getBox(frame,point) for (key,point) in self.fieldPositions.items()}

                #establish difference between current and starting position
                #uses variance in the color channels as difference
                change = {key:np.var(np.mean(cv2.absdiff(crntPosition[key],lastPosition[key]),(0,1))) for key in crntPosition}

                #find squares with the highes difference
                #best two are involved in the move
                candidates = sorted(change.keys(), key= lambda x: change[x],reverse=True)

                #use variance in the color channels to determine move direction
                #little variance indicates either black or white square
                #higher variance indicates colored chess piece
                if np.var(np.mean(crntPosition[candidates[0]],(0,1))) > np.var(np.mean(crntPosition[candidates[1]],(0,1))):
                    result = candidates[1]+candidates[0]
                else:
                    result = candidates[0]+candidates[1]

                break
                            
            prevFrame = frame
            
        cap.release()
        return result
    '''
    Returns a clipping of the image around position
    Using a box around the position reduces the impact of noise
    '''
    def getBox(self, image, position, size=8):  
        (x,y) = position
        return image[y-size:y+size,x-size:x+size]

    '''
    Transforms polar coordinates of lines to cartesian coordinates of start and end points
    '''
    def getCoords(self, lines):
        result = []
        if lines is not None:
            for i in range(0, len(lines)):
                rho = lines[i][0][0]
                theta = lines[i][0][1]
                a = math.cos(theta)
                b = math.sin(theta)
                x0 = a * rho
                y0 = b * rho

                #different calculations for horizontal and vertical lines
                if theta > 0.4*np.pi and theta < 0.6*np.pi:
                    pt1 = (self.width, int(y0 - (((x0-self.width)/(-b))*(a))))
                    pt2 = (0, int(y0 - ((x0/(-b))*(a))))
                else:
                    pt1 = (int(x0 - ((y0-self.height)/a)*(-b)), self.height)
                    pt2 = (int(x0 - (y0/a)*(-b)), 0)
                result.append((pt1, pt2))
        return result

    '''
    Calculates the intersection of two lines
    '''
    def getIntersection(self, line1, line2):
        (x1,y1) = line1[0]
        (x2,y2) = line1[1]
        (x3,y3) = line2[0]
        (x4,y4) = line2[1]
        denom = (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
        x = ((x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4))/denom
        y = ((x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4))/denom
        return (int(x),int(y))

    '''
    Calculates the vector that goes from the line starting point to its end point if repeated nrParts times
    '''
    def calcStep(self, line, nrParts):
        step = ((line[1][0]-line[0][0])/nrParts, (line[1][1]-line[0][1])/nrParts)
        offset = (step[0]/2, step[1]/2)
        return np.array(step), np.array(offset)


if __name__ == '__main__':
    md = MoveDetector('http://192.168.178.39/webcam/?action=stream')
    while(True):
        print(md.getMove())
        if input()=='q':
            break
