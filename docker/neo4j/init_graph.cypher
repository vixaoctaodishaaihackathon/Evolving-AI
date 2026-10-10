// Neo4j Initialization Script: Tier-N Global Supply Chain Knowledge Graph
// Compatible with Neo4j 5.x cypher-shell and Neo4j Browser

// Phase 1: Constraints and Indexes (Execute separately or in sequence)
CREATE CONSTRAINT unique_supplier_id IF NOT EXISTS FOR (s:Supplier) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT unique_component_id IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT unique_facility_id IF NOT EXISTS FOR (f:Facility) REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT unique_corridor_id IF NOT EXISTS FOR (cr:Corridor) REQUIRE cr.id IS UNIQUE;

// Phase 2: Enterprise OEM Node
MERGE (oem:Enterprise {id: "OEM_APEX"})
ON CREATE SET 
    oem.name = "Apex Global Dynamics Corp",
    oem.sector = "Automotive & Industrial Automation",
    oem.headquarters = "Detroit, USA",
    oem.sla_tolerance_days = 3;

// Phase 3: Tier-1 Direct Sub-System Integrators
MERGE (s:Supplier {id: "SUP_T1_01"})
ON CREATE SET s.name = "Alpha PowerSystems GmbH", s.tier = 1, s.country = "Germany", s.reliability_score = 0.94, s.contract_value_usd = 8500000.0, s.single_source = false;

MERGE (s:Supplier {id: "SUP_T1_02"})
ON CREATE SET s.name = "Kyoto Robotics & Sensors Ltd", s.tier = 1, s.country = "Japan", s.reliability_score = 0.96, s.contract_value_usd = 12000000.0, s.single_source = true;

MERGE (s:Supplier {id: "SUP_T1_03"})
ON CREATE SET s.name = "Shenzhen Mechatronics Group", s.tier = 1, s.country = "China", s.reliability_score = 0.88, s.contract_value_usd = 6200000.0, s.single_source = false;

// Phase 4: Tier-2 Component Manufacturers
MERGE (s:Supplier {id: "SUP_T2_01"})
ON CREATE SET s.name = "Nordic Silicon Wafers AS", s.tier = 2, s.country = "Norway", s.reliability_score = 0.92, s.contract_value_usd = 4100000.0, s.single_source = false;

MERGE (s:Supplier {id: "SUP_T2_02"})
ON CREATE SET s.name = "Formosa Micro-Controllers Corp", s.tier = 2, s.country = "Taiwan", s.reliability_score = 0.95, s.contract_value_usd = 7800000.0, s.single_source = true;

MERGE (s:Supplier {id: "SUP_T2_03"})
ON CREATE SET s.name = "Penang Packaging & Test Ltd", s.tier = 2, s.country = "Malaysia", s.reliability_score = 0.89, s.contract_value_usd = 3200000.0, s.single_source = false;

// Phase 5: Tier-3 Raw Materials & Chemical Refiners
MERGE (s:Supplier {id: "SUP_T3_01"})
ON CREATE SET s.name = "Atacama Lithium Minerals SA", s.tier = 3, s.country = "Chile", s.reliability_score = 0.85, s.contract_value_usd = 2500000.0, s.single_source = true;

MERGE (s:Supplier {id: "SUP_T3_02"})
ON CREATE SET s.name = "Pilbara Rare Earths Ltd", s.tier = 3, s.country = "Australia", s.reliability_score = 0.91, s.contract_value_usd = 3900000.0, s.single_source = false;

MERGE (s:Supplier {id: "SUP_T3_03"})
ON CREATE SET s.name = "Rheinland Speciality Polymer AG", s.tier = 3, s.country = "Germany", s.reliability_score = 0.93, s.contract_value_usd = 1800000.0, s.single_source = false;

// Phase 6: Pre-Qualified Backup Suppliers
MERGE (s:Supplier {id: "SUP_ALT_01"})
ON CREATE SET s.name = "LoneStar Power Components Inc", s.tier = 1, s.country = "USA", s.reliability_score = 0.91, s.contract_value_usd = 0.0, s.lead_time_days = 6, s.standby_rate_premium_pct = 8.5;

MERGE (s:Supplier {id: "SUP_ALT_02"})
ON CREATE SET s.name = "Saigon Advanced Assembly Ltd", s.tier = 2, s.country = "Vietnam", s.reliability_score = 0.89, s.contract_value_usd = 0.0, s.lead_time_days = 12, s.standby_rate_premium_pct = 4.2;

// Phase 7: Maritime & Multimodal Corridors
MERGE (c:Corridor {id: "COR_SUEZ_REDSEA"})
ON CREATE SET c.name = "Asia-Europe via Suez & Bab-el-Mandeb", c.transit_days = 24, c.geopolitical_chokepoint = true, c.risk_level = "CRITICAL";

MERGE (c:Corridor {id: "COR_CAPE_GOODHOPE"})
ON CREATE SET c.name = "Cape of Good Hope Bypass", c.transit_days = 35, c.geopolitical_chokepoint = false, c.risk_level = "LOW";

MERGE (c:Corridor {id: "COR_TRANSPACIFIC"})
ON CREATE SET c.name = "Trans-Pacific Ocean Corridor", c.transit_days = 18, c.geopolitical_chokepoint = false, c.risk_level = "MODERATE";

