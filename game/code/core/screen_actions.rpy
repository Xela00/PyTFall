init -9 python:

    """
    Alex: Why is all of this required? I cannot (yet) seen an advantage to writing any of these conditions to strings and evaluate those strings as/when needed.
    While that is possible also, it makes everything else redundant.

    @Review: I think that I've finally figured out what this is for, eval is usually not a very good idea in a sense that it can be slow.
    This is a better bet for most conditioning. Basically the advantage is speed...
    """
    #
    # Iff is used to hold and solve an if statement later, instead of immediately.
    #     c = Iff(myvar, ">", 7)
    #
    # This will check that myvar is above 7.
    # The problem is that the value of myvar will be stored at initialisation and never looked up again.
    # This means that the Iff instance is functionally the same as:
    #     c = myvar > 7
    #
    # To solve this, we use a class called S.
    # Example:
    #     p = S((mycontainer, "myvar"))
    #
    # S is a deleyed getattr call, similar to how Iff is a delayed if statement. S however, can do more then getattr.
    #     S((mycontainer, "myvar")) == getattr(mycontainer, "myvar") == mycontainer.myvar
    #
    #     S((mycontainer, "myfunc", a)) == getattr(mycontainer, "myfunc")(a) == mycontainer.myfunc(a)
    #
    # If the value reached by S is callable (say myvar holds an object with a __call__ function) then the result of value() will be returned instead.
    # To prevent this, you can return the function in a single-length tuple and its contents will be used as the value, but won't be called.
    #
    # S can also be used to solve sums (in a left-to-right order, anything more complex should be passed as a function):
    #     S((mycontainer, "myvar"), "+", 7) == getattr(mycontainer, "myvar") + 7 == mycontainer.myvar + 7
    #
    #     S((mycontainer, "myvar"), "+", (mycontainer, "myother")) == getattr(mycontainer, "myvar") + getattr(mycontainer, "myother") == mycontainer.myvar + mycontainer.myother
    #
    # S can use the following operators:
    #     +, -, *, **(power), /, //(integer division), %, /%(divmod),
    #     in, not in, is, ===, is not, !==,
    #     ==, eq, !=, ne, >, gt, >=, =>, ge, <, lt, <=, le
    #
    # Finally, as S thinks of tuples/lists as a stored getattr, they will always attempt to interpret lists/tuples. To get around this wrap the iterable in a single length tuple:
    #     S((mylist,))
    #
    # You can easily create S's for global_flags and properties in the renpy store using:
    #     global_flag_complex("flagname")
    #     renpy_store_complex("propertyname")
    #
    # Both the property and value of Iff's can be S instances.
    #
    # Iff can use the following operators:
    #     ==, eq, ===, is, !=, ne, !==, is not, >, gt, >=, =>, ge, <, lt, <=, le, in, not in
    #
    #
    # If you want Iff's or S's to be valid expressions for variables in other classes / uses, you should solve them using the solution function.
    #     solution(myiff)
    #       or
    #     solution(mys)
    #
    # solution always return a boolean, by following the following rules:
    #     Any single-length tuple will have its sole index be cast to bool.
    #         bool(tuple[0])
    #
    #     Any list or tuple with >1 indexes has all its indexes solved recursively.
    #         all([solution(i) for i in statement])
    #
    #     Any property that can be called (any instance with a __call__ function) will have its value solved.
    #         bool(statement())
    #
    #     Any string will be passed to eval().
    #         bool(eval(statement))
    #
    #     Everything else will be cast to bool and returned.
    #         bool(statement)
    #
    # Because solution defaults to AND logic when passed a list, to easily store and solve using OR logic, you should create and pass an IffOr instance.
    #     IffOr(myiff1, myiff2, myiff3)
    #
    # IffOr goes through each index it contains and runs it through a solution call. If one returns True, it stops and return True. If none do, it returns False.
    #

    def solution(statement):
        """
        Gets a solution to the statement by turning it into a boolean.
        statement = The statement to call.
        - All lists/tuples have their contents passed to solution. Returns result of all().
        - All objects with the "__call__" function return its value.
        - All strings are passed to eval()
        - All other values are cast to bool.
        """
        if isinstance(statement, list):
            return all([solution(r) for r in statement])

        elif isinstance(statement, tuple):
            if len(statement) > 1:
                return all([solution(r) for r in statement])

            else:
                return bool(statement)

        elif callable(statement):
            return bool(statement())

        elif isinstance(statement, basestring):
            return bool(eval(statement))

        else:
            return bool(statement)

    def global_flag_complex(name):
        """
        Returns a complex for global_flags.
        name = The name of the flag.
        """
        return S((global_flags, "flag", name))

    def renpy_store_complex(name):
        """
        Returns a complex for the renpy store.
        name = The name of the variable.
        """
        return S((renpy.store, name))

    class S(_object):
        """
        Solves a tuple-based eval statement.
        """

        def __init__(self, *args):
            """
            Creates a new S.
            args = The list of values to evaluate.
            """
            self.args = args

        def __call__(self):
            """
            Solves the statement.
            """
            sol = None
            op = None

            for a in self.args:
                tup = False
                nocall = False

                if isinstance(a, (list, tuple)):
                    tup = True

                    if len(a) == 1:
                        a = a[0]
                        nocall = True

                    elif len(a) == 2:
                        a = getattr(*a)

                    else:
                        a = getattr(a[0], a[1])(*a[2:])

                if not nocall and callable(a):
                    a = a()

                if op == None:
                    if not tup:
                        if a in ("+", "-", "/", "//", "*", "**", "%", "/%", "in", "not in", "is", "is not", "==", "!=", ">", "<", ">=", "<="):
                            op = a
                            continue

                    sol = a

                else:
                    if op == "+": sol += a
                    elif op == "-": sol -= a
                    elif op == "/": sol /= a
                    elif op == "//": sol = int(sol/a)
                    elif op == "*": sol *= a
                    elif op == "**": sol = sol**a
                    elif op == "%": sol %= a
                    elif op == "/%": sol = divmod(sol, a)
                    elif op == "in": sol = sol in a
                    elif op == "not in": sol = sol not in a
                    elif op in ("is", "==="): sol = sol is a
                    elif op in ("is not", "!=="): sol = sol is not a
                    elif op in ("==", "eq"): sol = sol == a
                    elif op in ("!=", "ne"): sol = sol != a
                    elif op in (">", "gt"): sol = sol > a
                    elif op in ("<", "lt"): sol = sol < a
                    elif op in (">=", "=>", "ge"): sol = sol >= a
                    elif op in ("<=", "le"): sol = sol <= a
                    else:
                        raise KeyError, "Unknown operator \"%s\" encountered."%op

            return sol


    class Iff(_object):
        """
        An easy way to curry a condition.
        """

        def __init__(self, prop, condition="==", value=True):
            """
            Creates a new Iff.
            prop = The property to check. Any functions are called.
            condition = The operation to perform.
            value = The value to check against. Any functions are called.
            """
            self.prop = prop
            self.condition = condition
            self.value = value

        def __call__(self):
            """
            Checks the condition and returns the result.
            """
            if self.condition is True: return bool(self.p)
            if self.condition is False: return not bool(self.p)
            if self.condition in ("==", "eq"): return self.p == self.v
            if self.condition in ("===", "is"): return self.p is self.v
            if self.condition in ("!=", "ne"): return self.p != self.v
            if self.condition in ("!==", "is not"): return self.p is not self.v
            if self.condition in (">", "gt"): return self.p > self.v
            if self.condition in (">=", "=>", "ge"): return self.p >= self.v
            if self.condition in ("<", "lt"): return self.p < self.v
            if self.condition in ("<=", "le"): return self.p <= self.v
            if self.condition in ("in",): return self.p in self.v
            if self.condition in ("not in",): return self.p not in self.v
            return False

        def __eq__(self, other):
            """
            Checks for equality with the given argument.
            other = The object to check against.
            """
            if not isinstance(other, Iff): return False
            if other.prop != self.prop: return False
            if other.condition != self.condition: return False
            if other.value != self.value: return False
            return True

        def __ne__(self, other):
            """
            Checks for inequality with the given argument.
            other = The object to check against.
            """
            return not self.__eq__(other)

        @property
        def p(self):
            if isinstance(self.prop, tuple) and len(self.prop) == 1:
                return self.prop[0]

            elif callable(self.prop):
                return self.prop()

            else:
                return self.prop

        @property
        def v(self):
            if isinstance(self.value, tuple) and len(self.value) == 1:
                return self.value[0]

            elif callable(self.value):
                return self.value()

            else:
                return self.value


    class IffOr(_object):
        """
        An easy way to curry an or operation.
        """

        def __init__(self, *statements):
            """
            Creates a new IffOr.
            statements = Individual statements (as per solution) to check.
            """
            self.statements = statements

        def __call__(self):
            """
            Solves the statements for this IffOr. Returns True if any statements are true.
            """
            for i in self.statements:
                if solution(i):
                    return True

            else:
                return False

        def __eq__(self, other):
            """
            Checks for equality with the given argument.
            other = The object to check against.
            """
            if not isinstance(other, IffOr): return False
            if set(other.statements) != set(self.statements): return False
            return True

        def __ne__(self, other):
            """
            Checks for inequality with the given argument.
            other = The object to check against.
            """
            return not self.__eq__(other)


    class OpenActionMenu(Action):
        """
        An action to open a sub menu.
        """

        def __init__(self, menu):
            self.menu = menu

        def __call__(self):
            # Get indexes
            i = l = len(pytfall.world_actions.nest)

            # Loop through the nests
            while i > 1:
                i -= 1
                # If we are in this level, stop
                if self.menu in pytfall.world_actions.nest[i]:
                    while l > i+1:
                        pytfall.world_actions.nest.pop()
                        l -= 1

                    break

            else:
                # Else we aren't in the nesting
                i = l
                while i > 1:
                    pytfall.world_actions.nest.pop()
                    i -= 1

            pytfall.world_actions.nest.append(self.menu)
            renpy.restart_interaction()

        def get_sensitive(self):
            """
            Whether the menu can be opened.
            """
            return self.menu not in pytfall.world_actions.nest


    class CloseActionMenus(_object):
        """
        Closes all the nested action menus.
        """

        def __init__(self, action):
            """
            Creates a new CloseActionMenus.
            action = The action that is closing the menus.
            """
            self.do = not isinstance(action, WorldActionMenu)

        def __call__(self):
            """
            Closes the menus if necessary.
            """
            if self.do:
                del pytfall.world_actions.nest[1:]


    class WorldActionsManager(_object):
        """
        The class that builds and stores the actions for locations.
        """

        def __init__(self):
            """
            Creates the manager.
            """
            self._l = None
            self._a = None
            self._n = None

            self.locations = dict()
            self.nest = []

        def __call__(self, index, girl=None):
            """
            Returns the list of actions for the location sorted by their index.
            name = The name of the location.
            girl = A girl to check for unique actions.
            """
            if isinstance(index, basestring):
                if index in self.locations and self.locations[index]:
                    if girl is not None:
                        if hasattr(girl, "world_actions"):
                            self._n = index + "_" + str(girl)
                            ga = girl.world_actions

                            # Only check first item
                            if not isinstance(ga.values()[0], (WorldAction, WorldActionMenu)):
                                # Convert the girls actions into proper actions
                                girl.world_actions = self.build(ga)

                            self.nest = self.combine(girl.world_actions, self.locations[index])
                            return

                    self._n = index
                    self.nest = [self.locations[index]]
                else:
                    if DEBUG_LOG:
                        devlog.warning("Tried to access WorldActions(\"%s\") before existence." % index)
            else:
                ls = self.nest[index]
                if isinstance(ls, WorldActionMenu): return ls()
                else:
                    return [ls[a] for a in sorted(ls)]

        def __contains__(self, name):
            """
            Whether the location has actions registered.
            name = The name of the location.
            """
            return name in self.locations

        def __eq__(self, name):
            """
            Whether the current location is the named.
            name = The name to check.
            """
            return name == self._n

        def __delitem__(self, name):
            """
            Deletes the dict of actions for the location.
            name = The name of the location.
            """
            del self.locations[name]

        def __getitem__(self, name):
            """
            Returns the dict of actions for the location.
            name = The name of the location.
            """
            return self.locations[name]

        def __ne__(self, name):
            """
            Whether the current location isn't the named.
            name = The name to check.
            """
            return name != self._n

        def __setitem__(self, name, store):
            """
            Sets the dict of actions for the location.
            name = The name of the location.
            store = The dict of WorldActions.
            """
            self.locations[name] = store

        def add(self, index, *args, **kwargs):
            """
            Creates a new WorldAction for the current location.
            """
            if isinstance(index, (list, tuple)):
                level = self.tree(index[:-1])
                index = index[-1]
            else:
                level = self._a

            if isinstance(args[0], WorldAction):
                level[index] = args[0]
            else:
                level[index] = WorldAction(*args, **kwargs)

        def build(self, store, is_action=False, is_menu=False):
            """
            Builds a dict into a set of working actions.
            store = The dict to use.
            is_action = Whether the store contains a WorldAction.
            is_menu = Whether the store contains a WorldActionMenu.
            """
            if is_action:
                return WorldAction(store.pop("button"), store.pop("action"), **store)

            elif is_menu:
                options = store.pop("options", None)
                m = WorldActionMenu(store.pop("button"), **kwargs)
                if options:
                    for k,v in options.iteritems(): m.add(k,v)

                return m

            else:
                d = dict()
                for k,v in store.iteritems():
                    m = "menu" in v
                    d[k] = self.build(v, is_action=not m, is_menu=m)

                return d

        def clear(self):
            """
            Clears the currently selected location.
            """
            self._n = None
            self.nest = []

        def combine(self, *sets):
            """
            Combines the action store a with b and returns the result.
            sets = The dictionaries to combine. Earlier indexes take priority.
            """
            c = sets[0]

            for a in sets[1:]:
                for i in a:
                    if i not in c:
                        c[i] = a[i]

                    else:
                        if isinstance(c[i], WorldActionMenu):
                            if isinstance(a[i], WorldActionMenu):
                                c[i] = WorldActionMenu(c[i].button, c[i].condition, c[i].null_button, c[i].null_condition)
                                c[i].options = self.combine(c[i].options, a[i].options)

                            else:
                                if i not in c[i].options:
                                    c[i].options[i] = a[i]

            return c

        def finish(self):
            """
            Finishes the current location and adds the created actions to it.
            """
            self.locations[self._l] = self._a
            self._l = None
            self._a = None

        def gm_choice(self, act, mode=None, condition=True, label=None,
                            null_condition=None, index=None, keysym=None,
                            **kwargs):
            """
            Creates a new GirlsMeets choice.
            act = The name of the act, also used as the renpy label by removing spaces and converting to lower case.
            mode = The GM mode to show for.
            condition = The condition to use to hide the action.
            label = The label to use instead of the act.
            null_condition = The condition to use to disable the action.
            index = The index to use. Defaults to act.
            kwargs = Other variables to pass to the GMJump instance.
            """
            # Get the label
            if label is None:
                label = act.lower().replace(" ", "")

            # Get the mode
            if isinstance(mode, (list, tuple)):
                mode = Iff(S((gm, "mode")), "in", mode)

            elif isinstance(mode, basestring):
                mode = Iff(S((gm, "mode")), "==", mode)

            # Update the condition
            if mode is not None:
                if isinstance(condition, (list, tuple)):
                    condition.insert(0, mode)
                elif condition is not None:
                    condition = (mode, condition)
                else:
                    condition = mode

            self.add(index or act, WorldAction(act, (GMJump(label, **kwargs),
                     Function(pytfall.world_actions.clear)), condition=condition,
                     null_button=act, null_condition=null_condition,
                     keysym=keysym))

        def location(self, name):
            """
            Starts building the actions for the location.
            name = The name of the location.
            Returns = False if the location already exists, True if it can be built.
            """
            if name in self:
                self._l = name
                self._a = self[name]
                return False

            else:
                self._l = name
                self._a = dict()
                return True

        def look_around(self, index="look_around"):
            """
            Adds the default "Look Around" action.
            index = The index to use. Defaults to "look_around".
            """
            self.add(index, WorldAction("Look Around", "look_around", WorldAction.NO_EVENTS))

        def meet_girls(self, index="meet_girls"):
            """
            Adds the default "Meet Girls" action.
            index = The index to use. Defaults to "meet_girls".
            """
            self.add(index, WorldAction("Meet Girls", ToggleField(gm, "show_girls")))

        def menu(self, index, *args, **kwargs):
            """
            Creates a new WorldActionMenu for the current location.
            """
            if isinstance(index, (list, tuple)):
                level = self.tree(index[:-1])
                index = index[-1]

            else: level = self._a

            if isinstance(args[0], WorldActionMenu): level[index] = args[0]
            else: level[index] = WorldActionMenu(*args, **kwargs)

        def remove(self, index):
            """
            Removes an action from the location.
            """
            if index in self._a: self._a.pop(index)

        def slave_market(self, store, tt_text, button="Buy Slaves", null_button="N/A",
                         buy_button="Purchase",
                         buy_tt="You can buy this great girl for the sum of %s Gold!",
                         index="slave_market"):
            """
            Adds the default "Go Shopping" slave market action.
            store = The store interface to use.
            tt_text = The default tooltip text.
            button = The text for the action button.
            null_button = The text for the action button when no slaves are available.
            buy_button = The text for the buy girl button.
            buy_tt = The tooltip for the buy girl button. Must contain 1 "%s" for the cost.
            index = The index to use. Defaults to "slave_market".
            """
            self.add(index,
                     WorldAction(button,
                                 Show("slave_shopping", transition=Dissolve(1.0),
                                      source=store, tt_text=tt_text,
                                      buy_button=buy_button, buy_tt=buy_tt),
                                 null_button=null_button,
                                 null_condition="not pytfall.sm.chars_list or not hero.AP"
                                 ))

        def tree(self, tree):
            """
            Navigates the tree to get the proper access.
            tree = The path to follow.
            """
            level = self._a
            lvl = 0

            if tree:
                for i in xrange(len(tree)):
                    if lvl == 6:
                        raise Exception, "WorldActionMenus can only have a depth of 6."

                    t = tree[i]
                    if t not in level:
                        self.menu(tree[0:i+1], t)

                    lvl += 1
                    level = level[t]

            return level

        def work(self, condition=True, index="work", name=None, returned="work"):
            """
            Adds the default "Word" action.
            condition = The condition to check if the player can work here.
            index = The index to use. Defaults to "work".
            """
            if not name:
                name = "Work"
            self.add(index, WorldAction(name, Return(["control", returned]), condition=condition, null_button="Work", null_condition=Iff(S((hero, "AP")), "==", False)))


    class WorldAction(_object):
        """
        The class that holds the logic for location actions.
        """

        NO_EVENTS = "_events_not_found"

        def __init__(self, button, action, label=None, cost=1,
                     condition=True, null_button=None, null_condition=None,
                     keysym=None):
            """
            Creates a new WorldAction.
            button = The label for the button.
            action = The string to use as an event trigger, or an actual screen action.
            label = The label to go to if no events are found for the event trigger.
            cost = The cost of the action in AP, only for event triggers.
            condition = The condition to check to see if the button should be shown.
                        A string to evaluate, a function to call, a value to cast to bool, or a list of the three.
            null_button = The label to use if the button should be shown, but have no action.
            null_condition = The condition to check to see if the null button should be shown.
                             Uses the same syntax as condition.
            """
            self.button = button
            self.action = action
            self.keysym = keysym
            self.label = label
            self.cost = cost
            self.condition = condition
            self.null_button = null_button
            self.null_condition = null_condition

        def __eq__(self, other):
            """
            Checks for equality with the given argument.
            other = The object to check against.
            """
            if not isinstance(other, WorldAction): return False
            if other.button != self.button: return False
            if other.action != self.action: return False
            if other.label != self.label: return False
            if other.cost != self.cost: return False
            if other.condition != self.condition: return False
            if other.null_button != self.null_button: return False
            if other.null_condition != self.null_condition: return False
            return True

        def __ne__(self, other):
            """
            Checks for inequality with the given argument.
            other = The object to check against.
            """
            return not self.__eq__(other)

        @property
        def available(self):
            """
            Whether the button should be shown.
            """
            # If the action is an event trigger
            if self.is_event_trigger:
                if not self.label and self.event_amount == 0:
                    return False

            return solution(self.condition)

        @property
        def event_amount(self):
            """
            The amount of events that can be triggered by this action.
            """
            a = 0
            for i in pytfall.world_events.events_cache:
                if i.trigger_type == self.action:
                    a += 1

            return a

        @property
        def is_event_trigger(self):
            """
            Whether this button contains an event trigger or a screen action.
            """
            return isinstance(self.action, basestring)

        @property
        def is_null(self):
            """
            Whether this button should show its null variant.
            """
            if self.null_button:
                return solution(self.null_condition)

            else:
                return False


    class WorldActionMenu(Action):
        """
        The class that holds actions as a sub-menu.
        """

        def __init__(self, button, condition=True, null_button=None,
                     null_condition=None, keysym=None):
            """
            Creates a new WorldActionMenu.
            button = The label for the button.
            condition = Whether this button should be seen or null.
                        A string to evaluate, a function to call, a value to cast to bool or a list of the three.
            null_button = The label for the button if null.
            null_condition = Whether this button should show its null variant.
                             Uses the same syntax as condition.
            """
            self.button = button
            self.keysym = keysym
            self.condition = condition
            self.null_button = null_button
            self.null_condition = null_condition

            self.options = dict()

        def __call__(self):
            """
            Returns the actions in this menu as a list.
            """
            return [self.options[a] for a in sorted(self.options)]

        def __contains__(self, index):
            """
            Checks whether the index is in this menu.
            index = The index for the option.
            """
            return index in self.options or index in self.options.values()

        def __eq__(self, other):
            """
            Checks for equality with the given argument.
            other = The object to check against.
            """
            if not isinstance(other, WorldActionMenu): return False
            if other.button != self.button: return False
            if other.condition != self.condition: return False
            if other.null_button != self.null_button: return False
            if other.null_condition != self.null_condition: return False
            if other.options.keys() != self.options.keys(): return False
            return True

        def __ne__(self, other):
            """
            Checks for inequality with the given argument.
            other = The object to check against.
            """
            return not self.__eq__(other)

        def __delitem__(self, index):
            """
            Dynamic deletion of options.
            index = The index for the option.
            """
            del self.options[index]

        def __getitem__(self, index):
            """
            Dynamic access of options.
            index = The index for the option.
            """
            return self.options[index]

        def __setitem__(self, index, value):
            """
            Dynamic mutation of options.
            index = The index for the option.
            value = The option.
            """
            self.options[index] = value

        @property
        def action(self):
            """
            The screen action for this menu.
            """
            return OpenActionMenu(self)

        @property
        def available(self):
            """
            Whether the button should be shown.
            """
            if not self.options:
                return False

            return solution(self.condition)

        @property
        def is_null(self):
            """
            Whether the button should display its null state.
            """
            if self.null_button:
                return solution(self.null_condition)
            else:
                return False

