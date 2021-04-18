"""
Changes:
- Increased corner defense.

Note:
- Attacks late game is super strong due to increased MP gain. This defensive
setup is not enough.
- Especially bad against pockets.
"""

"""
Summary of rule changes:
- Starting SP: 8
- Starting MP: 1/round
- SP Increment: 5
- MP Increment: round // 5
- MP Decay = 75%
"""

import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from copy import deepcopy

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

        self.t1 = [[5, 12], [26, 12]]
        self.w1 = [
            [0, 13], [5, 13], [26, 13], [27, 13],
            [2, 13], [6, 13], [25, 13],
            # Rest of the funnel wall (18 = 4 rounds), might consider building them at once.
            [7, 13], [8, 13], [9, 13], [10, 13], [11, 13], [12, 13], [13, 13], 
            [14, 13], [15, 13], [16, 13], [17, 13], [18, 13], [19, 13], [20, 13], 
            [21, 13], [22, 13], [23, 13], [24, 13]
        ]

        self.t2 = [[1, 13], [2, 12], [2, 11], [12, 12], [18, 12], [6, 12]]

        self.s1 = [[10, 10], [11, 10], [12, 10], [13, 10], [14, 10], [15, 10], [16, 10], [17, 10], [18, 10], [19, 10], [20, 10], [21, 10]]

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.smp(game_state)

        game_state.submit_turn()

    def smp(self, game_state):
        self.repair_damaged(game_state)
        self.build_defenses(game_state)
        self.shoot_your_shot(game_state)

    def repair_damaged(self, game_state):
        '''
        Go through the structures we have and begin refunding the structures
        lower than a certain health threshold.

        Note that the same structures we initiated refunds for might be upgraded
        in the same round, and thus invalidating the refund. I think that is okay.
        '''
        for x in range(28):
            for y in range(13):
                unit = game_state.contains_stationary_unit([x,y])
                if unit and unit.health < unit.max_health * .70:
                    game_state.attempt_remove([x,y])

    def funnel_built(self, game_state):
        '''
        Checks too see if the front line funnel is built, returns
        the number of SP needed to complete it (so 0 if it is built).
        '''
        SP_needed = len(self.w1)
        for loc in self.w1:
            if game_state.contains_stationary_unit(loc):
                SP_needed -= 1
        return SP_needed

    def build_defenses(self, game_state):
        '''
        This iteration uses a pocket. Never tried that before so why not?
        '''

        game_state.attempt_spawn(TURRET, self.t1)
        game_state.attempt_spawn(WALL, self.w1)

        # Key wall and turret upgrade.
        game_state.attempt_upgrade([5, 13])
        game_state.attempt_upgrade([5, 12])

        game_state.attempt_spawn(TURRET, self.t2)
        # Walls to extend the tunnel.
        game_state.attempt_spawn(WALL, [[3, 10], [4, 10], [5, 10], [6, 10]])
        # Upgrade corner turrets.
        game_state.attempt_upgrade([[26, 12], [2, 12]])
        game_state.attempt_spawn(TURRET, [[9, 12], [15, 12], [21, 12], [24, 12]])
        # Upgrade key walls.
        game_state.attempt_upgrade([[26, 13], [27, 13], [2, 13], [1, 13], [0, 13]])
        game_state.attempt_spawn(TURRET, [1, 12])
        game_state.attempt_spawn(
            WALL, 
            [[25, 12], [25, 11], [23, 12], [22, 12], [20, 12], [19, 12],
             [17, 12], [16, 12], [14, 12], [13, 12], [11, 12], [10, 12], [8, 12]])
        game_state.attempt_spawn(TURRET, [7, 12])      

        # Everything under this are luxuries, we split between offense and defense.
        tower_upgrades = [
            [1, 13], [1, 12], [2, 11], [6, 12], [7, 12], [24, 12], [21, 12], [18, 12], [15, 12], [12, 12], [9, 12]
        ]
        
        for loc in tower_upgrades[:game_state.turn_number // 5]:
            game_state.attempt_upgrade(loc)
        for loc in self.s1:
            game_state.attempt_spawn(SUPPORT, loc)
            game_state.attempt_upgrade(loc)

    def shoot_your_shot(self, game_state):
        '''
        Initiate offense. This currently only have very limited attack patterns.

        Attack 1: Early interceptors until pocket is ready.
        Attack 2: Demolishers when we have enough resources.
        '''
        if game_state.get_resource(1) >= 6 and random.random()>0.6:
            game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)
        # else:
        #     game_state.attempt_spawn(INTERCEPTOR, [24, 10], 1)    

    def print_stats(self, loc, unit_type, score_all):
        gamelib.debug_write('-------------------------------')
        gamelib.debug_write('location: ' + str(loc))
        gamelib.debug_write('type: ' + str(unit_type))
        gamelib.debug_write('score: %f' % score_all['score'])
        gamelib.debug_write('Damage score: %f' % score_all['dam_score'])
        gamelib.debug_write('Kill score: %f' % score_all['kill_score'])
        gamelib.debug_write('Edge score: %f' % score_all['edge_score'])
        gamelib.debug_write('Path:' + str(score_all['total_path']))
        # gamelib.debug_write('Buffs: ' + str(self.small_buff) + " " + str(self.big_buff))
        gamelib.debug_write('-------------------------------')


    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # # Let's record at what position we get scored on
        # state = json.loads(turn_string)
        # death = state["events"]["death"]
        # for item in death:
        #     # gamelib.debug_write("item: " + str(item))
        #     if item[3] == 1 and item[4]==False:
        #         loc = item[0]
        #         unit_type = item[1]
        #         if loc in self.left_corner:
        #             self.damage_upgrade_list.append([TURRET, [3, 12]])
        #             self.damage_upgrade_list.append([TURRET, [2, 12]])
        #         elif loc in self.right_corner:
        #             self.damage_upgrade_list.append([TURRET, [24, 12]])
        #             self.damage_upgrade_list.append([TURRET, [25, 12]])
        #         self.damage_upgrade_list.append([unit_type, loc])

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
