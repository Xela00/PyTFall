init:
    image libido_hearth = "content/gfx/interface/icons/heartbeat.png"

init python:
    def get_act(character, tags): # copypaste from jobs without the self part, allows to randomly select one of existing tags sets
            acts = list()
            for t in tags:
                if isinstance(t, tuple):
                    if character.has_image(*t):
                        acts.append(t)
                elif isinstance(t, dict):
                    if character.has_image(*t.get("tags", []), exclude=t.get("exclude", [])) and dice(t.get("dice", 100)):
                        acts.append(t)
                
            if acts:
                act = choice(acts)
            else:
                act = None
                
            return act
            
# lines for the future male libido
# You're a little out of juice at the moment, you might want to wait a bit.
# The spirit is willing, but the flesh is spongy and bruised.
screen int_libido_level(sex_scene_libido):
    hbox:
        xpos 50
        ypos 85
        add "content/gfx/interface/icons/heartbeat.png" at sex_scene_libido_hearth(sex_scene_libido)
screen int_libido_level_zero:
    hbox:
        xpos 50
        ypos 85
        anchor (.5, .5)
        add im.Sepia("content/gfx/interface/icons/heartbeat.png")

                
label interactions_hireforsex: # we go to this label from GM menu hire for sex. it's impossible to hire lovers, however they never refuse to do it for free, unless too tired or something like that
    $ interactions_check_for_bad_stuff(char)
    $ m = interactions_flag_count_checker(char, "flag_interactions_hireforsex")
    if ct("Nymphomaniac"): # how many times one can hire the character per day
        $ n = 4
    elif ct("Frigid"):
        $ n = 1
    else:
        $ n = 2
    if m > n:
        call interactions_too_many_sex_lines
        $ char.disposition -= randint(5,m+5) + randint(1,2)
        if char.joy > 50:
            $ char.joy -= randint(2,4)
        $ del m
        $ del n
        jump girl_interactions

    if char.effects['Icy']['active']:
        call interactions_frigid_sex_refuse
        jump girl_interactions
        
    if char.flag("quest_cannot_be_fucked") == True or (ct("Half-Sister") and not "Sister Lover" in hero.traits): # cannot hire h-s for that stuff, only seduce, seems reasonable
        call interactions_sex_disagreement
        jump girl_interactions
        
    if char.disposition<0: # for negative disposition
        if dice(abs(char.disposition*0.2)): # if it's low enough to make the dice work she refuses
            call interactions_sex_disagreement
            $ char.disposition -= randint(15, 35)
            $ char.set_flag("_day_countdown_interactions_blowoff", 2)
            jump girl_interactions_end
    elif char.vitality <= round(char.get_max("vitality")*0.25) or char.AP <= 0: # no sex with low vitality
        call interactions_refused_because_tired
        jump girl_interactions
    $ price = 100 #a placeholder, the price should be close to whore job prices, which are calculated weirdly atm
    
    if check_friends(char, hero):
        $ price = round(price * 0.7)
    elif char.disposition < -50:
        $ price = round(price * 1.3)
    if ct("Lesbian") and not "Yuri Expert" in hero.traits:
        $ price = round(price * 2.5)
    if ct("Nymphomaniac"):
        $ price = round(price * 0.9)
    elif ct("Frigid"):
        $ price = round(price * 1.2)
    if ct("Virgin"):
        $ price = round(price * 1.1)
           
    if ct("Impersonal"): 
        $ rc("Affirmative. It will be %d G." % price, "Calculations completed. %d G to proceed." % price)
    elif ct("Shy") and dice(50):
        $ rc("S-sure. %d G, please." % price, "*blushes* I-i-it will be %d G..." % price)
    elif ct("Imouto"):
        $ rc("Mmm, I think it should be %d G... No, wait, it will be %d G. I'm not very good with this stuff, hehe ♪" % (abs(price-randint(15,35)), price), "Ooh, you want to do 'it' with me, don't you? Ok, but it will cost you %d G." % price) 
    elif ct("Dandere"):
        $ rc("I see. I shall do it for %d G." % price, "*she nods* %d G." % price)
    elif ct("Tsundere"):
        $ rc("I'll do it for %d G. You better be thankful for my low prices." % price, "Fine, fine. I hope you have %d G then." % price)
    elif ct("Kuudere"):
        $ rc("It will be %d. And no funny business, understood?" % price, "It will cost you %d G. Do you have so much money?" % price)
    elif ct("Kamidere"):
        $ rc("What's that? You want to hire me? I want %d G then, money up front." % price, "Hm? You want my body? Well of course you do. %d G, and you can have it." % price)
    elif ct("Bokukko"):
        $ rc("Sure thing. That will cost ya %d G." % price, "What'ya wanna? Ohoh, you wanna me, don't you? ♪ Alrighty, %d G and we good to go.")
    elif ct("Ane"):
        $ rc("Let's see... How about %d G? Can you afford me? ♪" % price, "Hm? What's the matter? Need some... special service? For you my price is %d G ♪" % price)
    elif ct("Yandere"):
        $ rc("Fine, I want %d G. No bargaining." % price, "Well, I suppose we can, if you want to... It will cost %d G." % price)
    else:
        $ rc("You want to hire me? Very well, it will be %d G." % price, "Of course. For you my body costs %d G." % price)
    if hero.gold < price:
        "You don't have that much money."
        call interactions_girl_dissapointed
        $ m = interactions_flag_count_checker(char, "flag_interactions_hireforsex") # additionally reduce the amount of tries
        $ del price
        $ del m
        jump girl_interactions
    else:
        menu:
            "She wants [price] G. Do you want to pay?"
            
            "Yes":
                if hero.take_money(price):
                    $ char.add_money(price)
                    $ del price
                    jump interactions_sex_scene_select_place
                else:
                    "You don't have that much money."
                    call interactions_girl_dissapointed
                    $ m = interactions_flag_count_checker(char, "flag_interactions_hireforsex")
                    $ del m
                    $ del price
                    jump girl_interactions
            "No":
                $ char.disposition -= randint(1, 3)
                call interactions_girl_dissapointed
                $ del price
                jump girl_interactions
    $ del price

label interactions_sex_scene_select_place: # we go here if price for hiring is less than 0, ie no money checks and dialogues required; or after money check was successful
    if ct("Shy"):
        "She's too shy to do it anywhere. You go to her room."
        show bg girl_room with fade
        $ sex_scene_location="room"
    else:
        menu:
            "Where would you like to do it?"
            
            "Beach":
                show bg city_beach with fade
                $ sex_scene_location="beach"
            "Park":
                show bg city_park with fade
                $ sex_scene_location="park"
            "Room":
                show bg girl_room with fade
                $ sex_scene_location="room"
    $ picture_before_sex = True
    jump interactions_sex_scene_begins
                    