// Phase 8: Components
MERGE (c:Component {id: "CMP_01"}) ON CREATE SET c.name = "Central Vehicle ECU Sub-Assembly", c.critical = true;
MERGE (c:Component {id: "CMP_02"}) ON CREATE SET c.name = "Lidar Matrix Sensor Assembly", c.critical = true;
MERGE (c:Component {id: "CMP_03"}) ON CREATE SET c.name = "32-bit Automotive MCU Chip", c.critical = true;
MERGE (c:Component {id: "CMP_04"}) ON CREATE SET c.name = "Battery Grade Lithium Hydroxide", c.critical = true;
MERGE (c:Component {id: "CMP_05"}) ON CREATE SET c.name = "High-Temp Polyimide Resin", c.critical = false;

// Phase 9: Relationship Wiring (Using MATCH + MERGE to eliminate undefined variable errors)

// OEM depends on Tier-1
MATCH (t:Supplier {id: "SUP_T1_01"}), (oem:Enterprise {id: "OEM_APEX"}) MERGE (t)-[:SUPPLIES { contract_tier: 1, lead_time_days: 14 }]->(oem);
MATCH (t:Supplier {id: "SUP_T1_02"}), (oem:Enterprise {id: "OEM_APEX"}) MERGE (t)-[:SUPPLIES { contract_tier: 1, lead_time_days: 21 }]->(oem);
MATCH (t:Supplier {id: "SUP_T1_03"}), (oem:Enterprise {id: "OEM_APEX"}) MERGE (t)-[:SUPPLIES { contract_tier: 1, lead_time_days: 28 }]->(oem);

// Tier-1 depends on Tier-2
MATCH (t2:Supplier {id: "SUP_T2_02"}), (t1:Supplier {id: "SUP_T1_01"}) MERGE (t2)-[:SUPPLIES_TO { part: "Microcontroller" }]->(t1);
MATCH (t2:Supplier {id: "SUP_T2_02"}), (t1:Supplier {id: "SUP_T1_02"}) MERGE (t2)-[:SUPPLIES_TO { part: "Microcontroller" }]->(t1);
MATCH (t2:Supplier {id: "SUP_T2_03"}), (t1:Supplier {id: "SUP_T1_03"}) MERGE (t2)-[:SUPPLIES_TO { part: "Packaging IC" }]->(t1);
MATCH (t2:Supplier {id: "SUP_T2_01"}), (t1:Supplier {id: "SUP_T1_01"}) MERGE (t2)-[:SUPPLIES_TO { part: "Wafer Base" }]->(t1);

// Tier-2 depends on Tier-3
MATCH (t3:Supplier {id: "SUP_T3_02"}), (t2:Supplier {id: "SUP_T2_02"}) MERGE (t3)-[:SUPPLIES_TO { material: "Rare Earth Oxides" }]->(t2);
MATCH (t3:Supplier {id: "SUP_T3_01"}), (t2:Supplier {id: "SUP_T2_01"}) MERGE (t3)-[:SUPPLIES_TO { material: "Lithium Hydroxide" }]->(t2);
MATCH (t3:Supplier {id: "SUP_T3_03"}), (t2:Supplier {id: "SUP_T2_03"}) MERGE (t3)-[:SUPPLIES_TO { material: "Specialty Polymer" }]->(t2);

// Maritime Corridor routing
MATCH (t1:Supplier {id: "SUP_T1_03"}), (cr:Corridor {id: "COR_SUEZ_REDSEA"}) MERGE (t1)-[:SHIPPED_VIA]->(cr);
MATCH (t1:Supplier {id: "SUP_T1_02"}), (cr:Corridor {id: "COR_TRANSPACIFIC"}) MERGE (t1)-[:SHIPPED_VIA]->(cr);
MATCH (t2:Supplier {id: "SUP_T2_03"}), (cr:Corridor {id: "COR_SUEZ_REDSEA"}) MERGE (t2)-[:SHIPPED_VIA]->(cr);

// Pre-qualified backup supplier relationships
MATCH (t1:Supplier {id: "SUP_T1_03"}), (alt:Supplier {id: "SUP_ALT_02"}) MERGE (t1)-[:HAS_ALTERNATIVE_FALLBACK { standby_cost_multiplier: 1.08 }]->(alt);
MATCH (t1:Supplier {id: "SUP_T1_01"}), (alt:Supplier {id: "SUP_ALT_01"}) MERGE (t1)-[:HAS_ALTERNATIVE_FALLBACK { standby_cost_multiplier: 1.12 }]->(alt);

// Component BOM mapping
MATCH (m:Component {id: "CMP_04"}), (e:Component {id: "CMP_01"}) MERGE (m)-[:RAW_MATERIAL_FOR]->(e);
MATCH (m:Component {id: "CMP_03"}), (e:Component {id: "CMP_01"}) MERGE (m)-[:SUBCOMPONENT_OF]->(e);
MATCH (s:Component {id: "CMP_02"}), (oem:Enterprise {id: "OEM_APEX"}) MERGE (s)-[:INTEGRATED_INTO]->(oem);
