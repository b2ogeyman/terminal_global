import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from copy import deepcopy

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

        self.deleted_holes_last_turn = False
        self.left_corner_wall_update = False
        self.right_corner_wall_update = False

        self.wall1 = [[0, 13], [1, 13], [2, 13], [3, 13], [24, 13], [25, 13], [26, 13], [27, 13], [5, 11], [22, 11], [11, 9], [16, 9]]
        self.turret1 = [[5, 10], [22, 10], [11, 8], [16, 8]]
        self.upgrade1 = [[5, 10], [22, 10]]

        self.wall2 = [[4, 12], [23, 12], [10, 9], [12, 9], [15, 9], [17, 9], [6, 11], [21, 11], [4, 11], [23, 11], [7, 9], [20, 9]]
        self.turret2 = [[2, 12], [3, 12], [24, 12], [25, 12], [12, 8], [15, 8], [9, 8], [19, 8], [6, 10], [21, 10]]
        # self.upgrade2 = [[2, 13], [3, 13], [24, 13], [25, 13], [2, 12], [3, 12], [24, 12], [25, 12], [6, 10], [21, 10], [8, 8], [11, 8], [12, 8], [15, 8], [16, 8], [19, 8], [18, 8], [6, 11], [21, 11]]
        
        self.wall3 = [[7, 10], [8, 9], [9, 9], [13, 9], [14, 9], [18, 9], [19, 9], [20, 10], [1, 12], [26, 12], [10, 8], [17, 8]]
        self.turret3 = [[8, 8], [18, 8], [3, 11], [24, 11], [6, 9], [21, 9]]
        

        self.holes = [[23, 12], [4, 12], [7, 10], [20, 10], [10, 9], [17, 9], [4, 11], [23, 11], [7, 9], [20, 9], [10, 8], [17, 8]]

        self.left_corner = [[0,13], [1,13], [1,12], [2,12], [3,11]]
        self.right_corner = [[27,13], [26,13], [26,12], [25,12], [24,11]]

        self.start_att_locs = [[3, 10], [6, 7], [10, 3], [17, 3], [21, 7], [24, 10]]

        self.wall_line = [[0, 13], [1, 13], [2, 13], [3, 13], [24, 13], [25, 13], [26, 13], [27, 13], [4, 12], [23, 12], [5, 11], [6, 11], [21, 11], [22, 11], [7, 10], [20, 10], [8, 9], [9, 9], [10, 9], [11, 9], [12, 9], [13, 9], [14, 9], [15, 9], [16, 9], [17, 9], [18, 9], [19, 9]]

        self.small_buff = 0
        self.big_buff = 0

        self.damage_upgrade_list = []

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
        self.scored_on_locations = []

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

        self.Kais_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def check_corner_stat_interceptor(self, game_state, edge):
        att_locs_times = []
        def_locs = []
        if edge == game_state.game_map.TOP_LEFT: # target top-left edge
            att_locs_times = [[4, 14, 0, 3], [3, 14, 2, 5], [2, 14, 3, 5], [1, 14, 3, 4], [0, 14, 2, 2],
                              [3, 15, 0, 2], [2, 15, 1, 3], [1, 15, 1, 3], [2, 16, 0, 1]]
            def_locs = [[0, 14], [1, 14]]
        else:
            att_locs_times = [[23, 14, 0, 3], [24, 14, 2, 5], [25, 14, 3, 5], [26, 14, 3, 4], [27, 14, 2, 2],
                              [24, 15, 0, 2], [25, 15, 1, 3], [26, 15, 1, 3], [25, 16, 0, 1]]
            def_locs = [[26, 14], [27, 14]]

        # check the [0, 14] corner and see if there are chance of attacking
        total_attack_power = 0
        for loc_times in att_locs_times:
            location = loc_times[:2]
            unit = game_state.contains_stationary_unit(location)
            if unit != False and unit.unit_type == TURRET:
                if not unit.upgraded:
                    total_attack_power += 4 * loc_times[2] * 6
                else:
                    total_attack_power += 4 * loc_times[3] * 20
        
        total_defense_power = 0
        for location in def_locs:
            unit = game_state.contains_stationary_unit(location)
            # gamelib.debug_write("unit: " + str(unit))
            if unit != False:
                total_defense_power = max(total_defense_power, unit.health)
                # gamelib.debug_write("health: " + str(unit.health))
        unit_health = 40
        scout_health = 15 + self.small_buff + self.big_buff
        self_destruct_num_required = total_defense_power/unit_health
        scouts_killed = total_attack_power/(4 * scout_health)
        killed_num = total_attack_power/unit_health
        gamelib.debug_write("self_destruct_num_required_inter: " + str(self_destruct_num_required) + " killed_num_inter: " + str(killed_num))

        return int(self_destruct_num_required + killed_num) + 1, scouts_killed

    def check_corner_stat_demolisher(self, game_state, edge):
        att_locs_times = []
        att_locs_split = []
        def_loc = []
        if edge == game_state.game_map.TOP_LEFT: # target top-left edge
            att_locs_split = [[[4, 14, 0, 0], [3, 14, 0, 1], [2, 14, 0, 1], [1, 14, 0, 1], [0, 14, 0, 0],
                                [3, 15, 0, 0], [2, 15, 0, 0], [1, 15, 0, 0], [2, 16, 0, 0]], 
                              [[4, 14, 0, 1], [3, 14, 1, 1], [2, 14, 1, 1], [1, 14, 1, 1], [0, 14, 0, 1],
                                [3, 15, 0, 0], [2, 15, 0, 1], [1, 15, 0, 0], [2, 16, 0, 0]],
                              [[4, 14, 0, 0], [3, 14, 0, 1], [2, 14, 1, 1], [1, 14, 1, 1], [0, 14, 1, 1],
                                [3, 15, 0, 0], [2, 15, 0, 0], [1, 15, 0, 1], [2, 16, 0, 0]],
                              [[4, 14, 0, 1], [3, 14, 1, 1], [2, 14, 1, 1], [1, 14, 1, 1], [0, 14, 1, 1],
                                [3, 15, 0, 1], [2, 15, 1, 1], [1, 15, 1, 1], [2, 16, 0, 1]],
                              [[4, 14, 0, 1], [3, 14, 0, 1], [2, 14, 1, 1], [1, 14, 1, 1], [0, 14, 1, 1],
                                [3, 15, 0, 0], [2, 15, 0, 1], [1, 15, 1, 1], [2, 16, 0, 0]],
                              ]

            att_locs_times = [[4, 14, 0, 3], [3, 14, 2, 6], [2, 14, 4, 6], [1, 14, 4, 5], [0, 14, 3, 3],
                              [3, 15, 0, 2], [2, 15, 1, 3], [1, 15, 2, 4], [2, 16, 0, 1]]
            def_loc = [0, 14]
        else:
            att_locs_split = [[[23, 14, 0, 0], [23, 14, 0, 1], [25, 14, 0, 1], [26, 14, 0, 1], [27, 14, 0, 0],
                                [3, 15, 0, 0], [2, 15, 0, 0], [1, 15, 0, 0], [2, 16, 0, 0]], 
                              [[23, 14, 0, 1], [23, 14, 1, 1], [25, 14, 1, 1], [26, 14, 1, 1], [27, 14, 0, 1],
                                [3, 15, 0, 0], [2, 15, 0, 1], [1, 15, 0, 0], [2, 16, 0, 0]],
                              [[23, 14, 0, 0], [24, 14, 0, 1], [25, 14, 1, 1], [26, 14, 1, 1], [27, 14, 1, 1],
                                [3, 15, 0, 0], [2, 15, 0, 0], [1, 15, 0, 1], [2, 16, 0, 0]],
                              [[23, 14, 0, 1], [24, 14, 1, 1], [25, 14, 1, 1], [26, 14, 1, 1], [27, 14, 1, 1],
                                [3, 15, 0, 1], [2, 15, 1, 1], [1, 15, 1, 1], [2, 16, 0, 1]],
                              [[23, 14, 0, 1], [24, 14, 0, 1], [25, 14, 1, 1], [26, 14, 1, 1], [27, 14, 1, 1],
                                [24, 15, 0, 0], [25, 15, 0, 1], [26, 15, 1, 1], [25, 16, 0, 0]],
                              ]

            att_locs_times = [[23, 14, 0, 3], [24, 14, 2, 6], [25, 14, 4, 6], [26, 14, 4, 5], [27, 14, 3, 3],
                              [24, 15, 0, 2], [25, 15, 1, 3], [26, 15, 2, 4], [25, 16, 0, 1]]
            def_loc = [27, 14]

        unit_health = 5 + self.small_buff + self.big_buff
        gamelib.debug_write("small_buf: " + str(self.small_buff))
        gamelib.debug_write("big_buf: " + str(self.big_buff))
        gamelib.debug_write("dem_unit_health: " + str(unit_health))
        demolisher_num = 1000
        for n in range(0, int(game_state.number_affordable(DEMOLISHER)) + 1):
            cur = n
            damage = 0
            for i in range(5):
                damage += 8 * cur
                cur_attack_power = 0
                for entry in att_locs_split[i]:
                    unit = game_state.contains_stationary_unit(entry[:2])
                    if unit and unit.unit_type == TURRET:
                        if not unit.upgraded:
                            cur_attack_power += 2 * entry[2] * 6
                        else:
                            cur_attack_power += 2 * entry[3] * 20
                cur = max(0, cur - int(cur_attack_power / unit_health))
            if not game_state.contains_stationary_unit(def_loc) or damage >= game_state.contains_stationary_unit(def_loc).health:
                demolisher_num = n
                break
        

        total_attack_power = 0
        for loc_times in att_locs_times:
            location = loc_times[:2]
            unit = game_state.contains_stationary_unit(location)
            if unit != False and unit.unit_type == TURRET:
                if not unit.upgraded:
                    total_attack_power += loc_times[2] * 6
                else:
                    total_attack_power += loc_times[3] * 20
        
        scout_health = 15 + self.small_buff + self.big_buff
        scouts_killed = total_attack_power/scout_health
        gamelib.debug_write("send_required_dem: " + str(demolisher_num) + " killed_num_dem: " + str(-1))

        return demolisher_num, scouts_killed
    
    def check_corner_stat_scout(self, game_state, edge):
        att_locs_times = []
        def_locs = []
        if edge == game_state.game_map.TOP_LEFT: # target top-left edge
            att_locs_times = [[4, 14, 0, 3], [3, 14, 2, 6], [2, 14, 4, 6], [1, 14, 4, 5], [0, 14, 3, 3],
                              [3, 15, 0, 2], [2, 15, 1, 3], [1, 15, 2, 4], [2, 16, 0, 1]]
            def_locs = [[0, 14]]
        else:
            att_locs_times = [[23, 14, 0, 3], [24, 14, 2, 6], [25, 14, 4, 6], [26, 14, 4, 5], [27, 14, 3, 3],
                              [24, 15, 0, 2], [25, 15, 1, 3], [26, 15, 2, 4], [25, 16, 0, 1]]
            def_locs = [[26, 14]]

        # check the [0, 14] corner and see if there are chance of attacking
        total_attack_power = 0
        for loc_times in att_locs_times:
            location = loc_times[:2]
            unit = game_state.contains_stationary_unit(location)
            if unit != False and unit.unit_type == TURRET:
                if not unit.upgraded:
                    total_attack_power += loc_times[2] * 6
                else:
                    total_attack_power += loc_times[3] * 20
        
        total_defense_power = 0
        for location in def_locs:
            unit = game_state.contains_stationary_unit(location)
            # gamelib.debug_write("unit: " + str(unit))
            if unit != False:
                total_defense_power = max(total_defense_power, unit.health)
                # gamelib.debug_write("health: " + str(unit.health))
        unit_health = 15 + self.small_buff + self.big_buff
        self_destruct_num_required = total_defense_power/15
        killed_num = total_attack_power/unit_health
        gamelib.debug_write("self_destruct_num_required_scout: " + str(self_destruct_num_required) + " killed_num_scout: " + str(killed_num))

        return int(self_destruct_num_required + killed_num) + 1, killed_num

    def check_corner_attack(self, game_state, unit_type):
        #self.check_num_support(game_state)
        # if self.num_support < 6:
        #     return None, None
        group_num_left_required, group_num_right_required = None, None
        if unit_type == INTERCEPTOR:
            group_num_left_required = self.check_corner_stat_interceptor(game_state, game_state.game_map.TOP_LEFT)
            group_num_right_required = self.check_corner_stat_interceptor(game_state, game_state.game_map.TOP_RIGHT)
        elif unit_type == DEMOLISHER:
            group_num_left_required = self.check_corner_stat_demolisher(game_state, game_state.game_map.TOP_LEFT)
            group_num_right_required = self.check_corner_stat_demolisher(game_state, game_state.game_map.TOP_RIGHT)
        else:
            group_num_left_required = self.check_corner_stat_scout(game_state, game_state.game_map.TOP_LEFT)
            group_num_right_required = self.check_corner_stat_scout(game_state, game_state.game_map.TOP_RIGHT)

        total_num_required = min(group_num_left_required, group_num_right_required)
        target_edge = game_state.game_map.TOP_LEFT if group_num_left_required < group_num_right_required else game_state.game_map.TOP_RIGHT
        return target_edge, total_num_required[0], total_num_required[1]

    def use_holes(self, game_state):
        return game_state.turn_number %4 == 0

    def build_supports(self, game_state, path):
        band = game_state.get_band(path, 3.5)
        band.sort(key=lambda p : -p[1])
        self.small_buff, self.big_buff = 0, 0
        supports = []
        for loc in band:
            if loc[1] <= 13 and (loc[1] <= 9 or loc[0] + loc[1] <= 14 or loc[0] - loc[1] >= 13) and loc not in path and len(game_state.game_map[loc]) == 0:
                if game_state.can_spawn(SUPPORT, loc):
                    supports.append(loc)
                    game_state.attempt_spawn(SUPPORT, loc)
                    self.small_buff += game_state.game_map[loc][0].shieldPerUnit
                #game_state.attempt_remove(loc)
        supports.sort(key=lambda p : -p[1])
        for loc in supports:
            if loc[1] < 9:
                break
            res = game_state.attempt_upgrade(loc)
            if res > 0:
                self.small_buff -= 3
                self.big_buff += game_state.game_map[loc][0].shieldPerUnit

        band = game_state.get_band(path, 7)
        band.sort(key=lambda p : -p[1])
        for loc in band:
            if loc[1] <= 13 and (loc[1] <= 9 or loc[0] + loc[1] <= 14 or loc[0] - loc[1] >= 13) and loc not in path and len(game_state.game_map[loc]) == 0:
                if game_state.get_resource(SP) >= 8:
                    supports.append(loc)
                    game_state.attempt_spawn(SUPPORT, loc)
                    game_state.attempt_upgrade(loc)
                    self.big_buff += game_state.game_map[loc][0].shieldPerUnit
        if supports:
            game_state.attempt_remove(supports)

    def can_perform_corner(self, game_state, target_edge, unit_type):
        corner_open = True
        if target_edge == game_state.game_map.TOP_LEFT:
            for loc in self.left_corner:
                if game_state.contains_stationary_unit(loc):
                    corner_open = False
            if (unit_type == INTERCEPTOR or unit_type == SCOUT) and ((not game_state.contains_stationary_unit([1, 14])) and (not game_state.contains_stationary_unit([2, 14])) and (not game_state.contains_stationary_unit([3, 14])) and game_state.contains_stationary_unit([0, 14])):
                corner_open = False
        else:
            for loc in self.right_corner:
                if game_state.contains_stationary_unit(loc):
                    corner_open = False
            if (unit_type == INTERCEPTOR or unit_type == SCOUT) and ((not game_state.contains_stationary_unit([26, 14])) and (not game_state.contains_stationary_unit([25, 14])) and (not game_state.contains_stationary_unit([24, 14])) and game_state.contains_stationary_unit([27, 14])):
                corner_open = False
        return corner_open


    def Kais_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        left_corner_wall = game_state.contains_stationary_unit([0,13])
        right_corner_wall = game_state.contains_stationary_unit([27,13])
            
        if left_corner_wall != False and left_corner_wall.health < 0.5*left_corner_wall.max_health:
            if left_corner_wall.upgraded:
                self.left_corner_wall_update = True
                game_state.attempt_remove([0,13])
            else:
                self.left_corner_wall_update = False
                game_state.attempt_upgrade([0,13])
        else:
            self.left_corner_wall_update = False

        if right_corner_wall != False and right_corner_wall.health < 0.5*right_corner_wall.max_health:
            if right_corner_wall.upgraded:
                self.right_corner_wall_update = True
                game_state.attempt_remove([27,13])
            else:
                self.right_corner_wall_update = False
                game_state.attempt_upgrade([27,13])
        else:
            self.right_corner_wall_update = False

        if self.left_corner_wall_update:
            game_state.attempt_spawn(WALL, [0,13])
            game_state.attempt_upgrade([0,13])
        if self.right_corner_wall_update:
            game_state.attempt_spawn(WALL, [27,13])
            game_state.attempt_upgrade([27,13])

        attack_path = None


        if game_state.turn_number < 8:
            budget = game_state.get_resource(MP)
            if game_state.get_resource(SP, player_index=1)>30:
                attack_path = self.random_demolisher_attack(game_state)
            else:
                attack_path = self.attack_monte_carlo(game_state, score_th = 600)
            self.upgrade_from_damage(game_state, attack_path = attack_path)
            self.build_defenses(game_state, attack_path = attack_path)

        else: 

            attack_path = []
            if game_state.turn_number % 4 == 1:
                corner_attack = False
                target_edge = None
                target_edge_in, total_num_required_in, scouts_killed_in = self.check_corner_attack(game_state, INTERCEPTOR)
                target_edge_sc, total_num_required_sc, scouts_killed_sc = self.check_corner_attack(game_state, SCOUT)
                target_edge_dem, total_num_required_dem, scouts_killed_dem = self.check_corner_attack(game_state, DEMOLISHER)

                
                if self.check_defense_could_be_closed(game_state):
                    max_second_group_num = max(game_state.enemy_health + 2, 8)

                    if self.can_perform_corner(game_state, target_edge_in, INTERCEPTOR) and game_state.number_affordable(SCOUT) >= total_num_required_in + scouts_killed_in + 6:
                        corner_attack = True
                        target_edge = target_edge_in
                        total_num_required_in += int(max((game_state.get_resource(MP)//1)-(total_num_required_in + 2) - max_second_group_num, 0))

                        if target_edge_in == game_state.game_map.TOP_LEFT:
                            game_state.attempt_spawn(INTERCEPTOR, [3,10], total_num_required_in + 2)
                            game_state.attempt_spawn(SCOUT, [14, 0], 100)

                            for i in range(14):
                                attack_path += [[13 - i, i], [14 - i, i]]
                        else:
                            game_state.attempt_spawn(INTERCEPTOR, [24,10], total_num_required_in + 2)
                            game_state.attempt_spawn(SCOUT, [13, 0], 100)
                            for i in range(14):
                                attack_path += [[14 + i, i], [13 + i, i]]
                    elif self.can_perform_corner(game_state, target_edge_sc, SCOUT) and game_state.number_affordable(SCOUT) >= total_num_required_sc + scouts_killed_sc + 6 and game_state.number_affordable(WALL) >= 3:
                        corner_attack = True
                        target_edge = target_edge_sc
                        total_num_required_sc += int(max((game_state.get_resource(MP)//1)-(total_num_required_sc + 2) - max_second_group_num, 0))

                        if target_edge_sc == game_state.game_map.TOP_LEFT:
                            game_state.attempt_spawn(SCOUT, [14,0], total_num_required_sc + 2)
                            game_state.attempt_spawn(WALL, [[14,2], [15,3], [16,3]])
                            game_state.attempt_remove([[14,2], [15,3], [16,3]])
                            game_state.attempt_spawn(SCOUT, [16, 2], 100)

                            for i in range(14):
                                attack_path += [[13 - i, i], [14 - i, i]]
                        else:
                            game_state.attempt_spawn(SCOUT, [13,0], total_num_required_sc + 2)
                            game_state.attempt_spawn(WALL, [[13,2], [12,3], [11,3]])
                            game_state.attempt_remove([[13,2], [12,3], [11,3]])
                            game_state.attempt_spawn(SCOUT, [11, 2], 100)
                            for i in range(14):
                                attack_path += [[14 + i, i], [13 + i, i]]
                    elif self.can_perform_corner(game_state, target_edge_dem, DEMOLISHER) and game_state.number_affordable(SCOUT) >= 3 * total_num_required_dem + scouts_killed_dem + 4:
                        corner_attack = True
                        target_edge = target_edge_dem
                        total_num_required_dem += int(max((game_state.get_resource(MP)//1)-(total_num_required_dem + 2) - max_second_group_num, 0))

                        if target_edge_dem == game_state.game_map.TOP_LEFT:
                            game_state.attempt_spawn(DEMOLISHER, [6, 7], total_num_required_dem+1)
                            game_state.attempt_spawn(SCOUT, [14, 0], 100)

                            for i in range(14):
                                attack_path += [[13 - i, i], [14 - i, i]]
                        else:
                            game_state.attempt_spawn(DEMOLISHER, [21, 7], total_num_required_dem+1)
                            game_state.attempt_spawn(SCOUT, [13, 0], 100)
                            for i in range(14):
                                attack_path += [[14 + i, i], [13 + i, i]]

                gamelib.debug_write("game_state.get_resource(SP, player_index=1): " + str(game_state.get_resource(SP, player_index=1)))
                gamelib.debug_write("corner_attack: " + str(corner_attack))
                if corner_attack:
                    self.build_closed_defense(game_state, attack_path, target_edge)
                elif game_state.get_resource(SP, player_index=1)>20:
                    attack_path = self.random_demolisher_attack(game_state)
                else:
                    attack_path = self.attack_monte_carlo(game_state)
                    self.build_closed_defense(game_state, attack_path)
                self.upgrade_from_damage(game_state, attack_path = attack_path)
                self.build_defenses(game_state, attack_path = attack_path)
            else:
                self.build_closed_defense(game_state)
                self.upgrade_from_damage(game_state, attack_path = None)
                self.build_defenses(game_state, attack_path = None)  

            if game_state.turn_number % 4 == 0:
                self.remove_holes(game_state)
                for loc in self.left_corner + self.right_corner:
                    if game_state.contains_stationary_unit(loc) and game_state.game_map[loc][0].upgraded == False:
                        game_state.attempt_remove(loc)

            if game_state.turn_number % 4 == 2:
                for loc in self.left_corner + self.right_corner:
                    if game_state.contains_stationary_unit(loc) and game_state.game_map[loc][0].upgraded == True:
                        game_state.attempt_remove(loc)

        if attack_path:
            self.build_supports(game_state, attack_path)
        # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        # if game_state.turn_number < 5:
        #     self.interceptor_defend(game_state)

    

    def print_stats(self, loc, unit_type, score_all):
        gamelib.debug_write('-------------------------------')
        gamelib.debug_write('location: ' + str(loc))
        gamelib.debug_write('type: ' + str(unit_type))
        gamelib.debug_write('score: %f' % score_all['score'])
        gamelib.debug_write('Damage score: %f' % score_all['dam_score'])
        gamelib.debug_write('Kill score: %f' % score_all['kill_score'])
        gamelib.debug_write('Edge score: %f' % score_all['edge_score'])
        gamelib.debug_write('Path:' + str(score_all['total_path']))
        gamelib.debug_write('Buffs: ' + str(self.small_buff) + " " + str(self.big_buff))
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
            attack_all = tmp_game_state.attack_score(deploy_location, max_under_budget, DEMOLISHER, self.small_buff, self.big_buff)
            attack_score = attack_all["score"]
            if attack_all['kill_score'] >= 400:
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
            attack_all = tmp_game_state.attack_score(deploy_location, max_under_budget, SCOUT, self.small_buff, self.big_buff)
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
        

    def remove_holes(self, game_state):
        return game_state.attempt_remove(self.holes)

    def build_closed_defense(self, game_state, attack_path = None, target_edge = None):
        wall_line = self.wall_line.copy()
        if attack_path is not None:
            for pos in attack_path:
                if pos in wall_line:
                    wall_line.remove(pos)
        if target_edge is not None:
            remove_edge_locs = []
            if target_edge == game_state.game_map.TOP_LEFT:
                remove_edge_locs = [[0,13], [1, 13]]
            else:
                remove_edge_locs = [[27, 13], [26, 13]]
            for pos in remove_edge_locs:
                if pos in wall_line:
                    wall_line.remove(pos)

        game_state.attempt_spawn(WALL,wall_line)

    def check_defense_could_be_closed(self, game_state):
        breaks = 0
        for pos in self.wall_line:
            if not game_state.contains_stationary_unit(pos):
                breaks += 1
        return breaks + 3 < game_state.get_resource(SP)

    def build_defenses(self, game_state, attack_path = None):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download
        
        # first class buildings
        if attack_path is not None:
            wall1 = self.wall1.copy()
            wall2 = self.wall2.copy()
            wall3 = self.wall3.copy()
            turret1 = self.turret1.copy()
            turret2 = self.turret2.copy()
            turret3 = self.turret3.copy()
            upgrade1 = self.upgrade1.copy()
            # upgrade2 = self.upgrade2.copy()
            # upgrade3 = self.upgrade3.copy()
            for pos in attack_path:
                if pos in wall1:
                    wall1.remove(pos)
                if pos in wall2:
                    wall2.remove(pos)
                if pos in wall3:
                    wall3.remove(pos)
                if pos in turret1:
                    turret1.remove(pos)
                if pos in turret2:
                    turret2.remove(pos)
                if pos in turret3:
                    turret3.remove(pos)
                if pos in upgrade1:
                    upgrade1.remove(pos)
                # if pos in upgrade2:
                #     upgrade2.remove(pos)
                # if pos in upgrade3:
                #     upgrade3.remove(pos)
        else:
            wall1 = self.wall1.copy()
            wall2 = self.wall2.copy()
            wall3 = self.wall3.copy()
            turret1 = self.turret1.copy()
            turret2 = self.turret2.copy()
            turret3 = self.turret3.copy()
            upgrade1 = self.upgrade1.copy()
            # upgrade2 = self.upgrade2.copy()
            # upgrade3 = self.upgrade3.copy()
        game_state.attempt_spawn(WALL,wall1)
        game_state.attempt_spawn(TURRET,turret1)
        game_state.attempt_upgrade(upgrade1)

        game_state.attempt_spawn(WALL,wall2)
        game_state.attempt_spawn(TURRET,turret2) 
        # game_state.attempt_upgrade(upgrade2)

        game_state.attempt_spawn(WALL,wall3)
        game_state.attempt_spawn(TURRET,turret3) 

    def upgrade_from_damage(self, game_state, attack_path = None):
        for type_loc in self.damage_upgrade_list:
            unit_type, loc = type_loc
            if loc in self.holes or (attack_path and loc in attack_path):
                continue
            game_state.attempt_spawn(unit_type, loc)
            if game_state.turn_number % 4 not in [0, 3] and game_state.attempt_upgrade(loc)==1:
                self.damage_upgrade_list.remove(type_loc)

    def interceptor_defend(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        game_state.attempt_spawn(INTERCEPTOR, [6, 7], 1)
        game_state.attempt_spawn(INTERCEPTOR, [21, 7], 1)

    def random_demolisher_attack(self, game_state):
        att_loc = random.sample(self.start_att_locs, 1)[0]
        game_state.attempt_spawn(DEMOLISHER, att_loc, 100)
        return game_state.find_path_to_edge(att_loc)

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        death = state["events"]["death"]
        for item in death:
            # gamelib.debug_write("item: " + str(item))
            if item[3] == 1 and item[4]==False:
                loc = item[0]
                unit_type = item[1]
                self.damage_upgrade_list.append([unit_type, loc])


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
