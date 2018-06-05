init python:
    class SchoolCourse(_object):
        def __init__(self, name, difficulty, duration, days_to_complete,
                     effectiveness, data):
            self.name = name
            # self.trainer = trainer # restore after ST.
            self.difficulty = difficulty
            self.students = []
            self.students_progress = {}
            self.completed = set() # Students that completed this course
            self.duration = self.days_remaining = duration
            self.days_to_complete = days_to_complete # 25 or about 80% of duration is normal.
            self.effectiveness = effectiveness

            self.data = data
            
            self.building = None #so we know what building the course is associated with.

            self.set_image()
            self.set_price()

        def set_price(self):
            price = get_average_wage()
            price = price + price*self.difficulty
            self.price = round_int(price)

        def set_image(self):
            images = []
            folder = "content/schools/" + self.data["image"]
            for fn in renpy.list_files():
                if folder in fn and fn.endswith(IMAGE_EXTENSIONS):
                    images.append(fn)

            if not images:
                self.img = renpy.displayable("no_image")
            else:
                img = choice(images)
                self.img = renpy.displayable(img)

        def get_status(self, char):
            if char in self.students:
                return "Active!"

            days_to_complete = self.days_to_complete
            duration = self.duration

            if days_to_complete < duration*.65:
                dtc = " and Fast"
            elif days_to_complete < duration*.75:
                dtc = ""
            else:
                dtc = " and Slow"

            if self.difficulty >= char.tier+2:
                temp = "Great"
            elif self.difficulty >= char.tier:
                temp = "Good"
            else:
                temp = "Bad"

            return temp + dtc

        @property
        def tooltip(self):
            tt = self.data.get("desc", "No Description Available")

            temp = []
            for s in self.students:
                temp.append(s.nickname)

            if temp:
                tt += "\nStudents: "
                tt += ", ".join(temp)

            return tt

        def add_student(self, student):
            #Added this check to make sure the student isn't already in the class.
            #Should probably also check to make sure the student isn't in other classes?
            if student in self.students:
                return
                
            self.students.append(student)
            #Should probably also update their Workplace, and Action character fields
            #Workplace seems to be a building, so added .building to course obj and set to building obj
            student.workplace = self.building
            
            #This currently permits a student to be in multiple classes. 
            #I suppose that's technically ok, because they won't have the AP for all of them...
            
            
            if student not in self.students_progress:
                self.students_progress[student] = 0

        def remove_student(self):
            self.students.remove(student)

        def next_day(self):
            self.days_remaining -= 1

            students = [s for s in self.students if s.AP > 0]
            if not students:
                return

            if len(students) >= 3 and dice(25):
                best_student = choice(students)
            else:
                best_student = None

            for char in self.students:
                self.students_progress[char] += 1
                days_to_complete = self.days_to_complete # Mod on traits?
                ap_spent = char.AP

                primary_stats = []
                secondary_stats = []

                primary_skills = []
                secondary_skills = []

                for s in self.data['primary']: #this isn't being set correctly and crashing on Next Day call.
                    #self.data is a dict, so needs this accessor
                    if char.stats.is_stat(s):
                        if getattr(char, s) < char.get_max(s):
                            secondary_stats.append(s)
                    elif char.stats.is_skill(s):
                        primary_skills.append(s)
                    else:
                        raise Exception("{} is not a valid stat/skill for {} course.".format(
                                s, self.name
                        ))
                for s in self.data['secondary']:
                    if char.stats.is_stat(s):
                        if getattr(char, s) < char.get_max(s):
                            secondary_stats.append(s)
                    elif char.stats.is_skill(s):
                        secondary_skills.append(s)
                    else:
                        raise Exception("{} is not a valid stat/skill for {} course.".format(
                                s, self.name
                        ))
                #can't tell what these lines are trying to do, but commented out as currently do nothing.
                #secondary = self.data.secondary 
                #ss = primary + secon

                if char == best_student:
                    #give them an extra ap? Advantage of simplicity.
                    ap_spent +=1

                # Add stats/skills/exp mods.
                stat_pool = 1*ap_spent # Adjusts to difficulty (teacher tier)
                skills_pool = 2*ap_spent  # Adjusts to difficulty (teacher tier)
                
                #haven't taken into account Traits.
                
                #1) charge hero for course? 
                hero.take_money(self.price, reason=self.name)
                
                #2 add exp
                #sum of stat and skills pools will usually be 9 (3ap), giving 225 to 405 xp. Might need to be adjusted.
                char.add_exp(randint(25,45) * (stat_pool + skills_pool)) 
                    
                #) Improve stats of girl
                while(stat_pool > 0):
                    #randomly distribute stat_pool points among primary and secondary stats. 
                    #Can be replaced with something more sophistocated if desired.
                    if dice(50):
                        char.mod_stat(choice(primary_stats), 1)
                    else:
                        char.mod_stat(choice(secondary_stats), 1)
                    stat_pool -=1
                
                #) improve skills from class
                while(skills_pool > 0):
                    if dice(50):
                        char.mod_skill(choice(primary_skills), 1)
                    else:
                        char.mod_skill(choice(secondary_skills), 1)
                    skills_pool -=1
                    
                
                
                char.AP = 0


    class School(BaseBuilding):
        def __init__(self, id="-PyTFall Educators-",
                     img="content/schools/school.webp"):
            super(School, self).__init__(id=id, name=id)
            self.img = renpy.displayable(img)
            self.courses = []

        @property
        def is_school(self):
            #added so that checks to building objects in character/screens works right
            return True
            
        def add_cources(self):
            forced = max(0, 12-len(self.courses))
            for i in range(forced):
                self.create_course()

            if dice(50) and len(self.courses) < 20:
                self.create_course()

            if dice(10) and len(self.courses) < 30:
                self.create_course()

        def create_course(self):
            id = choice(school_courses.keys())

            v0 = max(0, hero.tier - 1)
            v1 = min(10, hero.tier + 3)
            difficulty = randint(v0, v1)

            duration = randint(20, 40)
            days_to_complete = round_int(duration*random.uniform(.5, .85))
            effectiveness = randint(60, 100)
            data = school_courses[id]

            course = SchoolCourse(id, difficulty, duration,
                                  days_to_complete, effectiveness,
                                  data)
            course.building = self # ref so that each course knows what building it is in.
            self.courses.append(course)
            

        def next_day(self):
            for c in self.courses[:]:
                c.next_day()
                if c.days_remaining <= 0:
                    self.courses.remove(c)

            self.add_courses()
