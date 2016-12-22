init -11 python:
    # Equipment checks and area effects!
    def has_items(item, chars):
        if isinstance(item, basestring):
            item = items[item]
        
        amount = 0
        for c in chars:
            amount += c.inventory[item]
            for i in c.eqslots.itervalues():
                if i == item:
                    amount += 1
                    
        return amount
    
    def equip_item(item, char, silent=False, area_effect=False):
        """First level of checks, all items should be equiped through this function!
        """
        if not can_equip(item, char, silent=silent):
            return

        # Gotta fix broken ceffect?:
        if item.slot == 'consumable' and area_effect:
            if not item.ceffect:
                char.equip(item)
                return
                
            # potentially not one and the same for group.
            loc = char.location
            targets = [chars[key] for key in chars if chars[key].location == loc]
            if hero.location == loc:
                targets.append(hero)
            
            if item.ceffect == 'alllocal':
                if loc in hero.buildings:
                    char.inventory.remove(item)
                    for t in targets:
                        t.equip(item)
                else:
                    renpy.call_screen('message_screen', "%s in not in any brothel! "% char.nickname)

            elif item.ceffect == 'freelocal':
                if loc in hero.buildings:
                    char.inventory.remove(item)
                    for t in targets:
                        if t.status != 'slave':
                            t.equip(item)
                else:
                    renpy.call_screen('message_screen', "%s in not in any brothel! "%char.nickname)

            elif item.ceffect == 'slavelocal':
                if loc in hero.buildings:
                    char.inventory.remove(item)
                    for t in targets:
                        if t.status == 'slave':
                            t.equip(item)
                else:
                    renpy.call_screen('message_screen', "%s in not in any brothel! "%char.nickname)
                    
            if item.ceffect == 'allslaves':
                char.inventory.remove(item)
                for t in [c for c in hero.chars if c.status == 'slave']:
                    t.equip(item)

            elif item.ceffect == 'allfree':
                char.inventory.remove(item)
                targets = [girl for girl in hero.chars if girl.status != 'slave']
                if hero.location == loc:
                    targets.append(hero)
                for t in targets:
                    t.equip(item)

            elif item.ceffect == 'allchars':
                char.inventory.remove(item)
                targets = hero.chars
                if hero.location == loc:
                    targets.append(hero)
                for t in targets:
                    t.equip(item)
        else:
            char.equip(item)
            
    def equip_for(girl, jobtype):
        # TODO: Must be updated to work with new base-traits and jobs system.
        if girl.autoequip:
            if jobtype == "Guard":
                girl.equip_for("Combat")
            elif jobtype == "ServiceGirl":
                girl.equip_for("Service")
            elif jobtype == "Stripper":
                girl.equip_for("Striptease")
            elif jobtype == "Prostitute":
                girl.equip_for("Sex")
                
    def transfer_items(source, target, item, amount=1, silent=False, force=False):
        """Transfers items between characters. 
        
        This will also log a fact of transfer between a character and MC is appropriate.
        @param: force: Option to forcibly take an item from a character.
        """
        if isinstance(item, basestring):
            item = items[item]

        given = amount * len(target) if isinstance(target, PytGroup) else amount

        if not can_transfer(source, target, item, amount=given, silent=silent, force=force):
            return False

        if not source.inventory.remove(item, given):
            return False

        received = amount * len(source) if isinstance(source, PytGroup) else amount

        if not any([item.slot == "consumable", (item.slot == "misc" and item.mdestruct)]):

            if isinstance(source, Char) and source.status != "slave":
                source.given_items[item.id] = source.given_items.get(item.id, 0) - given

            elif isinstance(source, PytGroup):
                for c in source.lst:
                    if c.status != "slave":
                        c.given_items[item.id] = c.given_items.get(item.id, 0) - given

            if isinstance(target, Char) and target.status != "slave":
                target.given_items[item.id] = target.given_items.get(item.id, 0) + received

            elif isinstance(target, PytGroup):
                for c in target.lst:
                    if c.status != "slave":
                        c.given_items[item.id] = c.given_items.get(item.id, 0) + received

        target.inventory.append(item, received)
        return True

                
    def can_equip(item, character, silent=True):
        """Checks if it is legal for a character to use/equip the item.
        
        @param: silent: If False, game will notify the player with a reason why an item cannot be equipped.
        """
        if isinstance(character, PytGroup):
            if item.jump_to_label:
                return

            # downstream function can trigger a response assuming char is a character
            global char
            for char in character.shuffled:
                if not can_equip(item, char, silent):
                    char = character
                    return
            char = character
            return True
        if item.unique and item.unique != character.id:
            if not silent:
                renpy.show_screen("message_screen", "This unique item cannot be equipped on {}!".format(character.name))
            return
        elif item.sex not in ["unisex", character.gender]:
            if not silent:
                renpy.show_screen('message_screen', "{} item cannot be equipped on a character of {} gender!".format(item.id, character.gender))
            return
        elif not item.usable:
            if not silent:
                renpy.show_screen("message_screen", "This item cannot be used or equipped!")
            return
        elif item.type in ["food"] and character.effects['Food Poisoning']['active']:
            if not silent:
                renpy.show_screen('message_screen', "She's already suffering from food poisoning. More food won't do any good.")
            return
        elif character.status == "slave":
            if item.slot in ["weapon"] and not item.type.lower().startswith("tool"):
                if not silent:
                    renpy.show_screen('message_screen', "Slaves are forbidden to use large weapons by law!")
                return
            elif item.type in ["armor"]:
                if not silent:
                    renpy.show_screen('message_screen', "Slaves are forbidden to wear armor by law!")
                return
            elif item.type in ["shield"]:
                if not silent:
                    renpy.show_screen('message_screen', "Slaves are forbidden to use shields by law!")
                return
        return True
                
    def can_transfer(source, target, item, amount=1, silent=True, force=False):
        """Checks if it is legal for a character to transfer the item.
        
        @param: silent: If False, game will notify the player with a reason why an item cannot be equipped.
        @param: force: Option to forcibly take an item from a character.
        """
        if isinstance(source, PytGroup):
            if item.jump_to_label:
                return

            for c in source.shuffled:
                if not can_transfer(c, target, item, amount, silent, force):
                    return
            return True
        if isinstance(target, PytGroup):
            if item.jump_to_label:
                return

            for c in target.shuffled:
                if not can_transfer(source, c, item, amount, silent, force):
                    return
            return True

        if all([item.unique, isinstance(target, Player), item.unique != "mc"]) or all([item.unique, item.unique != target.id]):
            if not silent:
                renpy.show_screen("message_screen", "This unique item cannot be given to {}!".format(target.name))
            return
        if not item.transferable:
            if not silent:
                renpy.show_screen('message_screen', "This item cannot be transferred!")
            return
        # Free girls should always refuse giving up their items unless MC gave it to them:
        # (Unless action is forced):
        if not force:
            if all([isinstance(source, Char), source.status != "slave", not(check_lovers(source, hero))]):
                if any([item.slot == "consumable", (item.slot == "misc" and item.mdestruct), source.given_items.get(item.id, 0) - amount < 0]):
                    if not silent:
                        source.override_portrait("portrait", "indifferent")
                        if "Impersonal" in source.traits:
                            source.say(choice(["Denied. It belongs only to me.", "You are not authorised to dispose of my property."]))
                        elif "Shy" in source.traits and dice(50):
                            source.say(choice(["W... what are you doing? It's not yours...", "Um, could you maybe stop touching my things, please?"]))
                        elif "Dandere" in source.traits:
                            source.say(choice(["Don't touch my stuff without permission.", "I'm not giving it away."]))
                        elif "Kuudere" in source.traits:
                            source.say(choice(["Would you like fries with that?", "Perhaps you would like me to give you the key to my flat where I keep my money as well?"]))
                        elif "Yandere" in source.traits:
                            source.say(choice(["Please refrain from touching my property.", "What do you think you doing with my belongings?"]))
                        elif "Tsundere" in source.traits:
                            source.say(choice(["Like hell am I giving away!", "Hey, hands off!"]))
                        elif "Imouto" in source.traits:
                            source.say(choice(["No way! Go get your own!", "Don't be mean! It's mine!"]))
                        elif "Bokukko" in source.traits:
                            source.say(choice(["Hey, why do ya take my stuff?", "Not gonna happen. It's mine alone."]))
                        elif "Kamidere" in source.traits:
                            source.say(choice(["And what makes you think I will allow anyone to take my stuff?", "Refrain from disposing of my property unless I say otherwise."]))
                        elif "Ane" in source.traits:
                            source.say(choice(["Please, don't touch it. Thanks.", "Excuse me, I do not wish to part with it."]))
                        else:
                            source.say(choice(["Hey, I need this too, you know.", "Eh? Can't you just buy your own?"]))
                        source.restore_portrait()
                    return
                
        return True
                
    def can_sell(item, silent=True):
        """Checks in an item can be sold to a shop.
        """
        if item.unique:
            if not silent:
                renpy.show_screen("message_screen", "Unique Items cannot be sold!")
            return
        elif not item.sellable:
            if not silent:
                renpy.show_screen("message_screen", "This item cannot be sold!")
            return
        return True

    def equipment_access(character, item=None, silent=False, allowed_to_equip=True):
        # Here we determine if a character would be willing to give MC access to her equipment:
        # Like if MC asked this character to equip or unequip an item.
        # We return True of access is granted!
        #
        # with allowed_to_equip=True (default) check whether we are allowed to equip the item,
        # with allowed_to_equip=False, check whether we are allowed to *un*equip
        char = character
        if isinstance(character, PytGroup):
            if item and item.jump_to_label:
                return False

            # get a response from one single individual
            global char
            for char in character.shuffled:
                if not equipment_access(char, item, silent, allowed_to_equip):
                    return False
            char = character
            return True

        if character == hero:
            return True # Would be weird if we could not access MCs inventory....

        # Always the same here as well...
        if character.status == "slave":
            return True

        # Always refuse if character hates the player:
        if character.disposition < -700:
            if not silent:
                interactions_girl_disp_is_too_low_to_give_money() # turns out money lines are perfect here
            return False

        if item:
            # Bad Traits:
            if item.badtraits.intersection(character.traits):
                if not silent:
                    interactions_character_doesnt_want_bad_item()
                return not allowed_to_equip

            # Always allow restorative items:
            if item.type == "restore":
                return True

            # Good traits:
            if item.goodtraits.intersection(character.traits):
                return allowed_to_equip

            # Just an awesome item in general:
            if item.eqchance >= 70:
                return allowed_to_equip

        if character.disposition < 850 and not check_lovers(character, hero):
            if not silent:
                interactions_character_doesnt_want_to_equip_item()
            return False

        return True

