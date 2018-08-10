from dcs.terrain import Terrain
from dcs.lua.parse import loads

from userdata.debriefing import *

from theater import *
from gen import *


class Operation:
    attackers_starting_position = None  # type: db.StartingPosition
    defenders_starting_position = None  # type: db.StartingPosition
    mission = None  # type: dcs.Mission
    conflict = None  # type: Conflict
    armorgen = None  # type: ArmorConflictGenerator
    airgen = None  # type: AircraftConflictGenerator
    aagen = None  # type: AAConflictGenerator
    extra_aagen = None  # type: ExtraAAConflictGenerator
    shipgen = None  # type: ShipGenerator
    triggersgen = None  # type: TriggersGenerator
    awacsgen = None  # type: AirSupportConflictGenerator
    visualgen = None  # type: VisualGenerator
    envgen = None  # type: EnvironmentGenerator

    environment_settings = None
    trigger_radius = TRIGGER_RADIUS_MEDIUM
    is_quick = None
    is_awacs_enabled = False

    def __init__(self,
                 game,
                 attacker_name: str,
                 defender_name: str,
                 attacker_clients: db.PlaneDict,
                 defender_clients: db.PlaneDict,
                 from_cp: ControlPoint,
                 to_cp: ControlPoint = None):
        self.game = game
        self.attacker_name = attacker_name
        self.defender_name = defender_name
        self.attacker_clients = attacker_clients
        self.defender_clients = defender_clients
        self.from_cp = from_cp
        self.to_cp = to_cp
        self.is_quick = False

    def initialize(self, mission: Mission, conflict: Conflict):
        self.mission = mission
        self.conflict = conflict

        self.armorgen = ArmorConflictGenerator(mission, conflict)
        self.airgen = AircraftConflictGenerator(mission, conflict, self.game.settings)
        self.aagen = AAConflictGenerator(mission, conflict)
        self.shipgen = ShipGenerator(mission, conflict)
        self.awacsgen = AirSupportConflictGenerator(mission, conflict, self.game)
        self.triggersgen = TriggersGenerator(mission, conflict, self.game)
        self.visualgen = VisualGenerator(mission, conflict, self.game)
        self.envgen = EnviromentGenerator(mission, conflict, self.game)

        player_name = self.from_cp.captured and self.attacker_name or self.defender_name
        enemy_name = self.from_cp.captured and self.defender_name or self.attacker_name
        self.extra_aagen = ExtraAAConflictGenerator(mission, conflict, self.game, player_name, enemy_name)

    def prepare(self, terrain: Terrain, is_quick: bool):
        with open("resources/default_options.lua", "r") as f:
            options_dict = loads(f.read())["options"]

        self.mission = dcs.Mission(terrain)
        self.mission.set_sortie_text("DCS Liberation : ")
        self.mission.add_picture_red("resources/ui/briefing_red.png")
        self.mission.add_picture_blue("resources/ui/briefing_blue.png")

        self.mission.options.load_from_dict(options_dict)
        self.is_quick = is_quick

        if is_quick:
            self.attackers_starting_position = None
            self.defenders_starting_position = None
        else:
            self.attackers_starting_position = self.from_cp.at
            self.defenders_starting_position = self.to_cp.at

    def generate(self):
        self.visualgen.generate()
        self.awacsgen.generate(self.is_awacs_enabled)

        self.extra_aagen.generate()

        if self.game.is_player_attack(self.conflict.attackers_side):
            cp = self.conflict.from_cp
        else:
            cp = self.conflict.to_cp

        self.triggersgen.generate(player_cp=cp,
                                  is_quick=self.is_quick,
                                  activation_trigger_radius=self.trigger_radius,
                                  awacs_enabled=self.is_awacs_enabled)

        if self.environment_settings is None:
            self.environment_settings = self.envgen.generate()
        else:
            self.envgen.load(self.environment_settings)

    def units_of(self, country_name: str) -> typing.Collection[UnitType]:
        return []

    def is_successfull(self, debriefing: Debriefing) -> bool:
        return True
