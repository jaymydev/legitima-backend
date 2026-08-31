"""La banque de questions, écrite à la main.

C'est l'actif éditorial du produit : elle se relit, se corrige, et ne dépend
d'aucun appel modèle. Les entrées sont dans l'ordre de probabilité décroissante,
et cet ordre EST la donnée — il n'y a pas de champ de score à maintenir à côté.

`answer` est un gabarit à balises. Il se lit sans être rempli : quelqu'un qui
n'a rien saisi voit déjà la forme, la longueur et l'ordre de ce qu'il doit dire.

Généré depuis les fichiers de rédaction ; les commentaires de relecture ne sont
pas embarqués — ils servaient à juger la banque, pas à la servir.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BankEntry:
    id: str
    question: str
    answer: str
    follow_up: str = ""
    avoid: str = ""
    #: Ne vaut que pour qui encadre. « Un membre de votre équipe décroche »
    #: servi à quelqu'un qui n'a pas d'équipe le prépare à un entretien qui
    #: n'existe pas — l'entrée n'est servie que si le client le demande.
    encadrement: bool = False

COMMUNES: list[BankEntry] = [
    BankEntry(
        id='parlez_moi_de_vous',
        question='Parlez-moi de vous.',
        answer="« Je suis <MÉTIER> depuis <NOMBRE_ANNÉES_EXPÉRIENCE>. Aujourd'hui je suis <POSTE_ACTUEL> chez <ENTREPRISE_ACTUELLE>, où je <CE_QUE_J_AI_FAIT>. Ce que je cherche maintenant, c'est <POSTE_VISÉ>. »",
        avoid='ne remontez pas à vos études. Trois phrases suffisent, le reste viendra en questions.',
    ),
    BankEntry(
        id='racontez_une_situation_difficile_que_vous',
        question='Racontez une situation difficile que vous avez gérée.',
        answer="« Sur <RÉALISATION>, nous avons eu <DIFFICULTÉ>. J'ai <CE_QUE_J_AI_FAIT>, et <RÉSULTAT>. »",
        avoid="ne racontez pas ce que l'équipe a fait. Chaque verbe de votre réponse doit avoir « je » comme sujet.",
    ),
    BankEntry(
        id='quels_sont_vos_points_forts',
        question='Quels sont vos points forts ?',
        answer="« <COMPÉTENCE>, surtout. Sur <RÉALISATION>, c'est ce qui m'a permis de <RÉSULTAT>. »",
        avoid="n'en citez pas trois. Un seul point fort prouvé vaut mieux que trois affirmés.",
    ),
    BankEntry(
        id='quel_est_votre_principal_defaut',
        question='Quel est votre principal défaut ?',
        answer="« <POINT_À_AMÉLIORER>. C'est pour ça que <CE_QUE_J_AI_FAIT> — ça ne l'efface pas, mais ça le tient. »",
        avoid="pas de faux défaut déguisé en qualité. « Je suis perfectionniste » s'entend comme un aveu de non-préparation.",
    ),
    BankEntry(
        id='parlez_moi_d_un_echec',
        question="Parlez-moi d'un échec.",
        answer="« Sur <RÉALISATION>, <DIFFICULTÉ>. Je m'y suis mal pris : <CE_QUE_J_AI_FAIT>. Ce que j'en ai tiré, c'est <POINT_À_AMÉLIORER>. »",
        avoid="ne choisissez pas un échec dont vous n'êtes pas responsable. C'est la responsabilité qu'on teste, pas la malchance.",
    ),
    BankEntry(
        id='comment_gerez_vous_la_pression_et',
        question='Comment gérez-vous la pression et les délais ?',
        answer="« Je hiérarchise et je préviens tôt. Sur <RÉALISATION>, quand <DIFFICULTÉ>, j'ai <CE_QUE_J_AI_FAIT> plutôt que de laisser filer. »",
        avoid='« je travaille bien sous pression » ne veut rien dire. Montrez un arbitrage précis.',
    ),
    BankEntry(
        id='racontez_un_desaccord_avec_un_collegue',
        question='Racontez un désaccord avec un collègue ou votre manager.',
        answer="« Sur <RÉALISATION>, nous n'étions pas d'accord sur <DIFFICULTÉ>. J'ai <CE_QUE_J_AI_FAIT>, et nous avons tranché sur <RÉSULTAT>. »",
        avoid="ne dites jamais que vous aviez raison. Ce qu'on évalue, c'est votre façon de sortir du désaccord, pas son issue.",
    ),
    BankEntry(
        id='comment_vous_organisez_vous',
        question='Comment vous organisez-vous ?',
        answer='« Je pars des échéances et je remonte. Concrètement sur <RÉALISATION>, <CE_QUE_J_AI_FAIT>, avec <OUTIL>. »',
        avoid='ne récitez pas une méthode. Ce qui compte est comment vous arbitrez quand tout est prioritaire.',
    ),
    BankEntry(
        id='quel_est_le_retour_le_plus',
        question="Quel est le retour le plus difficile qu'on vous ait fait ?",
        answer="« On m'a dit <POINT_À_AMÉLIORER>. Sur le coup c'était dur à entendre. J'ai <CE_QUE_J_AI_FAIT>, et aujourd'hui <RÉSULTAT>. »",
        avoid='ne racontez pas un retour que vous avez rejeté. On mesure votre capacité à encaisser, pas à argumenter.',
    ),
    BankEntry(
        id='preferez_vous_travailler_seul_ou_en',
        question='Préférez-vous travailler seul ou en équipe ?',
        answer="« Les deux ont leur moment. Sur <RÉALISATION>, j'ai <CE_QUE_J_AI_FAIT> seul, puis j'ai eu besoin de l'équipe pour <RÉSULTAT>. »",
        avoid="ne choisissez pas un camp. La question cherche votre lucidité sur le moment où l'on bascule.",
    ),
    BankEntry(
        id='ou_vous_voyez_vous_dans_trois',
        question='Où vous voyez-vous dans trois ans ?',
        answer="« Je veux être solide sur <COMPÉTENCE>, et avoir pris <POSTE_VISÉ> ou son périmètre. Ce qui compte pour moi, c'est <CE_QUI_VOUS_ATTIRE>. »",
        avoid="ni « à votre place », ni « je ne sais pas ». Une direction suffit, un plan de carrière n'est pas demandé.",
    ),
    BankEntry(
        id='qu_est_ce_qui_vous_motive',
        question="Qu'est-ce qui vous motive ?",
        answer="« <CE_QUI_VOUS_ATTIRE>. C'est ce que j'ai retrouvé sur <RÉALISATION>, et c'est ce que je cherche dans <POSTE_VISÉ>. »",
        avoid="« les défis » et « l'humain » ne disent rien. Nommez une chose concrète que vous avez aimé faire.",
    ),
    BankEntry(
        id='racontez_une_decision_difficile_que_vous',
        question='Racontez une décision difficile que vous avez prise.',
        answer="« Sur <RÉALISATION>, il fallait trancher entre <DIFFICULTÉ>. J'ai décidé de <CE_QUE_J_AI_FAIT>, en sachant que <RÉSULTAT>. »",
        avoid="ne présentez pas une décision sans coût. Une décision sans renoncement n'en est pas une.",
    ),
    BankEntry(
        id='comment_vous_tenez_vous_a_niveau',
        question='Comment vous tenez-vous à niveau ?',
        answer="« Sur <COMPÉTENCE>, j'ai <CE_QUE_J_AI_FAIT> — et je m'en suis servi tout de suite sur <RÉALISATION>. »",
        avoid='citer des formations sans usage. Ce qui compte est ce que vous en avez fait dans la semaine qui a suivi.',
    ),
    BankEntry(
        id='avez_vous_des_questions',
        question='Avez-vous des questions ?',
        answer="« Oui. Qu'est-ce qui ferait qu'au bout de six mois, vous vous direz que c'était le bon choix ? »",
        follow_up="Et selon le moment : « Qu'est-ce qui est le plus difficile dans ce poste aujourd'hui ? »",
        avoid="ne dites jamais « non, tout est clair ». C'est la seule réponse qui puisse coûter le poste à ce stade.",
    ),
]

SITUATIONS: list[BankEntry] = [
    BankEntry(
        id='un_client_vous_appelle_furieux_un',
        question='Un client vous appelle furieux un vendredi soir. Que faites-vous ?',
        answer="« Je le laisse dire, je reformule ce qui s'est passé, et je m'engage sur une seule chose : quand je le rappelle. Le reste attend lundi. »",
        avoid="ne promettez pas de régler le fond dans l'urgence. On teste votre sang-froid, pas votre héroïsme.",
    ),
    BankEntry(
        id='la_direction_vous_annonce_un_delai',
        question='La direction vous annonce un délai intenable. Comment réagissez-vous ?',
        answer='« Je dis oui à la contrainte et non au périmètre inchangé. Je reviens avec ce qui tient dans le délai et ce qui saute. »',
        avoid="ni « c'est impossible », ni « je vais essayer ». Les deux vous coûtent, l'un en posture, l'autre en crédibilité.",
    ),
    BankEntry(
        id='un_collegue_ne_livre_pas_ce',
        question='Un collègue ne livre pas ce dont vous dépendez. Que faites-vous ?',
        answer="« Je vais le voir avant d'alerter. Si rien ne bouge, je remonte le risque en factuel, sans en faire une affaire personnelle. »",
        avoid="ne dites pas que vous feriez à sa place. C'est ce qu'on répond quand on n'a jamais eu le problème.",
    ),
    BankEntry(
        id='vous_decouvrez_tardivement_une_erreur_que',
        question='Vous découvrez tardivement une erreur que vous avez commise. Comment gérez-vous ?',
        answer="« Je la remonte tout de suite, avec l'ampleur et une proposition de correction. Sur <RÉALISATION>, <CE_QUE_J_AI_FAIT>. »",
        avoid="ne dites pas que ça ne vous arrive pas. C'est la seule réponse qui disqualifie à coup sûr.",
    ),
    BankEntry(
        id='deux_managers_vous_donnent_des_priorites',
        question='Deux managers vous donnent des priorités contradictoires. Comment tranchez-vous ?',
        answer="« Je ne tranche pas seul : je remets les deux demandes côte à côte devant eux, avec ce que chacune coûte à l'autre. »",
        avoid='ne choisissez pas en silence. Le conflit ressortira, et ce sera le vôtre.',
    ),
    BankEntry(
        id='on_vous_demande_d_appliquer_une',
        question="On vous demande d'appliquer une décision avec laquelle vous êtes en désaccord.",
        answer="« Je dis mon désaccord une fois, argumenté, à la bonne personne. Si la décision tient, je l'applique sans la saboter. »",
        avoid='ni obéissance muette, ni résistance passive. On teste votre loyauté, pas votre soumission.',
    ),
    BankEntry(
        id='un_membre_de_votre_equipe_decroche',
        question='Un membre de votre équipe décroche. Que faites-vous ?',
        answer="« Je lui parle en tête-à-tête d'abord, sur les faits, sans diagnostic. Souvent la cause n'est pas celle qu'on croit. »",
        avoid='ne partez pas sur la sanction ni sur la vie privée. On cherche votre première réaction, et elle doit être une conversation.',
        encadrement=True,
    ),
    BankEntry(
        id='vous_reprenez_un_projet_en_cours',
        question='Vous reprenez un projet en cours, mal engagé. Par quoi commencez-vous ?',
        answer='« Par établir où on en est vraiment, avec les gens qui y sont. Avant de décider quoi que ce soit, je veux le vrai reste-à-faire. »',
        avoid="ne commencez pas par annoncer un plan. Personne ne croit un plan bâti en deux jours sur un dossier qu'on découvre.",
    ),
    BankEntry(
        id='il_vous_manque_une_information_pour',
        question='Il vous manque une information pour décider, et la décision ne peut pas attendre.',
        answer="« Je décide avec ce que j'ai, je dis clairement sur quelle hypothèse, et je fixe le moment où on la vérifie. »",
        avoid="ne dites pas que vous attendriez l'information. La question précise qu'on ne peut pas.",
    ),
    BankEntry(
        id='vous_etes_en_desaccord_technique_avec',
        question="Vous êtes en désaccord technique avec quelqu'un de bien plus expérimenté.",
        answer="« Je pose ma question plutôt que ma conclusion : ce que je ne comprends pas, c'est <DIFFICULTÉ>. Souvent la réponse est dans ce que je n'avais pas vu. »",
        avoid='ni renoncer par déférence, ni imposer. On teste comment vous faites avancer un désaccord asymétrique.',
    ),
    BankEntry(
        id='comment_dites_vous_non_a_votre',
        question='Comment dites-vous non à votre hiérarchie ?',
        answer="« Je ne dis pas non, je dis à quelles conditions c'est oui. Puis je laisse arbitrer. »",
        avoid="ne dites pas que vous ne dites jamais non. Ça s'entend comme une incapacité à protéger votre périmètre.",
    ),
    BankEntry(
        id='vous_devez_annoncer_une_mauvaise_nouvelle',
        question='Vous devez annoncer une mauvaise nouvelle à un client. Comment vous y prenez-vous ?',
        answer="« Tôt, moi-même, et avec l'option de sortie déjà préparée. L'ordre : le fait, l'impact, ce que je propose. »",
        avoid="ne noyez pas l'annonce dans du contexte. Le client entend la mauvaise nouvelle de toute façon, autant qu'elle soit claire.",
    ),
    BankEntry(
        id='deux_personnes_de_votre_equipe_sont',
        question='Deux personnes de votre équipe sont en conflit. Que faites-vous ?',
        answer='« Je les vois séparément pour comprendre, puis ensemble sur les faits et le fonctionnement à venir — pas sur qui a raison. »',
        avoid='ne tranchez pas le passé. Le seul terrain utile est ce qui se passe à partir de maintenant.',
        encadrement=True,
    ),
    BankEntry(
        id='on_vous_confie_une_charge_que',
        question='On vous confie une charge que vous savez impossible.',
        answer="« Je le dis au moment où on me la confie, pas après. Je propose ce qui tient, et ce qu'il faut arbitrer pour le reste. »",
        avoid="n'acceptez pas pour prouver votre bonne volonté. L'échec sera à vous seul.",
    ),
    BankEntry(
        id='vous_reprenez_le_poste_de_quelqu',
        question="Vous reprenez le poste de quelqu'un qui est parti fâché.",
        answer='« Je ne commente pas son départ. Je vais voir les gens qui travaillaient avec lui pour savoir ce qui reste en cours. »',
        avoid='ne cherchez pas à savoir pourquoi il est parti, et surtout ne le répétez pas.',
    ),
    BankEntry(
        id='le_perimetre_du_projet_change_en',
        question='Le périmètre du projet change en cours de route. Comment réagissez-vous ?',
        answer="« Je fais écrire le nouveau périmètre et j'en tire les conséquences sur le délai. Un changement non tracé devient un reproche plus tard. »",
        avoid='ne dites pas que vous vous adaptez. On veut savoir ce que vous faites, pas ce que vous ressentez.',
    ),
    BankEntry(
        id='comment_convainquez_vous_sans_autorite_hierarchique',
        question='Comment convainquez-vous sans autorité hiérarchique ?',
        answer='« En montrant à chacun ce que ça lui coûte de ne pas le faire. Sur <RÉALISATION>, <CE_QUE_J_AI_FAIT>. »',
        avoid="ne parlez pas de charisme ni de pédagogie. Parlez d'intérêts.",
    ),
    BankEntry(
        id='vous_devez_decider_et_votre_manager',
        question='Vous devez décider et votre manager est injoignable.',
        answer="« Je décide dans le périmètre qui est le mien, je documente, et je le préviens dès qu'il est joignable — sans attendre qu'il demande. »",
        avoid='ne dites pas que vous attendriez. Ne dites pas non plus que vous décideriez de tout.',
    ),
    BankEntry(
        id='un_processus_interne_ne_marche_pas',
        question='Un processus interne ne marche pas. Vous faites quoi ?',
        answer='« Je le suis quand même une fois en notant précisément où ça casse, puis je propose la correction avec le constat. »',
        avoid="ne le contournez pas en silence. C'est ce qu'on reproche, plus que le processus lui-même.",
    ),
    BankEntry(
        id='comment_integrez_vous_un_nouveau_dans',
        question='Comment intégrez-vous un nouveau dans votre équipe ?',
        answer="« Je lui donne une première chose utile à faire dans la semaine, et quelqu'un à qui poser ses questions bêtes. »",
        avoid="ne décrivez pas un parcours d'intégration théorique. Un geste concret vaut mieux qu'un processus.",
    ),
    BankEntry(
        id='votre_budget_est_coupe_en_cours',
        question='Votre budget est coupé en cours de projet.',
        answer="« Je reviens avec deux scénarios chiffrés plutôt qu'avec une plainte : ce qu'on garde, ce qu'on perd, et ce que ça implique. »",
        avoid="ne demandez pas le rétablissement du budget. Proposez des arbitrages, c'est ce qu'on attend.",
        encadrement=True,
    ),
    BankEntry(
        id='un_client_met_en_cause_quelqu',
        question="Un client met en cause quelqu'un de votre équipe devant vous.",
        answer="« J'écoute le fait, je ne commente pas la personne devant lui, et je reviens vers le client une fois que j'ai la version de mon équipe. »",
        avoid="ne désavouez jamais quelqu'un de votre équipe devant un tiers, même si le client a raison.",
        encadrement=True,
    ),
]

DEPLACEES: list[BankEntry] = [
    BankEntry(
        id='vous_comptez_avoir_des_enfants',
        question='Vous comptez avoir des enfants ?',
        answer="Dévier : « C'est un projet personnel, et ça n'aura pas d'effet sur ma disponibilité pour ce poste. »",
        follow_up="Rediriger : « Ce qui compte, c'est que <MISSION_DE_L_OFFRE> soit tenue. Sur <RÉALISATION>, j'ai <CE_QUE_J_AI_FAIT>. » Si vous choisissez de répondre, faites-le en une phrase et enchaînez sur le poste.",
        avoid='ne vous justifiez pas. Plus la réponse est longue, plus la question paraît légitime.',
    ),
    BankEntry(
        id='vous_etes_mariee_en_couple',
        question='Vous êtes mariée ? En couple ?',
        answer="Dévier : « Ma situation personnelle n'entre pas en jeu ici. »",
        follow_up='Rediriger : « Si la question porte sur ma mobilité ou mes horaires, je peux y répondre précisément. »',
        avoid='ne répondez pas par réflexe de politesse. Une fois la porte ouverte, les questions suivantes arrivent.',
    ),
    BankEntry(
        id='quel_age_avez_vous',
        question='Quel âge avez-vous ?',
        answer="Dévier : « J'ai <NOMBRE_ANNÉES_EXPÉRIENCE> d'expérience, dont <ANCIENNETÉ> sur <COMPÉTENCE>. »",
        avoid="ne donnez pas un chiffre puis une justification. L'expérience est la seule réponse pertinente à cette question.",
    ),
    BankEntry(
        id='vous_etes_d_origine_d_ou',
        question="Vous êtes d'origine… ? D'où vient votre nom ?",
        answer="Dévier : « Je suis <MÉTIER>, et c'est là-dessus que je peux être utile. »",
        follow_up='Rediriger : « Si la question porte sur les langues que je parle ou mon autorisation de travail, je peux répondre. »',
        avoid="n'entrez pas dans le récit familial. Il n'a rien à faire là et il ne vous servira pas.",
    ),
    BankEntry(
        id='vous_etes_pratiquant_vous_portez_ca',
        question='Vous êtes pratiquant ? Vous portez ça au travail ?',
        answer="Dévier : « Mes convictions ne regardent que moi et n'affectent pas mon travail. »",
        follow_up="Rediriger : « Si la question porte sur mes disponibilités ou une règle interne, dites-la-moi et j'y répondrai. »",
        avoid="ne négociez pas votre pratique dans un entretien. Faites préciser la règle de l'entreprise si elle existe.",
    ),
    BankEntry(
        id='vous_avez_eu_un_arret_maladie',
        question="Vous avez eu un arrêt maladie. De quoi s'agissait-il ?",
        answer="Dévier : « C'est réglé, et ça ne concerne plus mon travail aujourd'hui. »",
        follow_up='Rediriger : « Sur ma capacité à tenir le poste, je peux vous dire que <RÉALISATION> depuis. »',
        avoid='ne nommez pas la pathologie. Une donnée de santé donnée en entretien ne se reprend pas.',
    ),
    BankEntry(
        id='vous_avez_une_reconnaissance_de_travailleur',
        question='Vous avez une reconnaissance de travailleur handicapé ?',
        answer="Dévier : « Ce que je peux vous dire, c'est que je tiens <MISSION_DE_L_OFFRE> — sur <RÉALISATION>, <RÉSULTAT>. »",
        follow_up="Si vous choisissez d'en parler : « Oui, et ce dont j'ai besoin, c'est <AVANTAGE>. »",
        avoid="rien ne vous oblige à le déclarer en entretien. Mais si vous avez besoin d'un aménagement, le dire tôt vaut mieux que le découvrir tard.",
    ),
    BankEntry(
        id='votre_mari_fait_quoi_votre_femme',
        question='Votre mari fait quoi ? Votre femme travaille ?',
        answer="Dévier : « Ça n'entre pas en ligne de compte pour ce poste. »",
        avoid="la question sert souvent à évaluer votre besoin d'argent avant de négocier. N'y répondez pas avant d'avoir donné votre fourchette.",
    ),
    BankEntry(
        id='vous_etes_syndique_vous_votez_comment',
        question='Vous êtes syndiqué ? Vous votez comment ?',
        answer='Dévier : « Mes engagements personnels ne regardent que moi. »',
        avoid="ne répondez pas même si votre réponse vous semble sans risque. Ce n'est pas une question à laquelle on gagne à répondre.",
    ),
    BankEntry(
        id='vous_etes_trop_qualifie_pour_ce',
        question='Vous êtes trop qualifié pour ce poste.',
        answer="« Je comprends l'inquiétude : vous craignez que je parte vite. Ce que je viens chercher, c'est <CE_QUI_VOUS_ATTIRE>, et ça, ce poste le donne. »",
        avoid='ne contestez pas la qualification. Répondez à la crainte, pas à la phrase.',
    ),
    BankEntry(
        id='vous_etes_bien_jeune_pour_ce',
        question='Vous êtes bien jeune pour ce poste.',
        answer="« C'est vrai que je n'ai pas <NOMBRE_ANNÉES_EXPÉRIENCE> derrière moi. Ce que j'ai fait, c'est <RÉALISATION>, et <RÉSULTAT>. »",
        avoid="ne vous défendez pas sur l'âge, c'est un terrain que vous perdez. Déplacez sur ce qui est fait.",
    ),
    BankEntry(
        id='vous_avez_un_trou_dans_votre',
        question="Vous avez un trou dans votre CV. C'était pour raison de santé ?",
        answer="« C'était une période sans poste, elle est derrière moi. Ce qui compte pour ce poste, c'est <COMPÉTENCE>, et je l'ai gardée. »",
        avoid="ne confirmez ni n'infirmez la santé. La question porte sur le trou, répondez sur le trou.",
    ),
    BankEntry(
        id='vous_avez_le_permis_une_voiture',
        question='Vous avez le permis ? Une voiture ?',
        answer="« Si le poste demande des déplacements, je peux vous dire comment je m'organise : <CE_QUE_J_AI_FAIT>. »",
        avoid='ne répondez sur le permis que si la mobilité fait partie du poste. Sinon, faites préciser à quoi ça sert.',
    ),
    BankEntry(
        id='pourquoi_devrais_je_vous_croire',
        question='Pourquoi devrais-je vous croire ?',
        answer="« Vous n'avez pas à me croire sur parole. Sur <RÉALISATION>, <PRÉNOM> de <ENTREPRISE_PRÉCÉDENTE> peut vous le confirmer. »",
        avoid="ne montez pas d'un ton et ne vous excusez pas. La question teste votre calme.",
    ),
]

ETAPES: list[BankEntry] = [
    BankEntry(
        id='parlez_moi_de_vous_prequalification_telephonique',
        question='Parlez-moi de vous. — Préqualification téléphonique, RH',
        answer="« Je suis <MÉTIER> depuis <NOMBRE_ANNÉES_EXPÉRIENCE>, aujourd'hui <POSTE_ACTUEL> chez <ENTREPRISE_ACTUELLE>. Je cherche <POSTE_VISÉ>, et je suis disponible sous <PRÉAVIS>. »",
        avoid='ne développez pas. Ce coup de fil dure vingt minutes et sert à vérifier trois choses : cohérence, disponibilité, fourchette.',
    ),
    BankEntry(
        id='parlez_moi_de_vous_entretien_avec',
        question='Parlez-moi de vous. — Entretien avec le manager',
        answer="« Concrètement, ce que je fais c'est <CE_QUE_J_AI_FAIT>. Le plus proche de votre besoin, c'est <RÉALISATION> : <RÉSULTAT>. »",
        avoid="ne refaites pas votre CV chronologique. Le manager veut savoir ce que vous savez faire, pas d'où vous venez.",
    ),
    BankEntry(
        id='parlez_moi_de_vous_entretien_final',
        question='Parlez-moi de vous. — Entretien final, direction',
        answer="« En deux mots mon métier, et ce que je viens apporter : <COMPÉTENCE>, sur un périmètre comme <POSTE_VISÉ>. Ce qui m'intéresse chez vous, c'est <CE_QUI_VOUS_ATTIRE>. »",
        avoid='ne redites pas ce que vous avez dit au manager. La direction a lu le compte rendu.',
    ),
    BankEntry(
        id='pourquoi_ce_poste_chez_nous_entretien',
        question='Pourquoi ce poste, chez nous ? — Entretien RH',
        answer="« <MISSION_DE_L_OFFRE> correspond à ce que je fais déjà. Et ce que je cherche maintenant, c'est <CE_QUI_VOUS_ATTIRE>. »",
        avoid="ne parlez pas de la stratégie de l'entreprise avec les RH. Restez sur la cohérence de votre parcours.",
    ),
    BankEntry(
        id='pourquoi_ce_poste_chez_nous_entretien_2',
        question='Pourquoi ce poste, chez nous ? — Entretien final, direction',
        answer="« Sur <MISSION_DE_L_OFFRE>, j'ai <RÉALISATION>. Et ce que je vois de votre côté, c'est <CE_QUI_VOUS_ATTIRE> — c'est là que je pense être utile. »",
        avoid="ne répétez pas la réponse donnée aux RH. Montrez que vous avez compris l'enjeu de l'entreprise, pas seulement du poste.",
    ),
    BankEntry(
        id='quelles_sont_vos_pretentions_prequalification_telephonique',
        question='Quelles sont vos prétentions ? — Préqualification téléphonique',
        answer="« À ce stade je n'ai pas tout le périmètre. Ma fourchette est large : entre <PRÉTENTION_BASSE> et <PRÉTENTION_HAUTE>. On affinera quand j'en saurai plus. »",
        avoid='ne donnez pas votre chiffre exact au téléphone. Tout ce que vous dites là devient votre plafond pour la suite.',
    ),
    BankEntry(
        id='quelles_sont_vos_pretentions_entretien_rh',
        question='Quelles sont vos prétentions ? — Entretien RH',
        answer='« Entre <PRÉTENTION_BASSE> et <PRÉTENTION_HAUTE>, selon le périmètre exact. Quelle est la fourchette prévue de votre côté ? »',
        avoid="ne posez la question en retour qu'une fois. Insister deux fois passe pour un bras de fer.",
    ),
    BankEntry(
        id='quelles_sont_vos_pretentions_au_moment',
        question="Quelles sont vos prétentions ? — Au moment de l'offre",
        answer="« Nous étions partis sur <PRÉTENTION_HAUTE>. Si ce n'est pas possible, regardons <AVANTAGE> — avec ça je signe. »",
        avoid="n'acceptez pas dans la conversation. Demandez la proposition par écrit et une nuit pour décider.",
    ),
    BankEntry(
        id='pourquoi_quittez_vous_votre_poste_entretien',
        question='Pourquoi quittez-vous votre poste ? — Entretien RH',
        answer="« J'ai fait chez <ENTREPRISE_ACTUELLE> ce que je voulais y faire, notamment <RÉALISATION>. La suite que je cherche n'y existe pas. »",
        avoid="pas un mot négatif. Les RH cherchent un signal d'alerte, ne leur en donnez aucun.",
    ),
    BankEntry(
        id='pourquoi_quittez_vous_votre_poste_entretien_2',
        question='Pourquoi quittez-vous votre poste ? — Entretien avec le manager',
        answer="« Ce que je ne peux plus faire là-bas, c'est <CE_QUI_VOUS_ATTIRE>. Concrètement ça veut dire <CE_QUE_J_AI_FAIT>, et c'est ce que votre poste permet. »",
        avoid="restez sur le contenu du travail. Le manager s'intéresse à ce que vous voulez faire, pas à votre historique RH.",
    ),
    BankEntry(
        id='quels_sont_vos_points_forts_entretien',
        question='Quels sont vos points forts ? — Entretien RH',
        answer="« <COMPÉTENCE>. C'est ce qui a fait la différence sur <RÉALISATION>. »",
        avoid="n'employez pas de mots de personnalité — rigoureux, dynamique. Nommez une compétence de travail.",
    ),
    BankEntry(
        id='quels_sont_vos_points_forts_entretien_2',
        question='Quels sont vos points forts ? — Entretien technique',
        answer='« <COMPÉTENCE>, avec <OUTIL>. Sur <RÉALISATION>, <CE_QUE_J_AI_FAIT>, et <RÉSULTAT>. »',
        avoid="n'annoncez pas une maîtrise que la question suivante démontera. Ici tout est vérifié dans la minute.",
    ),
    BankEntry(
        id='quel_est_votre_principal_defaut_entretien',
        question='Quel est votre principal défaut ? — Entretien RH',
        answer="« <POINT_À_AMÉLIORER>. Ce que j'ai mis en place, c'est <CE_QUE_J_AI_FAIT>. »",
        avoid="le faux défaut est immédiatement repéré par un RH. C'est son métier.",
    ),
    BankEntry(
        id='racontez_une_situation_difficile_entretien_avec',
        question='Racontez une situation difficile. — Entretien avec le manager',
        answer="« Sur <RÉALISATION>, <DIFFICULTÉ>. J'ai <CE_QUE_J_AI_FAIT>, et <RÉSULTAT>. »",
        avoid='choisissez une difficulté opérationnelle, proche de ce que fait son équipe. Il évalue si vous tiendrez son quotidien.',
    ),
    BankEntry(
        id='racontez_une_situation_difficile_entretien_final',
        question='Racontez une situation difficile. — Entretien final, direction',
        answer="« Sur <RÉALISATION>, il a fallu arbitrer entre <DIFFICULTÉ>. J'ai tranché pour <CE_QUE_J_AI_FAIT>, en assumant <RÉSULTAT>. »",
        avoid="ne racontez pas un problème d'exécution à un directeur. Choisissez un arbitrage, avec son coût.",
    ),
    BankEntry(
        id='ou_vous_voyez_vous_dans_trois_2',
        question='Où vous voyez-vous dans trois ans ? — Entretien RH',
        answer='« Solide sur <COMPÉTENCE>, avec un périmètre proche de <POSTE_VISÉ>. »',
        avoid="n'annoncez pas que vous visez plus haut que le poste proposé. Les RH y entendent un risque de départ.",
    ),
    BankEntry(
        id='ou_vous_voyez_vous_dans_trois_3',
        question='Où vous voyez-vous dans trois ans ? — Entretien final, direction',
        answer='« Je veux avoir fait grandir <POSTE_VISÉ> et pouvoir prendre <CE_QUI_VOUS_ATTIRE>. »',
        avoid="ne soyez pas trop modeste ici. La direction recrute quelqu'un qui a une trajectoire.",
    ),
    BankEntry(
        id='que_savez_vous_de_nous_entretien',
        question='Que savez-vous de nous ? — Entretien RH',
        answer="« <CE_QUI_VOUS_ATTIRE>, et <MISSION_DE_L_OFFRE> dans l'annonce. »",
        avoid='deux phrases suffisent. Les RH vérifient que vous avez regardé, pas que vous avez étudié.',
    ),
    BankEntry(
        id='que_savez_vous_de_nous_entretien_2',
        question='Que savez-vous de nous ? — Entretien final, direction',
        answer="« Ce que je comprends de votre situation, c'est <CE_QUI_VOUS_ATTIRE>. Ce qui me semble difficile pour vous, c'est <DIFFICULTÉ>. »",
        avoid='ne récitez pas des chiffres publics. Dites ce que vous en déduisez.',
    ),
    BankEntry(
        id='avez_vous_des_questions_entretien_rh',
        question='Avez-vous des questions ? — Entretien RH',
        answer="« Quelles sont les étapes suivantes, et sur quel calendrier ? Et comment l'équipe est-elle composée aujourd'hui ? »",
        avoid="ne posez pas de question stratégique aux RH, ils n'ont pas la réponse et ça crée un malaise.",
    ),
    BankEntry(
        id='avez_vous_des_questions_entretien_avec',
        question='Avez-vous des questions ? — Entretien avec le manager',
        answer="« Qu'est-ce qui est le plus difficile dans ce poste aujourd'hui ? Et qu'est-ce qui ferait qu'à six mois vous seriez content de votre choix ? »",
        avoid="ne demandez pas ce qui est déjà dans l'annonce.",
    ),
    BankEntry(
        id='avez_vous_des_questions_entretien_final',
        question='Avez-vous des questions ? — Entretien final, direction',
        answer="« Où voulez-vous que <ÉQUIPE_VISÉE> soit dans deux ans ? Et qu'est-ce qui pourrait empêcher d'y arriver ? »",
        avoid="ne posez pas de question sur le salaire ou les congés à ce niveau, sauf si la personne l'ouvre.",
    ),
    BankEntry(
        id='faisons_le_bilan_de_vos_objectifs',
        question='Faisons le bilan de vos objectifs. — Face à votre manager direct',
        answer="« <OBJECTIF> : <AVANCEMENT>. <OBJECTIF_2> : <AVANCEMENT_2>. Ce que j'en retire, c'est <POINT_À_AMÉLIORER>. »",
        avoid="ne cachez pas ce qu'il sait déjà. Il a vu l'année, l'entretien n'est pas une découverte.",
    ),
    BankEntry(
        id='faisons_le_bilan_de_vos_objectifs_2',
        question='Faisons le bilan de vos objectifs. — Face au N+2 ou aux RH, en calibration',
        answer='« Les faits : <CHIFFRE> sur <OBJECTIF>. Le contexte : <DIFFICULTÉ>. »',
        avoid="ne supposez pas qu'ils connaissent votre année. Donnez les faits avant les nuances.",
    ),
    BankEntry(
        id='pourquoi_cette_mobilite_face_au_manager',
        question="Pourquoi cette mobilité ? — Face au manager de l'équipe visée",
        answer="« Ce que je viens chercher, c'est <CE_QUI_VOUS_ATTIRE>. Ce que j'apporte, c'est <COMPÉTENCE> — sur <RÉALISATION>, <RÉSULTAT>. »",
        avoid='ne parlez pas de ce qui ne va pas dans votre équipe actuelle. Il se demanderait ce que vous direz de la sienne.',
    ),
    BankEntry(
        id='pourquoi_cette_mobilite_face_a_votre',
        question='Pourquoi cette mobilité ? — Face à votre manager actuel',
        answer="« Je ne pars pas contre toi. Ce que je veux construire, c'est <COMPÉTENCE>, et ça se fait là-bas. Voilà ce que je propose pour la passation : <CE_QUE_J_AI_FAIT>. »",
        avoid="n'annoncez pas la nouvelle sans avoir pensé à la passation. C'est la première chose à laquelle il pensera.",
    ),
    BankEntry(
        id='pourquoi_cette_mobilite_face_aux_rh',
        question='Pourquoi cette mobilité ? — Face aux RH',
        answer="« Le poste correspond à <COMPÉTENCE> et à ce que je veux construire. J'ai prévenu <PRÉNOM>, et la passation est cadrée. »",
        avoid='les RH vérifient surtout que le processus est propre. Rassurez sur la forme autant que sur le fond.',
    ),
]

RECRUTEMENT: list[BankEntry] = [
    BankEntry(
        id='pourquoi_ce_poste_chez_nous',
        question='Pourquoi ce poste, chez nous ?',
        answer="« Dans l'annonce, ce qui m'a arrêté c'est <MISSION_DE_L_OFFRE>. Je l'ai déjà fait sur <RÉALISATION>, où <RÉSULTAT>. Et ce qui m'attire chez vous, c'est <CE_QUI_VOUS_ATTIRE>. »",
        avoid="ne dites pas « votre culture d'entreprise » sans nommer ce que vous avez lu ou entendu.",
    ),
    BankEntry(
        id='pourquoi_quittez_vous_votre_poste_actuel',
        question='Pourquoi quittez-vous votre poste actuel ?',
        answer="« Chez <ENTREPRISE_ACTUELLE> j'ai <RÉALISATION>. Ce que je ne peux plus y faire, c'est <CE_QUI_VOUS_ATTIRE> — et c'est précisément ce que propose ce poste. »",
        avoid='aucun reproche à votre employeur actuel, même mérité. On entend la critique, pas le contexte.',
    ),
    BankEntry(
        id='quelles_sont_vos_pretentions_salariales',
        question='Quelles sont vos prétentions salariales ?',
        answer='« Je me situe entre <PRÉTENTION_BASSE> et <PRÉTENTION_HAUTE>, selon le périmètre exact du poste. »',
        follow_up='Si on insiste : « Quelle est la fourchette prévue pour ce poste ? » — puis laissez le silence.',
        avoid="ne donnez pas un chiffre unique, il devient un plafond. Et jamais de chiffre avant d'avoir entendu le périmètre.",
    ),
    BankEntry(
        id='combien_gagnez_vous_actuellement',
        question='Combien gagnez-vous actuellement ?',
        answer="« Mon package actuel n'est pas le sujet : ce que je vise pour ce poste, c'est entre <PRÉTENTION_BASSE> et <PRÉTENTION_HAUTE>. »",
        follow_up='Si vous choisissez de le dire : « Je suis à <SALAIRE_ACTUEL>, et je vise <PRÉTENTION_BASSE> minimum pour ce poste. »',
        avoid="vous n'êtes pas obligé de répondre, mais éluder deux fois se paie en climat. Redirigez une fois, puis tranchez.",
    ),
    BankEntry(
        id='on_ne_peut_pas_aller_au',
        question='On ne peut pas aller au-delà de ce montant.',
        answer="« J'entends. Est-ce qu'on peut regarder <AVANTAGE> ? Avec ça, je peux avancer. »",
        avoid="n'acceptez pas dans la seconde, et ne refusez jamais sans contre-proposition. Demandez à y réfléchir jusqu'au lendemain.",
    ),
    BankEntry(
        id='vous_avez_une_periode_sans_emploi',
        question="Vous avez une période sans emploi entre deux postes. Que s'est-il passé ?",
        answer="« Entre <ENTREPRISE_PRÉCÉDENTE> et <ENTREPRISE_ACTUELLE>, j'ai eu <ANCIENNETÉ> sans poste. <CE_QUE_J_AI_FAIT>. Ce qui compte pour ce poste, c'est <COMPÉTENCE>, et je l'ai gardée. »",
        avoid="ne meublez pas. Une période assumée en une phrase passe mieux qu'une justification en cinq.",
    ),
    BankEntry(
        id='pourquoi_ce_changement_de_metier_ou',
        question='Pourquoi ce changement de métier ou de secteur ?',
        answer="« Je viens de <POSTE_PRÉCÉDENT>. Ce qui se transpose, c'est <COMPÉTENCE> — sur <RÉALISATION>, <RÉSULTAT>. Ce que je viens chercher ici, c'est <CE_QUI_VOUS_ATTIRE>. »",
        avoid='ne présentez pas la reconversion comme une rupture. Cherchez le fil, il existe presque toujours.',
    ),
    BankEntry(
        id='que_savez_vous_de_notre_entreprise',
        question='Que savez-vous de notre entreprise ?',
        answer="« <CE_QUI_VOUS_ATTIRE>. Et dans l'annonce, <MISSION_DE_L_OFFRE> m'a paru central. »",
        avoid='ne récitez pas la page « À propos ». Une chose précise et vraie vaut mieux que trois génériques.',
    ),
    BankEntry(
        id='pourquoi_vous_et_pas_un_autre',
        question='Pourquoi vous et pas un autre candidat ?',
        answer="« Je ne sais pas qui vous voyez d'autre. Ce que je peux dire, c'est que <MISSION_DE_L_OFFRE>, je l'ai déjà fait : <RÉALISATION>, <RÉSULTAT>. »",
        avoid='ne vous comparez pas à des gens que vous ne connaissez pas. Répondez sur vous.',
    ),
    BankEntry(
        id='cette_mission_de_l_annonce_vous',
        question="Cette mission de l'annonce, vous ne l'avez jamais faite. Comment ferez-vous ?",
        answer="« C'est exact, je ne l'ai pas encore faite. Le plus proche que j'aie fait, c'est <RÉALISATION>. Ce que j'y transpose, c'est <COMPÉTENCE>, et ce que je devrai apprendre, c'est <POINT_À_AMÉLIORER>. »",
        avoid="ne prétendez pas l'avoir déjà fait. La vérification est immédiate et le mensonge coûte le poste.",
    ),
    BankEntry(
        id='quelles_sont_vos_disponibilites',
        question='Quelles sont vos disponibilités ?',
        answer='« Je suis à <ANCIENNETÉ> chez <ENTREPRISE_ACTUELLE>, avec un préavis de <AVANTAGE>. Je peux commencer sous ce délai, et je suis souple sur la date exacte. »',
        avoid='ne promettez pas un délai que votre préavis ne permet pas. Ça se sait.',
    ),
    BankEntry(
        id='comment_vous_adaptez_vous_a_un',
        question='Comment vous adaptez-vous à un nouvel environnement ?',
        answer="« Quand je suis arrivé chez <ENTREPRISE_ACTUELLE>, <CE_QUE_J_AI_FAIT> pendant les premières semaines. Ça m'a permis de <RÉSULTAT>. »",
        avoid="« je m'adapte vite » sans exemple ne convainc personne.",
    ),
    BankEntry(
        id='qu_attendez_vous_d_un_manager',
        question="Qu'attendez-vous d'un manager ?",
        answer="« Qu'il soit clair sur ce qu'il attend et qu'il tranche quand il faut. Chez <ENTREPRISE_ACTUELLE>, ce qui m'a le plus aidé, c'est <CE_QUE_J_AI_FAIT>. »",
        avoid="ne décrivez pas l'inverse de votre manager actuel. Ça s'entend, et ça vous dessert.",
    ),
    BankEntry(
        id='comment_envisagez_vous_le_teletravail',
        question='Comment envisagez-vous le télétravail ?',
        answer="« Ce qui compte pour moi, c'est <AVANTAGE>. Je m'adapte à votre rythme dès lors que c'est clair dès le départ. »",
        avoid="n'en faites pas une condition avant d'avoir l'offre, sauf si c'en est vraiment une.",
    ),
    BankEntry(
        id='pouvons_nous_contacter_vos_references',
        question='Pouvons-nous contacter vos références ?',
        answer="« Oui. <PRÉNOM> chez <ENTREPRISE_PRÉCÉDENTE> peut parler de <RÉALISATION>. Je le préviens dès aujourd'hui. »",
        avoid="ne donnez jamais une référence sans l'avoir prévenue.",
    ),
    BankEntry(
        id='avez_vous_d_autres_processus_en',
        question="Avez-vous d'autres processus en cours ?",
        answer='« Oui, deux autres, à des stades différents. Celui-ci est celui qui correspond le mieux à <CE_QUI_VOUS_ATTIRE>. »',
        avoid="ne mentez pas en disant non — ça vous prive de tout levier. N'exagérez pas non plus, on vérifie.",
    ),
]

MOBILITE: list[BankEntry] = [
    BankEntry(
        id='pourquoi_voulez_vous_quitter_votre_equipe',
        question='Pourquoi voulez-vous quitter votre équipe actuelle ?',
        answer="« Sur <POSTE_ACTUEL>, j'ai <RÉALISATION>. Je ne pars pas contre quelque chose : ce que je veux faire maintenant, c'est <CE_QUI_VOUS_ATTIRE>, et c'est dans <ÉQUIPE_VISÉE> que ça se passe. »",
        avoid='aucun reproche à votre équipe actuelle. En interne, ce que vous dites revient toujours à leurs oreilles.',
    ),
    BankEntry(
        id='comment_votre_manager_actuel_prend_il',
        question='Comment votre manager actuel prend-il cette démarche ?',
        answer='« Je lui en ai parlé. <CE_QUE_J_AI_FAIT> pour que la transition se passe bien. »',
        avoid="ne dites jamais qu'il n'est pas au courant. Une mobilité cachée qui se découvre coûte les deux postes.",
    ),
    BankEntry(
        id='qu_apporteriez_vous_a_cette_equipe',
        question="Qu'apporteriez-vous à cette équipe ?",
        answer="« <COMPÉTENCE>, que j'ai construite sur <RÉALISATION>. Et je connais déjà <ENTREPRISE_ACTUELLE> : je n'ai pas besoin de six mois pour comprendre comment ça marche ici. »",
        avoid='ne survendez pas la connaissance interne, elle ne remplace pas le métier visé.',
    ),
    BankEntry(
        id='comment_assurerez_vous_la_passation',
        question='Comment assurerez-vous la passation ?',
        answer="« Sur <RÉALISATION>, ce qui doit continuer, c'est <CE_QUE_J_AI_FAIT>. Je propose <AVANTAGE> de recouvrement et une passation écrite. »",
        avoid="ne dites pas « je m'organiserai ». Proposez un délai et un livrable.",
    ),
    BankEntry(
        id='que_connaissez_vous_des_enjeux_de',
        question='Que connaissez-vous des enjeux de cette équipe ?',
        answer="« <CE_QUI_VOUS_ATTIRE>. J'ai échangé avec <PRÉNOM> pour comprendre ce qui bloque aujourd'hui. »",
        avoid="ne prétendez pas connaître ce que vous n'avez pas vérifié. En interne, c'est vérifiable en un message.",
    ),
    BankEntry(
        id='pourquoi_ce_site_cette_localisation',
        question='Pourquoi ce site, cette localisation ?',
        answer="« Le poste est à <SITE_VISÉ>. Ce qui m'y amène, c'est <CE_QUI_VOUS_ATTIRE>, et j'ai réglé la question pratique. »",
        avoid="ne laissez pas planer de doute sur votre capacité à être sur place. C'est la première inquiétude en face.",
    ),
    BankEntry(
        id='que_ferez_vous_si_cette_mobilite',
        question='Que ferez-vous si cette mobilité vous est refusée ?',
        answer="« Je continuerai sur <POSTE_ACTUEL>, et je referai une demande. Ce que je veux construire, c'est <COMPÉTENCE>, et il y a plusieurs chemins. »",
        avoid="ne menacez jamais de partir. C'est perçu comme un chantage et ça ferme la porte pour longtemps.",
    ),
    BankEntry(
        id='qu_est_ce_qui_vous_rend',
        question="Qu'est-ce qui vous rend légitime sur un métier que vous n'avez pas exercé ?",
        answer="« Je ne l'ai pas exercé. Ce que j'apporte, c'est <COMPÉTENCE> — sur <RÉALISATION>, <RÉSULTAT>. Ce que je devrai apprendre, c'est <POINT_À_AMÉLIORER>, et j'ai prévu <CE_QUE_J_AI_FAIT>. »",
        avoid="ne minimisez pas l'écart. Le nommer vous-même vous rend crédible.",
    ),
    BankEntry(
        id='quel_calendrier_envisagez_vous',
        question='Quel calendrier envisagez-vous ?',
        answer="« Je peux basculer sous <AVANTAGE>, avec un recouvrement si nécessaire. Le point dur, c'est <DIFFICULTÉ> — je propose de le traiter avant. »",
        avoid="n'annoncez pas une date que votre équipe actuelle ne pourra pas absorber.",
    ),
    BankEntry(
        id='le_poste_vise_est_au_meme',
        question='Le poste visé est au même niveau. Est-ce un problème pour vous ?',
        answer="« Non, si le périmètre change. Ce que je veux, c'est <CE_QUI_VOUS_ATTIRE>. Sur la rémunération, je vise <AUGMENTATION_DEMANDÉE> à terme, pas forcément tout de suite. »",
        avoid="ne dites pas que le salaire est indifférent si c'est faux. Vous ne pourrez plus le rouvrir ensuite.",
    ),
    BankEntry(
        id='qu_est_ce_que_vous_laissez',
        question="Qu'est-ce que vous laissez inachevé ?",
        answer="« <RÉALISATION> n'est pas terminé. Voilà où ça en est, et voilà ce que je propose pour que ça continue : <CE_QUE_J_AI_FAIT>. »",
        avoid='ne dites pas « rien ». Personne ne part sans laisser quelque chose, et le prétendre décrédibilise le reste.',
    ),
    BankEntry(
        id='vous_connaissez_deja_les_gens_de',
        question='Vous connaissez déjà les gens de cette équipe. Est-ce un avantage ?',
        answer="« Oui pour aller vite, mais je repars du même point qu'un externe sur <COMPÉTENCE>. Je ne compte pas sur la familiarité. »",
        avoid='ne vous appuyez pas sur les relations. Ça inquiète plus que ça ne rassure.',
    ),
]

EVOLUTION: list[BankEntry] = [
    BankEntry(
        id='qu_est_ce_qui_vous_fait',
        question="Qu'est-ce qui vous fait penser que vous êtes prêt ?",
        answer='« Je fais déjà <CE_QUE_J_AI_FAIT> sans que ce soit dans ma fiche de poste. Sur <RÉALISATION>, <RÉSULTAT>. »',
        avoid="ne parlez pas de potentiel ni d'envie. Une évolution s'accorde sur du fait, pas sur de la promesse.",
    ),
    # Remplacée : l'ancienne « Que faites-vous déjà du poste visé ? » redisait
    # « Qu'est-ce qui vous fait penser que vous êtes prêt ? » — même substance,
    # même gabarit. La question du calendrier, elle, n'était couverte nulle part.
    BankEntry(
        id='pourquoi_maintenant_et_pas_dans_un',
        question='Pourquoi maintenant, et pas dans un an ?',
        answer="« Parce que depuis <ANCIENNETÉ>, je fais déjà <CE_QUE_J_AI_FAIT>. Attendre un an, c'est un an de plus à tenir le poste sans le titre — et sans les moyens qui vont avec. »",
        avoid="ne répondez pas par l'impatience ni par une comparaison avec un collègue promu. Le calendrier se défend par les faits, pas par le sentiment d'injustice.",
    ),
    BankEntry(
        id='qu_est_ce_qui_changerait_concretement',
        question="Qu'est-ce qui changerait concrètement dans votre travail ?",
        answer="« Aujourd'hui je <CE_QUE_J_AI_FAIT>. Demain, ce serait <POSTE_VISÉ> : la différence, c'est <DIFFICULTÉ> et l'arbitrage que ça suppose. »",
        avoid="ne réduisez pas l'évolution à un titre ou à un salaire. Décrivez le changement de nature du travail.",
    ),
    BankEntry(
        id='comment_gererez_vous_d_encadrer_d',
        question="Comment gérerez-vous d'encadrer d'anciens pairs ?",
        answer="« En posant le cadre tout de suite, et en le disant. Sur <RÉALISATION>, j'ai déjà eu à <CE_QUE_J_AI_FAIT> avec des gens de mon niveau. »",
        avoid="ne dites pas « ça se passera bien ». C'est la difficulté numéro un de la promotion interne, et la minimiser inquiète.",
    ),
    BankEntry(
        id='qu_est_ce_qui_vous_manque',
        question="Qu'est-ce qui vous manque encore ?",
        answer="« <POINT_À_AMÉLIORER>. J'ai commencé à le travailler : <CE_QUE_J_AI_FAIT>. »",
        avoid="ne répondez pas « rien ». Vous confirmeriez précisément le doute qu'on a sur votre maturité.",
    ),
    BankEntry(
        id='nous_ne_sommes_pas_prets_a',
        question='Nous ne sommes pas prêts à vous donner ce poste maintenant.',
        answer="« Qu'est-ce qui manque, concrètement ? Si on fixe deux critères et une échéance, je m'y engage et on refait le point. »",
        avoid="n'acceptez pas un « pas encore » sans critères. Sans critères, la même conversation aura lieu dans un an.",
    ),
    BankEntry(
        id='quelles_preuves_chiffrees_pouvez_vous_avancer',
        question='Quelles preuves chiffrées pouvez-vous avancer ?',
        answer='« <CHIFFRE> sur <RÉALISATION>. Et <RÉSULTAT>, qui est vérifiable auprès de <PRÉNOM>. »',
        avoid="n'inventez pas un chiffre. En interne il sera vérifié, et cette fois-ci sans indulgence.",
    ),
    BankEntry(
        id='quelle_augmentation_demandez_vous',
        question='Quelle augmentation demandez-vous ?',
        answer='« Je vise <AUGMENTATION_DEMANDÉE>, cohérent avec <POSTE_VISÉ>. Je suis prêt à en discuter le calendrier. »',
        avoid="ne demandez pas l'évolution et l'augmentation dans la même phrase. Obtenez le périmètre d'abord.",
    ),
    BankEntry(
        id='quelle_est_votre_vision_pour_ce',
        question='Quelle est votre vision pour ce périmètre ?',
        answer="« Deux choses : <CE_QUE_J_AI_FAIT> d'abord, parce que <DIFFICULTÉ>. Puis <RÉALISATION>. »",
        avoid='ne proposez pas un plan de transformation. On attend des priorités, pas une révolution.',
    ),
    BankEntry(
        id='qui_vous_soutient_dans_cette_demarche',
        question='Qui vous soutient dans cette démarche ?',
        answer="« <PRÉNOM> connaît mon travail sur <RÉALISATION>. J'ai aussi échangé avec <ÉQUIPE_VISÉE>. »",
        avoid="ne citez personne que vous n'avez pas prévenu.",
    ),
]

ANNUEL: list[BankEntry] = [
    BankEntry(
        id='faisons_le_bilan_de_vos_objectifs_3',
        question='Faisons le bilan de vos objectifs.',
        answer="« <OBJECTIF> : <AVANCEMENT>. <OBJECTIF_2> : <AVANCEMENT_2>. Celui sur lequel j'ai le plus appris, c'est <RÉALISATION>. »",
        avoid="ne commencez pas par celui qui n'est pas atteint. Donnez l'ensemble, puis creusez.",
    ),
    BankEntry(
        id='cet_objectif_n_a_pas_ete',
        question="Cet objectif n'a pas été atteint. Que s'est-il passé ?",
        answer="« Non, <AVANCEMENT>. Ce qui a joué, c'est <DIFFICULTÉ>. Ce qui dépendait de moi, c'est <CE_QUE_J_AI_FAIT>, et voilà ce que je ferais autrement. »",
        avoid="ne mettez pas tout sur le contexte, même quand c'est vrai. Séparez ce qui dépendait de vous du reste.",
    ),
    BankEntry(
        id='quelle_est_votre_plus_grande_reussite',
        question="Quelle est votre plus grande réussite de l'année ?",
        answer='« <RÉALISATION>. <CE_QUE_J_AI_FAIT>, et <RÉSULTAT> — <CHIFFRE>. »',
        avoid="n'en citez qu'une. Trois réussites diluent, une seule s'imprime.",
    ),
    BankEntry(
        id='qu_est_ce_qui_vous_a',
        question="Qu'est-ce qui vous a freiné cette année ?",
        answer="« <DIFFICULTÉ>. J'ai <CE_QUE_J_AI_FAIT> pour le contourner, mais ça a coûté du temps sur <OBJECTIF>. »",
        avoid="ne transformez pas ça en plainte. Un frein nommé une fois est une information ; répété, c'est une posture.",
    ),
    BankEntry(
        id='quels_objectifs_vous_fixez_vous_pour',
        question="Quels objectifs vous fixez-vous pour l'an prochain ?",
        answer='« <OBJECTIF>, mesuré par <CHIFFRE>. Et je veux progresser sur <COMPÉTENCE>, ce qui suppose <CE_QUE_J_AI_FAIT>. »',
        avoid="ne proposez pas des objectifs sans indicateur. Ils vous seront reprochés flous l'an prochain.",
    ),
    BankEntry(
        id='de_quoi_avez_vous_besoin',
        question='De quoi avez-vous besoin ?',
        answer="« Pour tenir <OBJECTIF>, j'ai besoin de <AVANTAGE>. Sans ça, le risque est <DIFFICULTÉ>. »",
        avoid="ne demandez pas « plus de moyens ». Nommez une chose précise et ce qu'elle débloque.",
    ),
    BankEntry(
        id='comment_jugez_vous_votre_performance_cette',
        question='Comment jugez-vous votre performance cette année ?',
        answer='« Solide sur <OBJECTIF>, avec <CHIFFRE>. En retrait sur <POINT_À_AMÉLIORER>, et je sais pourquoi. »',
        avoid='ni auto-flagellation ni autosatisfaction. Une note haute et une note basse, assumées.',
    ),
    BankEntry(
        id='comment_voyez_vous_la_suite_pour',
        question='Comment voyez-vous la suite pour vous ?',
        answer="« À moyen terme, <POSTE_VISÉ>. Cette année, ce que je veux construire, c'est <COMPÉTENCE>. »",
        avoid="ne demandez pas une promotion dans l'entretien annuel si le sujet n'est pas ouvert. Posez le jalon, négociez ailleurs.",
    ),
    BankEntry(
        id='avez_vous_un_retour_a_me',
        question='Avez-vous un retour à me faire sur mon management ?',
        answer="« Ce qui m'aide, c'est <CE_QUE_J_AI_FAIT>. Ce qui m'aiderait davantage, c'est <AVANTAGE>. »",
        avoid="ne dites pas « tout va bien » si ce n'est pas vrai, mais ne videz pas votre sac. Une demande, pas un procès.",
    ),
    BankEntry(
        id='je_ne_suis_pas_d_accord',
        question="Je ne suis pas d'accord avec votre auto-évaluation.",
        answer="« D'accord. Sur quoi précisément ? Moi je m'appuyais sur <RÉALISATION> et <CHIFFRE>. »",
        avoid='ne cédez pas immédiatement, et ne vous braquez pas. Demandez le fait sur lequel repose le désaccord.',
    ),
    BankEntry(
        id='comment_est_votre_charge_de_travail',
        question='Comment est votre charge de travail ?',
        answer="« Tenable, avec <DIFFICULTÉ> sur <OBJECTIF>. Si <AVANTAGE> ne bouge pas, l'an prochain sera plus dur. »",
        avoid="ne dites pas « ça va » par réflexe si ce n'est pas vrai. C'est le seul moment de l'année où c'est écoutable.",
    ),
    BankEntry(
        id='quelle_formation_souhaitez_vous',
        question='Quelle formation souhaitez-vous ?',
        answer='« <COMPÉTENCE>, parce que <OBJECTIF> en dépend directement. »',
        avoid="ne demandez pas une formation sans la relier à un objectif. Elle passe en dernier dans l'arbitrage budgétaire.",
    ),
]

MI_ANNEE: list[BankEntry] = [
    BankEntry(
        id='ou_en_etes_vous_de_vos',
        question='Où en êtes-vous de vos objectifs ?',
        answer='« <OBJECTIF> : <AVANCEMENT>. À ce rythme, il sera tenu. <OBJECTIF_2> : <AVANCEMENT_2>, et là je ne suis pas certain. »',
        avoid='ne lissez pas. Un point de mi-année sert à signaler, pas à rassurer.',
    ),
    BankEntry(
        id='qu_est_ce_qui_ne_sera',
        question="Qu'est-ce qui ne sera pas tenu ?",
        answer="« <OBJECTIF>, probablement pas dans la forme prévue. La cause, c'est <DIFFICULTÉ>. Ce que je propose : <CE_QUE_J_AI_FAIT>. »",
        avoid="ne repoussez pas l'annonce à décembre. À mi-année c'est un ajustement, en décembre c'est un échec.",
    ),
    BankEntry(
        id='que_faut_il_ajuster',
        question='Que faut-il ajuster ?',
        answer="« Je propose de décaler <OBJECTIF> et de renforcer <OBJECTIF_2>. Ce que ça suppose, c'est <AVANTAGE>. »",
        avoid="ne proposez pas d'abandonner sans contrepartie. Un arbitrage se présente en échange, pas en renoncement.",
    ),
    BankEntry(
        id='de_quoi_avez_vous_besoin_pour',
        question='De quoi avez-vous besoin pour le second semestre ?',
        answer="« <AVANTAGE>, pour tenir <OBJECTIF>. Sinon, l'arbitrage sera <DIFFICULTÉ>. »",
        avoid="ne demandez rien. Ne rien demander à mi-année vaut acceptation des conditions actuelles jusqu'à décembre.",
    ),
    BankEntry(
        id='qu_est_ce_qui_a_change',
        question="Qu'est-ce qui a changé depuis le début de l'année ?",
        answer="« <DIFFICULTÉ> n'était pas prévu. Ça déplace <OBJECTIF>, et voilà comment j'ai réagi : <CE_QUE_J_AI_FAIT>. »",
        avoid='ne présentez pas le changement comme une excuse préparée. Décrivez le fait, puis votre réaction.',
    ),
    BankEntry(
        id='quelle_priorite_seriez_vous_pret_a',
        question='Quelle priorité seriez-vous prêt à abandonner ?',
        answer="« <OBJECTIF_2>, si <OBJECTIF> doit tenir. C'est le moins coûteux à décaler parce que <DIFFICULTÉ>. »",
        avoid="ne répondez pas « aucune ». Refuser d'arbitrer fait arbitrer à votre place.",
    ),
    BankEntry(
        id='y_a_t_il_un_signal',
        question="Y a-t-il un signal d'alerte à me donner ?",
        answer="« Oui : <DIFFICULTÉ>. Ça n'a pas encore d'effet visible, mais si rien ne bouge d'ici <AVANTAGE>, ça touchera <OBJECTIF>. »",
        avoid='ne gardez pas une alerte pour vous par crainte de paraître négatif. Une alerte tue est toujours reprochée après coup.',
    ),
    BankEntry(
        id='comment_vous_sentez_vous_a_mi',
        question='Comment vous sentez-vous à mi-parcours ?',
        answer="« Sur <OBJECTIF> je suis à l'aise. Ce qui me pèse, c'est <DIFFICULTÉ>. »",
        avoid='« ça va » ferme la conversation. Nommez une chose qui va et une qui pèse.',
    ),
    BankEntry(
        id='que_voulez_vous_que_je_retienne',
        question='Que voulez-vous que je retienne de ce point ?',
        answer='« Que <OBJECTIF> tiendra, et que <OBJECTIF_2> demande <AVANTAGE> pour tenir. »',
        avoid="ne résumez pas tout. Une phrase, deux au maximum — c'est celle-là qui sera notée.",
    ),
]

PERFORMANCE: list[BankEntry] = [
    BankEntry(
        id='comment_evaluez_vous_votre_performance',
        question='Comment évaluez-vous votre performance ?',
        answer="« Sur <OBJECTIF>, <CHIFFRE>. Ce qui est en dessous, c'est <POINT_À_AMÉLIORER>, et voilà ce que j'ai engagé : <CE_QUE_J_AI_FAIT>. »",
        avoid="n'attendez pas le verdict pour vous positionner. Celui qui parle en premier cadre la discussion.",
    ),
    BankEntry(
        id='ce_resultat_ne_correspond_pas_a',
        question='Ce résultat ne correspond pas à ce qui était attendu.',
        answer="« Sur quel point précisément ? Ce que j'avais compris comme attendu, c'était <OBJECTIF>. Voilà où j'en suis : <AVANCEMENT>. »",
        avoid='ne contestez pas globalement. Faites préciser le fait, un par un.',
    ),
    BankEntry(
        id='quelle_critique_anticipez_vous_de_notre',
        question='Quelle critique anticipez-vous de notre part ?',
        answer='« <POINT_À_AMÉLIORER>. Je ne le découvre pas : <CE_QUE_J_AI_FAIT> depuis <ANCIENNETÉ>. »',
        avoid='ne feignez pas la surprise sur un reproche déjà entendu. Ça aggrave tout le reste.',
    ),
    BankEntry(
        id='quels_chiffres_pouvez_vous_avancer',
        question='Quels chiffres pouvez-vous avancer ?',
        answer='« <CHIFFRE> sur <RÉALISATION>. Et <RÉSULTAT>, attestable par <PRÉNOM>. »',
        avoid="n'arrondissez pas à l'avantage. Un chiffre invérifiable détruit les autres.",
    ),
    BankEntry(
        id='comment_expliquez_vous_cet_ecart_avec',
        question='Comment expliquez-vous cet écart avec les attentes ?',
        answer='« Deux choses : <DIFFICULTÉ>, qui ne dépendait pas de moi, et <POINT_À_AMÉLIORER>, qui en dépendait. Sur le second, <CE_QUE_J_AI_FAIT>. »',
        avoid='ne mettez pas tout sur le contexte. La part assumée est ce qui rend le reste crédible.',
    ),
    BankEntry(
        id='qu_avez_vous_change_depuis_notre',
        question="Qu'avez-vous changé depuis notre dernier retour ?",
        answer="« <CE_QUE_J_AI_FAIT>, à partir de <ANCIENNETÉ>. L'effet visible, c'est <RÉSULTAT>. »",
        avoid='ne dites pas que vous y travaillez. Citez ce qui a changé, avec sa date.',
    ),
    BankEntry(
        id='sur_quoi_n_etes_vous_pas',
        question="Sur quoi n'êtes-vous pas prêt à céder ?",
        answer='« Sur <CE_QUI_VOUS_ATTIRE>. Le reste est négociable. »',
        avoid="ne répondez pas « rien ». Une évaluation où l'on cède sur tout se solde par des engagements intenables.",
    ),
    BankEntry(
        id='quels_engagements_prenez_vous_pour_la',
        question='Quels engagements prenez-vous pour la suite ?',
        answer="« <OBJECTIF>, mesuré par <CHIFFRE>, d'ici <AVANTAGE>. Ce qu'il me faut pour ça, c'est <AVANTAGE_2>. »",
        avoid='ne vous engagez pas sans contrepartie ni sans échéance. Un engagement flou devient un reproche.',
    ),
    BankEntry(
        id='votre_evaluation_est_plus_basse_que',
        question='Votre évaluation est plus basse que ce que vous espériez.',
        answer="« Je l'entends. Qu'est-ce qui, concrètement, aurait fait la différence ? Je veux savoir sur quoi travailler. »",
        avoid='ne discutez pas la note à chaud. Demandez le critère, la note se rediscutera avec des faits.',
    ),
    BankEntry(
        id='comment_vous_situez_vous_par_rapport',
        question='Comment vous situez-vous par rapport à vos pairs ?',
        answer='« Je ne connais pas leurs dossiers. Sur le mien : <CHIFFRE> sur <OBJECTIF>. »',
        avoid='ne vous comparez jamais, même flatteusement. Répondez sur vos faits.',
    ),
    BankEntry(
        id='que_proposez_vous_comme_plan_d',
        question="Que proposez-vous comme plan d'amélioration ?",
        answer="« Deux points : <POINT_À_AMÉLIORER> avec <CE_QUE_J_AI_FAIT>, et <COMPÉTENCE> avec <AVANTAGE>. Point d'étape à mi-parcours. »",
        avoid="n'acceptez pas un plan qu'on écrit sans vous. Proposez le vôtre, il sera presque toujours retenu.",
    ),
    BankEntry(
        id='le_contexte_a_t_il_joue',
        question='Le contexte a-t-il joué ?',
        answer="« Oui : <DIFFICULTÉ>. Ça n'annule pas <POINT_À_AMÉLIORER>, mais ça explique l'ampleur. »",
        avoid="n'invoquez le contexte qu'après avoir assumé votre part. Dans l'autre ordre, il ne s'entend pas.",
    ),
]

METIER_DEV_BACK: list[BankEntry] = [
    BankEntry(
        id='quand_choisiriez_vous_une_base_relationnelle',
        question="Quand choisiriez-vous une base relationnelle plutôt qu'une base documentaire ?",
        answer="« Relationnel quand les données ont des relations stables et qu'on a besoin de garanties transactionnelles. Documentaire quand le schéma bouge souvent ou qu'on lit toujours le même agrégat entier. Dans la plupart des projets que j'ai vus, le relationnel est le bon défaut. »",
        avoid='ne répondez pas par une préférence. On teste si vous savez arbitrer, pas ce que vous aimez.',
    ),
    BankEntry(
        id='qu_est_ce_qu_un_index',
        question="Qu'est-ce qu'un index, et quand est-il inutile ?",
        answer="« Un index accélère la lecture au prix de l'écriture et de l'espace. Il ne sert à rien sur une colonne peu sélective, sur une table minuscule, ou quand la requête ne peut pas l'utiliser — une fonction appliquée à la colonne, par exemple. »",
        avoid="ne récitez pas la définition seule. C'est la seconde moitié — quand il est inutile — qui est réellement évaluée.",
    ),
    BankEntry(
        id='une_requete_est_lente_en_production',
        question='Une requête est lente en production. Comment procédez-vous ?',
        answer="« Je mesure d'abord : plan d'exécution, volume réel, et est-ce lent pour tout le monde ou pour un cas. Ensuite seulement je touche. Sur <RÉALISATION>, <CE_QUE_J_AI_FAIT>, et <RÉSULTAT>. »",
        avoid="ne proposez pas d'ajouter un index en première réponse. C'est le réflexe qu'on cherche à ne pas voir.",
    ),
    BankEntry(
        id='comment_concevez_vous_une_api',
        question='Comment concevez-vous une API ?',
        answer="« Je pars des cas d'usage du client, pas de mes tables. Ressources nommées au pluriel, verbes HTTP respectés, codes d'erreur explicites, et une version dès le premier jour. »",
        avoid="ne partez pas du schéma de base de données. C'est l'erreur de conception la plus visible.",
    ),
    BankEntry(
        id='comment_gerez_vous_les_erreurs_dans',
        question='Comment gérez-vous les erreurs dans votre code ?',
        answer="« Je distingue ce qui est attendu de ce qui ne l'est pas. Attendu : je le modélise dans le type de retour. Inattendu : je laisse remonter, je journalise le contexte, et je ne renvoie jamais le détail interne au client. »",
        avoid="ne dites pas que vous entourez tout de try/catch. C'est un signal négatif fort.",
    ),
    BankEntry(
        id='quels_tests_ecrivez_vous_et_a',
        question='Quels tests écrivez-vous, et à quel niveau ?',
        answer="« Beaucoup d'unitaires sur la logique, quelques tests d'intégration sur les chemins qui traversent, et très peu de bout en bout — ceux-là coûtent cher et cassent souvent. Je teste ce qui a déjà cassé en priorité. »",
        avoid="ne dites pas « je teste tout ». Personne ne le fait, et ça s'entend.",
    ),
    BankEntry(
        id='un_bug_n_est_pas_reproductible',
        question="Un bug n'est pas reproductible. Que faites-vous ?",
        answer="« J'arrête de chercher à le reproduire à l'aveugle et je vais chercher des traces : journaux, horodatage, ce qui était différent chez cet utilisateur. Sur <RÉALISATION>, <CE_QUE_J_AI_FAIT>. »",
        avoid="ne dites pas que vous demanderiez à l'utilisateur de réessayer. C'est l'aveu qu'on n'a pas de traces.",
    ),
    BankEntry(
        id='comment_traitez_vous_la_dette_technique',
        question='Comment traitez-vous la dette technique ?',
        answer='« Je ne la traite pas en bloc. Je la paie quand je repasse sur la zone, et je garde une liste courte des endroits qui font vraiment mal. Sur <RÉALISATION>, <CE_QUE_J_AI_FAIT>. »',
        avoid="ne proposez pas de tout réécrire. C'est ce que craint tout manager qui pose la question.",
    ),
    BankEntry(
        id='que_regardez_vous_dans_une_revue',
        question='Que regardez-vous dans une revue de code ?',
        answer="« D'abord si ça résout le bon problème, ensuite les cas limites et la gestion d'erreur, et seulement à la fin le style. Je pose des questions plutôt que des ordres. »",
        avoid="ne commencez pas par le style. C'est ce que font les revues inutiles.",
    ),
    BankEntry(
        id='deux_requetes_arrivent_en_meme_temps',
        question='Deux requêtes arrivent en même temps sur la même ressource. Que se passe-t-il ?',
        answer="« Sans précaution, la dernière écrase la première. Selon le cas : transaction avec le bon niveau d'isolation, verrou optimiste avec un numéro de version, ou opération idempotente pour que rejouer ne casse rien. »",
        avoid="ne répondez pas « je mets un verrou ». Précisez lequel et ce qu'il coûte.",
    ),
    BankEntry(
        id='quelles_sont_les_erreurs_de_securite',
        question='Quelles sont les erreurs de sécurité les plus courantes ?',
        answer="« Faire confiance à l'entrée utilisateur, concaténer du SQL, exposer des messages d'erreur internes, et laisser des secrets dans le code ou les journaux. »",
        avoid='ne citez pas une liste de vulnérabilités apprise par cœur. Donnez celles que vous avez réellement vues.',
    ),
    BankEntry(
        id='comment_deployez_vous_et_que_faites',
        question='Comment déployez-vous, et que faites-vous si ça se passe mal ?',
        answer="« Petits déploiements fréquents, et un retour arrière possible en une commande. Si ça casse, je reviens en arrière d'abord et je comprends ensuite. »",
        avoid="ne dites pas que vous corrigez en avant sous pression. C'est comme ça qu'on empile deux incidents.",
    ),
    BankEntry(
        id='comment_abordez_vous_une_base_de',
        question='Comment abordez-vous une base de code que vous ne connaissez pas ?',
        answer="« Je pars d'un point d'entrée réel — une route, un test qui passe — et je suis le fil. Je ne lis pas le projet dans l'ordre des dossiers. »",
        avoid='ne dites pas que vous lisez la documentation. Elle est rarement à jour, et tout le monde le sait.',
    ),
    BankEntry(
        id='pourquoi_ce_langage_plutot_qu_un',
        question="Pourquoi ce langage plutôt qu'un autre ?",
        answer="« Pour ce type de service, <OUTIL> me donne <COMPÉTENCE>. Mais le choix qui compte est rarement le langage : c'est ce que l'équipe sait maintenir. »",
        avoid='ne défendez pas votre langage comme une identité. On teste votre pragmatisme.',
    ),
    BankEntry(
        id='quel_choix_technique_regrettez_vous',
        question='Quel choix technique regrettez-vous ?',
        answer="« Sur <RÉALISATION>, j'ai choisi <OUTIL>. <DIFFICULTÉ>. Ce que j'en retiens, c'est <POINT_À_AMÉLIORER>. »",
        avoid="ne répondez pas « aucun ». C'est la seule réponse qui disqualifie.",
    ),
]

METIER_COMMERCE: list[BankEntry] = [
    BankEntry(
        id='vendez_moi_ce_stylo',
        question='Vendez-moi ce stylo.',
        answer="« Avant de vous le vendre : vous écrivez beaucoup ? À la main ou à l'écran ? Qu'est-ce qui vous agace dans ce que vous utilisez aujourd'hui ? »",
        avoid="ne partez pas dans un argumentaire. L'exercice teste si vous questionnez avant de proposer — c'est tout.",
    ),
    BankEntry(
        id='comment_prospectez_vous',
        question='Comment prospectez-vous ?',
        answer="« Je pars d'une cible étroite plutôt que d'une liste large. J'écris quelque chose de spécifique à chacun, et je relance trois fois avant d'abandonner. Sur <RÉALISATION>, <CHIFFRE>. »",
        avoid="ne dites pas « je fais du volume ». On veut entendre une méthode, pas de l'endurance.",
    ),
    BankEntry(
        id='un_client_vous_dit_que_c',
        question="Un client vous dit que c'est trop cher.",
        answer="« Trop cher par rapport à quoi ? » — puis j'écoute. Souvent la réponse est un budget, parfois une comparaison, parfois un doute sur la valeur. Les trois n'appellent pas le même traitement.",
        avoid='ne baissez pas le prix dans la même phrase. Vous confirmez que le prix était gonflé.',
    ),
    BankEntry(
        id='comment_qualifiez_vous_un_besoin',
        question='Comment qualifiez-vous un besoin ?',
        answer="« Je cherche trois choses : qui décide, quel est le problème en euros ou en temps, et quelle est l'échéance. Sans les trois, je ne mets pas l'affaire dans mon pipe. »",
        avoid='ne récitez pas une méthode par son acronyme. Décrivez ce que vous demandez réellement.',
    ),
    BankEntry(
        id='quels_sont_vos_chiffres',
        question='Quels sont vos chiffres ?',
        answer='« <CHIFFRE> sur <RÉALISATION>, avec un cycle de <AVANCEMENT>. Mon taux de transformation était <CHIFFRE_2>. »',
        follow_up="Sans chiffres de vente à montrer — reconversion, premier poste : « Je n'ai pas encore de chiffres de vente. Ce que j'ai, c'est <RÉALISATION>, et voilà comment je compte prouver vite : <OBJECTIF>. »",
        avoid='ne donnez pas un chiffre sans son contexte — panier, cycle, secteur. Un chiffre nu ne veut rien dire et invite la question suivante. Et si vous n\'en avez pas, ne l\'inventez pas : proposez comment vous le construirez.',
    ),
    BankEntry(
        id='vous_n_avez_jamais_vendu_pourquoi',
        question="Vous n'avez jamais vendu. Pourquoi vous embaucher comme commercial ?",
        answer="« C'est vrai, et je ne vais pas vous réciter un argumentaire. Ce que j'ai déjà fait, c'est <RÉALISATION> — convaincre, tenir un objectif, encaisser des non. Ce qui me manque, c'est <POINT_À_AMÉLIORER>, et ça s'apprend plus vite que l'envie de vendre. »",
        follow_up="Si on insiste sur le risque : « Donnez-moi un périmètre d'essai et un chiffre à atteindre. Je préfère être jugé sur <OBJECTIF> que sur mon CV. »",
        avoid="ne compensez pas l'absence d'expérience par de l'enthousiasme. Proposez une preuve datée : un périmètre, un chiffre, une échéance.",
    ),
    BankEntry(
        id='comment_gerez_vous_un_refus',
        question='Comment gérez-vous un refus ?',
        answer="« Je demande pourquoi, sincèrement, et je note la raison. Beaucoup de non sont des « pas maintenant », et savoir lequel c'était vaut plus que l'affaire perdue. »",
        avoid='ne dites pas que ça ne vous atteint pas. On cherche ce que vous en faites, pas votre cuirasse.',
    ),
    BankEntry(
        id='comment_relancez_vous_sans_harceler',
        question='Comment relancez-vous sans harceler ?',
        answer='« Chaque relance apporte quelque chose de nouveau : une information, un cas client, une échéance. Jamais un simple « je reviens vers vous ». »',
        avoid="ne parlez pas de fréquence. Ce n'est pas le rythme qui agace, c'est le vide.",
    ),
    BankEntry(
        id='un_client_ne_repond_plus_que',
        question='Un client ne répond plus. Que faites-vous ?',
        answer="« Une relance de valeur, puis une relance de clôture : « dois-je considérer que ce n'est plus d'actualité ? ». Cette dernière fait répondre plus que toutes les autres. »",
        avoid="n'insistez pas indéfiniment. Un pipe encombré de dossiers morts vous fait rater les vivants.",
    ),
    BankEntry(
        id='comment_construisez_vous_votre_pipe',
        question='Comment construisez-vous votre pipe ?',
        answer="« À l'envers : je pars de l'objectif, je remonte par le taux de transformation, et j'en déduis le nombre d'affaires à ouvrir. »",
        avoid='ne décrivez pas un outil. On vous demande un raisonnement.',
    ),
    BankEntry(
        id='racontez_une_vente_que_vous_avez',
        question='Racontez une vente que vous avez perdue.',
        answer="« Sur <RÉALISATION>, j'ai perdu contre <DIFFICULTÉ>. Ce que je n'avais pas vu, c'est <POINT_À_AMÉLIORER>. Depuis, <CE_QUE_J_AI_FAIT>. »",
        avoid="ne mettez pas la perte sur le prix. C'est la réponse de celui qui n'a pas cherché la vraie cause.",
    ),
    BankEntry(
        id='un_client_demande_une_remise',
        question='Un client demande une remise.',
        answer='« Je ne donne rien sans contrepartie : un volume, une durée, une référence. « Je peux faire ce geste si on part sur <AVANTAGE>. » »',
        avoid="n'accordez jamais une remise dans la même phrase que la demande. Même une seconde de réflexion change la perception.",
    ),
    BankEntry(
        id='comment_vendez_vous_un_produit_dont',
        question='Comment vendez-vous un produit dont vous doutez ?',
        answer='« Je ne vends pas ce dont je doute au mauvais client. Je cherche à qui il convient vraiment, et je remonte le doute en interne. »',
        avoid="ne dites pas que vous vendez n'importe quoi à n'importe qui. Et ne dites pas que vous refuseriez de vendre.",
    ),
    BankEntry(
        id='quels_outils_utilisez_vous',
        question='Quels outils utilisez-vous ?',
        answer="« <OUTIL> pour le suivi. Ce qui compte n'est pas l'outil mais la discipline : tout ce qui n'est pas noté n'existe pas pour l'équipe. »",
        avoid="ne dites pas que vous gardez tout en tête. C'est rédhibitoire dans une équipe.",
    ),
    BankEntry(
        id='comment_organisez_vous_votre_semaine',
        question='Comment organisez-vous votre semaine ?',
        answer="« Prospection en bloc le matin, jamais entre deux rendez-vous. Les relances à heure fixe. Le reste s'adapte. »",
        avoid="ne dites pas que vous vous adaptez aux urgences. En vente, l'urgence chasse toujours la prospection.",
    ),
    BankEntry(
        id='un_bon_client_est_mecontent_et',
        question='Un bon client est mécontent et menace de partir.',
        answer="« Je vais le voir, physiquement si possible. J'écoute sans défendre, je reformule, et je reviens avec une seule proposition — pas trois. »",
        avoid='ne répondez pas par écrit à un client en colère. Ça amplifie toujours.',
    ),
]

METIER_COMPTA: list[BankEntry] = [
    BankEntry(
        id='decrivez_moi_une_cloture_mensuelle',
        question='Décrivez-moi une clôture mensuelle.',
        answer="« Je sécurise d'abord ce qui vient de l'extérieur : banques rapprochées, factures fournisseurs reçues, notes de frais. Ensuite les écritures récurrentes — abonnements, provisions, cut-off. Et je termine par les contrôles de cohérence avant d'éditer. »",
        avoid="ne donnez pas une liste sans ordre. C'est la séquence qu'on évalue, parce qu'elle révèle si vous l'avez faite.",
    ),
    BankEntry(
        id='qu_est_ce_que_le_cut',
        question="Qu'est-ce que le cut-off, et pourquoi ça compte ?",
        answer="« C'est le rattachement de la charge ou du produit à la bonne période, indépendamment de la date de la facture. Ça compte parce que c'est le premier endroit où un résultat se déforme, souvent sans mauvaise intention. »",
        avoid="ne le réduisez pas aux factures non parvenues. Les produits constatés d'avance comptent autant.",
    ),
    BankEntry(
        id='vous_avez_un_ecart_de_rapprochement',
        question='Vous avez un écart de rapprochement bancaire. Comment le traitez-vous ?',
        answer="« Je pars du plus gros écart et je remonte. En général c'est un décalage d'encaissement, une écriture passée deux fois, ou un frais bancaire non saisi. Je ne solde jamais un écart par une écriture d'ajustement sans en avoir trouvé la cause. »",
        avoid="ne dites jamais que vous ajustez pour équilibrer. C'est la réponse qui fait échouer l'entretien.",
    ),
    BankEntry(
        id='quels_sont_les_pieges_courants_en',
        question='Quels sont les pièges courants en TVA ?',
        answer="« L'autoliquidation quand on ne l'attend pas, la TVA sur encaissement pour les prestations de services contre la TVA sur débit pour les biens, et la déductibilité partielle sur certaines dépenses. »",
        avoid="ne prétendez pas maîtriser l'international si ce n'est pas le cas. La question suivante ira là.",
    ),
    BankEntry(
        id='comment_traitez_vous_une_immobilisation',
        question='Comment traitez-vous une immobilisation ?',
        answer="« J'inscris à l'actif, je détermine la durée d'utilisation, et j'amortis sur cette durée. Ce qui se discute en pratique, c'est la frontière entre charge et immobilisation, et la cohérence des durées entre biens comparables. »",
        avoid="ne parlez pas que d'amortissement linéaire. La question porte souvent sur la frontière charge/immo.",
    ),
    BankEntry(
        id='comment_gerez_vous_les_relances_clients',
        question='Comment gérez-vous les relances clients ?',
        answer="« Par ancienneté et par montant, pas par ordre d'arrivée. J'appelle avant d'écrire au-delà d'un certain seuil, et je préviens le commercial avant de mettre la pression. »",
        avoid='ne relancez pas un client sans avoir vérifié que la facture est juste. Une relance sur une facture erronée coûte la relation.',
    ),
    BankEntry(
        id='un_fournisseur_conteste_une_facture_que',
        question='Un fournisseur conteste une facture. Que faites-vous ?',
        answer="« Je remonte au bon de commande et à la réception avant de discuter. Neuf fois sur dix l'écart est là, pas dans la facture. »",
        avoid='ne réglez pas pour avoir la paix. Le même écart reviendra le mois suivant.',
    ),
    BankEntry(
        id='qu_est_ce_qui_change_quand',
        question="Qu'est-ce qui change quand un commissaire aux comptes intervient ?",
        answer="« La justification devient aussi importante que l'écriture. Je prépare les dossiers de preuve au fil de l'eau plutôt qu'au moment de la demande, et je documente les estimations. »",
        avoid='ne présentez pas le contrôle comme une contrainte. Ça se sent, et ça inquiète.',
    ),
    BankEntry(
        id='comment_determinez_vous_une_provision',
        question='Comment déterminez-vous une provision ?',
        answer="« Une obligation à la clôture, une sortie de ressources probable, et un montant estimable de façon fiable. Si l'un des trois manque, c'est une information en annexe, pas une provision. »",
        avoid="ne provisionnez pas « par prudence » sans les critères. C'est ce que le contrôle reprendra en premier.",
    ),
    BankEntry(
        id='comment_securisez_vous_vos_saisies',
        question='Comment sécurisez-vous vos saisies ?',
        answer='« Des contrôles qui ne dépendent pas de mon attention : rapprochements systématiques, contrôles de cohérence sur les comptes de bilan, et une relecture croisée sur les écritures inhabituelles. »',
        avoid='ne dites pas « je fais attention ». Tout le monde fait attention, et tout le monde se trompe.',
    ),
    BankEntry(
        id='quels_outils_avez_vous_pratiques',
        question='Quels outils avez-vous pratiqués ?',
        answer="« <OUTIL> principalement, sur <ANCIENNETÉ>. Ce qui se transpose d'un outil à l'autre, c'est <COMPÉTENCE> — la logique comptable ne change pas. »",
        avoid='ne bluffez pas sur un ERP. Une question de navigation suffit à le révéler.',
    ),
    BankEntry(
        id='le_delai_de_cloture_est_intenable',
        question='Le délai de clôture est intenable ce mois-ci.',
        answer="« Je préviens tout de suite avec ce qui sera prêt et ce qui ne le sera pas, et je propose une clôture partielle plutôt qu'une clôture fausse. »",
        avoid='ne livrez pas des chiffres non fiables dans le délai. En comptabilité, le retard se rattrape, le faux non.',
    ),
    BankEntry(
        id='vous_decouvrez_une_erreur_apres_la',
        question='Vous découvrez une erreur après la clôture.',
        answer="« Je l'évalue d'abord : significative ou non. Si elle l'est, je la remonte immédiatement avec l'impact chiffré et la correction proposée. Si elle ne l'est pas, je la corrige sur la période suivante et je la documente. »",
        avoid="ne corrigez rien en silence. C'est ce qui transforme une erreur en faute.",
    ),
    BankEntry(
        id='on_vous_demande_de_presenter_les',
        question='On vous demande de présenter les chiffres plus favorablement.',
        answer="« Je peux améliorer la présentation et l'explication, pas les chiffres. Si le sujet est une estimation, je dis la fourchette et l'hypothèse retenue. »",
        avoid='ne répondez pas seulement « je refuse ». Montrez la marge légitime avant la limite.',
    ),
    BankEntry(
        id='qu_est_ce_que_la_liasse',
        question="Qu'est-ce que la liasse fiscale, concrètement ?",
        answer="« L'ensemble des tableaux transmis à l'administration à partir des comptes annuels : bilan, compte de résultat et annexes normalisées. En pratique le travail est dans le passage du résultat comptable au résultat fiscal — les réintégrations et déductions. »",
        avoid="ne vous limitez pas à la définition. C'est le passage comptable/fiscal qui est évalué.",
    ),
]

METIER_DEV_FRONT: list[BankEntry] = [
    BankEntry(
        id='une_page_est_lente_comment_procedez',
        question='Une page est lente. Comment procédez-vous ?',
        answer="« Je mesure avant de toucher : qu'est-ce qui est lent — le premier affichage, l'interaction, le réseau ? L'outil de profilage me dit où part le temps. Sur <RÉALISATION>, <CE_QUE_J_AI_FAIT>, et <RÉSULTAT>. »",
        avoid="ne répondez pas « j'optimise les images » avant d'avoir mesuré. C'est le réflexe qu'on cherche à ne pas voir.",
    ),
    BankEntry(
        id='comment_gerez_vous_l_etat_dans',
        question="Comment gérez-vous l'état dans une application ?",
        answer="« Le plus localement possible. L'état global est un dernier recours : chaque chose qui y entre doit justifier pourquoi deux écrans en ont besoin. La plupart des applications que j'ai reprises souffraient de l'inverse. »",
        avoid='ne citez pas une bibliothèque comme réponse. On teste où vous mettez la frontière, pas quel outil vous connaissez.',
    ),
    BankEntry(
        id='qu_est_ce_que_l_accessibilite',
        question="Qu'est-ce que l'accessibilité change à votre façon de coder ?",
        answer="« Partir du HTML sémantique : un bouton est un bouton, pas une div cliquable. Le clavier d'abord — si tout marche au clavier, le lecteur d'écran suit presque toujours. Et tester avec l'outil d'audit avant la revue, pas après le ticket. »",
        avoid="ne réduisez pas l'accessibilité aux attributs ARIA. Les rajouter sur du mauvais HTML aggrave souvent les choses.",
    ),
    BankEntry(
        id='un_bug_n_apparait_que_sur',
        question="Un bug n'apparaît que sur un navigateur. Comment l'attaquez-vous ?",
        answer="« Je reproduis dans ce navigateur, je réduis au plus petit cas qui casse, et je cherche la différence d'implémentation — souvent une API récente ou un comportement par défaut. La table de compatibilité tranche vite. »",
        avoid='ne dites pas que vous ajouteriez un correctif spécifique sans comprendre. Ces rustines se paient à chaque mise à jour.',
    ),
    BankEntry(
        id='le_designer_livre_une_maquette_irrealisable',
        question='Le designer livre une maquette irréalisable dans le délai.',
        answer="« Je ne dis pas « c'est impossible », je chiffre : voilà ce que coûte chaque partie, voilà ce qui tient dans le délai. On décide ensemble ce qui se simplifie — c'est son métier autant que le mien. »",
        avoid='ne simplifiez pas la maquette en silence. Le designer le verra en production, et vous aurez perdu un allié.',
    ),
    BankEntry(
        id='comment_testez_vous_une_interface',
        question='Comment testez-vous une interface ?',
        answer="« Je teste le comportement, pas le rendu : ce que l'utilisateur voit et peut faire, pas la structure interne du composant. Les captures d'écran de non-régression sur les écrans qui rapportent, et très peu de tests bout en bout. »",
        avoid="ne dites pas que l'interface ne se teste pas. Ne dites pas non plus que vous testez chaque composant : personne n'y croit.",
    ),
    BankEntry(
        id='comment_travaillez_vous_avec_le_back',
        question='Comment travaillez-vous avec le back ?',
        answer="« Sur un contrat : on s'accorde sur la forme des données avant que chacun code, et je développe contre des données simulées sans attendre. Sur <RÉALISATION>, <CE_QUE_J_AI_FAIT>. »",
        avoid="ne racontez pas une relation de guichet — « je demande, ils fournissent ». On cherche quelqu'un qui négocie le contrat.",
    ),
    BankEntry(
        id='css_comment_evitez_vous_que_ca',
        question='CSS : comment évitez-vous que ça devienne ingérable ?',
        answer="« Une convention de nommage tenue, des styles portés par le composant plutôt que globaux, et la suppression systématique de ce qui ne sert plus. Le CSS ingérable vient rarement d'un mauvais choix, il vient de l'accumulation. »",
        avoid="ne répondez pas par le nom d'un outil. L'outil ne tient pas la discipline à votre place.",
    ),
    BankEntry(
        id='pourquoi_ce_framework_plutot_qu_un_2',
        question="Pourquoi ce framework plutôt qu'un autre ?",
        answer="« Pour ce produit, <OUTIL> me donne <COMPÉTENCE>. Mais le vrai critère est ailleurs : ce que l'équipe sait maintenir, et ce qu'on trouvera comme renfort dans deux ans. »",
        avoid='ne défendez pas votre framework comme un club de foot. La question teste votre pragmatisme, pas votre fidélité.',
    ),
    BankEntry(
        id='que_faites_vous_des_erreurs_cote',
        question='Que faites-vous des erreurs côté client ?',
        answer="« Elles remontent : un outil de collecte, avec le contexte — navigateur, écran, action en cours. Une erreur qui n'arrive qu'aux utilisateurs et jamais à moi est exactement celle qu'il faut voir. »",
        avoid="ne dites pas que la console suffit. La console de l'utilisateur, vous ne la verrez jamais.",
    ),
    BankEntry(
        id='comment_chargez_vous_une_page_le',
        question='Comment faites-vous pour qu\'une page paraisse rapide ?',
        answer="« Je charge d'abord ce qui se voit : le reste attend. Et je montre l'état d'avancement plutôt qu'un écran figé — la vitesse perçue compte autant que la vitesse mesurée. »",
        avoid='ne confondez pas poids et vitesse. Une page légère mal ordonnée paraît plus lente qu\'une page lourde bien servie.',
    ),
    BankEntry(
        id='le_responsive_comment_l_abordez_vous',
        question='Comment abordez-vous les différentes tailles d\'écran ?',
        answer="« Mobile d'abord, parce que c'est là que les choix font mal : ce qui tient sur un petit écran s'étend bien, l'inverse est faux. Et je teste sur un vrai téléphone, pas seulement dans le simulateur du navigateur. »",
        avoid='ne dites pas « je fais du responsive » sans dire par quel bout vous commencez. C\'est le bout qui est évalué.',
    ),
    BankEntry(
        id='un_composant_existe_deja_mais_ne',
        question='Un composant existe déjà mais ne fait pas tout à fait ce qu\'il vous faut.',
        answer="« Je regarde qui l'utilise avant de le modifier. Si l'écart est petit, je l'étends proprement ; s'il faut le tordre, je crée à côté et je note la dette. Tordre un composant partagé coûte à tous ses usages. »",
        avoid='ne dupliquez pas en silence et ne modifiez pas en aveugle. Les deux se découvrent au pire moment.',
    ),
    BankEntry(
        id='comment_restez_vous_a_jour_dans',
        question='Comment restez-vous à jour dans un écosystème qui bouge autant ?',
        answer="« Je trie : je lis large, mais je n'adopte que ce qui résout un problème que j'ai vraiment. Sur <COMPÉTENCE>, <CE_QUE_J_AI_FAIT> — et je l'ai utilisé sur <RÉALISATION> dans la foulée. »",
        avoid='ne montrez pas une adoption compulsive des nouveautés. Elle inquiète plus qu\'elle ne rassure : le produit vit des années.',
    ),
    BankEntry(
        id='quel_choix_technique_regrettez_vous_front',
        question='Quel choix technique regrettez-vous ?',
        answer="« Sur <RÉALISATION>, j'ai choisi <OUTIL>. <DIFFICULTÉ>. Ce que j'en retiens, c'est <POINT_À_AMÉLIORER>. »",
        avoid="ne répondez pas « aucun ». C'est la seule réponse qui disqualifie.",
    ),
]

METIER_DATA: list[BankEntry] = [
    BankEntry(
        id='on_vous_donne_un_jeu_de',
        question='On vous donne un jeu de données inconnu. Par quoi commencez-vous ?',
        answer="« Par le compter avant de l'analyser : combien de lignes, quelles clés, quels trous, quels doublons. Puis je vérifie une valeur que le métier connaît par cœur — si elle ne colle pas, rien d'autre ne comptera. »",
        avoid='ne partez pas sur la modélisation. La question teste votre méfiance, pas votre boîte à outils.',
    ),
    BankEntry(
        id='votre_chiffre_contredit_l_intuition_du',
        question="Votre chiffre contredit l'intuition du métier. Que faites-vous ?",
        answer="« Je vérifie d'abord mon chiffre — l'intuition du métier a souvent raison sur les ordres de grandeur. Si je confirme, je viens avec le détail du calcul et des exemples nominatifs qu'ils peuvent vérifier eux-mêmes. »",
        avoid="ne défendez pas votre chiffre avant de l'avoir revérifié. Se tromper est pardonné, s'obstiner non.",
    ),
    BankEntry(
        id='une_jointure_double_les_lignes_que',
        question="Une jointure double vos lignes. Que s'est-il passé ?",
        answer="« La clé de jointure n'est pas unique d'un des deux côtés — des doublons, ou une granularité différente de ce que je croyais. Je compte les deux tables sur la clé avant de joindre, plus jamais après. »",
        avoid="ne répondez pas « j'ajoute un distinct ». C'est cacher le problème sous le tapis, et il ressortira ailleurs.",
    ),
    BankEntry(
        id='comment_verifiez_vous_la_qualite_des',
        question='Comment vérifiez-vous la qualité des données ?',
        answer="« Des contrôles qui tournent sans moi : volumes attendus, bornes sur les valeurs, fraîcheur des sources. Et un principe : toute anomalie détectée en aval devient un contrôle en amont. »",
        avoid='ne dites pas que vous vérifiez à la main. La qualité qui dépend de votre vigilance ne survit pas à vos vacances.',
    ),
    BankEntry(
        id='modele_simple_ou_complexe_comment_choisissez',
        question='Modèle simple ou modèle complexe : comment choisissez-vous ?',
        answer="« Je commence par le plus simple qui donne une base de comparaison — souvent une règle ou une régression. Le complexe doit battre le simple d'assez loin pour payer son coût d'exploitation et d'explication. »",
        avoid='ne montrez pas de fascination pour la complexité. En face, quelqu\'un paiera la maintenance de votre choix.',
    ),
    BankEntry(
        id='comment_presentez_vous_un_resultat_a',
        question='Comment présentez-vous un résultat à des non-techniques ?',
        answer="« Je commence par la décision que le résultat permet, pas par la méthode. Un graphique, une phrase, et les limites dites clairement — ce que le chiffre ne dit pas est aussi important que ce qu'il dit. »",
        avoid='ne montrez jamais votre démarche avant votre conclusion. Ils décrocheront avant d\'y arriver.',
    ),
    BankEntry(
        id='on_vous_demande_une_analyse_pour',
        question='On vous demande une analyse pour hier. Que livrez-vous ?',
        answer="« Une réponse approximative honnête : l'ordre de grandeur, l'hypothèse prise, et ce qu'il faudrait pour affiner. Je note la version rapide comme telle — sinon elle devient la vérité officielle. »",
        avoid='ne refusez pas au nom de la rigueur, et ne livrez pas un chiffre précis non vérifié. Les deux vous coûtent la confiance.',
    ),
    BankEntry(
        id='votre_modele_se_degrade_en_production',
        question='Votre modèle se dégrade en production. Comment le voyez-vous, et que faites-vous ?',
        answer="« Je le vois parce que je surveille la performance en continu, pas parce qu'on se plaint. Ensuite je cherche ce qui a changé — presque toujours les données d'entrée, rarement le modèle lui-même. »",
        avoid="ne dites pas que vous réentraîneriez d'office. Réentraîner sur des données déformées automatise la dégradation.",
    ),
    BankEntry(
        id='correlation_et_causalite_comment_tranchez_vous',
        question='Corrélation et causalité : comment tranchez-vous en pratique ?',
        answer="« Par le test quand c'est possible — un groupe qui reçoit, un groupe qui ne reçoit pas. Quand ce n'est pas possible, je le dis : « les deux bougent ensemble, je ne peux pas dire qui cause quoi », et la décision se prend en le sachant. »",
        avoid='ne promettez jamais une causalité que le dispositif ne peut pas prouver. C\'est là-dessus que votre crédibilité se joue.',
    ),
    BankEntry(
        id='un_pipeline_casse_la_nuit_on',
        question='Un pipeline casse la nuit. On fait quoi le matin ?',
        answer="« D'abord prévenir qui consomme les chiffres — un tableau de bord faux fait plus de dégâts qu'un tableau de bord vide. Ensuite réparer, puis rejouer, et enfin ajouter le contrôle qui l'aurait attrapé. »",
        avoid='ne commencez pas par réparer en silence. Pendant ce temps, quelqu\'un décide sur des chiffres faux.',
    ),
    BankEntry(
        id='quelles_donnees_refuseriez_vous_d_utiliser',
        question="Quelles données refuseriez-vous d'utiliser ?",
        answer="« Celles que la personne n'a pas données pour cet usage. Le critère pratique : si l'usage était affiché à l'utilisateur, serait-il surpris ? Et il y a ce que la loi interdit, qui ne se discute pas. »",
        avoid='ne répondez pas « tout dépend du besoin ». La question teste précisément si quelque chose ne dépend pas du besoin.',
    ),
    BankEntry(
        id='le_metier_demande_un_tableau_de',
        question='Le métier demande un tableau de bord de plus.',
        answer="« Je demande quelle décision il servira et qui le regardera chaque semaine. Sans réponse, je propose plutôt de répondre à la question du moment — un tableau de bord de plus, c'est un tableau de bord de plus à maintenir. »",
        avoid='ne livrez pas sans poser la question. Le cimetière des tableaux de bord jamais ouverts décrédibilise toute l\'équipe.',
    ),
    BankEntry(
        id='comment_documentez_vous_vos_analyses',
        question='Comment documentez-vous vos analyses ?',
        answer="« La requête avec le résultat, l'hypothèse prise, et la date des données. Le test : quelqu'un d'autre peut-il reproduire mon chiffre sans me parler ? Sur <RÉALISATION>, <CE_QUE_J_AI_FAIT>. »",
        avoid='ne dites pas que le code se documente lui-même. Les hypothèses ne sont jamais dans le code.',
    ),
    BankEntry(
        id='comment_mesurez_vous_l_impact_de',
        question='Comment mesurez-vous l\'impact de votre travail ?',
        answer="« Par la décision changée, pas par l'analyse produite. Sur <RÉALISATION>, <CE_QUE_J_AI_FAIT>, et <RÉSULTAT> — c'est ça que je compte, pas le nombre de rapports. »",
        avoid='ne mesurez pas votre valeur en livrables. Une analyse qui ne change aucune décision est un coût.',
    ),
    BankEntry(
        id='quel_projet_data_regrettez_vous',
        question='Quel projet data regrettez-vous ?',
        answer="« Sur <RÉALISATION>, <DIFFICULTÉ>. Ce que j'aurais dû faire plus tôt, c'est <CE_QUE_J_AI_FAIT>. Ce que j'en retiens, c'est <POINT_À_AMÉLIORER>. »",
        avoid="ne choisissez pas un regret purement technique. Les échecs data sont presque toujours des échecs de cadrage.",
    ),
]

METIER_OPS: list[BankEntry] = [
    BankEntry(
        id='un_service_est_tombe_racontez_votre',
        question='Un service est tombé en production. Racontez votre première heure.',
        answer="« Rétablir d'abord, comprendre ensuite : le retour arrière ou la bascule avant le diagnostic. Je tiens un fil d'horodatage de ce que je fais — c'est la matière du post-mortem, et ça évite de refaire deux fois la même chose à chaud. »",
        avoid='ne racontez pas une heure de diagnostic héroïque. Ce qu\'on évalue, c\'est le temps de rétablissement, pas la beauté de l\'analyse.',
    ),
    BankEntry(
        id='comment_decidez_vous_de_ce_qui_alerte',
        question="Comment décidez-vous de ce qui mérite une alerte ?",
        answer="« Une alerte doit réveiller quelqu'un qui peut agir. Si elle n'exige pas d'action immédiate, c'est un signal de tableau de bord, pas une alerte. Je supprime autant d'alertes que j'en crée. »",
        avoid='ne dites pas que vous alertez sur tout par prudence. La fatigue d\'alerte est précisément ce qui fait rater la vraie.',
    ),
    BankEntry(
        id='les_sauvegardes_comment_savez_vous_qu',
        question='Vos sauvegardes : comment savez-vous qu\'elles marchent ?',
        answer="« Parce que je restaure régulièrement, pas parce que le travail de sauvegarde est vert. Une sauvegarde jamais restaurée est une hypothèse, pas une sauvegarde. »",
        avoid='ne répondez pas que sur la sauvegarde. La question porte en réalité sur la restauration, et l\'entretien le vérifiera.',
    ),
    BankEntry(
        id='un_deploiement_a_casse_la_production',
        question='Un déploiement a cassé la production un vendredi soir.',
        answer="« Retour arrière immédiat — c'est pour ça qu'il doit tenir en une commande. Le correctif attendra lundi ; comprendre à froid vaut mieux que corriger à chaud sur un système déjà blessé. »",
        avoid='ne débattez pas du « pas de déploiement le vendredi ». Dites plutôt ce qui rend un déploiement du vendredi sans danger.',
    ),
    BankEntry(
        id='comment_gerez_vous_les_secrets',
        question='Comment gérez-vous les secrets ?',
        answer="« Un gestionnaire dédié, des secrets qui tournent, et rien dans le code ni dans les journaux. Le test honnête : combien de temps pour révoquer un secret compromis ? Si la réponse est « on ne sait pas », c'est le chantier prioritaire. »",
        avoid="ne dites pas que les secrets sont dans les variables d'environnement et que ça suffit. La question suivante sera : qui y a accès ?",
    ),
    BankEntry(
        id='l_infrastructure_as_code_qu_est',
        question="L'infrastructure en code : qu'est-ce que ça change vraiment ?",
        answer="« Ça rend l'infrastructure relisable et reconstructible : la revue avant le changement, l'historique de qui a changé quoi, et un environnement qui se recrée au lieu de se réparer. Le prix, c'est la discipline de ne plus rien faire à la main. »",
        avoid="ne vendez pas l'outil. La valeur est dans le « plus rien à la main » — et c'est le plus dur à tenir.",
    ),
    BankEntry(
        id='le_developpeur_dit_ca_marche_sur',
        question='Le développeur dit « ça marche sur ma machine ».',
        answer="« C'est une information : la différence est dans l'environnement. Je cherche l'écart — version, configuration, données — et je le fais disparaître pour de bon, pas juste pour ce cas. »",
        avoid='pas d\'ironie sur les développeurs. En face, on cherche quelqu\'un qui fait équipe avec eux, pas un gardien de temple.',
    ),
    BankEntry(
        id='comment_reduisez_vous_la_facture_cloud',
        question='Comment réduisez-vous la facture cloud sans rien casser ?',
        answer="« Je commence par mesurer qui dépense quoi — la moitié de la facture est souvent dans des ressources que plus personne ne regarde. Puis j'éteins ce qui ne sert pas, je redimensionne ce qui est surdimensionné, et je réserve ce qui est stable. »",
        avoid='ne promettez pas un pourcentage d\'économie avant d\'avoir vu la facture. C\'est le vendeur qui parle, pas l\'ingénieur.',
    ),
    BankEntry(
        id='comment_menez_vous_un_post_mortem',
        question='Comment menez-vous un post-mortem ?',
        answer="« Sans coupable : on cherche ce qui, dans le système, a permis l'erreur — pas qui l'a faite. Une chronologie, des causes, et deux ou trois actions datées. Un post-mortem sans action est une cérémonie. »",
        avoid='ne dites jamais que l\'incident venait d\'une erreur humaine et qu\'on a rappelé les consignes. C\'est l\'aveu qu\'il se reproduira.',
    ),
    BankEntry(
        id='comment_migrez_vous_sans_coupure',
        question='Comment migrez-vous sans coupure ?',
        answer="« Par étapes réversibles : les deux systèmes en parallèle, le trafic bascule progressivement, et à chaque étape je peux revenir. La migration en une nuit, c'est celle qu'on raconte dans les post-mortems. »",
        avoid='ne présentez pas un plan sans marche arrière. La question en face sera toujours : et si ça se passe mal à mi-chemin ?',
    ),
    BankEntry(
        id='quelle_est_votre_politique_de_mise',
        question='Quelle est votre politique de mise à jour ?',
        answer="« Régulière et petite : un système en retard de deux ans ne se met plus à jour, il se remplace. Les correctifs de sécurité passent vite, le reste suit un rythme — et tout passe d'abord hors production. »",
        avoid='ni « toujours la dernière version », ni « on ne touche pas à ce qui marche ». Les deux extrêmes coûtent des incidents.',
    ),
    BankEntry(
        id='comment_rendez_vous_l_astreinte_vivable',
        question="Comment rendez-vous l'astreinte vivable ?",
        answer="« En traitant chaque réveil comme un défaut : ce qui a sonné la nuit doit être corrigé, automatisé ou déclassé le lendemain. Une astreinte qui sonne souvent est un système malade, pas une équipe dévouée. »",
        avoid='ne portez pas l\'astreinte en médaille. L\'endurance n\'est pas la compétence évaluée.',
    ),
    BankEntry(
        id='comment_dimensionnez_vous_une_infrastructure',
        question='Comment dimensionnez-vous une infrastructure ?',
        answer="« À partir de la charge mesurée ou estimée, avec de la marge pour le pic — et l'élasticité pour l'exceptionnel. Sur <RÉALISATION>, <CE_QUE_J_AI_FAIT>, et <RÉSULTAT>. »",
        avoid='ne dimensionnez pas « large pour être tranquille ». Quelqu\'un paie la tranquillité tous les mois.',
    ),
    BankEntry(
        id='quel_incident_vous_a_le_plus',
        question='Quel incident vous a le plus appris ?',
        answer="« Sur <RÉALISATION>, <DIFFICULTÉ>. Sur le moment, <CE_QUE_J_AI_FAIT>. Ce qui a changé durablement après, c'est <RÉSULTAT>. »",
        avoid='ne racontez pas un incident où vous n\'avez rien changé après. C\'est l\'après qui est évalué.',
    ),
    BankEntry(
        id='quels_outils_et_pourquoi_ceux_la',
        question='Quels outils, et pourquoi ceux-là ?',
        answer="« <OUTIL>, sur <ANCIENNETÉ>. Mais l'outil compte moins que ce qu'il outille : ce qui se transpose, c'est <COMPÉTENCE>. »",
        avoid='ne récitez pas une liste. Un outil bien défendu vaut mieux que dix cités.',
    ),
]

METIER_CYBER: list[BankEntry] = [
    BankEntry(
        id='par_ou_commencez_vous_pour_evaluer',
        question="Par où commencez-vous pour évaluer la sécurité d'un système ?",
        answer="« Par ce qu'il protège : quelles données, quels accès, qui voudrait quoi. Sans ça, on durcit au hasard. Ensuite l'exposition réelle — comptes, entrées, dépendances — avant tout outil de scan. »",
        avoid='ne commencez pas par les outils. Un scan sans modèle de menace produit une liste, pas une évaluation.',
    ),
    BankEntry(
        id='un_collaborateur_a_clique_sur_un',
        question='Un collaborateur a cliqué sur un lien de phishing. Que se passe-t-il ?',
        answer="« D'abord contenir : mot de passe, sessions, poste. Ensuite comprendre l'ampleur. Et surtout : la personne qui signale vite est une alliée — si cliquer coûte une humiliation, le prochain clic ne sera pas signalé. »",
        avoid='ne parlez pas de sanction. La peur est exactement ce qui transforme un clic en compromission silencieuse.',
    ),
    BankEntry(
        id='comment_priorisez_vous_des_vulnerabilites',
        question='Comment priorisez-vous des vulnérabilités ?',
        answer="« Par l'exploitabilité chez nous, pas par le score générique : exposée ou interne, exploitée dans la nature ou théorique, sur quoi elle ouvre. Une note moyenne sur un système exposé passe avant une critique sur un serveur isolé. »",
        avoid='ne dites pas que vous traitez par score décroissant. C\'est la réponse de celui qui n\'a jamais vidé la liste.',
    ),
    BankEntry(
        id='le_metier_refuse_une_mesure_qui',
        question='Le métier refuse une mesure de sécurité qui le ralentit.',
        answer="« Je commence par croire à leur contrainte : une mesure contournée protège moins que pas de mesure, parce qu'elle rassure. Je cherche le même niveau de protection dans un chemin qui ne les ralentit pas — il existe presque toujours. »",
        avoid='ne passez pas en force par la hiérarchie en premier recours. Vous gagnerez la mesure et perdrez tous les signalements futurs.',
    ),
    BankEntry(
        id='une_faille_mediatisee_tombe_ce_matin',
        question='Une faille médiatisée tombe ce matin. La direction panique.',
        answer="« Je réponds à deux questions vite : sommes-nous concernés, et sommes-nous exposés. La réponse honnête est souvent « concernés, pas exposés » — et je la donne avec ce qui reste à vérifier, pas comme une certitude. »",
        avoid='ne surfez pas sur la peur pour obtenir du budget. Ça marche une fois, puis plus personne ne vous croit.',
    ),
    BankEntry(
        id='racontez_une_investigation_d_incident',
        question="Racontez une investigation d'incident.",
        answer="« Sur <RÉALISATION>, <DIFFICULTÉ>. J'ai remonté la chronologie par les journaux, <CE_QUE_J_AI_FAIT>, et <RÉSULTAT>. Ce qui a permis l'entrée a été corrigé — pas seulement l'entrée elle-même. »",
        avoid='ne racontez pas une intuition géniale. On évalue la méthode : préserver, tracer, remonter.',
    ),
    BankEntry(
        id='que_journalisez_vous_et_pourquoi_pas',
        question='Que journalisez-vous, et pourquoi pas tout ?',
        answer="« Les authentifications, les élévations de droits, les accès aux données sensibles — ce qui raconte « qui a fait quoi ». Pas tout : un journal illisible ne sert à rien le jour où on en a besoin, et journaliser des données sensibles crée le risque qu'on prétend surveiller. »",
        avoid='ne répondez pas « tout, on ne sait jamais ». C\'est une réponse de stockage, pas de sécurité.',
    ),
    BankEntry(
        id='mots_de_passe_mfa_votre_position',
        question='Mots de passe, double authentification : votre position pratique ?',
        answer="« La double authentification partout où c'est possible — c'est la mesure au meilleur rapport effort-protection qui existe. Sur les mots de passe : longs, uniques, dans un gestionnaire. La rotation forcée tous les mois, elle, fabrique des mots de passe faibles. »",
        avoid='ne récitez pas une politique de complexité d\'il y a dix ans. Le domaine a changé d\'avis, et l\'entretien le sait.',
    ),
    BankEntry(
        id='un_dirigeant_demande_une_exception_aux',
        question='Un dirigeant demande une exception aux règles de sécurité.',
        answer="« Je documente : ce qu'il demande, ce que ça expose, et qui accepte le risque — par écrit. Souvent, voir le risque écrit suffit à le faire renoncer. S'il signe, c'est son arbitrage, et c'est son droit. »",
        avoid='ni céder en silence, ni refuser frontalement. Votre rôle est d\'éclairer le risque, pas de le porter à sa place.',
    ),
    BankEntry(
        id='un_pentest_que_regardez_vous_en',
        question='Sur un test d\'intrusion, que regardez-vous en premier ?',
        answer="« Ce qui est exposé sans authentification, puis les chemins d'élévation une fois entré. Et les mots de passe par défaut avant toute sophistication — c'est encore comme ça qu'on entre le plus souvent. »",
        avoid='ne racontez pas une technique exotique en premier. L\'entretien vérifie que vous commencez par les portes, pas par les fenêtres du troisième.',
    ),
    BankEntry(
        id='comment_evaluez_vous_un_fournisseur',
        question='Comment évaluez-vous la sécurité d\'un fournisseur ?',
        answer="« Par ce qu'il fera de nos données et de nos accès : où elles vivent, qui y accède, comment on est prévenus en cas d'incident, comment on sort. Le questionnaire ne suffit pas — je regarde les engagements contractuels. »",
        avoid='ne vous contentez pas d\'une certification citée. Demandez ce qu\'elle couvre — souvent pas le service qu\'on achète.',
    ),
    BankEntry(
        id='conformite_et_securite_quelle_difference',
        question='Conformité et sécurité : quelle différence ?',
        answer="« La conformité prouve qu'on suit des règles ; la sécurité résiste à quelqu'un qui n'en suit aucune. On peut être conforme et vulnérable. Je me sers de la conformité comme levier de budget, jamais comme mesure de protection. »",
        avoid='ne méprisez pas la conformité pour autant. C\'est souvent elle qui finance ce que la sécurité n\'obtient pas seule.',
    ),
    BankEntry(
        id='comment_faites_vous_de_la_sensibilisation',
        question='Comment faites-vous de la sensibilisation qui marche ?',
        answer="« Courte, concrète, et sur des cas de chez nous — le faux courriel qu'on a vraiment reçu, pas un générique. Et je mesure autre chose que la présence : le taux de signalement, pas le taux de clic. »",
        avoid='ne proposez pas la formation annuelle obligatoire comme réponse. Tout le monde sait qu\'elle ne change rien.',
    ),
    BankEntry(
        id='quelle_veille_faites_vous',
        question='Quelle veille faites-vous ?',
        answer="« Deux niveaux : les alertes qui exigent une action chez nous — celles-là en continu — et le fond, sur <COMPÉTENCE>, où je trie fort. Sur <RÉALISATION>, c'est la veille qui m'a fait <CE_QUE_J_AI_FAIT>. »",
        avoid='ne citez pas dix sources. Une veille se juge à ce qu\'elle a déclenché, pas à ce qu\'elle agrège.',
    ),
    BankEntry(
        id='votre_meilleure_trouvaille',
        question='Votre meilleure trouvaille ?',
        answer="« Sur <RÉALISATION>, j'ai trouvé <DIFFICULTÉ>. Je l'ai remontée proprement à qui pouvait corriger, <CE_QUE_J_AI_FAIT>, et <RÉSULTAT>. »",
        avoid='ne racontez rien qui ressemble à un accès non autorisé, même ancien, même « pour voir ». L\'entretien évalue aussi votre éthique.',
    ),
]

METIER_RH: list[BankEntry] = [
    BankEntry(
        id='comment_menez_vous_un_entretien_de',
        question='Comment menez-vous un entretien de recrutement ?',
        answer="« Structuré : les mêmes questions pour tous les candidats du poste, ancrées sur du vécu — « racontez une fois où » plutôt que « comment feriez-vous ». Je note pendant, je décide après, jamais dans le couloir. »",
        avoid='ne parlez pas de feeling ni de « fit ». C\'est la porte ouverte aux biais, et la personne en face le sait.',
    ),
    BankEntry(
        id='un_manager_veut_se_separer_de',
        question="Un manager veut se séparer de quelqu'un « qui ne va pas ».",
        answer="« Je demande les faits : quels manquements, dits quand, écrits où. S'il n'y a rien d'écrit, le vrai travail commence par le retour au salarié — pas par la procédure. Mon rôle est que la suite soit juste et solide, dans cet ordre. »",
        avoid='ne devenez ni l\'exécutant du manager ni l\'avocat du salarié. Le jour où vous choisissez un camp par défaut, vous ne servez plus à rien.',
    ),
    BankEntry(
        id='on_vous_rapporte_des_faits_de',
        question='On vous rapporte des faits de harcèlement. Vos premiers gestes ?',
        answer="« Écouter sans qualifier, consigner les faits datés, et protéger d'abord — éloigner sans punir personne le temps de l'enquête. Puis l'enquête, réelle, avec les deux parties entendues. Ce que je ne fais jamais : promettre un secret que la loi ne me permet pas de tenir. »",
        avoid='ne minimisez pas et ne dramatisez pas au premier récit. Les deux détruisent la confiance qu\'il a fallu pour venir vous voir.',
    ),
    BankEntry(
        id='le_candidat_parfait_demande_au_dessus',
        question='Le candidat parfait demande vingt pour cent au-dessus de la grille.',
        answer="« Je regarde d'abord si la grille est juste — s'il est le troisième à demander ça, le problème est la grille, pas les candidats. Sinon : ce qui est possible hors salaire, et ce que coûte vraiment le poste non pourvu pendant six mois de plus. »",
        avoid='ne perdez pas le candidat pour défendre la grille par principe. Chiffrez ce que coûte le poste vide, puis arbitrez.',
    ),
    BankEntry(
        id='comment_mesurez_vous_qu_un_recrutement',
        question="Comment mesurez-vous qu'un recrutement est réussi ?",
        answer="« À un an, pas à la signature : la personne est là, elle tient le poste, et son manager referait le choix. Je regarde aussi le chemin — délai, expérience candidat — mais le juge, c'est l'année. »",
        avoid='ne répondez pas par le délai de recrutement. Recruter vite la mauvaise personne est le plus cher des échecs RH.',
    ),
    BankEntry(
        id='un_salarie_vient_vous_voir_en',
        question='Un salarié vient vous voir « en confiance ». Que garantissez-vous ?',
        answer="« Je le dis avant qu'il parle : ce qui reste entre nous, et ce que je ne pourrai pas garder pour moi — un danger, des faits graves. La confiance tient à cette clarté-là, pas à une promesse de silence intenable. »",
        avoid='ne promettez jamais la confidentialité absolue. Le jour où vous devez la rompre, vous perdez ce salarié et tous ceux à qui il parlera.',
    ),
    BankEntry(
        id='une_equipe_a_un_turnover_eleve',
        question='Une équipe a un turnover élevé. Que faites-vous ?',
        answer="« Je vais chercher les faits : les entretiens de départ relus ensemble, pas un par un. Le motif se répète toujours — et c'est souvent le management ou la charge, rarement le salaire seul. Ensuite je traite la cause, pas le symptôme. »",
        avoid='ne partez pas sur une prime de rétention. Payer les gens pour rester dans une équipe malade retarde le diagnostic.',
    ),
    BankEntry(
        id='comment_travaillez_vous_avec_les_representants',
        question='Comment travaillez-vous avec les représentants du personnel ?',
        answer="« En continu, pas seulement quand c'est obligatoire : un sujet difficile passe mieux quand il n'est pas le premier contact de l'année. Je donne l'information tôt, même incomplète — la découvrir par la rumeur coûte plus cher. »",
        avoid='ne les décrivez ni en adversaires ni en chambre d\'enregistrement. Les deux postures se paient en conflit.',
    ),
    BankEntry(
        id='un_manager_et_un_salarie_vous',
        question='Un manager et un salarié vous donnent deux versions incompatibles.',
        answer="« Je ne tranche pas sur les récits : je cherche ce qui est datable et vérifiable — écrits, témoins, chronologie. Et je garde en tête que la vérité est souvent entre les deux, pas au milieu : chacun dit vrai sur une partie. »",
        avoid='ne donnez pas raison au manager par réflexe hiérarchique. C\'est le réflexe que le salarié attend, et qu\'il testera.',
    ),
    BankEntry(
        id='la_diversite_au_dela_des_mots',
        question='La diversité : au-delà des mots, que faites-vous ?',
        answer="« Des mécanismes, pas des intentions : des annonces relues pour leur langage, des viviers élargis, des entretiens structurés qui comparent les mêmes choses. Et je mesure — sans mesure, la conviction ne survit pas au premier arbitrage. »",
        avoid='ne répondez pas par des valeurs. La question teste si vous savez transformer une intention en processus.',
    ),
    BankEntry(
        id='comment_annoncez_vous_une_decision_impopulaire',
        question='Comment annoncez-vous une décision impopulaire ?',
        answer="« Vite, en vrai, et sans la faire porter à d'autres : la décision, sa raison, ce qui ne changera pas et ce qui reste ouvert. Les gens encaissent une décision dure mieux qu'un flou qui dure. »",
        avoid='ne l\'enrobez pas d\'éléments de langage. Ils s\'entendent immédiatement et décrédibilisent aussi les annonces sincères.',
    ),
    BankEntry(
        id='comment_tenez_vous_la_confidentialite_des',
        question='Comment tenez-vous la confidentialité de ce que vous savez ?',
        answer="« Par une règle simple : je ne dis jamais d'où je sais, et je n'utilise une information que par le canal qui la rend actionnable. Le jour où l'on doute de ma discrétion, mon bureau devient vide — et un RH sans information ne protège plus personne. »",
        avoid='ne racontez pas un cas réel identifiable pour illustrer. Vous feriez la démonstration inverse.',
    ),
    BankEntry(
        id='de_quelle_mesure_rh_etes_vous',
        question='De quelle mesure RH êtes-vous le plus fier ?',
        answer="« <RÉALISATION>. <CE_QUE_J_AI_FAIT>, et <RÉSULTAT> — mesuré, pas ressenti. »",
        avoid='ne citez pas un processus déployé. Citez ce qu\'il a changé pour des personnes réelles.',
    ),
    BankEntry(
        id='comment_restez_vous_a_jour_en',
        question='Comment restez-vous à jour en droit du travail ?',
        answer="« Une source de référence suivie sérieusement, et le réflexe de vérifier avant d'affirmer — le droit social bouge trop pour la mémoire seule. Sur <COMPÉTENCE>, <CE_QUE_J_AI_FAIT>. »",
        avoid='ne jouez pas au juriste si vous ne l\'êtes pas. Savoir quand consulter est la compétence évaluée.',
    ),
    BankEntry(
        id='on_vous_demande_ce_que_les',
        question='« Les RH, ça ne produit rien. » On vous le dit en entretien.',
        answer="« Un mauvais recrutement coûte des mois de salaire, un départ évitable coûte le double, un contentieux perdu coûte plus encore. Mon travail, c'est que ces coûts n'arrivent pas — sur <RÉALISATION>, <RÉSULTAT>. »",
        avoid='ne vous vexez pas et ne philosophez pas sur l\'humain. Répondez en chiffres, c\'est le terrain de celui qui pose la question.',
    ),
]

METIER_MARKETING: list[BankEntry] = [
    BankEntry(
        id='comment_mesurez_vous_qu_une_campagne',
        question="Comment mesurez-vous qu'une campagne a marché ?",
        answer="« Par ce qu'elle devait produire, fixé avant de la lancer : des ventes, des inscriptions, des demandes — pas des impressions. Si l'objectif n'était pas mesurable avant le lancement, c'est le cadrage qui a échoué, pas la campagne. »",
        avoid='ne citez pas la portée ni les mentions j\'aime. C\'est le piège tendu par la question.',
    ),
    BankEntry(
        id='votre_budget_est_divise_par_deux',
        question='Votre budget est divisé par deux. Que coupez-vous ?',
        answer="« Ce qui ne se mesure pas d'abord, puis ce qui coûte le plus par résultat. Je protège ce qui rapporte de façon prouvée et ce qui met du temps à reconstruire — couper le long terme se paie l'année suivante, en pire. »",
        avoid='ne défendez pas le budget entier. Refuser d\'arbitrer, c\'est laisser quelqu\'un d\'autre couper à l\'aveugle.',
    ),
    BankEntry(
        id='le_commercial_dit_que_vos_leads',
        question='Le commercial dit que vos contacts ne valent rien.',
        answer="« Je vais écouter ses appels ou en faire avec lui — la réponse est là, pas dans les tableaux. Souvent les deux sont vrais : mes contacts sont trop tôt dans leur réflexion, et son discours ne les prend pas là où ils sont. On corrige les deux bouts. »",
        avoid='ne répondez pas par vos volumes. Le volume de contacts inutiles est exactement ce qu\'on vous reproche.',
    ),
    BankEntry(
        id='comment_definissez_vous_une_cible',
        question='Comment définissez-vous une cible ?',
        answer="« Par le problème qu'on résout, pas par la démographie : qui a ce problème assez fort pour payer, où se renseigne-t-il, qu'a-t-il déjà essayé. Puis je vais parler à quelques-uns en vrai — les personas de salle de réunion font de belles campagnes qui ne convertissent pas. »",
        avoid='ne récitez pas un persona avec prénom et âge. La question teste si vous êtes déjà sorti parler aux clients.',
    ),
    BankEntry(
        id='racontez_une_campagne_qui_a_echoue',
        question='Racontez une campagne qui a échoué.',
        answer="« Sur <RÉALISATION>, <DIFFICULTÉ>. Ce que les chiffres m'ont dit, c'est <RÉSULTAT>, et ce que j'aurais dû tester avant, c'est <POINT_À_AMÉLIORER>. La suivante a intégré la leçon : <CE_QUE_J_AI_FAIT>. »",
        avoid='ne choisissez pas un échec dû au budget ou à la validation tardive. On évalue votre lecture, pas vos excuses.',
    ),
    BankEntry(
        id='notoriete_ou_conversion_comment_arbitrez_vous',
        question='Notoriété ou conversion : comment arbitrez-vous ?',
        answer="« Par le stade de l'entreprise : sans notoriété, la conversion n'a rien à convertir ; sans conversion, la notoriété ne se finance pas. En pratique je sécurise la conversion d'abord — elle prouve — et je défends une part fixe pour le long terme, sanctuarisée. »",
        avoid='ne choisissez pas un camp par école. La question cherche un raisonnement de répartition, pas une doctrine.',
    ),
    BankEntry(
        id='que_testez_vous_en_premier_sur',
        question='Que testez-vous en premier sur une page qui ne convertit pas ?',
        answer="« La promesse avant la couleur du bouton : est-ce que la page dit en cinq secondes ce qu'on gagne et pour qui c'est ? Puis une seule chose à la fois, avec assez de trafic pour conclure — sinon c'est de la superstition avec des chiffres. »",
        avoid='ne racontez pas un test multivarié sur un petit trafic. Ça dit que vous testez pour le rituel, pas pour la réponse.',
    ),
    BankEntry(
        id='la_direction_veut_etre_sur_le',
        question='La direction veut « être sur le réseau du moment ».',
        answer="« Je demande qui on veut y toucher, et je vérifie si notre cible y est vraiment. Si oui, on essaie petit et mesuré. Si non, je montre où elle est — refuser sans contre-proposition, c'est perdre l'arbitrage suivant. »",
        avoid='ne cédez pas pour faire plaisir ni ne refusez par posture. Les deux se paient : l\'un en budget, l\'autre en influence.',
    ),
    BankEntry(
        id='comment_construisez_vous_un_message',
        question='Comment construisez-vous un message ?',
        answer="« Je pars des mots des clients — ceux des appels, des avis, des entretiens — pas des nôtres. Un bénéfice principal, une preuve, un appel à l'action. Si je dois expliquer le message, il est raté. »",
        avoid='ne partez pas des caractéristiques du produit. Le glissement bénéfice-caractéristique est exactement ce qu\'on écoute.',
    ),
    BankEntry(
        id='referencement_ou_payant_comment_repartissez_vous',
        question='Référencement naturel ou payant : comment répartissez-vous ?',
        answer="« Le payant pour apprendre vite et tenir le court terme, le naturel pour construire un actif qui reste. Le piège du tout-payant : le jour où on coupe, il ne reste rien. Je fais financer le second par ce que prouve le premier. »",
        avoid='n\'opposez pas les deux. Ils ne travaillent pas au même horizon, et c\'est la répartition qu\'on évalue.',
    ),
    BankEntry(
        id='quel_indicateur_refusez_vous_de_suivre',
        question='Quel indicateur refusez-vous de suivre ?',
        answer="« Ceux qui montent tout seuls sans que rien d'utile ne se passe — abonnés cumulés, impressions, mentions j'aime. Je les regarde, mais je refuse qu'on pilote dessus : un indicateur de vanité qui devient objectif fabrique du travail de vanité. »",
        avoid='ne dites pas que tout se suit. Refuser un indicateur est un acte de pilotage, et c\'est lui qu\'on teste.',
    ),
    BankEntry(
        id='une_crise_sur_les_reseaux_que',
        question='Une crise démarre sur les réseaux. Que faites-vous la première heure ?',
        answer="« Je qualifie avant de répondre : vraie faute, malentendu, ou provocation — les trois n'appellent pas la même réponse. Vraie faute : reconnaître vite, en une fois. Le pire des choix, c'est la réponse juridique à un problème humain. »",
        avoid='ne supprimez pas les commentaires en premier geste. La capture d\'écran survit toujours à la suppression.',
    ),
    BankEntry(
        id='comment_travaillez_vous_avec_des_creatifs',
        question='Comment travaillez-vous avec des créatifs ?',
        answer="« Je donne le problème, pas la solution : à qui on parle, ce qu'on veut qu'il fasse, ce qu'on a comme preuves. Et je critique par rapport au brief, jamais par goût — « je n'aime pas » n'est pas un retour. »",
        avoid='ne racontez pas de retours esthétiques. Le créatif en face de vous a déjà démissionné pour moins que ça.',
    ),
    BankEntry(
        id='votre_meilleure_campagne',
        question='Votre meilleure campagne ?',
        answer="« <RÉALISATION>. Le pari, c'était <CE_QUE_J_AI_FAIT>, et ça a donné <RÉSULTAT> — <CHIFFRE>. »",
        avoid='ne racontez pas la plus créative. Racontez celle qui a le mieux atteint son objectif, même si elle était sobre.',
    ),
    BankEntry(
        id='comment_prouvez_vous_la_valeur_du',
        question='Comment prouvez-vous la valeur du marketing en interne ?',
        answer="« En parlant la langue du chiffre d'affaires : ce que coûte un client acquis, ce qu'il rapporte, et ce que le marketing y change. Sur <RÉALISATION>, <CHIFFRE>. Le marketing qui ne se relie pas aux ventes finit coupé en premier. »",
        avoid='ne défendez pas la marque dans l\'abstrait. Celui qui arbitre le budget compte en euros, comptez avec lui.',
    ),
]

METIER_LOGISTIQUE: list[BankEntry] = [
    BankEntry(
        id='une_rupture_sur_votre_reference_la',
        question='Une rupture de stock sur votre référence la plus vendue. Que faites-vous ?',
        answer="« Dans l'ordre : sécuriser ce qui reste pour les commandes engagées, donner une date honnête au commerce, et chercher le dépannage — autre entrepôt, fournisseur alternatif, produit de substitution. Ensuite seulement, comprendre pourquoi l'alerte n'a pas sonné avant. »",
        avoid='ne commencez pas par chercher le coupable. La première heure appartient aux clients, pas à l\'enquête.',
    ),
    BankEntry(
        id='comment_dimensionnez_vous_un_stock',
        question='Comment dimensionnez-vous un stock ?',
        answer="« Par la demande réelle et sa variabilité, le délai de réapprovisionnement, et le coût de la rupture comparé au coût de possession. Le stock de sécurité se calcule, il ne se ressent pas — « large pour être tranquille » coûte tous les mois. »",
        avoid='ne répondez pas par une formule récitée. Dites ce que vous faites des références qui ne rentrent pas dans la formule.',
    ),
    BankEntry(
        id='un_transporteur_vous_lache_la_veille',
        question="Un transporteur vous lâche la veille d'un pic. Que faites-vous ?",
        answer="« J'active le plan B qui existe avant la crise : un second transporteur déjà référencé, même plus cher. Puis je trie ce qui doit absolument partir. Le jour même, on exécute — la renégociation attendra la semaine suivante. »",
        avoid='ne dites pas que ça ne vous arriverait pas grâce à votre relation transporteur. Ça arrive à tout le monde, et l\'entretien le sait.',
    ),
    BankEntry(
        id='l_inventaire_revele_un_ecart_entre',
        question="L'inventaire révèle un écart entre le système et le physique.",
        answer="« Je corrige le système sur le physique — la réalité a toujours raison — puis je cherche la cause par famille d'écart : erreurs de réception, de prélèvement, casse non déclarée, ou vol. Chaque cause a son remède, et aucun n'est « compter plus souvent » seul. »",
        avoid='ne banalisez pas l\'écart en « démarque habituelle ». C\'est l\'explication qui empêche de trouver la vraie.',
    ),
    BankEntry(
        id='comment_reduisez_vous_les_couts_sans',
        question='Comment réduisez-vous les coûts sans dégrader le service ?',
        answer="« Je pars de ce que le client ne voit pas : les trajets à vide, les surstocks, les reconditionnements évitables. Sur <RÉALISATION>, <CE_QUE_J_AI_FAIT>, et <RÉSULTAT> — sans toucher au délai de livraison. »",
        avoid='ne proposez pas de baisser le niveau de service en premier levier. C\'est le levier de celui qui n\'a pas cherché les autres.',
    ),
    BankEntry(
        id='comment_gerez_vous_un_pic_saisonnier',
        question='Comment gérez-vous un pic saisonnier ?',
        answer="« Il se gagne avant : les prévisions partagées avec le commerce, les renforts formés avant le rush, le stock pré-positionné. Pendant, je pilote court — un point chaque matin sur les trois chiffres qui comptent — et je garde une marge pour l'imprévu. »",
        avoid='ne racontez pas l\'héroïsme du pic passé en courant. Un pic réussi est ennuyeux, et c\'est ça qu\'on veut entendre.',
    ),
    BankEntry(
        id='que_regardez_vous_chaque_matin',
        question='Que regardez-vous chaque matin ?',
        answer="« Trois choses : ce qui n'est pas parti hier et pourquoi, ce qui doit partir aujourd'hui et ce qui le menace, et le taux de service de la veille. Le reste est du pilotage hebdomadaire — un tableau qu'on regarde chaque jour sans agir est un fond d'écran. »",
        avoid='ne listez pas quinze indicateurs. On évalue votre capacité à choisir ceux qui déclenchent une action.',
    ),
    BankEntry(
        id='un_litige_de_reception_avec_un',
        question='Un litige de réception avec un fournisseur récurrent.',
        answer="« Je documente à la réception — photos, quantités, réserves sur le bon — sinon il n'y a pas de litige, il y a ma parole contre la sienne. Puis je traite le cas, et si ça se répète, je remonte au contrat : un litige récurrent est un problème de processus, pas de livreur. »",
        avoid='ne bloquez pas le paiement en premier geste sur un bon fournisseur. Vous gagnerez le litige et perdrez les priorités de livraison.',
    ),
    BankEntry(
        id='l_entrepot_sature_comment_l_ameliorez',
        question="L'entrepôt sature. Comment l'améliorez-vous ?",
        answer="« Avant de pousser les murs : je regarde ce qui dort — les rotations lentes qui occupent les meilleures places, les emplacements figés depuis des années. Reclasser selon la rotation réelle libère souvent l'équivalent d'une travée. Sur <RÉALISATION>, <RÉSULTAT>. »",
        avoid='ne demandez pas des mètres carrés en première réponse. C\'est la réponse la plus chère, elle vient en dernier.',
    ),
    BankEntry(
        id='la_qualite_veut_bloquer_un_lot',
        question='La qualité veut bloquer un lot, le commerce veut livrer. Vous êtes au milieu.',
        answer="« Je ne tranche pas un débat qui a un propriétaire : si la qualité bloque, le lot ne part pas. Mon travail, c'est de réduire le coût de la décision — isoler le lot, chercher un lot de remplacement, donner au commerce une date fiable pour son client. »",
        avoid='ne cherchez pas le compromis « on livre une partie ». Sur un sujet de conformité, le compromis est le nom de la faute.',
    ),
    BankEntry(
        id='comment_choisissez_vous_un_prestataire',
        question='Comment choisissez-vous un prestataire ?',
        answer="« Sur ses chiffres vérifiables — taux de service, litiges, délais — et sur une visite : un quai se lit mieux qu'une plaquette. Puis je démarre petit avant de basculer, et je garde toujours une alternative vivante. Un prestataire unique finit par le savoir. »",
        avoid='ne choisissez pas au prix seul, et dites-le. Le moins cher qui livre mal coûte plus cher, et l\'entretien attend cette phrase.',
    ),
    BankEntry(
        id='la_securite_dans_l_entrepot_votre',
        question="La sécurité dans l'entrepôt : votre rôle ?",
        answer="« Elle passe avant la cadence, et ça se prouve dans les arbitrages : une allée encombrée arrête le prélèvement, un chariot douteux s'immobilise, même un jour de pic. Le jour où l'équipe voit la sécurité céder devant l'urgence, elle cède partout. »",
        avoid='ne récitez pas les consignes affichées. Racontez un moment où la sécurité a coûté de la productivité et où vous avez tenu.',
    ),
    BankEntry(
        id='comment_gerez_vous_les_retours',
        question='Comment gérez-vous les retours ?',
        answer="« Comme un flux à part entière, pas comme une corvée : un circuit dédié, un tri rapide — remise en stock, reconditionnement, rebut — et une boucle vers l'amont, parce qu'un retour a toujours une cause et qu'elle est souvent évitable. »",
        avoid='ne traitez pas les retours comme du bruit. Leur coût est invisible dans les tableaux et réel dans les marges.',
    ),
    BankEntry(
        id='jusqu_ou_allez_vous_en_tracabilite',
        question='Jusqu\'où allez-vous en traçabilité ?',
        answer="« Jusqu'où le risque le justifie : au lot quand la réglementation ou le rappel l'exigent, à l'unité quand la valeur ou la fraude le demandent. Tracer coûte à chaque mouvement — je trace ce qui protège, pas ce qui rassure. »",
        avoid='ne promettez pas la traçabilité totale. Elle n\'existe que dans les appels d\'offres.',
    ),
    BankEntry(
        id='quelle_amelioration_avez_vous_menee',
        question='Quelle amélioration avez-vous menée de bout en bout ?',
        answer="« <RÉALISATION>. Le point de départ, c'était <DIFFICULTÉ>. <CE_QUE_J_AI_FAIT>, avec l'équipe de terrain — pas contre elle — et <RÉSULTAT>, tenu dans la durée. »",
        avoid='ne racontez pas une amélioration qui n\'a pas survécu à votre attention. « Tenu six mois après » est la partie qui compte.',
    ),
]

#: « Avant d'entrer » : le bloc qu'on lit avec cinq minutes et un couloir.
#:
#: Écrit à la main comme le reste de la banque, un plan par type d'entretien,
#: du geste le plus rentable au moins. Trois gestes maximum : au-delà, ce n'est
#: plus un plan, c'est une révision — et il n'y a pas le temps d'une révision.
#: Aucune balise : ce bloc se lit tel quel, il ne se remplit pas.
#:
#: Quand une personnalisation a été générée, son plan d'action — plus
#: spécifique — remplace celui-ci côté client.
ACTION_PLANS: dict[str, list[str]] = {
    "recruitment": [
        "Relisez l'annonce une dernière fois : c'est d'elle que viendront les questions.",
        "Redites votre réalisation à voix haute, une fois, avec son résultat.",
        "Gardez une question à poser sur le poste : elle se prépare maintenant, pas dans la pièce.",
    ],
    "internal_mobility": [
        "Redites vos deux phrases : pourquoi vous partez, pourquoi vous arrivez. C'est sur les deux qu'on vous attend.",
        "Préparez un mot sur ce que votre départ coûte à votre équipe actuelle, et comment vous proposez de l'amortir.",
        "Nommez précisément ce qui vous attire dans l'équipe visée : « changer » n'est pas une destination.",
    ],
    "role_evolution": [
        "Relisez vos exemples : chaque responsabilité visée doit s'appuyer sur une chose que vous faites déjà.",
        "Redites en une phrase ce que vous demandez, et depuis quand vous en tenez déjà une partie.",
        "Décidez de votre réponse si c'est « pas maintenant » : ce que vous demandez à la place, et à quelle échéance.",
    ],
    "annual_review": [
        "Relisez vos objectifs de l'année un par un, avec où vous en êtes sur chacun.",
        "Choisissez le résultat que vous voulez qu'on retienne, et redites-le à voix haute avec son chiffre.",
        "Préparez ce que vous demandez pour l'année qui vient — l'entretien sert aussi à ça.",
    ],
    "mid_year": [
        "Relisez vos objectifs et repérez ceux qui ne tiendront pas en l'état.",
        "Pour chacun, préparez l'ajustement que vous proposez : c'est maintenant qu'il se négocie, pas en fin d'année.",
        "Choisissez une avancée à mettre en avant, même modeste — le point d'étape n'est pas qu'une liste de retards.",
    ],
    "performance_review": [
        "Relisez chaque affirmation que vous comptez faire, et vérifiez que vous pouvez l'étayer d'un fait.",
        "Redites votre meilleur résultat à voix haute, avec ce qui le prouve.",
        "Repérez le point qu'on pourrait vous opposer et décidez de votre réponse — une phrase, pas une plaidoirie.",
    ],
}
