init -5 python:
    class GuardJob(Job):
        def __init__(self):
            """Creates reports for GuardJob.
            """
            super(GuardJob, self).__init__()
            self.id = "Guarding"
            self.type = "Combat"

            self.event_type = "jobreport"

            # Traits/Job-types associated with this job:
            self.occupations = ["Warrior"] # General Strings likes SIW, Warrior, Server...
            self.occupation_traits = [traits["Warrior"], traits["Mage"], traits["Knight"], traits["Shooter"]] # Corresponding traits...

            # Relevant skills and stats:
            self.base_skills = {"attack": 20, "defense": 20, "agility": 60, "magic": 20}
            self.base_stats = {"security": 100}

            self.desc = "Don't let them take your shit!"

        def traits_and_effects_effectiveness_mod(self, worker, log):
            """Affects worker's effectiveness during one turn. Should be added to effectiveness calculated by the function below.
               Calculates only once per turn, in the very beginning.
            """
            effectiveness = 0
             # effects always work
            if worker.effects['Food Poisoning']['active']:
                log.append("%s suffers from Food Poisoning, and is very far from her top shape." % worker.name)
                effectiveness -= 50
            elif worker.effects['Down with Cold']['active']:
                log.append("%s is not feeling well due to colds..." % worker.name)
                effectiveness -= 15
            elif worker.effects['Drunk']['active']:
                log.append("%s is drunk, which affects her coordination. Not the best thing when you need to guard something." % worker.name)
                effectiveness -= 20
            elif worker.effects['Revealing Clothes']['active']:
                if dice(50):
                    log.append("Her revealing clothes attract unneeded attention, interfering with work.")
                    effectiveness -= 10
                else:
                    log.append("Her revealing clothes help to pacify some aggressive customers.")
                    effectiveness += 10

            if locked_dice(65): # traits don't always work, even with high amount of traits there are normal days when performance is not affected

                traits = list(i.id for i in worker.traits if i in ["Abnormally Large Boobs",
                              "Aggressive", "Coward", "Stupid", "Neat", "Psychic", "Adventurous",
                              "Natural Leader", "Scars", "Artificial Body", "Sexy Air",
                              "Courageous", "Manly", "Sadist", "Nerd", "Smart", "Peaceful"])

                if "Lolita" in worker.traits and worker.height == "short":
                    traits.append("Lolita")
                if traits:
                    trait = choice(traits)
                else:
                    return effectiveness

                if trait == "Abnormally Large Boobs":
                    log.append("Her massive tits get in the way and keep her off balance as %s tries to work security." % worker.name)
                    effectiveness -= 25
                elif trait == "Aggressive":
                    if dice(50):
                        log.append("%s keeps disturbing customers who aren't doing anything wrong. Maybe it's not the best job for her." % worker.name)
                        effectiveness -= 35
                    else:
                        log.append("Looking for a good fight, %s patrols the area, scaring away the rough customers." % worker.name)
                        effectiveness += 50
                elif trait == "Lolita":
                    log.append("%s is too small to be taken seriously. Some of the problematic customers just laugh at her." % worker.name)
                    effectiveness -= 50
                elif trait == "Coward":
                    log.append("%s keeps asking for backup every single time an incident arises." % worker.name)
                    effectiveness -= 25
                elif trait == "Stupid":
                    log.append("%s has trouble adapting to the constantly evolving world of crime prevention." % worker.name)
                    effectiveness -= 15
                elif trait == "Smart":
                    log.append("%s keeps learning new ways to prevent violence before it happens." % worker.name)
                    effectiveness += 15
                elif trait == "Neat":
                    log.append("%s refuses to dirty her hands on some of the uglier looking criminals." % worker.name)
                    effectiveness -= 15
                elif trait == "Psychic":
                    log.append("%s knows when customers are going to start something, and prevents it easily." % worker.name)
                    effectiveness += 30
                elif trait == "Adventurous":
                    log.append("Her experience fighting bandits as an adventurer makes working security relatively easier.")
                    effectiveness += 25
                elif trait == "Natural Leader":
                    log.append("%s often manages to talk customers of starting an incident." % worker.name)
                    effectiveness += 50
                elif trait == "Scars":
                    log.append("One look at her scars is enough to tell the violators that %s means business." % worker.name)
                    effectiveness += 20
                elif trait == "Artificial Body":
                    log.append("%s makes no effort to hide the fact that she was a construct, intimidating would-be violators." % worker.name)
                    effectiveness += 25
                elif trait == "Sexy Air":
                    log.append("People around %s back her up her just because of her sexiness." % worker.name)
                    effectiveness += 15
                elif trait == "Courageous":
                    log.append("%s refuses to back down no matter the odds, making a great guard." % worker.name)
                    effectiveness += 25
                elif trait == "Manly":
                    log.append("Considering %s is bigger than a number of the guys, she prevents a lot of trouble just by being there." % worker.name)
                    effectiveness += 35
                elif trait == "Sadist":
                    log.append("%s gladly beats it out of any violators. Everyone deserves to be punished." % worker.name)
                    effectiveness += 15
                elif trait == "Nerd":
                    log.append("%s feels like a super hero while protecting your workers." % worker.name)
                    effectiveness += 15
                elif trait == "Peaceful":
                    log.append("%s has to deal with some very unruly patrons that give her a hard time." % worker.name)
                    effectiveness -= 35
            return effectiveness
