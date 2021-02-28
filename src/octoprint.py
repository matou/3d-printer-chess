import requests
import time

class Octoprint:

    def __init__(self, host='http://192.168.178.39', api_key='', a1=(26,38), 
                 min_z=53, z_up=40, z_park=150, grab_ex=6, pawn_grab_ex_offset=4, 
                 field_size=27, sleep=True, sleep_park=10, sleep_home=42, 
                 sleep_move=19, sleep_remove=14):
        """Create a new Octoprint object, that can send commands to your Octoprint instance.

        host -- The URL of your Octoprint instance. 
        api_key -- Your Octoprint API key.
        a1 -- tuple; the x-/y- position of the chess board's A1 field in mm (the midpoint of the field).
        min_z -- the minimum height that the z axis is allowed to go down (so that the gripper still clears the printbed.
        z_up -- the z height in which x/y movements with chess pieces in the gripper are performed. 
        z_park -- the parking height of the gripper
        grab_ex -- how much to 'extrude' for the gripper to close (for non-pawn chess pieces)
        pawn_grab_ex_offset -- how much more to extrude if we're grabbing pawns
        field_size -- the length/width of a single chess field
        sleep -- whether or not to insert delays (required to make sure that the printer stops moving before we try to detect another move)
        sleep_park -- how long to delay after a park command
        sleep_home -- how long to delay after a home command
        sleep_move -- how long to delay after a move command
        sleep_remove -- how long to delay after a remove command
        """


        self.base_url = host
        self.api_key = api_key
        self.printhead = self.base_url + '/api/printer/printhead'
        self.extruder = self.base_url + '/api/printer/tool'
        self.headers = { 'Content-Type': 'application/json', 'X-Api-Key': self.api_key}
        self.a1 = a1
        self.min_z = min_z
        self.z_up = z_up
        self.z_park = z_park
        self.field_size = field_size
        self.grab_ex = grab_ex
        self.pawn_grab_ex_offset = pawn_grab_ex_offset
        self.sleep_park = sleep_park
        self.sleep_home = sleep_home
        self.sleep_move = sleep_move
        self.sleep_remove = sleep_remove
        self.sleep = sleep
        print('To close the gripper with the extruder motor, cold extrusion must be enabled (make sure there is no filament in the printer!!!). Send g-code command \'M302 P1;\' to your printer through the Octoprint terminal. Not all firmwares support this command. You might need to adapt your firmware accordingly.')

    def home(self):
    """Homes the x/y/z axis of the printer. Somehow this doesn't always work for me."""
        command = { 'command': 'home', 'axes': 'x, y, z' }
        r = requests.post(self.printhead, headers=self.headers, json=command)
        print('sent homing command')
        if self.sleep:
            time.sleep(self.sleep_home)

    def move(self, x, y):
    """Moves the gripper over a given chess field.
       Expects two integers, e.g., for field A1, call move(1,1), for C5 call move(3,5)."""

        command = {'command': 'jog', 
                    'x': self.a1[0] + (x-1)*self.field_size,
                    'y': self.a1[1] + (y-1)*self.field_size,
                    'absolute': True }
        r = requests.post(self.printhead, headers=self.headers, json=command)

    def remove(self, x, y, pawn=False):
    """ Removes the chess piece at the given coordinates. 

        x -- the x-coordinate. A,B,C,...,H corresponds to 1,2,3,...,8
        y -- the y-coordinate. 1,2,3,..,8
        pawn -- whether the piece to move is a pawn
        """
        self.grab_at(x,y,pawn)
        command = {'command': 'jog', 
                    'x': 0,
                    'y': 0,
                    'absolute': True }
        r = requests.post(self.printhead, headers=self.headers, json=command)

        ex = self.grab_ex+self.pawn_grab_ex_offset if pawn else self.grab_ex
        command = {'command': 'extrude', 'amount': (-1)*ex}
        r = requests.post(self.extruder, headers=self.headers, json=command)
        if self.sleep:
            time.sleep(self.sleep_remove)

    def move_down(self):
    """Moves the gripper down to the board"""
        command = {'command': 'jog',
                    'z': self.min_z, 
                    'speed': 5000,
                    'absolute': True }
        r = requests.post(self.printhead, headers=self.headers, json=command)

    def grab(self, pawn=False):
    """Grabs the figure underneath the current gripper position.

        pawn -- whether the piece to move is a pawn"""
        command = {'command': 'jog',
                    'z': self.min_z,
                    'speed': 5000,
                    'absolute': True }
        r = requests.post(self.printhead, headers=self.headers, json=command)

        ex = self.grab_ex+self.pawn_grab_ex_offset if pawn else self.grab_ex
        command = {'command': 'extrude', 'amount': ex}
        r = requests.post(self.extruder, headers=self.headers, json=command)

        command = {'command': 'jog',
                    'z': 40,
                    'speed': 5000,
                    'absolute': False}
        r = requests.post(self.printhead, headers=self.headers, json=command)

        
    def put_down(self, pawn=False):
    """Puts down a carried chess piece at the current position. 

    pawn -- whether the carried piece is a pawn (default: False)
    """
        #x_move = -1-self.pawn_grab_ex_offset/2 if pawn else -1
        command = {'command': 'jog',
                    'x': -1,
                    'absolute': False}
        r = requests.post(self.printhead, headers=self.headers, json=command)

        command = {'command': 'jog',
                    'z': self.min_z,
                    'speed': 5000, 
                    'absolute': True }
        r = requests.post(self.printhead, headers=self.headers, json=command)
       
        ex = self.grab_ex+self.pawn_grab_ex_offset if pawn else self.grab_ex
        command = {'command': 'extrude', 'amount': (-1)*ex}
        r = requests.post(self.extruder, headers=self.headers, json=command)

        command = {'command': 'jog',
                    'x': 1,
                    'absolute': False}
        r = requests.post(self.printhead, headers=self.headers, json=command)

        command = {'command': 'jog',
                    'z': self.z_park,
                    'speed': 5000,
                    'absolute': True}
        r = requests.post(self.printhead, headers=self.headers, json=command)

    def grab_at(self, x, y, pawn=False):
    """Grab the chess piece at the given position. 

        x -- the x-coordinate. A,B,C,...,H corresponds to 1,2,3,...,8
        y -- the y-coordinate. 1,2,3,..,8
        pawn -- whether the piece to move is a pawn
        """

        self.move(x,y)
        self.grab(pawn=pawn)

    def put_down_at(self, x, y, pawn=False):
    """Place the chess piece at the given position.

        x -- the x-coordinate. A,B,C,...,H corresponds to 1,2,3,...,8
        y -- the y-coordinate. 1,2,3,..,8
        pawn -- whether the piece to move is a pawn
        """
        self.move(x,y)
        self.put_down(pawn=pawn)

    def from_to(self, x0,y0,x1,y1, pawn=False):
    """Move a chess piece from a given field on the board to another given field on the board. 

        x0 -- the x-coordinate to pick up the piece. A,B,C,...,H corresponds to 1,2,3,...,8
        y0 -- the y-coordinate.to pick up the piece 1,2,3,..,8
        x1 -- the x-coordinate to place the piece. A,B,C,...,H corresponds to 1,2,3,...,8
        y1 -- the y-coordinate to place the piece. 1,2,3,..,8
        pawn -- whether the piece to move is a pawn
        """
        self.grab_at(x0,y0, pawn=pawn)
        self.put_down_at(x1,y1, pawn=pawn)
        self.park()
        if self.sleep:
            time.sleep(self.sleep_move)
     

    def park(self):
    """Move to a parking position that does not obstruct the camera view."""
        command = {'command': 'jog',
                    'z': self.z_park,
                    'speed': 5000, 
                    'absolute': True }
        r = requests.post(self.printhead, headers=self.headers, json=command)
        command = {'command': 'jog',
                    'x': 230,
                    'y': 230,
                    'speed': 5000, 
                    'absolute': True }
        r = requests.post(self.printhead, headers=self.headers, json=command)
        if self.sleep:
            time.sleep(self.sleep_park)

    def tantrum(self):
    """Do some random movements that throw chess pieces from the board"""
        self.move(8,4)
        self.move_down()
        self.move(1,2)
        self.move(8,1)
        self.move(1,7)

    def shake(self):
    """Do some weird movements"""
        self.move(5,5)
        self.move_down()
        for i in range(10):
            self.move(5,5)
            self.move(4,5)

    def prod(self):
    """Prod the white king from the board"""
        command = {'command': 'jog',
                    'x': 147,
                    'y': 70,
                    'z': 74,
                    'speed': 5000, 
                    'absolute': True }
        r = requests.post(self.printhead, headers=self.headers, json=command)
        command = {'command': 'jog',
                    'x': 147,
                    'y': 15,
                    'z': 74,
                    'speed': 5000, 
                    'absolute': True }
        r = requests.post(self.printhead, headers=self.headers, json=command)
        for i in range(3):
            command = {'command': 'jog',
                        'x': 147,
                        'y': 120,
                        'z': 74,
                        'speed': 5000, 
                        'absolute': True }
            r = requests.post(self.printhead, headers=self.headers, json=command)
            command = {'command': 'jog',
                        'x': 107,
                        'y': 120,
                        'z': 74,
                        'speed': 5000, 
                        'absolute': True }
            r = requests.post(self.printhead, headers=self.headers, json=command)

if __name__ == '__main__':
    import secrets

    o = Octoprint(api_key=secrets.api_key, sleep=False)
    
    o.park()
    o.move(1,1)
    o.grab()
    o.move(8,8)
    o.put_down()