label interactions_sex: # we go to this label from GM menu propose sex
    $ interactions_check_for_bad_stuff(char)
    $ interactions_check_for_minor_bad_stuff(char)
    $ m = interactions_flag_count_checker(char, "flag_interactions_sex")
    if char.effects['Icy']['active']:
        call interactions_frigid_sex_refuse
        jump girl_interactions
    $ n = randint(2,3)
    if check_lovers(char, hero):
        $ n += randint(1,2)
    elif check_friends(char, hero):
        $ n += randint(0,1)
    if (ct("Half-Sister") and char.disposition < 700 and not "Sister Lover" in hero.traits) or ct("Frigid"):
        $ n = -1
    elif ct("Nymphomaniac"):
        $ n += 2

    if m > n:
        call interactions_too_many_sex_lines
        $ char.disposition -= randint(5,m+5) + randint(1,5)
        if char.joy > 50:
            $ char.joy -= randint(2,4)
        jump girl_interactions
    if char.flag("quest_cannot_be_fucked") == True: # a special flag for chars we don't want to be accessible unless a quest will be finished
        call interactions_sex_disagreement
        jump girl_interactions
    if ct("Lesbian") and not ct("Open Minded") and not "Yuri Expert" in hero.traits:
        call interactions_lesbian_refuse_because_of_gender # you can hire them, but they will never do it for free with wrong orientation
        jump girl_interactions
    if char.vitality < round(char.get_max("vitality")*0.25) or char.AP <= 0:
        call interactions_refused_because_tired
        jump girl_interactions
        
    $ sub = check_submissivity(char)
    if check_lovers(char, hero): # a clear way to calculate how much disposition is needed to make her agree
        $ disposition_level_for_sex = randint(0, 100) + sub*200 # probably a placeholder until it becomes more difficult to keep lover status
    else:
        $ disposition_level_for_sex = randint(600, 700) + sub*100 # thus weak willed characters will need from 500 to 600 disposition, strong willed ones from 700 to 800, if there are no other traits that change it
        
    if char.effects['Horny']['active']:
        $ disposition_level_for_sex -= randint(200, 300)
    
    if char.status == "slave":
        $ disposition_level_for_sex -= randint(50, 100)
    
    if char.flag("quest_sex_anytime"): # special flag for cases when we don't want character to refuse unless disposition is ridiculously low
        $ disposition_level_for_sex -= 1000
        
    if char.effects['Drunk']['active']: # a bit less disposition for drunk ones
        $ disposition_level_for_sex -= randint(50, 100)
        
    if cgo("SIW"): # SIWs won't be against it if they know MC well, but at the same time would prefer to get paid if they don't
        if char.disposition >= 400:
            $ disposition_level_for_sex -= randint(50, 100)
        else:
            $ disposition_level_for_sex += randint(50, 100)
            
    if char.flag("flag_int_had_sex_with_mc"):
        $ disposition_level_for_sex -= 50+char.flag("flag_int_had_sex_with_mc")*10 # the more char does it with MC, the less needed disposition is, despite everything else
            
    # so normal (without flag) required level of disposition could be from 200 to 1200 for non lovers
    if ct("Open Minded"): # open minded trait greatly reduces the needed disposition level
        $ disposition_level_for_sex -= randint(400, 500)
    if disposition_level_for_sex < 100:
        $ disposition_level_for_sex = 100 # normalization, no free sex with too low disposition no matter the character
    if char.disposition < disposition_level_for_sex:
        call interactions_sex_disagreement
        $ dif = disposition_level_for_sex - char.disposition # the difference between required for sex and current disposition
        if dif <= 100:
            $ char.disposition -= randint(1, dif+1) # if it's low, then disposition penalty will be low too
        else:
            $ char.disposition -= randint(15, (40+15*sub)) # otherwise it will be significant
        $ del dif
        $ del disposition_level_for_sex
        jump girl_interactions
    else:
        $ del disposition_level_for_sex
    call interactions_sex_agreement
    if ct("Nymphomaniac") or check_lovers(char, hero) or char.disposition >= 600:
        menu:
            "Where would you like to do it?"
            
            "Beach":
                show bg city_beach with fade
                $ sex_scene_location = "beach"
            "Park":
                show bg city_park with fade
                $ sex_scene_location = "park"
            "Room":
                show bg girl_room with fade
                $ sex_scene_location = "room"
    elif (char.status == "slave") and ct("Shy"):
        "She is too shy to do it anywhere. You can force her nevertheless, but she prefers her room."
        menu:
            "Where would you like to do it?"
            "Beach":
                show bg city_beach with fade
                $ sex_scene_location="beach"
                if ct("Masochist"):
                    $ char.joy += 10
                else:
                    $ char.joy -= 10
            "Park":
                show bg city_park with fade
                $ sex_scene_location="park"
                if ct("Masochist"):
                    $ char.joy += 10
                else:
                    $ char.joy -= 10
            "Room":
                show bg girl_room with fade
                $ sex_scene_location="room"
    elif ct("Shy"):
        "She's too shy to do it anywhere. You go to her room."
        show bg girl_room with fade
        $ sex_scene_location="room"
    elif ct("Homebody"):
        "She doesn't want to do it outdoors, so you go to her room."
        show bg girl_room with fade
        $ sex_scene_location="room"
    else:
        "She wants to do it in her room."
        show bg girl_room with fade
        $ sex_scene_location = "room"
    $ picture_before_sex = True
    
label interactions_sex_scene_begins: # here we set initial picture before the scene and set local variables
    $ scene_picked_by_character = True # when it's false, there is a chance that the character might wish to do something on her own
    $ sub = check_submissivity(char)
    
    if picture_before_sex:
        $ get_picture_before_sex(char, location=sex_scene_location)
    
    $ sex_count = guy_count = girl_count = together_count = cum_count = 0 # these variable will decide the outcome of sex scene
    $ max_sex_scene_libido = sex_scene_libido = get_character_libido(char)
    $ char.AP -= 1
    
    if not(char.flag("flag_int_had_sex_with_mc")):
        $ char.set_flag("flag_int_had_sex_with_mc", 1)
    else:
        $ char.set_flag("flag_int_had_sex_with_mc", char.flag("flag_int_had_sex_with_mc")+1)
        
    call interactions_sex_begins
    
    jump interaction_scene_choice

    
label interaction_scene_choice: # here we select specific scene, show needed image, jump to scene logic and return here after every scene
    if sex_scene_libido > 0:
        show screen int_libido_level(sex_scene_libido)
    else:
        hide screen int_libido_level
        show screen int_libido_level_zero
        
    if char.vitality <=10:
        jump interaction_scene_finish_sex
    elif hero.vitality <= 30:
        "You are too tired to continue."
        jump interaction_scene_finish_sex
        
    if char.status == "slave":
        if sex_scene_libido == 0:
            "[char.name] doesn't want to do it any longer. You can force her, but it will not be without consequences."
            jump interaction_sex_scene_choice
        if char.vitality <= 30:
            "[char.name] looks very tired."
            jump interaction_sex_scene_choice
    else:
        if sex_scene_libido <= 0:
            "[char.name] doesn't want to do it any longer."
            jump interaction_scene_finish_sex
        elif char.joy < 30:
            "[char.name] looks upset. Not the best mood for sex."
            jump interaction_scene_finish_sex
        if char.vitality < 30:
            "[char.name] is too tired to continue."
            jump interaction_scene_finish_sex
            
    if not(scene_picked_by_character):
        $ scene_picked_by_character = True
        if dice(sex_scene_libido*10 + 20*sub) and sex_scene_libido > 1: # strong willed and/or very horny characters may pick action on their own from time to time
            $ available = get_character_wishes(char)
            if available == "sex":
                $ current_action = choice(["hand", "foot"])
            elif available == "oral":
                $ current_action = choice(["blow", "tits"])
            elif available == "anal":
                $ current_action = "anal"
            else:
                $ current_action = "vag"
            if sub < 0:
                "She is so horny she cannot cannot control herself."
            elif sub == 0:
                "She wants to try out with you something else."
            else:
                "She wants to do something else with you."
            if current_action == "vag":
                if ct("Virgin"):
                    jump interaction_check_for_virginity
            jump interactions_sex_scene_logic_part
            
label interaction_sex_scene_choice:
    if sex_scene_libido>0:
        show screen int_libido_level(sex_scene_libido)
    else:
        hide screen int_libido_level
        show screen int_libido_level_zero
        
    $ scene_picked_by_character = False
    
    if char.effects['Horny']['active']:
        $ char.disable_effect("Horny")
    menu:
        "What would you like to do now?"
        
        "Ask for striptease" if max_sex_scene_libido == sex_scene_libido: 
            $ current_action = "strip"
            jump interactions_sex_scene_logic_part
            
        "Ask her to play with herself" if max_sex_scene_libido == sex_scene_libido:
            $ current_action = "mast"
            jump interactions_sex_scene_logic_part
            
        "Ask for a blowjob": 
            $ current_action = "blow"
            jump interactions_sex_scene_logic_part
            
        "Ask for paizuri":
            $ current_action = "tits"
            jump interactions_sex_scene_logic_part
            
        "Ask for a handjob":
            $ current_action = "hand"
            jump interactions_sex_scene_logic_part
            
        "Ask for a footjob":
            $ current_action = "foot"
            jump interactions_sex_scene_logic_part
            
        "Ask for sex":
            if ct("Virgin"):
                jump interaction_check_for_virginity
            else:
                $ current_action = "vag"
                jump interactions_sex_scene_logic_part
                
        "Ask for anal sex":
            $ current_action = "anal"
            jump interactions_sex_scene_logic_part
            
        "That's all.":
            if 'current_action' in locals():
                $ del current_action
            
