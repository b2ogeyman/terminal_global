import gamelib
import random
import math
import warnings
from copy import deepcopy
from sys import maxsize
import json
import numpy as np
from collections import OrderedDict



class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))
        self.start_att_locs = [[13, 0], [14, 0]]
        self.side_walls = [[0, 13], [1, 12], [2, 11], [3, 10], [4, 9], [5, 8], [6, 7], [27, 13], [26, 12], [25, 11], [24, 10], [23, 9], [22, 8], [21, 7]]

        self.buff_walls = [[4, 12], [23, 12], [5, 12], [22, 12], [6, 11], [21, 11]]
        self.back_walls = [[6, 10], [7, 9], [8, 8], [9, 8], [10, 8], [11, 8], [12, 8], [13, 8], [14, 8], [15, 8], [16, 8], [17, 8], [18, 8], [19, 8], [20, 9], [21, 10]]
        self.turrets = [[5, 11], [22, 11]]

        self.upgrade_walls = [[0, 13], [27, 13], [1, 12], [26, 12], [2, 11], [25, 11]]
        self.extra_left = [[3, 10], [4, 9], [5, 8]]
        self.extra_right = [[24, 10], [23, 9], [22, 8]]
        self.supports = [[14, 8], [12, 8], [13, 8], [15, 8], [11, 8], [16, 8], [10, 8], [17, 8], [9, 8], [18, 8], [8, 8], [19, 8]]
        self.left_cover = [[6, 10], [5, 11], [4, 12], [3, 13]]
        self.right_cover = [[21, 10], [22, 11], [23, 12], [24, 13]]
        self.attack_paths = OrderedDict()
        self.off_limits = []
        for i in range(1, 13):
            self.off_limits += [[13+i, i], [12+i, i], [15-i,i], [14-i,i]]
        self.off_limits += [[13, 0], [14, 0]]
        self.off_limits += self.back_walls
        self.last_attack = 0
        self.all_locs = []
        self.left_locs = []
        self.right_locs = []
        for x in range(28):
            for y in range(8, 13):
                if [x,y] not in self.off_limits and x + y >= 13 and x - y <= 14 and (x <= 8 or x >= 19):
                    self.all_locs.append([x,y])
                    if x <= 8:
                        self.left_locs.append([x,y])
                    else:
                        self.right_locs.append([x,y])

        #self.start_att_locs = [[3, 10], [6, 7], [10, 3], [17, 3], [21, 7], [24, 10]]
        self.removals = [[] for i in range(110)]

        self.last_game_state = None
        self.just_scored = False
        self.just_beat = False
        self.allowance = 2

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
        
        if game_state.turn_number == 30:
            if self.extra_left[0] in self.upgrade_walls or self.extra_right[0] in self.upgrade_walls:
                if self.extra_left[0] not in self.upgrade_walls:
                    self.upgrade_walls += self.extra_left
                if self.extra_right[0] not in self.upgrade_walls:
                    self.upgrade_walls += self.extra_right
            else:
                self.upgrade_walls += self.intertwine(self.extra_left, self.extra_right)
        self.starter_strategy(game_state)
        self.last_game_state = game_state
        self.just_scored = False
        self.just_beat = False
        game_state.submit_turn()

    def gen_av(self, game_state, l, cap):
        res = []
        if cap < 1:
            return res
        for x in l:
            if not game_state.contains_stationary_unit(x):
                res.append(x)
                if len(res) == cap:
                    break
        return res
    
    def intertwine(self, l, r):
        res = []
        for i in range(max(len(l), len(r))):
            cur = []
            if i < len(l):
                cur.append(l[i])
            if i < len(r):
                cur.append(r[i])
            res += cur
        return res

    def build_defense(self, game_state):
        if game_state.turn_number < 10:
            game_state.attempt_spawn(TURRET, self.turrets)
            game_state.attempt_spawn(WALL, self.buff_walls)
            game_state.attempt_spawn(WALL, self.back_walls)
            game_state.attempt_spawn(WALL, self.side_walls)
            #game_state.attempt_spawn(WALL, self.back_walls)
            for loc in self.turrets:
                if game_state.contains_stationary_unit(loc) and game_state.contains_stationary_unit(loc).unit_type == TURRET:
                    game_state.attempt_upgrade(loc)
          #  game_state.attempt_upgrade(self.upgrade_buff)
        else: 
            #gamelib.debug_write('Support points: ', game_state.get_resource(SP))
            if game_state.turn_number == 10:
                game_state.attempt_remove(self.buff_walls)
            if self.allowance <= 10:
                if self.just_scored or self.just_beat or (game_state.turn_number >= 16 and game_state.turn_number - self.last_attack >= 6):
                    self.allowance += 2
            
            #game_state.attempt_upgrade(self.upgrade_walls)
            if game_state.turn_number % 4 == 1:
                game_state.attempt_spawn(WALL, [[7, 7], [20, 7]])
            if game_state.turn_number % 4 == 2:
                game_state.attempt_spawn(WALL, [[7, 7], [20, 7]])
                game_state.attempt_remove([[7, 7], [20, 7]])
            #self.all_locs.sort(key = lambda p : self.usefulness_quotient(game_state, p), reverse = True)
            self.left_locs.sort(key = lambda p : self.usefulness_quotient(game_state, p), reverse = True)
            self.right_locs.sort(key = lambda p : self.usefulness_quotient(game_state, p), reverse = True)
            have_left = 0
            have_right = 0
            for loc in self.left_locs:
                if game_state.contains_stationary_unit(loc) and game_state.contains_stationary_unit(loc).unit_type == TURRET:
                    have_left += 1
            for loc in self.right_locs:
                if game_state.contains_stationary_unit(loc) and game_state.contains_stationary_unit(loc).unit_type == TURRET:
                    have_right += 1
            gamelib.debug_write(have_left, have_right, self.allowance)
            top_right = self.gen_av(game_state, self.right_locs, self.allowance//2  - have_right)
            top_left = self.gen_av(game_state, self.left_locs, self.allowance//2  - have_left)
            
            #gamelib.debug_write('Allowance: ', self.allowance)
            #gamelib.debug_write('Top left: ', top_left)
            #gamelib.debug_write('Top right: ', top_right)

            '''
            if game_state.turn_number == 24:
                gamelib.debug_write('All locations:')
                for loc in self.all_locs:
                    gamelib.debug_write(loc, self.usefulness_quotient(game_state, loc))
            '''
            '''
            for loc in self.left_locs:
                if game_state.contains_stationary_unit(loc) and game_state.contains_stationary_unit(loc).unit_type == TURRET and loc not in self.left_locs[:self.allowance//2+5]:
                    game_state.attempt_remove(loc)
                    if game_state.contains_stationary_unit([loc[0], loc[1]+1]) and game_state.contains_stationary_unit([loc[0], loc[1]+1]).unit_type == WALL:
                        game_state.attempt_remove([loc[0], loc[1]+1])

            for loc in self.right_locs:
                if game_state.contains_stationary_unit(loc) and game_state.contains_stationary_unit(loc).unit_type == TURRET and loc not in self.right_locs[:self.allowance//2+5]:
                    game_state.attempt_remove(loc)
                    if game_state.contains_stationary_unit([loc[0], loc[1]+1]) and game_state.contains_stationary_unit([loc[0], loc[1]+1]).unit_type == WALL:
                        game_state.attempt_remove([loc[0], loc[1]+1])
            '''
            for loc in self.intertwine(self.right_locs, self.left_locs):
                unit = game_state.contains_stationary_unit(loc)
                if unit and unit.unit_type == TURRET and not unit.pending_removal and [loc[0], loc[1]+1] not in self.off_limits:
                    num1 = game_state.attempt_spawn(WALL, [loc[0], loc[1]+1])
                    if num1 > 0:
                        game_state.attempt_upgrade([loc[0], loc[1]+1])
                if not unit and game_state.contains_stationary_unit([loc[0], loc[1]+1]) and game_state.contains_stationary_unit([loc[0], loc[1]+1]).unit_type == WALL:
                    game_state.attempt_remove([loc[0], loc[1]+1])
            
            if len(top_right) >= len(top_left):
                lst = self.intertwine(top_right, top_left)
            else:
                lst = self.intertwine(top_left, top_right)
            for loc in lst:
                num = game_state.attempt_spawn(TURRET, loc)
                if game_state.contains_stationary_unit(loc) and game_state.contains_stationary_unit(loc).unit_type == TURRET:
                    game_state.attempt_upgrade(loc)
                    if [loc[0], loc[1]+1] not in self.off_limits:
                        num1 = game_state.attempt_spawn(WALL, [loc[0], loc[1]+1])
                        if num1 > 0:
                            game_state.attempt_upgrade([loc[0], loc[1]+1])




    def starter_strategy(self, game_state):
        for x in range(28):
            for y in range(14):
                unit = game_state.contains_stationary_unit([x,y])
                if unit and unit.health < unit.max_health * .70:
                    game_state.attempt_remove([x,y])
        need_walls = 0
        att_walls = 0
        if game_state.turn_number <= 10:
            att_walls = 1
        elif game_state.turn_number % 4 == 0:
            att_walls = 4
        for loc in self.back_walls + self.side_walls:
            if not game_state.contains_stationary_unit(loc):
                need_walls += 1
        sp = game_state._player_resources[0]['SP']
        game_state._player_resources[0]['SP'] -= min(sp, att_walls)
        if game_state.turn_number > 15:
            sp1 = game_state._player_resources[0]['SP']
            game_state._player_resources[0]['SP'] -= min(sp1, need_walls)
            self.build_defense(game_state)
            game_state._player_resources[0]['SP'] += min(sp1, need_walls)
            game_state.attempt_spawn(WALL, self.side_walls)
            game_state.attempt_upgrade(self.upgrade_walls)
        else:
            self.build_defense(game_state)
        budget = game_state.get_resource(SP)
        n = int((budget - need_walls) / 8)
        nb = 0
        for i, loc in enumerate(self.supports):
            if nb >= n:
                break
            if game_state.can_spawn(SUPPORT, loc):
                game_state.attempt_spawn(SUPPORT, loc)
                game_state.attempt_upgrade(loc)
              #  self.back_walls.append([loc[0], loc[1]+1])
                nb += 1
            elif game_state.contains_stationary_unit(loc) and game_state.contains_stationary_unit(loc).unit_type == WALL:
                game_state.attempt_remove(loc)
                nb += 1
        game_state.attempt_spawn(WALL, self.back_walls)

   #     if game_state.turn_number >= 1:
   #         gamelib.debug_write('Removed last turn: ' + str(self.removals[game_state.turn_number - 1]))
        game_state._player_resources[0]['SP'] += min(sp, att_walls)
        if game_state.turn_number <= 10:
            self.attack_monte_carlo(game_state, score_th=500)
        
        elif game_state.turn_number % 4 == 0:
            hole = self.attack_monte_carlo(game_state)
            if hole:
                game_state.attempt_spawn(WALL, hole)


    def use_func(self, game_state, attack_path, turret_loc):
        att, df = 0, 0
        for loc in attack_path:
            if game_state.game_map.distance_between_locations(turret_loc, loc) <= 3.5:
                att += 1
            if game_state.game_map.distance_between_locations(turret_loc, loc) <= 4.5 or game_state.game_map.distance_between_locations([turret_loc[0], turret_loc[1]+1], loc) <= 4.5:
                df += 1
        return [att, -df]
    
    def usefulness_quotient(self, game_state, turret_loc):
        q = 0
        for i, (key, attack_path) in enumerate(reversed(self.attack_paths.items())):
            res = []
            [res.append(x) for x in attack_path if x not in res] 
            p = self.use_func(game_state, res, turret_loc)        
            q += 4 * (.9 ** i) * p[0]
            q += (.9 ** i) * p[1]
        return q


        
    def print_stats(self, loc, unit_type, score_all, hole, ints_num, try_max, cover):
        gamelib.debug_write('-------------------------------')
        gamelib.debug_write('location: ' + str(loc))
        gamelib.debug_write('type: ' + str(unit_type))
        gamelib.debug_write('score: %f' % score_all['score'])
        gamelib.debug_write('Damage score: %f' % score_all['dam_score'])
        gamelib.debug_write('Kill score: %f' % score_all['kill_score'])
        gamelib.debug_write('Edge score: %f' % score_all['edge_score'])
        gamelib.debug_write('Closed hole: ' + str(hole))
        gamelib.debug_write('Number left: %f' % score_all['number_left'])
    #    if ints_num:
        gamelib.debug_write('ints_num: %f' % ints_num)
        gamelib.debug_write('Cover: %f' % cover)
        gamelib.debug_write('Path:' + str(score_all['total_path']))

        gamelib.debug_write('-------------------------------')

    def setup_state(self, game_state, hole, cover):
        tmp_game_state = deepcopy(game_state)
        tmp_game_state.game_map.add_unit(WALL, hole)
        if game_state.turn_number >= 1:
            for loc in self.removals[game_state.turn_number - 1]:
                if not tmp_game_state.contains_stationary_unit(loc):
                    tmp_game_state.game_map.add_unit(self.last_game_state.contains_stationary_unit(loc).unit_type, loc, player_index = 1)
                    if self.last_game_state.contains_stationary_unit(loc).upgraded:
                        tmp_game_state.game_map[loc][0].upgrade()
                        tmp_game_state.game_map[loc][0].health = tmp_game_state.game_map[loc][0].max_health

        if cover:
            if hole == [7, 7]:
                tmp_game_state.attempt_spawn(WALL, self.right_cover)
            else:
                tmp_game_state.attempt_spawn(WALL, self.left_cover)

        return tmp_game_state

    def attack_monte_carlo(self, game_state, score_th = None):
        # randomly generate attacks and select the best ones
        # friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        deploy_locations = self.start_att_locs
        holes  = [[7, 7], [20, 7]]
        scout_good = True
        # first for demolisher:
        d_best_score = -100
        d_best_location = None
        d_best_number = None
        d_best_all = None
        d_best_hole = None
        d_best_extra = None
        d_best_cover = False


        for deploy_location in deploy_locations:
            for hole in holes:
                for cover in [True, False]:
                    max_under_budget = game_state.number_affordable(DEMOLISHER)
                    # gamelib.debug_write("DEMOLISHER cost is: " + str(game_state.type_cost(DEMOLISHER)[MP])+ "max_number is " + str(max_under_budget) + " with a budget of "+ str(budget))
                    tmp_game_state = self.setup_state(game_state, hole, cover)

                    attack_all = tmp_game_state.attack_score(deploy_location, max_under_budget, DEMOLISHER)
                    attack_score = attack_all["score"]
                    ints_num = 0
                    try_max = max_under_budget - 1
                    if attack_all['edge_score'] > 1001:
                        try_max = max_under_budget - 1
                        tmp_game_state = self.setup_state(game_state, hole, cover)
                    #    if game_state.turn_number == 40 and deploy_location == [13, 0] and hole == [20, 7] and not cover:
                    #        tmp_game_state.attack_score(deploy_location, try_max, DEMOLISHER, debug=True)
                        if tmp_game_state.attack_score(deploy_location, try_max, DEMOLISHER)['edge_score'] > 1:
                            ints_num = int(game_state.get_resource(MP) - 3 * try_max)
                                           
                    if ints_num > 0:
                        max_under_budget = try_max
                        attack_score += (ints_num - 1) * 1000

                    if attack_all['kill_score'] >= 300 or attack_all['edge_score'] >= 10000:
                        scout_good = False
                    if attack_score > d_best_score:
                        d_best_score = attack_score
                        d_best_location = deploy_location
                        d_best_number = max_under_budget
                        d_best_all = attack_all
                        d_best_hole = hole
                        d_best_extra = ints_num
                        d_best_cover = cover
                    self.print_stats(deploy_location, DEMOLISHER, attack_all, hole, ints_num, try_max, cover)
                 #gamelib.debug_write("find better score:"+ str(best_score))

        # then for scout:
        s_best_score = -100
        s_best_location = None
        s_best_number = None
        s_best_all = None
        s_best_hole = None
        if scout_good:
            for deploy_location in deploy_locations:
                for hole in holes:
                    max_under_budget = game_state.number_affordable(SCOUT)
                    # gamelib.debug_write("DEMOLISHER cost is: " + str(game_state.type_cost(DEMOLISHER)[MP])+ "max_number is " + str(max_under_budget) + " with a budget of "+ str(budget))
                    tmp_game_state = self.setup_state(game_state, hole, False)
             #       if game_state.turn_number == 40 and deploy_location == [13, 0] and hole == [7, 7]:
             #           tmp_game_state.attack_score(deploy_location, max_under_budget, SCOUT, debug=True)
                    attack_all = tmp_game_state.attack_score(deploy_location, max_under_budget, SCOUT)
                    attack_score = attack_all["edge_score"]
                    if attack_score > s_best_score:
                        s_best_score = attack_score
                        s_best_location = deploy_location
                        s_best_number = max_under_budget
                        s_best_all = attack_all
                        s_best_hole = hole
                # gamelib.debug_write("find better score:"+ str(best_score))

        #gamelib.debug_write("Best demolisher score: " + str(d_best_score))
        #self.print_stats(d_best_location, DEMOLISHER, d_best_all, d_best_hole)
        if scout_good:
           self.print_stats(s_best_location, SCOUT, s_best_all, s_best_hole, -1, -1, False)

        if d_best_score > s_best_score:
            best_type = DEMOLISHER
            best_location = d_best_location
            best_number = d_best_number
            best_score = d_best_score
            best_hole = d_best_hole
            best_extra = d_best_extra
        else:
            best_type = SCOUT
            best_location = s_best_location
            best_number = s_best_number
            best_score = s_best_score
            best_hole = s_best_hole

        if score_th is None or best_score > score_th:
            if best_type == SCOUT:
                game_state.attempt_spawn(best_type, best_location, best_number)
            else:
                if d_best_cover:
                    spawned = []
                    if best_hole == [7, 7]:
                        for loc in self.right_cover:
                            num = game_state.attempt_spawn(WALL, loc)
                            if num > 0:
                                spawned.append(loc)
                        game_state.attempt_remove(spawned)
                    else:
                        for loc in self.left_cover:
                            num = game_state.attempt_spawn(WALL, loc)
                            if num > 0:
                                spawned.append(loc)
                        game_state.attempt_remove(spawned)
                game_state.attempt_spawn(best_type, best_location, best_number)
                game_state.attempt_spawn(INTERCEPTOR, best_location, best_extra)
            #path = game_state.find_path_to_edge(best_location)
            return best_hole
        else: 
            return None




    def on_action_frame(self, turn_string):

        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        moves = events["move"]

        if state['turnInfo'][1] > 5:
            for move in moves:
                loc = move[1]
                if move[5] == 2 and move[3] != 5:
                    if state['turnInfo'][1] not in self.attack_paths:
                        self.attack_paths[state['turnInfo'][1]] = []
                    else:
                        self.attack_paths[state['turnInfo'][1]].append(loc)

        for unit in state['p2Units'][6]:
            if unit[2] == 1 and not [unit[0], unit[1]] in self.removals[state['turnInfo'][1]]:
                self.removals[state['turnInfo'][1]].append([unit[0], unit[1]])
        
        for breach in events['breach']:
            if breach[4] == 2:
                self.just_scored = True
                if breach[0] in self.extra_left + self.extra_right:
                    if self.extra_left[0] not in self.upgrade_walls:
                        self.upgrade_walls += self.extra_left
                    if self.extra_right[0] not in self.upgrade_walls:
                       self.upgrade_walls += self.extra_right
        for death in events['death']:
            if death[3] == 1 and death[1] == 2:
                self.just_beat = True
        for spawn in events['spawn']:
            if spawn[3] == 2 and spawn[1] in [3, 4]:
                self.last_attack = state['turnInfo'][1]

            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
