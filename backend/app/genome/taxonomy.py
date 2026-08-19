TRAITS = [
    "AI Infrastructure",
    "Consumer Hardware",
    "Data Center",
    "Robotics",
    "Automotive",
    "Enterprise",
    "Cloud",
    "Developer Tools",
    "Software",
    "Other"
]

def get_base_genome_vector():
    """Returns a genome vector initialized to 0.0 for all traits."""
    return {trait: 0.0 for trait in TRAITS}
