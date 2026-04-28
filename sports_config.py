"""Catégories sport + mots-clés Pexels pour Star Boxe Coaching Brest."""

SPORTS_CATEGORIES = {
    "boxing": {
        "pexels_keyword": "boxing training",
        "hashtags": "#StarBoxeCoaching #StarBoxeBrest #AielloBatonon #ChampionDuMonde #BoxeThai #Boxe #BoxingTraining #SportCombat #BrestSport #Coaching",
    },
    "mma": {
        "pexels_keyword": "MMA fighter training",
        "hashtags": "#MMA #ArtsMartiaux #MMAFrance #CombatSport #StarBoxeBrest #Grappling #MuayThai #Kickboxing #FightLife #BrestFight",
    },
    "musculation": {
        "pexels_keyword": "weight training gym",
        "hashtags": "#Musculation #Fitness #Gym #Bodybuilding #ForceMentale #StarBoxeBrest #TrainHard #GainMuscle #SportBrest #IronLife",
    },
    "yoga": {
        "pexels_keyword": "yoga pose dynamic",
        "hashtags": "#Yoga #YogaLife #CorpsEsprit #YogaBrest #Flexibilite #Meditation #BienEtre #YogaFrance #StarBoxeBrest #Balance",
    },
    "pilates": {
        "pexels_keyword": "pilates workout",
        "hashtags": "#Pilates #CoreStrength #Gainage #PilatesFrance #SportFeminin #Posture #PilatesBrest #StarBoxeBrest #FitBody #CoreWork",
    },
    "miha_bodytec": {
        "pexels_keyword": "EMS electrostimulation training",
        "hashtags": "#MihaBodytec #EMS #Electrostimulation #EMSTraining #20MinFit #SportInnovant #GainDeTemps #StarBoxeBrest #TechnoSport #BodyTec",
    },
    "cardio": {
        "pexels_keyword": "cardio fitness intense",
        "hashtags": "#Cardio #HIIT #Fitness #Endurance #BruleGraisses #SportAddict #CardioWorkout #StarBoxeBrest #FitFrance #Intensite",
    },
    "coaching": {
        "pexels_keyword": "personal trainer coaching",
        "hashtags": "#CoachingPersonnalise #PersonalTrainer #CoachSport #ObjectifFitness #StarBoxeBrest #Transformation #Motivation #CoachBrest #ResultatGaranti #AielloBatonon",
    },
}

# Info Star Boxe Brest (sera enrichi après recherche web)
STAR_BOXE_INFO = {
    "name": "Star Boxe Coaching",
    "instagram": "@starboxe29",
    "location": "Brest, Bretagne, France",
    "address": "13 Rue Amiral Troude, 29200 Brest",
    "phone": "06 13 94 16 42",
    "website": "starboxe.com",
    "facebook": "facebook.com/starboxebrest",
    "rating": "4.8/5",
    "hours": "10h-13h30 / 17h30-21h15",
    "coach": "Aiello Batonon",
    "coach_bio": (
        "Né au Gabon, arrivé à Brest à 12 ans. "
        "Champion de France Muay Thai 2009. "
        "Champion d'Europe WPMF -75kg 2010. "
        "Champion du Monde WPMF -75kg 2 avril 2011 — "
        "premier Brestois à détenir un titre mondial de Boxe Thaï. "
        "BPJEPS sports de contact. +1000 personnes coachées."
    ),
    "disciplines": list(SPORTS_CATEGORIES.keys()),
    "coaching_price": "80€/heure",
    "cta": "Réserve ton cours d'essai GRATUIT",
    "cta_mp": "Envoie ESSAI en MP pour ton premier cours gratuit !",
}
