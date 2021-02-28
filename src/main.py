from sunfish import Position, initial, Searcher, print_pos, MATE_LOWER, MATE_UPPER, parse, render
import re
import time
from octoprint import Octoprint
import secrets
from moveDetection import MoveDetector


def parse_move(move):
    xf = ord(move[0]) - ord('a') + 1
    yf = int(move[1])
    xt = ord(move[2]) - ord('a') + 1
    yt = int(move[3])
    return xf, yf, xt, yt

def is_pawn(x, y, hist, last_move=False):
    h = hist[-2].rotate() if last_move else hist[-1]
    p = h[0][100 - y*10 + x]
    return p == 'p' or p == 'P'

def new_field_is_empty(x,y,hist):
    f = hist[-2].rotate()[0][100 - y*10 + x]
    return f == '.'
    

def main():

    md = MoveDetector('http://192.168.178.39/webcam/?action=stream')
    o = Octoprint(api_key=secrets.api_key)

    print('Welcome to 3d printer chess.')
    s = None
    while s != 'n' and s != 'y':
        s = input('Should we home the 3d printer? (y/n)\n')
    if s == 'y':
        o.home()

    print('Homing finished. Parking.')
    o.park()

    hist = [Position(initial, 0, (True,True), (True,True), 0, 0)]
    searcher = Searcher()

    print('Game started')
    while True:
        print_pos(hist[-1])

        if hist[-1].score <= -MATE_LOWER:
            print('You lost')
            break
    
        print('Your move:\a')
        move = None
        while move not in hist[-1].gen_moves():
            match = re.match('([a-h][1-8])'*2, md.getMove())
            if match:
                move = parse(match.group(1)), parse(match.group(2))
            else:
                print('Please enter a move like g8f6')
        hist.append(hist[-1].move(move))

        print_pos(hist[-1].rotate())

        if hist[-1].score <= -MATE_LOWER:
            print('You won')
            break

        start = time.time()
        for _depth, move, score in searcher.search(hist[-1], hist):
            if time.time() - start > 1:
                break

        if score == MATE_UPPER:
            print('Checkmate!')
    
        smove = render(119-move[0]) + render(119-move[1])
        print('My move:', smove)
        hist.append(hist[-1].move(move))

        #print(hist[-1][0])

        xf,yf,xt,yt = parse_move(smove)
        capturing = not new_field_is_empty(xt, yt, hist)
        if capturing:
            pawn = is_pawn(xt,yt, hist, last_move=True)
            #print('Capturing pawn:', pawn)
            o.remove(xt,yt,pawn)
        pawn = is_pawn(xt,yt, hist)
        o.from_to(xf,yf,xt,yt, pawn=pawn)


if __name__ == '__main__':
    main()
