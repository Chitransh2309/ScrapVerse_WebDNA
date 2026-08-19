import math
from typing import List, Dict, Any
from app.db.models.genome_models import GenomeSnapshot
from app.db.models.mutation_models import MutationCandidate
from app.db.models.evidence_models import Evidence

# Deterministic Severity Thresholds
SEVERITY_THRESHOLDS = {
    "insignificant": 0.05,
    "low": 0.10,
    "medium": 0.20,
    "high": 0.35,
    "critical": 0.50
}

def determine_severity(magnitude: float) -> str:
    if magnitude >= SEVERITY_THRESHOLDS["critical"]:
        return "critical"
    elif magnitude >= SEVERITY_THRESHOLDS["high"]:
        return "high"
    elif magnitude >= SEVERITY_THRESHOLDS["medium"]:
        return "medium"
    elif magnitude >= SEVERITY_THRESHOLDS["low"]:
        return "low"
    else:
        return "insignificant"

def determine_mutation_type(old_val: float, new_val: float) -> str:
    if old_val < 0.01 and new_val > 0.01:
        return "Addition"
    elif new_val > old_val:
        return "Expansion"
    else:
        return "Contraction"

def calculate_confidence(evidences: List[Evidence]) -> float:
    """
    Deterministic confidence based on evidence count and diversity.
    """
    if not evidences:
        return 0.0
        
    source_types = set([ev.type for ev in evidences])
    diversity_bonus = min(0.2, (len(source_types) - 1) * 0.1)
    
    # Base confidence relies on the strongest evidence piece
    base_confidence = max([ev.confidence for ev in evidences])
    
    # Adding volume bonus
    volume_bonus = min(0.15, len(evidences) * 0.02)
    
    final_confidence = min(0.99, base_confidence + diversity_bonus + volume_bonus)
    return round(final_confidence, 4)

def compare_genomes(
    g1: GenomeSnapshot, 
    g2: GenomeSnapshot, 
    job_id: str,
    recent_evidence: List[Evidence]
) -> List[MutationCandidate]:
    """
    Compares two genomes and returns a list of MutationCandidates for deltas.
    """
    mutations = []
    
    traits = set(g1.traits.keys()).union(set(g2.traits.keys()))
    
    # Calculate overall vector magnitude
    # We could use overall Euclidean distance, but spec asks to calculate per trait first, 
    # then maybe overall. The spec says "MutationMagnitude = ||G2 - G1||". 
    # We will also calculate per-trait magnitude which is simply abs(delta).
    
    for trait in traits:
        old_val = g1.traits.get(trait, 0.0)
        new_val = g2.traits.get(trait, 0.0)
        
        delta = new_val - old_val
        magnitude = abs(delta)
        
        if magnitude >= SEVERITY_THRESHOLDS["insignificant"]:
            # Gather relevant evidence for this trait
            trait_evidence = [ev for ev in recent_evidence if ev.trait == trait]
            evidence_ids = [ev.id for ev in trait_evidence]
            confidence = calculate_confidence(trait_evidence)
            
            percent_change = 0.0
            if old_val > 0:
                percent_change = (delta / old_val) * 100.0
            elif old_val == 0 and new_val > 0:
                percent_change = 100.0 # Technically infinite, but we'll cap at 100 for additions
                
            mutation = MutationCandidate(
                company_id=g2.company_id,
                sequence_job_id=job_id,
                trait=trait,
                old_value=round(old_val, 4),
                new_value=round(new_val, 4),
                delta=round(delta, 4),
                percentage_change=round(percent_change, 2),
                mutation_type=determine_mutation_type(old_val, new_val),
                magnitude=round(magnitude, 4),
                severity=determine_severity(magnitude),
                confidence=confidence,
                evidence_ids=evidence_ids
            )
            mutations.append(mutation)
            
    return mutations