init -10 python:
    @renpy.pure
    class ModSet(Action, FieldEquality):
        """
        :doc: data_action

        Adds `value` to `set` or removes 'value' from it in case it is already in the set.

        `set`
            The set to modify. This may be a python set or list.
        `value`
            The value.
        """

        identity_fields = [ 'set', 'value' ]

        def __init__(self, set, value):
            self.set = set
            self.value = value

        def get_selected(self):
            return self.value in self.set

        def __call__(self):
            if self.value in self.set:
                self.set.remove(self.value)
            else:
                if isinstance(self.set, list):
                    self.set.append(self.value)
                else:
                    self.set.add(self.value)

            renpy.restart_interaction()


    class ModFilterSet(ModSet):
        """Adjusted ModSet to update gui filters for characters.
        """
        def __init__(self, filters, set, value):
            self.set = getattr(filters, set)
            self.filters = filters
            self.value = value

        def __call__(self):
            if self.value in self.set:
                self.set.remove(self.value)
            else:
                self.set.add(self.value)
            self.filters.filter()
            renpy.restart_interaction()


    class SetFilter(SetField):
        """Set the filter for char filters and updates them.
         """
        def __init__(self, container, value):
            super(SetFilter, self).__init__(container, "sorting_order", value)

        def __call__(self):
            setattr(self.container, self.name, self.value)
            self.container.filter()
            renpy.restart_interaction()


    class NullAction(Action):
        """
        Overrides the NullAction action to allow for the action to present an insensitive button.
        """

        def __init__(self, insensitive=False, selected=False):
            """
            Creates a new NullAction.
            insensitive = Whether to show an insensitive button.
            """
            self.ins = insensitive
            self.sel = selected

        def __call__(self):
            """
            Nothing.
            """
            return

        def get_selected(self):
            """
            Whether the button should be selected.
            """
            return self.sel

        def get_sensitive(self):
            """
            Whether the button should be insensitive.
            """
            return not self.ins


    @renpy.pure
    class SetScreenVariableC(Action, FieldEquality):
        """
        Allows us to use a func to update a screen variable
        """

        identity_fields = []
        equality_fields = []

        def __init__(self, name, callable, **kwargs):
            self.name = name
            self.callable = callable
            self.kwargs = kwargs

        def __call__(self):

            cs = renpy.current_screen()

            if cs is None:
                return

            cs.scope[self.name] = self.callable(**self.kwargs)
            renpy.restart_interaction()


    # Menu extensions:
    class MenuExtensionAction(Action):
        def __init__(self, actions, extra_action=None):
            if extra_action:
                if "return" in actions:
                    actions.remove("return")
                actions.append(extra_action)
            self.actions = actions
        def __call__(self):
            for callable in self.actions:
                callable()


