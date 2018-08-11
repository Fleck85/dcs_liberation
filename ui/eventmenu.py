from dcs.helicopters import helicopter_map

from ui.eventresultsmenu import *

from game import *
from game.event import *
from .styles import STYLES


UNITTYPES_FOR_EVENTS = {
    FrontlineAttackEvent: [CAS, PinpointStrike],
    FrontlinePatrolEvent: [CAP, PinpointStrike],
    BaseAttackEvent: [CAP, CAS, PinpointStrike],
    InterceptEvent: [CAP],
    InsurgentAttackEvent: [CAS],
    NavalInterceptEvent: [CAS],
    AntiAAStrikeEvent: [CAS],
    InfantryTransportEvent: [Embarking],
}


class EventMenu(Menu):
    aircraft_scramble_entries = None  # type: typing.Dict[PlaneType , Entry]
    aircraft_client_entries = None  # type: typing.Dict[PlaneType, Entry]
    armor_scramble_entries = None  # type: typing.Dict[VehicleType, Entry]
    ca_slot_entry = None
    awacs = None  # type: IntVar

    def __init__(self, window: Window, parent, game: Game, event: event.Event):
        super(EventMenu, self).__init__(window, parent, game)

        self.event = event
        self.aircraft_scramble_entries = {}
        self.armor_scramble_entries = {}
        self.aircraft_client_entries = {}

        if self.event.attacker_name == self.game.player:
            self.base = self.event.from_cp.base
        else:
            self.base = self.event.to_cp.base

        self.frame = self.window.right_pane
        self.awacs = IntVar()

    def display(self):
        self.window.clear_right_pane()
        row = 0

        def header(text, style="strong"):
            nonlocal row
            head = Frame(self.frame, **STYLES["header"])
            head.grid(row=row, column=0, sticky=N+EW, columnspan=5)
            Label(head, text=text, **STYLES[style]).grid()
            row += 1

        def label(text, _row=None, _column=None, sticky=None):
            nonlocal row
            Label(self.frame, text=text, **STYLES["widget"]).grid(row=_row and _row or row, column=_column and _column or 0, sticky=sticky)

            if _row is None:
                row += 1

        def scrable_row(unit_type, unit_count):
            nonlocal row
            Label(self.frame, text="{} ({})".format(db.unit_type_name(unit_type), unit_count), **STYLES["widget"]).grid(row=row, sticky=W)

            scramble_entry = Entry(self.frame, width=2)
            scramble_entry.grid(column=1, row=row, sticky=E, padx=5)
            scramble_entry.insert(0, "0")
            self.aircraft_scramble_entries[unit_type] = scramble_entry
            Button(self.frame, text="+", command=self.scramble_half(True, unit_type), **STYLES["btn-primary"]).grid(column=2, row=row)

            client_entry = Entry(self.frame, width=2)
            client_entry.grid(column=3, row=row, sticky=E, padx=5)
            client_entry.insert(0, "0")
            self.aircraft_client_entries[unit_type] = client_entry
            Button(self.frame, text="+", command=self.client_one(unit_type), **STYLES["btn-primary"]).grid(column=4, row=row)

            row += 1

        def scramble_armor_row(unit_type, unit_count):
            nonlocal row
            Label(self.frame, text="{} ({})".format(db.unit_type_name(unit_type), unit_count), **STYLES["widget"]).grid(row=row, sticky=W)
            scramble_entry = Entry(self.frame, width=2)
            scramble_entry.insert(0, "0")
            scramble_entry.grid(column=1, row=row, sticky=E, padx=5)
            self.armor_scramble_entries[unit_type] = scramble_entry
            Button(self.frame, text="+", command=self.scramble_half(False, unit_type),**STYLES["btn-primary"]).grid(column=2, row=row)

            row += 1

        threat_descr = self.event.threat_description
        if threat_descr:
            threat_descr = "Approx. {}".format(threat_descr)

        # Header
        header("Mission Menu", "title")

        # Mission Description
        Label(self.frame, text="{}. {}".format(self.event, threat_descr), **STYLES["mission-preview"]).grid(row=row, column=0, columnspan=5, sticky=S+EW, padx=5, pady=5)
        row += 1

        header("Aircraft :")

        if self.base.aircraft:
            Label(self.frame, text="Amount", **STYLES["widget"]).grid(row=row, column=1, columnspan=2)
            Label(self.frame, text="Client slots", **STYLES["widget"]).grid(row=row, column=3, columnspan=2)
            row += 1

        filter_to = UNITTYPES_FOR_EVENTS[self.event.__class__]
        for unit_type, count in self.base.aircraft.items():
            if filter_to and db.unit_task(unit_type) not in filter_to:
                continue

            if unit_type in helicopter_map and self.event.__class__ != InsurgentAttackEvent:
                continue

            scrable_row(unit_type, count)

        if not self.base.total_planes:
            label("None", sticky=W)

        header("Armor :")
        armor_counter = 0
        for unit_type, count in self.base.armor.items():
            if filter_to and db.unit_task(unit_type) not in filter_to:
                continue
            scramble_armor_row(unit_type, count)
            armor_counter += 1

        if not self.base.total_armor or armor_counter == 0:
            label("None", sticky=W)

        header("Misc :")

        # Options
        awacs_enabled = self.game.budget >= AWACS_BUDGET_COST and NORMAL or DISABLED
        Label(self.frame, text="AWACS ({}m)".format(AWACS_BUDGET_COST), **STYLES["widget"]).grid(row=row, column=0, sticky=W)
        Checkbutton(self.frame, var=self.awacs, state=awacs_enabled,  **STYLES["radiobutton"]).grid(row=row, column=3, sticky=E)
        row += 1

        Label(self.frame, text="Combined Arms Slots", **STYLES["widget"]).grid(row=row, sticky=W)
        self.ca_slot_entry = Entry(self.frame,  width=2)
        self.ca_slot_entry.insert(0, "0")
        self.ca_slot_entry.grid(column=2, row=row, sticky=E, padx=5)
        Button(self.frame, text="+", command=self.add_ca_slot, **STYLES["btn-primary"]).grid(column=3, row=row, padx=15)
        row += 1

        header("Ready ?")
        Button(self.frame, text="Commit", command=self.start, **STYLES["btn-primary"]).grid(column=0, row=row, sticky=E, padx=5, pady=(10,10))
        Button(self.frame, text="Back", command=self.dismiss, **STYLES["btn-warning"]).grid(column=3, row=row, sticky=E, padx=5, pady=(10,10))
        row += 1

    def _scrambled_aircraft_count(self, unit_type: UnitType) -> int:
        value = self.aircraft_scramble_entries[unit_type].get()
        if value and int(value) > 0:
            return min(int(value), self.base.aircraft[unit_type])
        return 0

    def _scrambled_armor_count(self, unit_type: UnitType) -> int:
        value = self.armor_scramble_entries[unit_type].get()
        if value and int(value) > 0:
            return min(int(value), self.base.armor[unit_type])
        return 0

    def scramble_half(self, aircraft: bool, unit_type: UnitType) -> typing.Callable:
        def action():
            entry = None  # type: Entry
            total_count = 0
            if aircraft:
                entry = self.aircraft_scramble_entries[unit_type]
                total_count = self.base.aircraft[unit_type]
            else:
                entry = self.armor_scramble_entries[unit_type]
                total_count = self.base.armor[unit_type]

            existing_count = int(entry.get())
            entry.delete(0, END)
            entry.insert(0, "{}".format(int(existing_count + math.ceil(total_count/2))))

        return action

    def add_ca_slot(self):
        value = self.ca_slot_entry.get()
        amount = int(value and value or "0")
        self.ca_slot_entry.delete(0, END)
        self.ca_slot_entry.insert(0, str(amount+1))

    def client_one(self, unit_type: UnitType) -> typing.Callable:
        def action():
            entry = self.aircraft_client_entries[unit_type]  # type: Entry
            value = entry.get()
            amount = int(value and value or "0")
            entry.delete(0, END)
            entry.insert(0, str(amount+1))
        return action

    def start(self):

        # Set Awacs value
        if self.awacs.get() == 1:
            self.event.is_awacs_enabled = True
            self.game.awacs_expense_commit()
        else:
            self.event.is_awacs_enabled = False

        # Set Combined Arms slot count
        ca_slot_entry_value = self.ca_slot_entry.get()
        ca_slots = int(ca_slot_entry_value and ca_slot_entry_value or "0")
        self.event.ca_slots = ca_slots

        scrambled_aircraft = {}
        scrambled_sweep = {}
        scrambled_cas = {}
        for unit_type, field in self.aircraft_scramble_entries.items():
            amount = self._scrambled_aircraft_count(unit_type)
            if amount > 0:
                task = db.unit_task(unit_type)

                scrambled_aircraft[unit_type] = amount
                if task == CAS:
                    scrambled_cas[unit_type] = amount
                elif task == CAP:
                    scrambled_sweep[unit_type] = amount

        scrambled_clients = {}
        for unit_type, field in self.aircraft_client_entries.items():
            value = field.get()
            if value and int(value) > 0:
                amount = int(value)
                scrambled_clients[unit_type] = amount

        scrambled_armor = {}
        for unit_type, field in self.armor_scramble_entries.items():
            amount = self._scrambled_armor_count(unit_type)
            if amount > 0:
                scrambled_armor[unit_type] = amount

        if type(self.event) is BaseAttackEvent:
            e = self.event  # type: BaseAttackEvent
            if self.game.is_player_attack(self.event):
                e.player_attacking(cas=scrambled_cas,
                                   escort=scrambled_sweep,
                                   armor=scrambled_armor,
                                   clients=scrambled_clients)
            else:
                e.player_defending(interceptors=scrambled_aircraft,
                                   clients=scrambled_clients)
        elif type(self.event) is InterceptEvent:
            e = self.event  # type: InterceptEvent
            if self.game.is_player_attack(self.event):
                e.player_attacking(interceptors=scrambled_aircraft,
                                   clients=scrambled_clients)
            else:
                e.player_defending(escort=scrambled_aircraft,
                                   clients=scrambled_clients)
        elif type(self.event) is FrontlineAttackEvent:
            e = self.event  # type: FrontlineAttackEvent
            e.player_attacking(armor=scrambled_armor, strikegroup=scrambled_aircraft, clients=scrambled_clients)
        elif type(self.event) is FrontlinePatrolEvent:
            e = self.event  # type: FrontlinePatrolEvent
            e.player_attacking(interceptors=scrambled_aircraft, clients=scrambled_clients, armor=scrambled_armor)
        elif type(self.event) is NavalInterceptEvent:
            e = self.event  # type: NavalInterceptEvent

            if self.game.is_player_attack(self.event):
                e.player_attacking(strikegroup=scrambled_aircraft, clients=scrambled_clients)
            else:
                e.player_defending(interceptors=scrambled_aircraft, clients=scrambled_clients)
        elif type(self.event) is AntiAAStrikeEvent:
            e = self.event  # type: AntiAAStrikeEvent
            if self.game.is_player_attack(self.event):
                e.player_attacking(strikegroup=scrambled_aircraft, clients=scrambled_clients)
            else:
                e.player_defending(interceptors=scrambled_aircraft, clients=scrambled_clients)
        elif type(self.event) is InsurgentAttackEvent:
            e = self.event  # type: InsurgentAttackEvent
            if self.game.is_player_attack(self.event):
                assert False
            else:
                e.player_defending(strikegroup=scrambled_aircraft, clients=scrambled_clients)
        elif type(self.event) is InfantryTransportEvent:
            e = self.event  # type: InfantryTransportEvent
            if self.game.is_player_attack(self.event):
                e.player_attacking(transport=scrambled_aircraft, clients=scrambled_clients)
            else:
                assert False

        self.game.initiate_event(self.event)
        EventResultsMenu(self.window, self.parent, self.game, self.event).display()

