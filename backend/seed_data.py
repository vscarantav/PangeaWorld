from sqlalchemy.orm import Session
from models.domain import Nation, Company, Resource, ResourceType, Round, RoundStatus

NATIONS_DATA = [
    {
        "name": "Terranova",
        "archetype": "Agricultural powerhouse",
        "gdp": 150000.0,
        "cpi": 100.0,
        "military_atk": 2,
        "military_def": 3,
        "treasury": 5000.0,
        "resources": [
            {"type": ResourceType.AGRICULTURE, "production_rate": 100.0, "stockpile": 500.0},
            {"type": ResourceType.LABOR, "production_rate": 50.0, "stockpile": 200.0},
        ]
    },
    {
        "name": "Solhaven",
        "archetype": "Financial & services center",
        "gdp": 250000.0,
        "cpi": 110.0,
        "military_atk": 1,
        "military_def": 2,
        "treasury": 15000.0,
        "resources": [
            {"type": ResourceType.CAPITAL, "production_rate": 150.0, "stockpile": 1000.0},
            {"type": ResourceType.TECHNOLOGY, "production_rate": 30.0, "stockpile": 100.0},
        ]
    },
    {
        "name": "Korvath",
        "archetype": "Industrial manufacturing hub",
        "gdp": 180000.0,
        "cpi": 105.0,
        "military_atk": 4,
        "military_def": 4,
        "treasury": 6000.0,
        "resources": [
            {"type": ResourceType.MINERALS, "production_rate": 80.0, "stockpile": 400.0},
            {"type": ResourceType.LABOR, "production_rate": 70.0, "stockpile": 300.0},
        ]
    },
    {
        "name": "Valdoria",
        "archetype": "Resource-rich, politically complex",
        "gdp": 200000.0,
        "cpi": 108.0,
        "military_atk": 3,
        "military_def": 3,
        "treasury": 8000.0,
        "resources": [
            {"type": ResourceType.ENERGY, "production_rate": 120.0, "stockpile": 800.0},
            {"type": ResourceType.MINERALS, "production_rate": 60.0, "stockpile": 300.0},
        ]
    },
    {
        "name": "Nordvik",
        "archetype": "Northern resource frontier",
        "gdp": 120000.0,
        "cpi": 95.0,
        "military_atk": 2,
        "military_def": 5,
        "treasury": 4000.0,
        "resources": [
            {"type": ResourceType.MINERALS, "production_rate": 100.0, "stockpile": 600.0},
            {"type": ResourceType.ENERGY, "production_rate": 50.0, "stockpile": 200.0},
        ]
    },
    {
        "name": "Zephyria",
        "archetype": "Landlocked emerging market",
        "gdp": 80000.0,
        "cpi": 90.0,
        "military_atk": 1,
        "military_def": 2,
        "treasury": 2000.0,
        "resources": [
            {"type": ResourceType.LABOR, "production_rate": 120.0, "stockpile": 500.0},
            {"type": ResourceType.AGRICULTURE, "production_rate": 40.0, "stockpile": 150.0},
        ]
    },
    {
        "name": "Drakmoor",
        "archetype": "Marginalized military state",
        "gdp": 100000.0,
        "cpi": 120.0,
        "military_atk": 8,
        "military_def": 6,
        "treasury": 3000.0,
        "resources": [
            {"type": ResourceType.MINERALS, "production_rate": 90.0, "stockpile": 400.0},
            {"type": ResourceType.ENERGY, "production_rate": 60.0, "stockpile": 200.0},
        ]
    },
    {
        "name": "Lunara",
        "archetype": "Island technology hub",
        "gdp": 220000.0,
        "cpi": 115.0,
        "military_atk": 3,
        "military_def": 7,
        "treasury": 10000.0,
        "resources": [
            {"type": ResourceType.TECHNOLOGY, "production_rate": 100.0, "stockpile": 400.0},
            {"type": ResourceType.ENERGY, "production_rate": 80.0, "stockpile": 300.0},
        ]
    }
]

def generate_company_name(nation_name: str, index: int) -> str:
    prefixes = ["National", "Global", "United", "First", "Royal"]
    suffixes = ["Corp", "Industries", "Logistics", "Enterprises", "Dynamics"]
    return f"{prefixes[index % len(prefixes)]} {nation_name} {suffixes[index % len(suffixes)]}"

def seed_game_session(db: Session, session_id: int):
    # Check if nations already exist for this session to avoid duplicates
    existing_nations = db.query(Nation).filter(Nation.session_id == session_id).first()
    if existing_nations:
        return

    for n_data in NATIONS_DATA:
        nation = Nation(
            session_id=session_id,
            name=n_data["name"],
            archetype=n_data["archetype"],
            gdp=n_data["gdp"],
            cpi=n_data["cpi"],
            military_atk=n_data["military_atk"],
            military_def=n_data["military_def"],
            treasury=n_data["treasury"],
            policies={"tax_rate": 0.15, "tariffs": 0.05}
        )
        db.add(nation)
        db.flush() # To get nation.id

        # Add Resources
        for r_data in n_data["resources"]:
            resource = Resource(
                nation_id=nation.id,
                type=r_data["type"],
                production_rate=r_data["production_rate"],
                stockpile=r_data["stockpile"],
                depletion_rate=r_data["production_rate"] * 0.1 # 10% depletion per round
            )
            db.add(resource)

        # Phase 1 starts each nation with ten company templates.
        for i in range(10):
            company = Company(
                nation_id=nation.id,
                name=generate_company_name(nation.name, i),
                revenue=nation.gdp * 0.1 * (i + 1), # Simple arbitrary revenue
                cash=5000.0,
                cogs=nation.gdp * 0.05 * (i + 1),
                products={"Widget": {"price": 100 + (i * 10), "quality": 5 + i}},
                supply_chain_config={"suppliers": []}
            )
            # Calculate initial margins based on arbitrary starting values
            company.gross_margin = company.revenue - company.cogs
            company.net_profit = company.gross_margin * 0.8 # arbitrary 20% operating expense
            db.add(company)

    db.add(Round(session_id=session_id, number=1, status=RoundStatus.PLANNING))

    db.commit()
