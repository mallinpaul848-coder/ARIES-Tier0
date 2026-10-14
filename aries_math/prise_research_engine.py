"""ARIES Tier-0 PRISE Research Math Engine.
Deterministic research utilities; experimental descriptors are not mathematical proofs.
Standard-library only.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json, math
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

VORTEX_CYCLE: Tuple[int, ...] = (1, 2, 4, 8, 7, 5)
PHASE8_DIRECTIONS: Tuple[Tuple[int, int], ...] = ((1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1))
PRIZE_PROBLEM_ROUTES = {
 "P_VS_NP": ("complexity", "SAT", "proof_obligations"),
 "RIEMANN_HYPOTHESIS": ("analytic_number_theory", "zero_checks", "proof_obligations"),
 "NAVIER_STOKES": ("PDE", "regularity", "numerical_checks", "proof_obligations"),
 "YANG_MILLS": ("mathematical_physics", "existence_gap", "proof_obligations"),
 "HODGE_CONJECTURE": ("algebraic_geometry", "cycle_class", "proof_obligations"),
 "BIRCH_SWINNERTON_DYER": ("number_theory", "elliptic_curves", "proof_obligations"),
}

class DigitalRootSystem:
    """Base-10 digital-root utilities."""
    @staticmethod
    def compute(n: int) -> int:
        n = int(n)
        if n == 0: return 0
        r = abs(n) % 9
        return 9 if r == 0 else r
    @staticmethod
    def triad(n: int) -> Dict[str, int]:
        n = int(n)
        return {"digital_root": DigitalRootSystem.compute(n), "mod_3": n % 3, "mod_9": n % 9}

def vortex369(n: int) -> int:
    """Return the 1,2,4,8,7,5 cycle position; zero maps to zero."""
    if int(n) == 0: return 0
    return VORTEX_CYCLE[(abs(int(n)) - 1) % len(VORTEX_CYCLE)]

def phase8(x: float, y: float) -> Dict[str, Any]:
    """Map a finite 2-D vector to one of eight compass directions."""
    x, y = float(x), float(y)
    if not (math.isfinite(x) and math.isfinite(y)): raise ValueError("Phase-8 inputs must be finite")
    if x == 0 and y == 0: return {"phase": None, "direction": (0, 0), "magnitude": 0.0}
    angle = math.atan2(y, x) % (2 * math.pi)
    phase = int(math.floor((angle + math.pi / 8) / (math.pi / 4))) % 8
    return {"phase": phase, "direction": PHASE8_DIRECTIONS[phase], "magnitude": math.hypot(x, y)}

def helixo_features(values: Sequence[float]) -> Dict[str, Any]:
    """Reproducible descriptive features, not a claim of a physical law."""
    xs = [float(v) for v in values]
    if any(not math.isfinite(v) for v in xs): raise ValueError("Helixo inputs must be finite")
    if not xs: return {"count":0,"sum":0.0,"mean":0.0,"energy":0.0,"digital_roots":[],"phase8":[]}
    total = math.fsum(xs)
    return {"count":len(xs), "sum":total, "mean":total/len(xs),
            "energy":math.fsum(v*v for v in xs),
            "digital_roots":[DigitalRootSystem.compute(int(v)) for v in xs],
            "phase8":[phase8(xs[i], xs[i+1]) for i in range(0,len(xs)-1,2)]}

@dataclass
class PRISEProfile:
    priority: float = 1.0
    risk: float = 1.0
    impact: float = 1.0
    systemic: float = 1.0
    emergent: float = 1.0
    def score(self) -> float:
        vals = asdict(self)
        if any(not math.isfinite(v) or v < 0 for v in vals.values()):
            raise ValueError("PRISE weights must be finite and non-negative")
        return (self.priority+self.impact+self.systemic+self.emergent)/(1.0+self.risk)

@dataclass
class ProofObligation:
    statement: str
    method: str
    status: str = "open"
    evidence: List[str] = field(default_factory=list)
    def update(self, status: str, evidence: Optional[str] = None) -> None:
        if status not in {"open","candidate","refuted","verified"}:
            raise ValueError("invalid proof-obligation status")
        if status == "verified" and not evidence:
            raise ValueError("verified requires independently checkable proof evidence")
        self.status = status
        if evidence: self.evidence.append(evidence)

class ARIESPRISEResearchEngine:
    """Problem router, experimental feature calculator, and audit-ledger helper."""
    version = "1.0.0"
    def analyze(self, problem: str, values: Sequence[float] = (), profile: Optional[PRISEProfile] = None) -> Dict[str, Any]:
        key = problem.strip().upper().replace(" ","_").replace("-","_")
        routes = PRIZE_PROBLEM_ROUTES.get(key, ("general_reasoning","counterexample_search","proof_obligations"))
        p = profile or PRISEProfile()
        payload = {"engine":"ARIES PRISE Research Math Engine","version":self.version,
          "problem":key,"route":list(routes),"prise":{**asdict(p),"score":p.score()},
          "features":helixo_features(values),"evidence_status":"exploratory_only","proof_claim":False,
          "warning":"Digital-root, vortex, Phase-8, and Helixo features are experimental descriptors. They do not prove P vs NP or any Millennium Prize problem."}
        canonical = json.dumps(payload,sort_keys=True,separators=(",",":"),allow_nan=False)
        payload["fingerprint_sha256"] = sha256(canonical.encode("utf-8")).hexdigest()
        return payload
    @staticmethod
    def audit_obligations(obligations: Iterable[ProofObligation]) -> Dict[str, Any]:
        items = [asdict(o) for o in obligations]
        counts = {s:sum(1 for i in items if i["status"]==s) for s in ("open","candidate","refuted","verified")}
        return {"obligations":items,"counts":counts,
          "research_complete":bool(items) and counts["open"]==0 and counts["candidate"]==0,
          "millennium_problem_solved":False,
          "note":"Checklist completion is not a mathematical proof."}
