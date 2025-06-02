from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class Company:
    company_id: str
    category: str
    name: str
    phone: List[str]
    address: str
    city: str
    state: str
    postalCode: int
    websiteUrl: Optional[str]
    years: Optional[int]
    description: Optional[str]
    reportUrl: str
    owners: Dict[str, str]
