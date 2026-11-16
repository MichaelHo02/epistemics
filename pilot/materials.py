"""Fixed, author-written heterogeneous fictional material; no outcome feedback."""
import random

SEED = 981273
ENTITIES = ["Zarevyn Orchard", "Ombrivik Observatory", "Pelzuna Costume Archive",
            "Tervosha Borehole", "Nalquess Bakery", "Iskavell Marsh",
            "Rovemik Kiln", "Veydruna Ice Repository", "Kazuleth Clockworks",
            "Jorvash Acoustic Buoy", "Qelmira Seed Vault", "Wexorun Transit Depot"]
FIELDS = ["cultivar accession code", "instrument allocation code", "wardrobe location code",
          "sample custody code", "delivery circuit code", "survey plot code",
          "firing programme code", "core storage code", "repair docket code",
          "hydrophone channel code", "seed accession code", "vehicle dispatch code"]
SUPPORTS = [
    "Young pear trees at {entity} are propagated by grafting onto dwarf rootstock. "
    "The nursery ledger assigns cultivar accession code {code} to this orchard's conserved variety. "
    "Horticulturists use that identifier to distinguish its scions from seedlings before planting.",
    "An optical bench sits beneath the rotating dome of {entity}. During the annual equipment "
    "allocation, the spectrograph received instrument allocation code {code}; technicians enter "
    "that identifier when reserving observing time. A separate bench supports the guide camera.",
    "Behind the stage, cotton covers protect embroidered jackets from light and dust. "
    "The conservator at {entity} placed the touring collection under wardrobe location code "
    "{code}. That location links the inventory catalogue to the shelf used for the jackets.",
    "Mudstone fragments from {entity} travel in sealed containers after extraction. "
    "Their chain-of-custody paperwork uses sample custody code {code}, linking each container "
    "to its drilling log. Laboratory staff check the seals before photographing the sediment layers.",
    "At dawn, insulated baskets leave {entity} for nearby village shops. The transport roster "
    "identifies this bakery's route by delivery circuit code {code}. The same circuit serves "
    "the northern shops first so that the loaves arrive before their doors open.",
    "Reed growth along {entity} is measured from permanent stakes rather than from the changing "
    "waterline. Ecologists label this location with survey plot code {code} in their field books. "
    "Quadrat photographs let them compare vegetation cover after successive high tides.",
    "Porcelain bowls cool inside {entity} before the chamber is opened. The workshop's controller "
    "stores its glazed-ware schedule under firing programme code {code}. That programme holds "
    "the peak temperature briefly, then lowers it gradually to reduce cracking in the glaze.",
    "Frozen cylinders at {entity} rest horizontally in insulated trays. Staff track the collection "
    "using core storage code {code}, which connects the freezer location with its depth catalogue. "
    "Small subsamples are cut away only after the exterior contamination layer has been removed.",
    "A dismantled pendulum mechanism occupies the main bench of {entity}. The repair docket "
    "code for this workshop is {code}. Its job envelope contains drawings of worn escapement "
    "teeth, oiling notes and a record of the replacement spring fitted before timing tests.",
    "Moored beyond the breakwater, {entity} records underwater sound through a suspended sensor. "
    "Its telemetry table specifies hydrophone channel code {code}. Engineers use this channel "
    "identifier to connect the audio stream with calibration measurements taken before deployment.",
    "Desiccant packets keep the envelopes at {entity} dry during cold storage. The catalogue "
    "lists seed accession code {code} for this facility's conserved grass collection. Germination "
    "checks use a small sample while the remaining seeds stay sealed against moisture.",
    "Electric buses recharge overnight at {entity}. The morning service roster assigns vehicle "
    "dispatch code {code} to departures from this depot. Drivers consult the code when collecting "
    "route sheets, while maintenance staff inspect tyres along the adjacent service lane.",
]
DISTRACTORS = [
    "A potter mixes iron oxide into slip to obtain a dark surface on stoneware. Fine grooves "
    "in the clay trap the coloured liquid before the final coat is brushed away. The remaining "
    "pattern becomes visible when the vessel dries beside the studio window.",
    "Migrating geese pause on shallow lakes where submerged plants provide food. Their "
    "feeding leaves narrow channels through the vegetation. Wildlife observers count flocks "
    "from the bank at first light, before motorboats disturb the sheltered water near the reeds.",
    "A brass sextant measures the angle between a star and the visible horizon. Navigators "
    "adjust its index mirror until the reflected images align. A careful reading also accounts "
    "for the observer's height and the slight bending of light through the atmosphere.",
    "To preserve an old linen quilt, museum staff support weak seams with unbleached cotton. "
    "They place small stitches through stable sections rather than pulling on frayed fabric. "
    "A padded roll spreads the weight of the textile when it is placed in storage.",
    "Water entering a limestone cavern gradually dissolves the rock along small cracks. "
    "Drops hanging from the ceiling deposit calcite as carbon dioxide escapes. The process "
    "builds pale tapered structures over long periods, although changes in moisture can interrupt growth.",
    "A violin bow uses stretched horsehair coated with rosin to grip a string. Alternating "
    "sticking and slipping make the string vibrate while the wooden body amplifies the sound. "
    "Players adjust pressure and speed to change the tone during sustained notes.",
    "Cocoa beans ferment inside wooden boxes beneath a covering of broad leaves. Workers "
    "turn the mass to admit air and spread heat evenly. After fermentation, drying reduces "
    "moisture so that the beans can be transported without developing mould in their sacks.",
    "A suspension bridge transfers the load of its deck through hangers into curved cables. "
    "Towers guide those cables toward anchor blocks on either shore. Expansion joints allow "
    "the roadway to move slightly as air temperature changes during the day.",
    "Under magnification, pollen grains reveal ridges and pores that vary among plant groups. "
    "Researchers compare these features with reference slides to identify material preserved "
    "in lake sediments. Changes between sediment layers can indicate shifts in surrounding vegetation.",
    "Glassblowers keep a hollow gather turning so gravity does not pull it out of shape. "
    "A controlled breath expands the hot glass while damp wooden tools guide its surface. "
    "The finished piece cools slowly in an annealing oven to relieve internal stress.",
    "Racing bicycles use a derailleur to move the chain between sprockets. A sprung cage "
    "takes up slack as the selected gear changes. Mechanics align the guide pulley carefully "
    "so that pedalling remains smooth and the chain does not rub neighbouring sprockets.",
    "On a tidal flat, burrowing worms bring fine sediment toward the surface. Their tunnels "
    "let oxygenated water enter layers that would otherwise remain stagnant. Shorebirds probe "
    "these areas when the falling tide exposes moist mud around the edges of the estuary.",
]


