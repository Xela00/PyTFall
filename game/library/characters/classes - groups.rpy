# classes and methods for groups of Characters:
init -8 python:
    class listDelegator(_object):
        """ only provides obvious solutions, everything else needs a remedy """

        def __init__(self, l, flatten=None, remedy=None, at="?"):
            self.lst = l
            self._flatten = flatten or []
            self.remedy = remedy if remedy is not None else {}

        def __getitem__(self, item):

            if not isinstance(self.lst, (list, renpy.python.RevertableList)):
                renpy.error(self._at+"["+self._type(item)+"("+str(item)+")]")

            return self.unlist([d[item] for d in self.lst], at="["+self._type(item)+"("+str(item)+")]")

        def __getattr__(self, item):
            """ an undefined attribute was requested from the group """
            # required for pickle
            if item.startswith('__') and item.endswith('__'):
                return super(listDelegator, self).__getattr__(item)

            if callable(getattr(self.lst[0], item)):

                def wrapper(*args, **kwargs):
                    return self.unlist([getattr(c, item)(*args, **kwargs) for c in self.lst], at=item+"()")

                return wrapper

            return self.unlist([getattr(c, item) for c in self.lst], at=item)

        def __isub__(self, other):
            for x in self.lst: x -= other
            return self.unlist(self.lst)

        def _type(self, var):
            """ generalizations """
            if isinstance(var, basestring): return "<str>"
            if isinstance(var, (list, renpy.python.RevertableList)): return '<list>'
            if isinstance(var, (dict, renpy.python.RevertableDict)): return '<dict>'
            return str(type(var))

        def unlist(self, arr, at="", remedy=None):
            """ try to get a single value for a list """
            if not isinstance(arr, list):
                raise Exception("expected list "+self._at+at+"")

            if len(arr) == 0:
                return False

            if len(arr) == 1:
                return arr[0]

            tp = self._type(arr[0])

            if all(self._type(r) == tp for r in arr[1:]):

                if all(cmp(arr[0], r) == 0 for r in arr[1:]):
                    return arr[0]

                #if remedy is None and self.remedy is None and isinstance(arr[0], dict):
                #    ks = set(arr[0].keys())
                #    if all(cmp(ks, set(r.keys())) == 0 for r in arr[1:]):
                #        return listDelegator([listDelegator([c[k] for c in arr]) for k in list(ks)])
            else:
                tp = '*'

            if at in self._flatten:
                return list(set([item for sublist in arr for item in sublist]))

            if remedy is None:
                remedy = self.remedy

            if isinstance(remedy, dict):
                remedy = remedy[at+":"+tp]

            """ In case of an error here: define a remedy for the unlisting"""
            return remedy(arr) if callable(remedy) else remedy


    class PytGInv(listDelegator):

        def __init__(self, inv):
            super(PytGInv, self).__init__(inv, flatten=['filters', 'page_content', 'slot_filter'], at="PytGInv")

        def __getitem__(self, item):
            return min([x[item] for x in self.lst])

        @property
        def max_page(self):
            return min([x.max_page for x in self.lst])

        def remove(self, item, amount=1):
            """ see Inventory.remove(): False means not enough items """
            return all([x.remove(item,amount) for x in self.lst])

        def append(self, item, amount=1):
            all([x.append(item,amount) for x in self.lst])

    class PytGroup(listDelegator):

        def __init__(self, characters):

            super(PytGroup, self).__init__(characters, flatten=['traits', 'attack_skills', 'magic_skills'], at="PytGroup")

            self.status = listDelegator([c.status for c in self.selected], at="status", remedy="Various")
            self.autobuy = listDelegator([c.autobuy for c in self.selected], at="autobuy", remedy=False)

            # determines what to show as a count for items, if not equal
            self.inventory = PytGInv([c.inventory for c in self.selected])

            self.eqslots = listDelegator([c.eqslots for c in self.selected], remedy=False, at="eqslots")
            self.front_row = listDelegator([c.front_row for c in self.selected], remedy=False, at="front_row")
            self.autoequip = listDelegator([c.autoequip for c in self.selected], remedy=False, at="autoequip")
            self.action = listDelegator([c.action for c in self.selected], remedy=renpy.error, at="action")

            self.img = "content/gfx/interface/images/group.png"
            self.portrait = "content/gfx/interface/images/group_portrait.png"
            self.entire_group_len = len(characters)

            self.name = "A group of "+str(self.entire_group_len)
            self.nickname = "group"

        def __getitem__(self, item):
            return self.unlist([c[item] for c in self.lst], at="["+self._type(item)+"]")
        @property
        def shuffled(self):
            return random.sample(self.selected, self.entire_group_len)

        @property
        def selected(self):
            return self.lst

        @property
        def autocontrol(self):
            # for some reason have to determine this on the fly for every access.
            ret = {}
            for k in self.lst[0].autocontrol:
                ret[k] = listDelegator([c.autocontrol[k] for c in self.lst], remedy=False)
            return ret

        @autocontrol.setter
        def autocontrol(self, v):
            ret = {}
            for k in self.lst[0].autocontrol:
                for c in self.lst:
                    c.autocontrol[k] = v;

        @property
        def given_items(self):
            return {k:min([c.given_items[k] for c in self.lst]) for k in self.lst[0].given_items.keys()}
        @property
        def wagemod(self):
            return round(float(sum([c.wagemod for c in self.selected])) / max(self.entire_group_len, 1), 1)
        @wagemod.setter
        def wagemod(self, v):
            for c in self.selected:
                c.wagemod = v

        def show(self, what, resize=(None, None), cache=True):
            if what == "portrait":
                what = self.portrait
            elif what != self.img:
                what = self.img

            return ProportionalScale(what, resize[0], resize[1])

        def __len__(self):
            return self.entire_group_len