screen location_actions(actions, girl=None, pos=(.98, .98), anchor=(1.0, 1.0), align=None, style="dropdown_gm"):
    python:
        if pytfall.world_actions != actions:
            pytfall.world_actions(actions, girl)

        if not align:
            if not anchor: anchor = (.0, .0)
            if not pos: pos = (0, 0)

    hbox:
        if align:
            align align

        else:
            box_reverse (anchor[0] >= .5)
            anchor anchor
            pos pos

        spacing 11

        for i in range(0, 10):
            if i < len(pytfall.world_actions.nest):
                if style == "main_screen_3":
                    frame:
                        style_group "main_screen_3"
                        has vbox
                        for a in pytfall.world_actions(i):
                            use action_button(a)
                else:
                    frame:
                        style_group "dropdown_gm"
                        has vbox
                        for a in pytfall.world_actions(i):
                            use action_button(a)

screen action_button(a):
    if a.available:
        if a.is_null:
            textbutton a.null_button:
                xsize 200
                action NullAction(insensitive=True)
        elif isinstance(a, WorldAction) and a.is_event_trigger:
            textbutton a.button:
                xsize 200
                action (CloseActionMenus(a), Function(pytfall.world_events.run_events, a.action, a.label, a.cost))
                keysym a.keysym
        elif isinstance(a, WorldActionMenu):
            textbutton "< " + a.button:
                xsize 200
                action a.action
                keysym a.keysym
        else:
            textbutton a.button:
                xsize 200
                action (CloseActionMenus(a), a.action)
                keysym a.keysym

label _events_not_found:
    $ hero.say(choice(["Damn, I couldn't find anything...",
                       "There is nothing here.",
                       "Nothing.",
                       "This is pointless."]))
    return
