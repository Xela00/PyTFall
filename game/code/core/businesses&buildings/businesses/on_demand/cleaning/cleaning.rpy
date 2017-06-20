init -5 python:
    class Cleaners(OnDemandBusiness):
        COMPATIBILITY = []
        MATERIALS = {"Wood": 2, "Bricks": 2}
        COST = 500
        ID = "Cleaners"
        IMG = "content/buildings/upgrades/cleaners.jpg"
        def __init__(self, name="Cleaning Block", instance=None, desc="Until it shines!",
                     img="content/buildings/upgrades/cleaners.jpg", build_effort=0,
                     materials=None, in_slots=0, cost=0, **kwargs):
            super(Cleaners, self).__init__(name=name, instance=instance,
                  desc=desc, img=img, build_effort=build_effort,
                  materials=materials, cost=cost, **kwargs)
            self.jobs = set([simple_jobs["Cleaning"]])

        def business_control(self):
            """This checks if there are idle workers willing/ready to clean in the building.
            Cleaning is always active, checked on every tick.
            Cleaners are on call at all times.
            Whenever dirt reaches 200, they start cleaning till it’s 0 or are on standby on idle otherwise.
            If dirt reaches 600 (they cannot coop or there are simply no pure cleaners),
            all “Service Types” that are free help out and they are released when dirt reaches 50 or below.
            If dirt reaches 900, we check for auto-cleaning and do the “magical” thing if player has
            the money and is willing to pay (there is a checkbox for that already).
            If there is no auto-cleaning, we call all workers in the building to clean…
            unless they just refuse that on some principal (trait checks)...
            """
            # while 1:
            #     yield self.env.timeout(1)
            # TODO: FIGURE OUT WHAT TO DO WITH JOBPOINTS!
            building = self.instance
            make_nd_report_at = 0 # We build a report every 25 ticks but only if this is True!
            dirt_cleaned = 0 # We only do this for the ND report!

            cleaning = False # set to true if there is active cleaning in process
            using_all_service_workers = False
            using_all_workers = False

            power_flag_name = "jobs_cleaning_power"
            job = simple_jobs["Cleaning"]
            all_cleaners = self.get_pure_cleaners(job, power_flag_name) # Everyone that cleaned for the report.
            cleaners = all_cleaners.copy() # cleaners on active duty

            while 1:
                dirt = building.get_dirt()
                if dirt >= 900:
                    if building.auto_clean:
                        price = building.get_cleaning_price()
                        if hero.take_money(price):
                            building.dirt = 0
                            dirt = 0
                            temp = "{}: {} Building was auto-cleaned!".format(self.env.now,
                                                building.name)
                            self.log(temp)

                    if not using_all_workers and dirt:
                        using_all_workers = True
                        all_cleaners = self.all_on_deck(cleaners, job, power_flag_name)
                        cleaners = all_cleaners.union(cleaners)

                    if not make_nd_report_at and dirt:
                        wlen = len(cleaners)
                        make_nd_report_at = min(self.env.now+25, 100)
                        if self.env:
                            temp = "{}: {} Workers have started to clean {}!".format(self.env.now,
                                                set_font_color(wlen, "red"), building.name)
                            self.log(temp)
                elif dirt >= 600:
                    if not using_all_workers:
                        using_all_workers = True
                        all_cleaners = self.all_on_deck(cleaners, job, power_flag_name)
                        cleaners = all_cleaners.union(cleaners)

                    if not make_nd_report_at:
                        wlen = len(cleaners)
                        make_nd_report_at = min(self.env.now+25, 100)
                        if self.env:
                            temp = "{}: {} Workers have started to clean {}!".format(self.env.now,
                                                set_font_color(wlen, "red"), building.name)
                            self.log(temp)
                elif dirt >= 200:
                    if not make_nd_report_at:
                        wlen = len(cleaners)
                        make_nd_report_at = min(self.env.now+25, 100)
                        if self.env:
                            temp = "{}: {} Workers have started to clean {}!".format(self.env.now,
                                                set_font_color(wlen, "red"), building.name)
                            self.log(temp)

                # switch back to normal cleaners only
                if dirt <= 100 and using_all_workers:
                    using_all_workers = False
                    cleaners = self.get_pure_cleaners(job, power_flag_name)

                if make_nd_report_at and building.dirt > 0:
                    for w in cleaners:
                        value = -w.flag(power_flag_name)
                        dirt_cleaned += value
                        building.clean(value)

                condition1 = make_nd_report_at and self.env.now == make_nd_report_at
                condition2 = make_nd_report_at and building.dirt <= 0
                if condition1 or condition2:
                    self.write_nd_report(all_cleaners, dirt_cleaned)
                    make_nd_report_at = 0
                    dirt_cleaned = 0

                yield self.env.timeout(1)

        def get_pure_cleaners(self, job, power_flag_name):
            cleaners = set(self.get_workers(job, amount=float("inf"),
                            match_to_client=None, priority=True, any=False))
            for w in cleaners:
                # TODO Review, revice and account for effectiveness!!!
                if not w.flag(power_flag_name):
                    value = -int(round(1 + w.get_skill("service") * 0.025 + w.agility * 0.03))
                    w.set_flag(power_flag_name, value)
            return cleaners

        def all_on_deck(self, cleaners, job, power_flag_name):
            power_flag_name = "jobs_cleaning_power"
            # calls everyone in the building to clean it
            cleaners.union(self.get_workers(job, amount=float("inf"),
                           match_to_client=None, priority=True, any=True))
            for w in cleaners:
                if not w.flag(power_flag_name):
                    value = -int(round(1 + w.get_skill("service") * 0.025 + w.agility * 0.03))
                    w.set_flag(power_flag_name, value)
            return cleaners

        def write_nd_report(self, pure_cleaners, dirt_cleaned):
            job, loc = self.job, self.instance
            log = NDEvent(job=job, loc=loc, team=pure_cleaners, business=self)

            wlen = len(pure_cleaners)
            temp = "{} Workers cleaned {} today!".format(set_font_color(wlen, "red"), loc.name)
            log.append(temp)

            log.img = Fixed(xysize=(820, 705))
            log.img.add(Transform(loc.img, size=(820, 705)))
            vp = vp_or_fixed(pure_cleaners, ["maid", "cleaning"], {"exclude": ["sex"], "resize": (150, 150), "type": "any"})
            log.img.add(Transform(vp, align=(.5, .9)))

            log.team = pure_cleaners

            temp = "{} cleaned {} dirt!".format(", ".join([w.nickname for w in pure_cleaners]), dirt_cleaned)
            log.append(temp)

            # Stat mods
            log.logloc('dirt', dirt_cleaned)

            # for w in self.all_workers:
            #     log.logws('vitality', -randint(15, 25), w)  # = ? What to do here?
            #     log.logws('exp', randint(15, 25), w) # = ? What to do here?
            #     if dice(33):
            #         log.logws('service', 1, w) # = ? What to do here?
            # ... We prolly need to log how much dirt each individual worker is cleaning or how much wp is spent...
            log.event_type = "jobreport" # Come up with a new type for team reports?

            log.after_job()
            NextDayEvents.append(log)

        def clean(self, cleaners, building):
            while cleaners and dirt - dirt_cleaned >= 10:
                # Job Points:
                flag_name = "_jobs_cleaning_points"
                for w in cleaners[:]:
                    if not w.flag(flag_name) or w.flag(flag_name) <= 0:
                        self.convert_AP(w, cleaners, flag_name)

                    # Cleaning itself:
                    if w in cleaners:
                        dirt_cleaned = dirt_cleaned + w.flag(power_flag_name)
                        w.mod_flag("_jobs_cleaning_points", -1) # 1 point per 1 dp? Is this reasonable...? Prolly, yeah.
                        w.mod_flag("job_cleaning_points_spent", 1) # So we know what to do during the job event buildup and stats application.

                if config.debug and self.env and not counter % 2:
                    wlen = len(cleaners)
                    # We run this once per 2 du and only for debug purposes.
                    temp = "{}: Debug: ".format(self.env.now)
                    temp = temp + " {} Workers are currently cleaning {}!".format(set_font_color(wlen, "red"), building.name)
                    temp = temp + set_font_color(" Cleaned: {} dirt".format(dirt_cleaned), "blue")
                    self.log(temp)

                # We may be running this outside of SimPy...
                if self.env:
                    yield self.env.timeout(1)

                counter += 1

            temp = "{}: Cleaning process of {} is now finished!".format(self.env.now, building.name)
            temp = set_font_color(temp, "red")
            self.log(temp)

            # Once the loop is broken:
            # Restore the lists:
            self.active_workers = list()
            for w in cleaners:
                self.instance.available_workers.append(w)

            # Build the report:
            simple_jobs["Cleaning"](cleaners_original, cleaners, building, dirt, dirt_cleaned)
