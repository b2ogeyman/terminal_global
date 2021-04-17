import gamelib
import random
import math
import warnings
from copy import deepcopy
from sys import maxsize
import json


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))
        self.start_att_locs = [[3, 10], [6, 7], [10, 3], [17, 3], [21, 7], [24, 10]]
        self.scout_walls = [[0, 13], [1, 13], [2, 13], [3, 13], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13], [11, 13], [12, 13], [13, 12], [13, 11], [14, 13], [15, 13], [16, 13], [17, 13], [18, 13], [19, 13], [20, 13], [21, 13], [22, 13], [23, 13], [24, 13], [25, 13], [26, 13], [27, 13]]
        self.scout_walls_upgrade = [[0,13], [12, 13], [13, 12], [13, 11], [14, 13], [27, 13]]

        self.dynamic_walls = [[7, 13], [20, 13]]
        self.dynamic_turrets = [[7, 12], [20, 12]]
        self.permanent_walls = []
        self.permanent_turrets = []
        self.supports = [[7,9], [8,9], [9, 9], [10, 9], [11, 9], [12, 9], [13, 9], [14, 9], [15, 9], [16, 9], [17, 9], [18, 9], [19, 9], [20, 9], [7, 8], [8,8], [9, 8], [10, 8], [11, 8], [12, 8], [13, 8], [14, 8], [15, 8], [16, 8], [17, 8], [18, 8], [19, 8], [20, 8]]
        self.attacks = {}

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
        # This is a good place to do initial setup
    
    def on_turn(self, turn_state):

        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.
        
        self.starter_strategy(game_state)

        game_state.submit_turn()


    def starter_strategy(self, game_state):
        
        if self.dynamic_walls:
            game_state.attempt_spawn(WALL, self.dynamic_walls)
        if self.dynamic_turrets:
            game_state.attempt_spawn(TURRET, self.dynamic_turrets)
        if self.dynamic_walls + self.dynamic_turrets:
            game_state.attempt_upgrade(self.dynamic_walls + self.dynamic_turrets)
        if self.permanent_walls:
            game_state.attempt_spawn(WALL, self.permanent_walls)
        if self.permanent_turrets:
            game_state.attempt_spawn(TURRET, self.permanent_turrets)
        if self.permanent_walls + self.permanent_turrets:
            game_state.attempt_upgrade(self.permanent_walls + self.permanent_turrets)
        for i, loc in enumerate(self.supports):
            if i % 4 == 3 and loc[1] == 9:
                self.permanent_walls.append([loc[0], loc[1]+2])
                self.permanent_turrets.append([loc[0], loc[1]+1])
            game_state.attempt_spawn(SUPPORT, loc)
            game_state.attempt_upgrade(loc)
            if not game_state.contains_stationary_unit(loc):
                break
        if game_state.turn_number == 20:
            self.permanent_walls += [[0, 13], [1, 13], [26, 13], [27, 13]]
            self.permanent_turrets += [[2, 12], [25, 12]]
        #game_state.contains_stationary_unit([i, 12]) and 
        if game_state.turn_number >= 20:
            for i in range(28):
                if game_state.contains_stationary_unit([i, 12]) and ((i, 12) not in self.attacks or self.attacks[(i, 12)] <= game_state.turn_number - 25) and [i, 12] not in self.permanent_turrets:
                    game_state.attempt_remove([[i, 13], [i, 12]])
                    if [i, 13] in self.dynamic_walls:
                        self.dynamic_walls.remove([i, 13])
                    if [i, 12] in self.dynamic_turrets:
                        self.dynamic_turrets.remove([i, 12])
        if game_state.turn_number <= 15:
            self.attack_monte_carlo(game_state, score_th=500)
        elif game_state.turn_number % 2 == 0:
            self.attack_monte_carlo(game_state)


        
    def print_stats(self, loc, unit_type, score_all):
        gamelib.debug_write('-------------------------------')
        gamelib.debug_write('location: ' + str(loc))
        gamelib.debug_write('type: ' + str(unit_type))
        gamelib.debug_write('score: %f' % score_all['score'])
        gamelib.debug_write('Damage score: %f' % score_all['dam_score'])
        gamelib.debug_write('Kill score: %f' % score_all['kill_score'])
        gamelib.debug_write('Edge score: %f' % score_all['edge_score'])
        gamelib.debug_write('Path:' + str(score_all['total_path']))
        gamelib.debug_write('-------------------------------')

    def attack_monte_carlo(self, game_state, score_th = None):
        # randomly generate attacks and select the best ones
        # friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        deploy_locations = self.start_att_locs


        # first for demolisher:
        d_best_score = -100
        d_best_location = None
        d_best_number = None
        d_best_all = None
        for deploy_location in deploy_locations:
            max_under_budget = game_state.number_affordable(DEMOLISHER)
            # gamelib.debug_write("DEMOLISHER cost is: " + str(game_state.type_cost(DEMOLISHER)[MP])+ "max_number is " + str(max_under_budget) + " with a budget of "+ str(budget))
            tmp_game_state = deepcopy(game_state)
            attack_all = tmp_game_state.attack_score(deploy_location, max_under_budget, DEMOLISHER)
            attack_score = attack_all["score"]
            if attack_all['kill_score'] >= 800:
                attack_score += 100000
            if attack_score> d_best_score:
                d_best_score = attack_score
                d_best_location = deploy_location
                d_best_number = max_under_budget
                d_best_all = attack_all
                # gamelib.debug_write("find better score:"+ str(best_score))

        # then for scout:
        s_best_score = -100
        s_best_location = None
        s_best_number = None
        s_best_all = None
        for deploy_location in deploy_locations:
            max_under_budget = game_state.number_affordable(SCOUT)
            # gamelib.debug_write("DEMOLISHER cost is: " + str(game_state.type_cost(DEMOLISHER)[MP])+ "max_number is " + str(max_under_budget) + " with a budget of "+ str(budget))
            tmp_game_state = deepcopy(game_state)
            attack_all = tmp_game_state.attack_score(deploy_location, max_under_budget, SCOUT)
            attack_score = attack_all["score"]
            if attack_score> s_best_score:
                s_best_score = attack_score
                s_best_location = deploy_location
                s_best_number = max_under_budget
                s_best_all = attack_all
                # gamelib.debug_write("find better score:"+ str(best_score))

        #gamelib.debug_write("Best demolisher score: " + str(d_best_score))
        self.print_stats(d_best_location, DEMOLISHER, d_best_all)
        self.print_stats(s_best_location, SCOUT, s_best_all)

        if d_best_score > s_best_score:
            best_type = DEMOLISHER
            best_location = d_best_location
            best_number = d_best_number
            best_score = d_best_score
        else:
            best_type = SCOUT
            best_location = s_best_location
            best_number = s_best_number
            best_score = s_best_score

        if score_th is None or best_score > score_th:
            game_state.attempt_spawn(best_type, best_location, best_number)
            path = game_state.find_path_to_edge(best_location)
            return path
        else: 
            return None




    def on_action_frame(self, turn_string):

        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        moves = events["move"]
        did = {}
        for move in moves:
            loc = move[1]
            if tuple(loc) not in did and move[5] == 2 and loc[1] == 13 and move[0][1] == 14 and len(self.dynamic_walls) < 27:
                if loc[0] > 0 and [loc[0]-1, loc[1]] not in self.dynamic_walls:
                    self.dynamic_walls.append([loc[0]-1, loc[1]])
                    if loc[0] - 1 != 0:
                        self.dynamic_turrets.append([loc[0] - 1, loc[1]-1])
                        self.attacks[(loc[0] - 1, loc[1]-1)] = state['turnInfo'][1]
                elif loc[0] < 27 and [loc[0]+1, loc[1]] not in self.dynamic_walls:
                    self.dynamic_walls.append([loc[0]+1, loc[1]])
                    if loc[0] + 1 != 27:
                        self.dynamic_turrets.append([loc[0] + 1, loc[1]-1])
                        self.attacks[(loc[0] + 1, loc[1]-1)] = state['turnInfo'][1]
            did[tuple(loc)] = True
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
        attacks = events["attack"]
        for attack in attacks:
            if attack[6] == 1 and attack[0][1] == 12:
                self.attacks[tuple(attack[0])] = state['turnInfo'][1] #turn number


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
