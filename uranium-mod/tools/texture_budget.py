"""Per-texture colour budgets, shared by the generator and the validator.

A 16x16 texture drawn with dozens of nearly-identical shades is the clearest
single sign that a machine made it rather than a person. Vanilla blocks run
6-17 distinct colours and vanilla items 7-11; past roughly twenty the eye stops
reading shapes and starts reading noise, however good the shapes are.

These numbers are what each texture actually uses, not a ceiling with room to
drift. Raising one should be a decision, not an accident -- which is the point
of keeping them in a file both the generator and the asset validator read.
"""

DEFAULT_BUDGET = 12

COLOUR_BUDGET = {
    # Blocks: matrix greys plus the six-step uranium ramp.
    "uranium_ore.png": 4 + 6,
    "deepslate_uranium_ore.png": 5 + 6,
    "raw_uranium_block.png": 3 + 6,
    "uranium_block.png": 6,
    # The centrifuge maps carry steel, gold trim and green glow at once.
    "centrifuge_tower.png": 10,
    "centrifuge_tower_glow.png": 3,
    "centrifuge_rotor_top.png": 9,
    "centrifuge_rotor_top_glow.png": 4,
    "centrifuge_shaft.png": 9,
    "centrifuge_base.png": 6,
    "centrifuge_deck.png": 5,
    "centrifuge_bottom.png": 7,
    # A 64x32 sheet the player model cuts up, not a sprite.
    "shielded.png": 8,
    # The GUI sheet is a widget skin rather than pixel art: bevels, a heat
    # gradient and text all legitimately need many tones.
    "centrifuge.png": 4096,
    "icon.png": 64,
}


def budget_for(basename):
    return COLOUR_BUDGET.get(basename, DEFAULT_BUDGET)