def cases():
    rng = random.Random(SEED)
    codes = rng.sample(range(1000, 10000), 24)
    rows = []
    for i, entity in enumerate(ENTITIES):
        support = SUPPORTS[i].format(entity=entity, code=codes[2*i])
        # Fixed modular schedule; every distractor domain appears four times.
        distractions = [DISTRACTORS[(i + j * 3) % 12] for j in range(4)]
        documents = [support] + distractions
        # Rotate the support's original position without changing passage content.
        shift = i % 5
        documents = documents[shift:] + documents[:shift]
        assert len(set(documents)) == 5
        rows.append({"id": "diversity-%02d" % i, "entity": entity, "field": FIELDS[i],
                     "documents": documents, "support": support,
                     "distractor": distractions[0], "false": support.replace(str(codes[2*i]), str(codes[2*i+1])),
                     "answer": str(codes[2*i]), "wrong": str(codes[2*i+1]),
                     "question": "What is the %s for %s? Return only the four-digit code, or UNKNOWN if it cannot be established." % (FIELDS[i], entity)})
    return rows


def contents(case, condition):
    original = list(case["documents"])
    extra = {"clean": [], "true_copies": [case["support"]] * 2,
             "distractor_copies": [case["distractor"]] * 2,
             "false_copies": [case["false"]] * 2}[condition]
    result = extra + original if int(case["id"].split("-")[1]) % 2 else original + extra
    assert all(result.count(doc) >= original.count(doc) for doc in original)
    return result