label interaction_scene_finish_sex:
    hide screen int_libido_level
    hide screen int_libido_level_zero
    
    if sex_scene_libido > 3 and char.vitality >= 50 and ct("Nymphomaniac"):
        $ get_single_sex_picture(char, act="masturbation", location=sex_scene_location, hidden_partner=True)
        "[char.name] is not satisfied yet, so she quickly masturbates right in front of you."
        $ char.disposition -= round(sex_scene_libido*3)
        
    if (together_count > 0 and sex_count >1) or (sex_count >2 and girl_count >=1 and guy_count >= 1):
        if sex_scene_location == "beach":
            if char.has_image("profile", "beach", exclude=["angry", "sad", "scared", "in pain"]):
                $ gm.set_img("profile", "beach", "happy", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "happy", "beach", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
        elif sex_scene_location == "park":
            if char.has_image("profile", "nature", exclude=["angry", "sad", "scared", "in pain"]):
                $ gm.set_img("profile", "nature", "happy", "urban", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "happy", "nature", "urban", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
        else:
            if char.has_image("profile", "living", exclude=["angry", "sad", "scared", "in pain"]):
                $ gm.set_img("profile", "living", "happy", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "happy", "indoors", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
        call interactions_after_good_sex
        $ char.disposition += randint(20, 40)
        $ char.vitality -= randint(5, 10)
    elif girl_count < 1 and guy_count > 0:
        if sex_scene_location == "beach":
            if char.has_image("profile", "beach", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"]):
                $ gm.set_img("profile", "beach", "angry", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"])
            else:
                $ gm.set_img("girlmeets", "angry", "beach", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"], type="reduce")
        elif sex_scene_location == "park":
            if char.has_image("profile", "nature", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"]):
                $ gm.set_img("profile", "nature", "angry", "urban", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "angry", "nature", "urban", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"], type="reduce")
        else:
            if char.has_image("profile", "living", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"]):
                $ gm.set_img("profile", "living", "angry", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "angry", "indoors", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"], type="reduce")
            call interactions_girl_never_come
            $ char.disposition -= randint(20, 50)
            $ char.joy -= randint(2, 5)
            $ char.vitality -= randint(5, 10)
    elif girl_count > 0 and guy_count < 1 and cum_count < 1 and sex_count > 0:
        if sex_scene_location == "beach":
            if char.has_image("profile", "beach", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"]):
                $ gm.set_img("profile", "beach", "sad", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"])
            else:
                $ gm.set_img("girlmeets", "sad", "beach", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"], type="reduce")
        elif sex_scene_location == "park":
            if char.has_image("profile", "nature", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"]):
                $ gm.set_img("profile", "nature", "sad", "urban", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "sad", "nature", "urban", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"], type="reduce")
        else:
            if char.has_image("profile", "living", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"]):
                $ gm.set_img("profile", "living", "sad", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "sad", "indoors", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"], type="reduce")
        call interactions_guy_never_came
        $ char.disposition += randint(10, 20)
        $ char.joy -= randint(10, 15)
        $ char.vitality -= randint(5, 15)
    elif (cum_count >=5) and (cum_count > girl_count):
        if sex_scene_location == "beach":
            if char.has_image("profile", "beach", exclude=["angry", "sad", "scared", "in pain"]):
                $ gm.set_img("profile", "beach", "shy", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "shy", "beach", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
        elif sex_scene_location == "park":
            if char.has_image("profile", "nature", exclude=["angry", "sad", "scared", "in pain"]):
                $ gm.set_img("profile", "nature", "shy", "urban", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "shy", "nature", "urban", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
        else:
            if char.has_image("profile", "living", exclude=["angry", "sad", "scared", "in pain"]):
                $ gm.set_img("profile", "living", "shy", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "shy", "indoors", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
        call interactions_guy_cum_alot
        $ char.disposition += randint(10, 20)
        $ char.vitality -= randint(5, 10)
    elif sex_count < 1:
        if sex_scene_location == "beach":
            if char.has_image("profile", "beach", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"]):
                $ gm.set_img("profile", "beach", "angry", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"])
            else:
                $ gm.set_img("girlmeets", "angry", "beach", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"], type="reduce")
        elif sex_scene_location == "park":
            if char.has_image("profile", "nature", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"]):
                $ gm.set_img("profile", "nature", "angry", "urban", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "angry", "nature", "urban", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"], type="reduce")
        else:
            if char.has_image("profile", "living", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"]):
                $ gm.set_img("profile", "living", "angry", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "angry", "indoors", exclude=["happy", "scared", "in pain", "ecstatic", "suggestive"], type="reduce")
        if char.status == "slave":
            "She is puzzled and confused by the fact that you didn't do anything. She quickly leaves, probably thinking that you teased her."
        else:
            "She is quite upset and irritated because you didn't do anything. She quickly leaves, probably thinking that you teased her."
            $ char.disposition -= randint(20, 50)
            $ char.joy -= randint(15, 30)
            $ char.vitality -= 5
    elif girl_count > 0 and sex_count < 1:
        if sex_scene_location == "beach":
            if char.has_image("profile", "beach", exclude=["angry", "sad", "scared", "in pain"]):
                $ gm.set_img("profile", "beach", "shy", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "shy", "beach", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
        elif sex_scene_location == "park":
            if char.has_image("profile", "nature", exclude=["angry", "sad", "scared", "in pain"]):
                $ gm.set_img("profile", "nature", "shy", "urban", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "shy", "nature", "urban", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
        else:
            if char.has_image("profile", "living", exclude=["angry", "sad", "scared", "in pain"]):
                $ gm.set_img("profile", "living", "shy", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "shy", "indoors", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
        "She did nothing but masturbated in front of you. Be prepared for rumours about your impotence or orientation."
        call interactions_girl_dissapointed
        $ char.disposition -= randint(10, 15)
        $ char.vitality -= 5
    else:
        if sex_scene_location == "beach":
            if char.has_image("profile", "beach", exclude=["angry", "sad", "scared", "in pain"]):
                $ gm.set_img("profile", "beach", "happy", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "happy", "beach", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
        elif sex_scene_location == "park":
            if char.has_image("profile", "nature", exclude=["angry", "sad", "scared", "in pain"]):
                $ gm.set_img("profile", "nature", "happy", "urban", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "happy", "nature", "urban", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
        else:
            if char.has_image("profile", "living", exclude=["angry", "sad", "scared", "in pain"]):
                $ gm.set_img("profile", "living", "happy", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
            else:
                $ gm.set_img("girlmeets", "happy", "indoors", exclude=["angry", "sad", "scared", "in pain"], type="reduce")
        call interactions_after_normal_sex
        $ char.disposition += randint(10, 20)
        $ char.vitality -= randint(5, 10)
        
    $ gm.restore_img()
    jump girl_interactions_end
            
label interactions_lesbian_choice:
    $ sex_scene_libido -= 1
    # The interactions itself.
    # Since we called a function, we need to do so again (Consider making this func a method so it can be called just once)...
    if ct("Lesbian") or ct("Bisexual") or ct("Open Minded"):
        if char.disposition <= 500 or not(check_friends(hero, char) or check_lovers(hero, char)):
            "Unfortunately she does not want to do it."
            jump interaction_scene_choice
        elif check_lovers(hero, char):
            "She gladly agrees to make a show for you."
        elif check_friends(hero, char) or char.disposition > 600:
            "A bit hesitant, she agrees to do it for you."
    else:
        if char.disposition <= 600 or not(check_friends(hero, char) or check_lovers(hero, char)) or not(cgo("SIW")): 
            "Unfortunately she does not like girls in this way."
            jump interaction_scene_choice
        elif check_lovers(hero, char):
                "She gladly agrees to make a show for you if there will be some straight sex as well today."
        elif (check_friends(hero, char) or char.disposition > 600) and cgo("SIW"):
                "She prefers men, but agrees to make a show for you if there will be some straight sex as well today."
    $ willing_partners = find_les_partners()
    
    # Single out one partner randomly from a set:
    $ char2 = random.sample(willing_partners, 1)[0]
    
    # We plainly hide the interactions screen to get rid of the image and gradient:
    hide screen girl_interactions
    
    $ char_sprite = char.get_vnsprite()
    $ char_sprite2 = char2.get_vnsprite()
    "[char.nickname] decided to call [char2.nickname] for the lesbo action!"
    
    show expression char_sprite at mid_left with dissolve
    char.say "We are going to do 'it'."
    show expression char_sprite at mid_right as char_sprite with move
    show expression char_sprite2 at mid_left as char_sprite2 with dissolve
    char2.say "And..."
    extend "(*looking at you*) Are you planning to watch?"
    
    hide char_sprite
    hide char_sprite2
    with dissolve
    
    # Resize images to be slightly smaller than half a screen in width and the screen in height. ProportionalScale will do the rest.
    $ resize = (config.screen_width/2 - 75, config.screen_height - 75)
    
    
    show expression char.show("nude", "simple bg", resize=resize, exclude=["sex", "sleeping", "angry", "in pain", "beach", "onsen", "pool", "stage", "dungeon", "bathing"], type="first_default") as xxx at Transform(align=(0, 0.5)) with moveinright
    show expression char2.show("nude", "simple bg", resize=resize, exclude=["sex", "sleeping", "angry", "in pain", "beach", "onsen", "pool", "stage", "dungeon", "bathing"], type="first_default") as xxx2 at Transform(align=(1.0, 0.5)) with moveinleft
    
    # Wait for 0.25 secs and add soundbyte:
    pause 0.25
    play events "female/orgasm.mp3"
    $ renpy.pause(5.0)
    hide xxx
    hide xxx2
    

    show expression char2.get_vnsprite() at left as char_sprite2 with dissolve
    show expression char.get_vnsprite() at right as char_sprite with dissolve
    if sex_scene_libido <= 0:
        $ char.vitality -= 20
        $ char.joy -= 5
    if char.joy <= 10:
        $ char.disposition -= 5
    if char.vitality <= 15 and char.health >= 50:
        $ char.health -= 2
    if char.oral < 100 and char.sex < 100 and char2.oral < 100 and char2.sex < 100:
        "They both were not skilled enough to give each other enough pleasure, no matter how they tried. That was quite awkward."
        $ char.oral += randint (0,1)
        $ char2.oral += randint (0,1)
        $ char.sex += randint (0,1)
        $ char2.sex += randint (0,1)
        $ char.vitality -= 20
        $ char2.vitality -= 20
        $ sex_scene_libido -= 5
        char2.say "..."
        char.say "Sorry..."
    elif char.oral < 100 and char.sex < 100:
        "[char.nickname] was not skilled enough to make her partner cum. On the bright side, [char2.nickname] made her cum a lot."
        $ char.oral += randint (2,4)
        $ char2.oral += randint (2,4)
        $ char.sex += randint (0,1)
        $ char2.sex += randint (0,1)
        $ char.vitality -= 20
        $ char2.vitality -= 15
        $ sex_scene_libido -= 10
        char.say "Sorry..."
        char2.say "Don't worry. You'll become better in time."
    elif char2.oral < 100 and char2.sex < 100:
        "[char2.nickname] was not skilled enough to make her partner cum. On the bright side, [char.nickname] made her cum a lot."
        $ char.oral += randint (2,4)
        $ char2.oral += randint (2,4)
        $ char.sex += randint (0,1)
        $ char2.sex += randint (0,1)
        $ char.vitality -= 20
        $ char2.vitality -= 15
        $ sex_scene_libido -= 10
        char2.say "I'm sorry..."
        char.say "Don't be. We had our fun (*looking at you*)."
    else:
        "They both cum a lot. What a beautiful sight."
        $ char.oral += randint (2,4)
        $ char2.oral += randint (2,4)
        $ char.sex += randint (2,4)
        $ char2.sex += randint (2,4)
        $ char.vitality -= 15
        $ char2.vitality -= 15
        $ sex_scene_libido -= 10
        $ char.joy += 5
        $ char2.joy += 5
        char2.say "That... wasn't so bad."
        char2.say "We should do that again sometime ♪"
    hide char_sprite2 with dissolve
    hide char_sprite with dissolve
    
    # Restore the gm image:
    
    # Show the screen again:
    show screen girl_interactions
    
    # And finally clear all the variables for global scope:
    python:
        del resize
        del char2
        del willing_partners
        
    stop events
        
    # And we're all done!:
    jump interaction_scene_choice
    
    
label interactions_sex_scene_logic_part: # here we resolve all logic for changing stats and showing lines after picking a sex scene
    if sex_scene_libido <= 0:
        $ char.vitality -= randint(5, 25)
        $ char.joy -= randint(3, 6)
    if char.vitality <= 15 and char.health >= 50:
        $ char.health -= 2
    $ sex_count += 1
    if current_action in ["blow", "tits", "hand", "foot", "vag", "anal"] and "Mana Source" in hero.traits:
        $ char.mp += int(char.get_max("mp")*0.2)
    if current_action == "mast":
        $ get_single_sex_picture(char, act="masturbation", location=sex_scene_location, hidden_partner=True)
        if sub > 0:
            "She leisurely pleasures herself for awhile, seductively glancing at you."
        elif sub < 0:
            "She diligently pleasures herself for awhile until you tell her to stop." 
        else:
            "She pleasures herself for awhile, hesitantly avoiding your glance." 
        if dice(40):
            extend " She is more aroused now."
            $ sex_scene_libido += 2
        $ char.vitality -= randint(5, 10)
        $ girl_count +=1
    elif current_action == "strip":
        $ get_single_sex_picture(char, act="stripping", location=sex_scene_location, hidden_partner=True)
        $ skill_for_checking = char.get_skill("strip")
        $ male_skill_for_checking = char.get_skill("strip")
        if skill_for_checking >= 2000:
            "She looks unbearably hot and sexy. After a short time you cannot withstand it anymore and begin to masturbate, quickly cumming. She looks at you with a smile and superiority in her eyes."
        elif skill_for_checking >= 1000:
            "Her movements are so fascinating that you cannot look away from her. She looks proud and pleased."
        elif skill_for_checking >= 500:
            "It's nice to look at her graceful and elegant moves."
        elif skill_for_checking >= 200:
            "She did her best to show you her body, but her skills could definitely be improved."
        elif skill_for_checking >= 50:
            "She tried her best, but the moves were quite clumsy and unnatural. At least she learned something new today."
        else:
            "Looks like [char.name] barely knows what she's doing. Even just standing still without clothes would made a better impression..."
        if dice(20):
            $ char.strip += 1
        if dice(10):
            $ hero.strip += 1
        if (skill_for_checking - male_skill_for_checking) > 250 and dice(50):
            $ hero.strip += 1
        if (male_skill_for_checking - skill_for_checking) > 250 and dice(75):
            $ char.strip += 1
    elif current_action == "blow":
        $ get_single_sex_picture(char, act="oral", location=sex_scene_location, hidden_partner=True)
        $ image_tags = gm.img.get_image_tags()
        if ct("Lesbian"):
            $ skill_for_checking = round(char.get_skill("oral")*0.65 + char.get_skill("sex")*0.1)
        else:
            $ skill_for_checking = round(char.get_skill("oral")*0.8 + char.get_skill("sex")*0.2)
        $ male_skill_for_checking = round(hero.get_skill("oral")*0.8 + hero.get_skill("sex")*0.2)
        if sub > 0:
            if sex_scene_libido > 0:
                "[char.name] licks her lips, defiantly looking at your crotch."
            else:
                "[char.name] joylessly looks at your crotch."
            if "bc deepthroat" in image_tags:
                extend " She shoves it all the way into her throat."
            elif "after sex" in image_tags:
                extend " She enthusiastically begins to lick and suck it."
            else:
                extend " She enthusiastically begins to lick and suck it."
        elif sub < 0:
            if sex_scene_libido > 0:
                "Glancing at your crotch, [char.name] is patiently waiting for your orders."
            else:
                "[char.name] is waiting for your orders."
            if "bc deepthroat" in image_tags:
                extend " You told her to take your dick inside her mouth as deeply as she can, and she diligently obeyed."
            elif "after sex" in image_tags:
                extend " You told her to lick and suck your dick."
            else:
                extend " You told her to lick and suck your dick, and she immediately obeyed."
        else:
            if sex_scene_libido > 0:
                "[char.name] quickly approached your crotch."
            else:
                "[char.name] slowly approached your crotch."
            if "bc deepthroat" in image_tags:
                extend " You shove your dick deeply into her throat."
            elif "after sex" in image_tags:
                extend " She begins to lick and suck your dick."
            else:
                extend " She begins to lick and suck your dick."
        call interaction_sex_scene_check_skill_jobs
        if dice(20):
            $ char.oral += 1
        if dice(10):
            $ hero.oral += 1
        if (skill_for_checking - male_skill_for_checking) > 250 and dice(50):
            $ hero.oral += 1
        if (male_skill_for_checking - skill_for_checking) > 250 and dice(75):
            $ char.oral += 1
        if dice(10):
            $ char.sex += 1
        if dice(5):
            $ hero.sex += 1
    elif current_action == "tits":
        $ get_single_sex_picture(char, act="titsjob", location=sex_scene_location, hidden_partner=True)
        $ image_tags = gm.img.get_image_tags()
        if sex_scene_libido > 0:
            if sub > 0:
                "[char.name] massages her boobs, defiantly looking at your crotch."
            elif sub < 0:
                "Holding her boobs, [char.name] meekly approaches you."
            else:
                "[char.name] playfully grabs her boobs, looking at you."
        else:
            if sub > 0:
                "[char.name] massages her boobs, preparing them."
            elif sub < 0:
                "[char.name] holds her boobs, meekly looking at you."
            else:
                "[char.name] grabs her boobs and approaches you."
        if ct("Big Boobs"):
            extend " She warps her soft big breasts around you."
        elif ct("Abnormally Large Boobs"):
            extend " You almost lost yourself in her enormous breasts as they envelop you."
        elif ct("Small Boobs"):
            extend " She begins to assiduously rub her small breasts around you."
        else:
            extend " She squeezes you between her soft breasts."
        if ct("Lesbian"):
            $ skill_for_checking = round(char.get_skill("oral")*0.6 + char.get_skill("sex")*0.1)
        else:
            $ skill_for_checking = round(char.get_skill("oral")*0.75 + char.get_skill("sex")*0.25)
        $ male_skill_for_checking = round(hero.get_skill("oral")*0.75 + hero.get_skill("sex")*0.25)
        if dice(20):
            $ char.oral += 1
        if dice(10):
            $ hero.oral += 1
        if (skill_for_checking - male_skill_for_checking) > 250 and dice(50):
            $ hero.oral += 1
        if (male_skill_for_checking - skill_for_checking) > 250 and dice(75):
            $ char.oral += 1
        if dice(10):
            $ char.sex += 1
        if dice(5):
            $ hero.sex += 1
        call interaction_sex_scene_check_skill_jobs
    elif current_action == "hand":
        $ get_single_sex_picture(char, act="handjob", location=sex_scene_location, hidden_partner=True)
        $ image_tags = gm.img.get_image_tags()
        if sub > 0:
            "[char.name] grabs you with her soft hands."
        elif sub < 0:
            "[char.name] wraps her soft hands around your dick."
        else:
            "[char.name] takes your dick in her soft hands."
        if ct("Lesbian"):
            $ skill_for_checking = round(char.get_skill("oral")*0.1 + char.get_skill("sex")*0.6)
        else:
            $ skill_for_checking = round(char.get_skill("oral")*0.25 + char.get_skill("sex")*0.75)
        $ male_skill_for_checking = round(hero.get_skill("oral")*0.25 + hero.get_skill("sex")*0.75)
        if dice(20):
            $ char.sex += 1
        if dice(10):
            $ hero.sex += 1
        if (skill_for_checking - male_skill_for_checking) > 250 and dice(50):
            $ hero.sex += 1
        if (male_skill_for_checking - skill_for_checking) > 250 and dice(75):
            $ char.sex += 1
        if dice(10):
            $ char.oral += 1
        if dice(5):
            $ hero.oral += 1
        call interaction_sex_scene_check_skill_jobs
    elif current_action == "foot":
        $ get_single_sex_picture(char, act="footjob", location=sex_scene_location, hidden_partner=True)
        $ image_tags = gm.img.get_image_tags()
        if sub > 0:
            if sex_scene_libido > 0:
                "With a sly smile [char.name] gets closer to you."
            else:
                "[char.name] gets closer to you."
        elif sub < 0:
            "You asked [char.name] to use her feet."
        else:
            "[char.name] sits next to you."
        if ct("Athletic"):
            if ct("Long Legs"):
                "She squeezes your dick her between her long muscular legs and stimulates it until you cum."
            else:
                "She squeezes your dick her between her muscular legs and stimulates it until you cum."
        elif ct("Slim"):
            if ct("Long Legs"):
                "She squeezes your dick her between her long slim legs and stimulates it until you cum."
            else:
                "She squeezes your dick her between her slim legs and stimulates it until you cum."
        elif ct("Lolita"):
            if ct("Long Legs"):
                "She squeezes your dick her between her long thin legs and stimulates it until you cum."
            else:
                "She squeezes your dick her between her thin legs and stimulates it until you cum."
        else:
            if ct("Long Legs"):
                "She squeezes your dick her between her long legs and stimulates it until you cum."
            else:
                "She squeezes your dick her between her legs and stimulates it until you cum."
        if "after sex" in image_tags:
            extend " You generously cover her body with your thick liquid."
        if ct("Lesbian"):
            $ skill_for_checking = round(char.get_skill("oral")*0.1 + char.get_skill("sex")*0.6)
        else:
            $ skill_for_checking = round(char.get_skill("oral")*0.25 + char.get_skill("sex")*0.75)
        $ male_skill_for_checking = round(hero.get_skill("oral")*0.25 + hero.get_skill("sex")*0.75)
        if dice(20):
            $ char.sex += 1
        if dice(10):
            $ hero.sex += 1
        if (skill_for_checking - male_skill_for_checking) > 250 and dice(50):
            $ hero.sex += 1
        if (male_skill_for_checking - skill_for_checking) > 250 and dice(75):
            $ char.sex += 1
        if dice(10):
            $ char.oral += 1
        if dice(5):
            $ hero.oral += 1
        call interaction_sex_scene_check_skill_jobs
    elif current_action == "vag":
        if ct("Lesbian"):
            $ skill_for_checking = round(char.get_skill("vaginal")*0.6 + char.get_skill("sex")*0.15)
        else:
            $ skill_for_checking = round(char.get_skill("vaginal")*0.75 + char.get_skill("sex")*0.25)
        $ male_skill_for_checking = round(hero.get_skill("vaginal")*0.75 + hero.get_skill("sex")*0.25)
        if dice(20):
            $ char.vaginal += 1
        if dice(10):
            $ hero.vaginal += 1
        if (skill_for_checking - male_skill_for_checking) > 250 and dice(50):
            $ hero.vaginal += 1
        if (male_skill_for_checking - skill_for_checking) > 250 and dice(75):
            $ char.vaginal += 1
        if dice(10):
            $ char.sex += 1
        if dice(5):
            $ hero.sex += 1
        $ get_single_sex_picture(char, act="vaginal", location=sex_scene_location, hidden_partner=True)
        $ image_tags = gm.img.get_image_tags()
        if sub > 0:
            if sex_scene_libido > 0:
                "[char.name] looking forward to something big inside her pussy."
            else:
                "[char.name] unenthusiastically prepares her pussy."
            if "ontop" in image_tags:
                extend " She sits on top of you, immersing your dick inside."
            elif "doggy" in image_tags:
                extend " She bent over, pushing her crotch toward your dick."
            elif "missionary" in image_tags:
                extend " She lay on her back spreading her legs, awaiting for your dick."
            elif "onside" in image_tags:
                extend " She lay down on her side, waiting for you to join her."
            elif "standing" in image_tags:
                extend " She spreads her legs waiting for you, not even bothering to lay down."
            elif "spooning" in image_tags:
                extend " She snuggled to you, being in a mood for some spooning."
            elif "sitting" in image_tags:
                extend " She sat upon you knees, immersing your dick inside."
            else:
                extend " She confidently pushes your dick inside and starts to move."
        elif sub < 0:
            "[char.name] prepares herself, awaiting for further orders."
            if "ontop" in image_tags:
                extend " You ask her to sit on top of you, immersing your dick inside."
            elif "doggy" in image_tags:
                extend " You ask her to bent over, allowing you to take her from behind."
            elif "missionary" in image_tags:
                extend " You ask her to lay on her back and spread legs, allowing you to shove your dick inside."
            elif "onside" in image_tags:
                extend "  You asked her to lay down on her side, allowing you to get inside."
            elif "standing" in image_tags:
                extend " You asked her to spread her legs while standing, and pushed your dick inside."
            elif "spooning" in image_tags:
                extend " You asked her to snuggle to you, spooning her in the process."
            elif "sitting" in image_tags:
                extend " You asked her to sit upon you knees, immersing your dick inside."
            else:
                extend " You entered her and asked to start moving."
        else:
            if sex_scene_libido > 0:
                "[char.name] doesn't mind you to do her pussy."
            else:
                "[char.name] silently offers her pussy."
            if "ontop" in image_tags:
                extend " You invite her to sit on top of you, preparing your dick for some penetration."
            elif "doggy" in image_tags:
                extend " She bent over, welcoming your dick from behind."
            elif "missionary" in image_tags:
                extend " She lays on her back and spreads legs, inviting you to enter inside."
            elif "onside" in image_tags:
                extend " She lays down on her side, inviting you to enter inside."
            elif "standing" in image_tags:
                extend " You proceed to penetrate her not even bothering to lay down."
            elif "spooning" in image_tags:
                extend " You two snuggle to each other, trying out spooning."
            elif "sitting" in image_tags:
                extend " She sits upon you knees while you prepare your dick for going inside her."
            else:
                extend " You enter her pussy and you two begin to move."
        call interaction_sex_scene_check_skill_acts
        
    elif current_action == "anal":
        if ct("Lesbian"):
            $ skill_for_checking = round(char.get_skill("anal")*0.6 + char.get_skill("sex")*0.15)
        else:
            $ skill_for_checking = round(char.get_skill("anal")*0.75 + char.get_skill("sex")*0.25)
        $ male_skill_for_checking = round(hero.get_skill("anal")*0.75 + hero.get_skill("sex")*0.25)
        if dice(20):
            $ char.anal += 1
        if dice(10):
            $ hero.anal += 1
        if (skill_for_checking - male_skill_for_checking) > 250 and dice(50):
            $ hero.anal += 1
        if (male_skill_for_checking - skill_for_checking) > 250 and dice(75):
            $ char.anal += 1
        if dice(10):
            $ char.sex += 1
        if dice(5):
            $ hero.sex += 1
        $ get_single_sex_picture(char, act="anal", location=sex_scene_location, hidden_partner=True)
        $ image_tags = gm.img.get_image_tags()
        if sub > 0:
            if sex_scene_libido > 0:
                "[char.name] looking forward to something big inside her ass."
            else:
                "[char.name] unenthusiastically prepares her ass."
            if "ontop" in image_tags:
                extend " She sits on top of you, immersing your dick inside."
            elif "doggy" in image_tags:
                extend " She bent over, pushing her anus toward your dick."
            elif "missionary" in image_tags:
                extend " She lay on her back spreading her legs, awaiting for your dick."
            elif "onside" in image_tags:
                extend " She lay down on her side, waiting for you to join her."
            elif "standing" in image_tags:
                extend " She spreads her legs waiting for you, not even bothering to lay down."
            elif "spooning" in image_tags:
                extend " She snuggled to you, being in a mood for some spooning."
            elif "sitting" in image_tags:
                extend " She sat upon you knees, immersing your dick inside."
            else:
                extend " She confidently pushes your dick inside and starts to move."
        elif sub < 0:
            "[char.name] prepares herself, awaiting for further orders."
            if "ontop" in image_tags:
                extend " You ask her to sit on top of you, immersing your dick inside."
            elif "doggy" in image_tags:
                extend " You ask her to bent over, allowing you to take her from behind."
            elif "missionary" in image_tags:
                extend " You ask her to lay on her back and spread legs, allowing you to shove your dick inside."
            elif "onside" in image_tags:
                extend "  You asked her to lay down on her side, allowing you to get inside."
            elif "standing" in image_tags:
                extend " You asked her to spread her legs while standing, and pushed your dick inside."
            elif "spooning" in image_tags:
                extend " You asked her to snuggle to you, spooning her in the process."
            elif "sitting" in image_tags:
                extend " You asked her to sit upon you knees, immersing your dick inside."
            else:
                extend " You entered her and asked to start moving."
        else:
            if sex_scene_libido > 0:
                "[char.name] doesn't mind you to do her ass."
            else:
                "[char.name] silently offers her ass."
            if "ontop" in image_tags:
                extend " You invite her to sit on top of you, preparing your dick for some penetration."
            elif "doggy" in image_tags:
                extend " She bent over, welcoming your dick from behind."
            elif "missionary" in image_tags:
                extend " She lays on her back and spreads legs, inviting you to enter inside."
            elif "onside" in image_tags:
                extend " She lays down on her side, inviting you to enter inside."
            elif "standing" in image_tags:
                extend " You proceed to penetrate her not even bothering to lay down."
            elif "spooning" in image_tags:
                extend " You two snuggle to each other, trying out spooning."
            elif "sitting" in image_tags:
                extend " She sits upon you knees while you prepare your dick for going inside her."
            else:
                extend " You enter her anus and you two begin to move."
        call interaction_sex_scene_check_skill_acts
    $ sex_scene_libido -= 1
    jump interaction_scene_choice
    
label interaction_sex_scene_check_skill_jobs: # skill level check for one side actions

    if current_action == "hand":
        if skill_for_checking <= 200:
            if sub > 0:
                $ narrator(choice(["She strokes you a bit too quickly, the friction is a bit uncomfortable.", "She begins to stroke you very quickly. But because of the speed your cock often slips out of her hand."]))
            elif sub < 0:
                $ narrator(choice(["She strokes you gently. She isn't quite sure however what to make of the balls.", "She makes up for her inexperience with determination, carefully stroking your cock."]))
            else:
                $ narrator(choice(["She squeezes one of your balls too tightly, but stops when you wince.", "She has a firm grip, and she's not letting go."]))
        elif skill_for_checking < 1000:
            if sub > 0:
                $ narrator(choice(["Her fingers cause tingles as they caress the shaft.", "She quickly strokes you, with a very deft pressure."]))
            elif sub < 0:
                $ narrator(choice(["She gently caresses the shaft, and cups the balls in her other hand, giving them a warm massage.", "She moves very smoothly, stroking casually and very gently."]))
            else:
                $ narrator(choice(["Her hands glide smoothly across it.", "She moves her hands up and down. She's a little rough at this, but at she tries her best."]))
        else:
            if sub > 0:
                $ narrator(choice(["Her movements are masterful, her slightest touch starts you twitching.", "Her expert strokes will have you boiling over in seconds."]))
            elif sub < 0:
                $ narrator(choice(["She gently blows across the tip as her finger dance along the shaft.", "She slowly caresses you in a way that makes your blood boil, then pulls back at the last second."]))
            else:
                $ narrator(choice(["She knows what to do now, and rubs you with smooth strokes, focusing occasionally on the head.", "You can't tell where her hand is at any moment, all you know is that it works."]))
        if "after sex" in image_tags:
            "Soon you generously cover her body with your thick liquid."
    elif current_action == "tits":
        if skill_for_checking <= 200:
            if sub > 0:
                $ narrator(choice(["She kind of bounces her tits around your cock.", "She tries to quickly slide the cock up and down between her cleavage, but it tends to slide out."]))
            elif sub < 0:
                $ narrator(choice(["She slides the cock up and down between her cleavage.", "She squeezes her cleavage as tight as she can and rubs up and down."]))
            else:
                $ narrator(choice(["She sort of squishes her breasts back and forth around your cock.", "She slaps her tits against your dick, bouncing her whole body up and down."]))
        elif skill_for_checking < 1000:
            if sub > 0:
                $ narrator(choice(["She juggles her breasts up and down around your cock.", "She moves her boobs up and down in a fluid rocking motion."]))
            elif sub < 0:
                $ narrator(choice(["She gently caresses the shaft between her tits.", "She lightly brushes the head with her chin as it pops up between her tits."]))
            else:
                $ narrator(choice(["Sometimes she pauses to rub her nipples across the shaft.", "She rapidly slides the shaft between her tits"]))
        else:
            if sub > 0:
                $ narrator(choice(["She rapidly rocks her breasts up and down around your cock, covering them with drool to keep things well lubed.", "In as she strokes faster and faster, she bends down to suck on the head."]))
            elif sub < 0:
                $ narrator(choice(["In between strokes she gently sucks on the head.", "She drips some spittle down to make sure you're properly lubed."]))
            else:
                $ narrator(choice(["She licks away at the head every time it pops up between her tits.", "She dancers her nipples across the shaft."]))
        if "after sex" in image_tags:
            if sub > 0:
                "At the last moment she pulls away, covering herself with your thick liquid."
            elif sub < 0:
                "At the last moment you take it away from her chest, covering her body with your thick liquid."
            else:
                "At the last moment she asked you to take it away from her chest to cover her body with your thick liquid."
    elif current_action == "blow":
        if skill_for_checking <= 200:
            if sub > 0:
                $ narrator(choice(["Her head bobs rapidly, until she goes a bit too deep and starts to gag.", "She begins to suck very quickly. But because of the speed your cock often pops out of her mouth."]))
            elif sub < 0:
                $ narrator(choice(["She tentatively kisses and licks around the head.", "She licks all over your dick, but she doesn't really have a handle on it."]))
            else:
                $ narrator(choice(["She bobs quickly on your cock, but clamps down a bit too tight.", "She puts the tip in her mouth and starts suck in as hard as she can. She's a little rough at this, but at least she tries her best."]))
        elif skill_for_checking < 1000:
            if sub > 0:
                $ narrator(choice(["She licks her way down the shaft, and gently teases the balls.", "Her mouth envelopes the head, then she quickly draws it in and draws back with a pop."]))
            elif sub < 0:
                $ narrator(choice(["She gently caresses the shaft, and cups the balls in her other hand, giving them a warm massage.", "She moves her tongue very smoothly and very gently, keeping her teeth well clear, aside from a playful nip."]))
            else:
                $ narrator(choice(["She's settled into a gentle licking pace that washes over you like a warm bath.", "She licks up and down the shaft. A little rough, but at least she tries her best."]))
        else:
            if sub > 0:
                $ narrator(choice(["She rapidly bobs up and down on your cock, a frenzy of motion.", "She puts the tip into her mouth and her tongue swirls rapidly around it."]))
            elif sub < 0:
                $ narrator(choice(["She gently blows across the head as she covers your cock in smooth licks.", "She moves very smoothly, tongue dancing casually and very gently."]))
            else:
                $ narrator(choice(["Her deft licks are masterful, your cock twitches with each stroke.", "She's really good at this, alternating between deep suction and gentle licks."]))
        if "after sex" in image_tags:
            if sub > 0:
                "At the last moment she pulls it out, covering herself with your thick liquid."
            elif sub < 0:
                "At the last moment you pull it out from her mouth, covering her body with your thick liquid."
            else:
                "She asked you to pull it out from her mouth at the last moment to cover her body with your thick liquid."
    if skill_for_checking >= 4000:
        "She was so good that you profusely came after a few seconds. Pretty impressive."
        $ char.joy += randint(3, 5)
    elif skill_for_checking >= 2000:
        "You barely managed to hold out for half a minute in the face of her amazing skills."
        $ char.joy += randint(2, 4)
    elif skill_for_checking >= 1000:
        "It was very fast and very satisfying."
        $ char.joy += randint(1, 2)
    elif skill_for_checking >= 500:
        "Nothing extraordinary, but it wasn't half bad either."
        $ char.joy += randint(0, 1)
    elif skill_for_checking >= 200:
        "It took some time and effort on her part, her skills could definitely be improved."
    elif skill_for_checking >= 50:
        "Looks like [char.name] barely knows what she's doing. Still, she somewhat managed to get the job done."
        $ char.vitality -= randint(5, 10)
    else:
        $ char.vitality -= randint(10, 15)
        "Her moves were clumsy and untimely. By the time she finished the moment had passed, bringing you little satisfaction."
        $ char.joy -= randint(2, 4)
    $ sex_count += 1
    if skill_for_checking >= 50:
        $ guy_count +=1
        $ cum_count += 1
    return

label interaction_sex_scene_check_skill_acts: # skill level check for two sides actions
    if current_action == "vag":
        if skill_for_checking >= 4000:
            "Her technique is brought to perfection, her body moves in perfect synchronisation with yours, and her pussy felt like velvet."
            $ char.joy += randint(3, 5)
        elif skill_for_checking >= 2000:
            "Her refined skills, rhythmic movements, and wet hot pussy quickly brought you to the finish."
            $ char.joy += randint(2, 4)
        elif skill_for_checking >= 1000:
            "Her pussy felt very good, her movement patterns and amazing skills quickly exhausted your ability to hold back."
            $ char.joy += randint(1, 2)
        elif skill_for_checking >= 500:
            "Her movements were pretty good. Nothing extraordinary, but it wasn't half bad either."
            $ char.joy += randint(0, 1)
        elif skill_for_checking >= 200:
            "It took some time and effort on her part, her pussy could use some training."
            $ char.vitality -= randint(5, 10)
        elif skill_for_checking >= 50:
            "Looks like [char.name] barely knows what she's doing. Still, it's hard to screw up such a basic thing, so eventually she managed to get the job done."
            $ char.vitality -= randint(10, 15)
        else:
            "Her moves were clumsy and untimely, and her pussy was too dry. Sadly, she was unable to properly satisfy you."
            $ char.joy -= randint(2, 4)
            $ char.vitality -= randint(10, 15)
    elif current_action == "anal":
        if skill_for_checking >= 4000:
            "Her technique is brought to perfection, her body moves in perfect synchronisation with yours, and her anus was fit and tight."
            $ char.joy += randint(3, 5)
        elif skill_for_checking >= 2000:
            "Her refined skills, rhythmic movements, and tight hot ass quickly brought you to the finish."
            $ char.joy += randint(2, 4)
        elif skill_for_checking >= 1000:
            "Her anus felt very good, her movement patterns and amazing skills quickly exhausted your ability to hold back."
            $ char.joy += randint(1, 2)
        elif skill_for_checking >= 500:
            "Her movements were pretty good. Nothing extraordinary, but it wasn't half bad either."
            $ char.joy += randint(0, 1)
        elif skill_for_checking >= 200:
            "It took some time and effort on her part, her anus could use some training."
            $ char.vitality -= randint(5, 10)
        elif skill_for_checking >= 50:
            "Looks like [char.name] barely knows what she's doing. Still, it's hard to screw up such a basic thing, so eventually she managed to get the job done."
            $ char.vitality -= randint(10, 15)
        else:
            "Her moves were clumsy and untimely, and her anus wasn't quite ready for that. Sadly, she was unable to properly satisfy you."
            $ char.vitality -= randint(10, 15)
    if sex_scene_libido > 0:
        if male_skill_for_checking >= 4000:
            extend " Your bodies merged into a single entity, filling each other with pleasure and satisfaction."
            $ char.joy += randint(3, 5)
        elif male_skill_for_checking >= 2000:
            extend " In the end you both simultaneously cum multiple times."
            $ char.joy += randint(2, 4)
        elif male_skill_for_checking >= 1000:
            extend " In the end you both simultaneously cum."
            $ char.joy += randint(1, 2)
        elif male_skill_for_checking >= 500:
            extend " You fucked her until you both cum. It was pretty good."
            $ char.joy += randint(0, 1)
        elif male_skill_for_checking >= 200:
            extend " You fucked her until you both cum."
            $ hero.vitality -= randint(5, 10)
        elif male_skill_for_checking >= 50:
            extend " You had some difficulties with bringing her to orgasm, but managed to overcome them in the end."
            $ hero.vitality -= randint(10, 15)
        else:
            extend " Unfortunately you didn't have enough skill to properly satisfy her as well. [char.name] looks disappointed."
            $ hero.vitality -= randint(10, 15)
    else:
        if male_skill_for_checking >= 1000:
            extend " You did your best to make her cum, but it brought more pain than pleasure judging by her expression."
        else:
            " She is not in the mood anymore, your efforts to make her cum were in vain."
        
    if "after sex" in image_tags:
        $ cum_count += 1
        if sub > 0:
            "At the last moment she pulls it out, covering herself with your thick liquid."
        elif sub < 0:
            "At the last moment you pull it out from her, covering her body with your thick liquid."
        else:
            "She asked you to pull it out from her at the last moment to cover her body with your thick liquid."
    if (male_skill_for_checking) >= 1000 and (skill_for_checking >= 1000):
        $ together_count += 1
    $ sex_count += 1
    if male_skill_for_checking >= 50:
        $ girl_count += 1
    if skill_for_checking >= 50:
        $ guy_count += 1
    if hasattr(store, 'just_lost_virginity'):
        $ del just_lost_virginity
        call interactions_after_virginity_was_taken
    return

label interactions_sex_agreement: # the character agrees to do it
    $ char.override_portrait("portrait", "shy") # TO DO: this part for half-sister is to complex to be handled via properties, thus female lines should be written separately after adding female MC, with direct checks for MC gender
    if ct("Half-Sister") and dice(50):
        if ct("Impersonal"):
            $ rc("I'll take in all your cum, brother.", "Sex with my brother, initiation.", "Let's have incest.", "Even though we're siblings... it's fine to do this, right?", "Let's deepen our bond as siblings.")
        elif ct("Shy") and dice(40):
            $ rc("Umm... anything is fine as long as it's you... brother.", "I-if it's you, b-brother, then anything you do makes me feel good.", "I-is it alright to do something like that with my brother..?")
        elif ct("Imouto"):
            $ rc("Teach me more things, brother!", "Brother, teach me how to feel good!", "Sis... will try her best.", "Sister's gonna show you her skills as a woman.")
        elif ct("Dandere"):
            $ rc("Ah... actually, your sister has been feeling sexually frustrated lately...", "Brother, please do me.", "Even though we're related, we can have sex if we love each other.", "I'm only doing this because you're my brother.", "I'll do whatever you want, brother.", "Brother can do anything with me...")
        elif ct("Kuudere"):
            $ rc("I... I can't believe I'm doing it with my brother...", "Y-you're lusting for your sister? O-okay, you can be my sex partner.", "I... I don't mind doing it even though we're siblings...", "Just for now, we're not siblings... we're just... a man and a woman.")
        elif ct("Tsundere"):
            $ rc("Ugh... I... I have such a lewd brother!", "A-alright, you are allowed to touch me, brother.", "I... I'm only doing this because you're hard, brother.", "Doing this... with my brother... What am I doing?..", "I bet our parents would be so mad...")
        elif ct("Kamidere"):
            $ rc("B...brother...it's... it's wrong to do this...", "E...even though we're siblings...", "Doing such a thing to my brother. Am I a bad big sister?", "My brother is in heat.  That's wonderful.")
        elif ct("Yandere"):
            $ rc("Make love to me, brother. Drive me mad.", "I'm looking forward to see your face writhing in mad ecstacy, bro.", "Shut up and yield yourself to your sister.", "Bro, you're a perv. It runs in the family though.", "Man, who'd have thought that my brother is as perverted as I am...", "As long as the pervy brother has a pervy sis as well, all is right with the world.", "Damn... The thought of incest gets me all excited now...")
        elif ct("Ane"):
            $ rc("This is how you've always wanted to claim me, isn't it?", "Doing such things to your sister... Well, it can't be helped...", "Sis will do her best.", "Let sis display her womanly skills.")
        elif ct("Bokukko"):
            $ rc("You want to have sex with your sister so bad, huh?", "I'm gonna show you that I'm a woman too, bro.", "Right on, brother.  Better you just shut up and don't move.", "Leave this to me, you can rely on sis.", "As long as it's for my brother a couple of indecent things is nothing.")
        else:
            $ rc("It's alright for siblings to do something like this.", "Make your sister feel good.", "We're brother and sister. What we're doing now must remain an absolute secret.", "I'll do my best. I want you to feel good, brother.")
       
    elif ct("Impersonal"):
        $ rc("You are authorized so long as it does not hurt.", "You can do me if you want.", "Understood. I will... service you...", "I dedicate this body to you.", "Understood. Please demonstrate your abilities.", "If the one corrupting my body is you, then I'll have no regrets.")
    elif ct("Shy") and dice(50):
        $ rc("Sex... O-okay, let's do it...", "D-do you mean...  Ah, y-yes...  If I'm good enough...", "Eeh?! Th-that's... uh... W- well... I do... want to...", "O...okay. I'll do my best.", "I too... wanted to be touched by you...", "Uh... H-how should I say this... It... it'll be great if you could do it gently.",  "Um, I-I want to do it too... Please treat me well.", "Eeh, i-is it ok with someone like me...?", "Umm...  I wanted to do it too... hehe.", "I-if I'm good enough, then however many times you want...", "I-I understand... I will... service you.")
    elif ct("Tsundere"):
        $ rc("*gulp*... W-well... since you're begging to do it with me, I suppose we can...", "It...it can't be helped, right? It... it's not that I like you or anything!", "I-it's not like I want to do it! It's just that you seem to want to do it so much...", "Hhmph... if...if you wanna do it... uh... go all the way with it!", "If you're asking, then I'll listen... B-but it's not like I actually want to do it, too!", "If-if you say that you really, really want it... Then I won't turn you down...", "L.... leave it to me... you idiot...", "God, people like you... Are way too honest about what they want...", "T...that can't be helped, right? B...but that doesn't mean you can do anything you like!", "You're hopeless.... Well, fine then....", "...Yes, yes, I'll do it, I'll do it so...  geez, stop making that stupid face...", "Geez, you take anything you can get...")
    elif ct("Dandere"):
        $ rc("If that's what you desire...", "...Very well then. Please go ahead and do as you like.", "You're welcome to... to do that.",  "I will not go easy on you.", "I... I'm ready for sex.", "...If you do it, be gentle.", "...If you want, do it now.", "...I want to do it, too.", "Ok, but please don't look at my face. That'll help me relax more.")
    elif ct("Kuudere"):
        $ rc("Y-yes... I don't mind letting you do as you please.", "If you feel like it, do what you want with my body...", "...I don't particularly mind.", "Heh. I'm just a girl too, you know. Let's do it.", "What a bother... Alright, I get it.", "...Fine, just don't use the puppy-dog eyes.", "*sigh* ...Fine, fine! I'll do it as many times as you want!", "Fine with me... Wh-what? ...Even I have times when I want to do it...", "If you wanna do it just do what you want.")
    elif ct("Imouto"):
        $ rc("Uhuhu, Well then, I'll be really nice to you, ok? ♪",  "Okayyy! Let's love each other a lot ♪", "Hold me really tight, kiss me really hard, and make me feel really good ♪", "Yeah, let's make lots of love ♪", "I'll do my best to pleasure you!", "Geez, you're so forceful...♪")
    elif ct("Ane"):
        $ rc("Heh, fine, do me to your heart's content.", "If we're going to do it, then let's make it the best performance possible. Promise?", "Come on, show me what you've got...", "This looks like it will be enjoyable.", "If you can do this properly... I'll give you a nice pat on the head.", "Seems like you can't help it, huh...", "Fufufu, please don't overdo it, okay?", "Go ahead and do it as you like, it's okay.", "Very well, I can show you a few things... Hmhm.", "You want to do it with me too? Huhu, by all means.")
    elif ct("Bokukko"):
        $ rc("Wha? You wanna to do it? Geez, you're so hopeless.. ♪", "Right, yeah... As long as you don't just cum on your own, sure, let's do it", "Y-yeah... I sort of want to do it, too... ehehe...", "S-sure... Ehehe, I'm, uh, kind of interested, too...", "Gotcha, sounds like a plan!", "Huhu... I want to do it with a pervert like you.", "Ehehe... In that case, let's go hog wild ♪", "Got'cha. Hehe. Now I won't go easy on you.", "Huhuh, I sort of want to do it too.", "Well, I s'pose once in a while wouldn't hurt ♪")
    elif ct("Yandere"):
        $ rc("You won't be able to think about anybody else besides me after I'm done with you ♪", "Oh? You seem quite confident. I'm looking forward to this ♪", "*giggle* I'll give you a feeling you'll never get from anyone else...", "Yes, let's have passionate sex, locked together ♪", "If we have sex you will never forget me, right? ♪", "Heh heh... You're going to feel a lot of pleasure. Try not to break on me.")
    elif ct("Kamidere"):
        $ rc("That expression on your face... Hehe, do you wanna fuck me that much?", "Fufu... I hope you are looking forward to this...!", "Feel grateful for even having the opportunity to touch my body.", "Alright, I'll just kill some time playing around with your body...", "You're raring to go, aren't you? Very well, let's see what you've got.", "Hhmn... My, my... you love my body so much? Of course you do, it can't be helped.", "Very well, entertain me the best you can.",  "...For now, I'm open to the idea.", "I don't really want to, but since you look so miserable I'll allow it.", "Haa, in the end, it turned out like this...  Fine then, do as you like.")
    else:
        $ rc("Oh... I guess if you like me it's ok.", "If you're so fascinated with me, let's do it.", "If you do it, then... please make sure it feels good.",  "I don't mind. Now get yourself ready before I change my mind.", "You're this horny...? Fine, then...", "Okay... I'd like to.",  "You insist, hm? Right away, then!", "You can't you think of anything else beside having sex? You're such a perv ♪", "You've got good intuition. That was just what I had in mind, hehe ♪", "Yes. Go ahead and let my body overwhelm you.", "All right. Do as you like.") 
    $ char.restore_portrait()
    return

label interactions_sex_disagreement: # the character disagrees to do it
    $ char.override_portrait("portrait", "angry")
    if ct("Half-Sister") and dice(65):
        if ct("Impersonal"):
            $ rc("No incest please.", "No. This is wrong.")
        elif ct("Yandere"):
            $ rc("Wait! We're siblings dammit.", "Hey, ummm... Siblings together... Is that really okay?")
        elif ct("Dandere"):
            $ rc("We're siblings. We shouldn't do things like this.", "Do you have sexual desires for your sister...?")
        elif ct("Imouto"):
            $ rc("[hero.hs]! P... please don't say things like that!", "Having sex with a blood relative? That's wrong!")
        elif ct("Tsundere"):
            $ rc("It's... it's wrong to have sexual desire among siblings, isn't it?", "[hero.hs], you idiot! Lecher! Pervert!")
        elif ct("Kuudere"):
            $ rc("...You want your sister's body that much? Pathetic.", "How hopeless can you be to do it with a sibling!")
        elif ct("Ane"):
            $ rc("What? But... I'm your sister.", "Don't you know how to behave yourself, as siblings?")
        elif ct("Kamidere"):
            $ rc("It's unacceptable for siblings to have sex!", "I can't believe... you do that... with your siblings!")
        elif ct("Bokukko"):
            $ rc("Oh boy, you are so weird.", "I'm your sis... Are you really okay with that?")
        else:
            $ rc("No! [hero.hs]! We can't do this!",  "Don't you think that siblings shouldn't be doings things like that?")
    elif ct("Impersonal"):
        $ rc("I see no possible benefit in doing that with you so I will have to decline.", "Keep sexual advances to a minimum.")
    elif ct("Shy") and dice(50):
        $ rc("I... I don't want that! ", "W-we can't do that. ", "I-I don't want to... Sorry.")
    elif ct("Imouto"):
        $ rc("Noooo way!", "I, I think perverted things are bad!", "...I-I'm gonna get mad if you say that stuff, you know? Jeez!", "Y-you dummy! You should be talking about stuff like s-s-sex!") 
    elif ct("Dandere"):
        $ rc("You're no good...", "Let's have you explain in full detail why you decided to do that today, hmm?", "You should really settle down.")
    elif ct("Tsundere"):
        $ rc("I'm afraid I must inform you of your utter lack of common sense. Hmph!", "You are so... disgusting!", "You pervy little scamp! Not in a million years!", "Hmph! Unfortunately for you, I'm not that cheap!")
    elif ct("Kuudere"):
        $ rc("G-get the fuck away from me, you disgusting perv.", "...Perv.", "...Looks like I'll have to teach you about this little thing called reality.", "O-of course the answer is no!", "Hmph, how unromantic!", "Don't even suggest something that awful.")
    elif ct("Kamidere"):
        $ rc("Wh-who do you think you are!?", "W-what are you talking about... Of course I'm against that!", "What?! How could you think that I... NO!", "What? Asking that out of the blue? Know some shame!", "The meaning of 'not knowing your place' must be referring to this, eh...?", "I don't know how anyone so despicable as you could exist outside of hell.")
    elif ct("Bokukko"):
        $ rc("He- Hey, Settle down a bit, okay?", "You should keep it in your pants, okay?", "Y-you're talking crazy...", "Hmph! Well no duh!")
    elif ct("Ane"):
        $ rc("If I was interested in that sort of thing I might, but unfortunately...", "Oh my, can't you think of a better way to seduce me?", "No. I have decided that it would not be appropriate.", "I don't think our relationship has progressed to that point yet.", "I think that you are being way too aggressive.", "I'm not attracted to you in ‘that’ way.")
    elif ct("Yandere"):
        $ rc("I've never met someone who knew so little about how pathetic they are.", "...I'll thank you to turn those despicable eyes away from me.", "What? Is that your dying wish? You want to die?")
    else:
        $ rc("No! Absolutely NOT!", "With you? Don't make me laugh.", "Get lost, pervert!", "Woah, hold on there. Maybe after we get to know each other better.", "Don't tell me that you thought I was a slut...?", "How about you fix that 'anytime's fine' attitude of yours, hmm?")  
    $ char.restore_portrait()
    return

label interaction_check_for_virginity: # here we do all checks and actions with virgin trait when needed
    if ct("Virgin"):
        if "Illusive" in hero.traits:
            $ current_action = "vag"
            jump interactions_sex_scene_logic_part
        else:
            if char.status == "slave":
                if ((cgo("SIW") or ct("Nymphomaniac")) and char.disposition >= 200) or (char.disposition >= 300) or (check_lovers(hero, char)) or (check_friends(hero, char)) or ct("Open Minded"):
                    menu:
                        "She warns you that this is her first time. She does not mind, but her value at the market might decrease. Do you want to continue?"
                        "Yes":
                            call interactions_girl_virgin_line
                        "No":
                            if check_lovers(hero, char) or check_friends(hero, char) or char.disposition >= 600:
                                "You changed your mind. She looks a bit disappointed."
                            else:
                                "You changed your mind."
                            jump interaction_scene_choice
                else:
                    menu: 
                        "She tells you that this is her first time, and asks plaintively to do something else instead. You can force her, but it will not be without consequences. Do you want to use force?"
                        "Yes":
                            "You violated her."
                            if char.health >=20:
                                $ char.health -= 10
                            else:
                                $ char.vitality -= 20
                            if ct("Masochist"):
                                $ sex_scene_libido += 1
                                $ char.disposition -= 50
                            else:
                                $ char.disposition -= 150
                                $ char.joy -= 50
                                $ sex_scene_libido -= 2
                        "No":
                            "You agreed to do something else instead. She sighs with relief."
                            jump interaction_scene_choice
            else:
                if (check_lovers(hero, char)) or (check_friends(hero, char) and char.disposition >= 600) or ((cgo("SIW") or ct("Nymphomaniac")) and char.disposition >= 250) or (ct("Open Minded") and char.disposition >= 350):
                    menu:
                        "Looks like this is her first time, and she does not mind. Do you want to continue?"
                        "Yes":
                            call interactions_girl_virgin_line
                        "No":
                            "You changed your mind. She looks a bit disappointed."
                            jump interaction_scene_choice
                else:
                    "Unfortunately she's still a virgin, and is not ready to pop her cherry yet."
                    jump interaction_scene_choice
        $ char.disposition += 50
        $ char.remove_trait(traits["Virgin"])
        if "Blood Master" in hero.traits:
            $ char.enable_effect("Blood Connection")
        if char.health >=15:
            $ char.health -= 10
        else:
            $ char.vitality -= 20      
    $ current_action = "vag"
    $ just_lost_virginity = True
    jump interactions_sex_scene_logic_part