label shop_control:
    $ result = ui.interact()
    if result[0] == "item":
        if result[1] in (char, shop):
            $ amount = 1
            $ focus = result[2]
            if result[1] == char:
                $ purchasing_dir = 'sell'
                $ item_price = int(focus.price*shop.sell_margin)
            else:
                $ purchasing_dir = 'buy'
                $ item_price = int(focus.price*shop.buy_margin)
            
        elif result[1] == 'buy/sell':
            if purchasing_dir == 'buy':
                $ result = char.take_money(item_price*amount, "Items")
                if result:
                    play sound "content/sfx/sound/world/purchase_1.ogg"
                    python:
                        for i in xrange(amount):
                            shop.inventory.remove(focus)
                            char.inventory.append(focus)
                            shop.gold += item_price
                else:
                    $ focus = None
                    $ renpy.say("", choice(["Not enought money!",
                                                         "No freebees I fear...",
                                                         "You'll need more money for this purchase"]))
                $ amount = 1
                $ focus = False
                
            elif purchasing_dir == 'sell':
                if not can_sell(focus, silent=False):
                    jump shop_control
                elif shop != pytfall.general_store and (not shop.locations.intersection(focus.locations) or focus.type.lower() not in shop.sells):
                    $ focus = None
                    $ renpy.say("", "I will not buy this item from you!")
                else:                         
                    $ result = bool(shop.gold - (item_price*amount) >= 0)
                    if result:
                        play sound "content/sfx/sound/world/purchase_1.ogg"
                        python:
                            for i in xrange(amount):
                                shop.gold -= item_price
                                char.add_money(item_price, "Items")
                                char.inventory.remove(focus)
                                shop.inventory.append(focus)
                    else:
                        $ focus = None
                        $ renpy.say("", "This is a bit more than I can pay!")
                    $ amount = 1
                    $ focus = None
            
    elif result[0] == 'control':
        if isinstance(result[1], basestring):
            if result[1] == 'return':
                $ focus = None
                return
        elif result[1] > 0:
            if purchasing_dir == 'sell':
                $ amount = min(amount + result[1], char.inventory[focus])
            elif purchasing_dir == 'buy':
                $ amount = min(amount + result[1], shop.inventory[focus])
        else:
            $ amount = max(amount + result[1], 1)
    jump shop_control
