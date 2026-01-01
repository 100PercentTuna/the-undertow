"""
Production few-shot examples for geopolitical analysis.

Real examples to guide agent outputs.
"""

# ============================================================================
# MOTIVATION ANALYSIS EXAMPLES
# ============================================================================

MOTIVATION_EXAMPLE_1 = {
    "input": {
        "headline": "Israel Recognizes Somaliland as Independent State",
        "summary": "Israel has formally recognized Somaliland's independence, making it one of the few countries to do so. The recognition includes a defense cooperation agreement and establishment of diplomatic missions.",
    },
    "output": {
        "individual_layer": {
            "decision_maker": "Prime Minister Benjamin Netanyahu",
            "political_position": "Facing coalition pressures and legal challenges, seeking foreign policy wins to shore up domestic standing. Recognition of Somaliland costs nothing domestically while delivering a tangible diplomatic achievement.",
            "domestic_needs": "Nationalist base wants expanded Israeli influence. Religious parties indifferent to Horn of Africa. Security establishment supports Red Sea access.",
            "key_assessments": [
                "Netanyahu personally drives Israel's 'periphery doctrine' revival",
                "Timing coincides with domestic political turbulence—distraction value",
                "No domestic constituency opposes this move",
            ],
            "confidence": 0.85,
        },
        "institutional_layer": {
            "foreign_ministry_role": "Executing long-planned expansion of African relations. Somaliland fits pattern of cultivating non-Arab African states (South Sudan, Chad, Rwanda).",
            "military_intelligence_role": "Mossad has maintained quiet contacts with Somaliland for years. IDF interested in Red Sea monitoring capabilities.",
            "economic_actors": ["Defense contractors eyeing new market", "Port operators assessing Berbera opportunities"],
            "key_assessments": [
                "Recognition culminates years of quiet engagement, not sudden decision",
                "Intelligence community drove the relationship; diplomats formalized it",
            ],
            "confidence": 0.80,
        },
        "structural_layer": {
            "systemic_position": "Israel seeks strategic depth beyond immediate neighborhood. Hostile encirclement (Iran, Hezbollah, Hamas) drives search for distant allies.",
            "threat_environment": "Iranian expansion in Yemen threatens Red Sea. Houthi attacks on shipping demonstrate vulnerability. Somaliland offers counter-positioning.",
            "economic_structure": "Limited—Israel's economy doesn't depend on Horn of Africa. Strategic value dominates economic.",
            "geographic_imperatives": "Red Sea access is existential for Eilat port. Bab el-Mandeb chokepoint vulnerability drives all Israeli Red Sea policy.",
            "key_assessments": [
                "Structural pressures make some form of Red Sea positioning inevitable",
                "Somaliland is optimal target: strategic location, eager for recognition, no Arab League membership",
            ],
            "confidence": 0.90,
        },
        "opportunistic_layer": {
            "what_changed": "Somalia's internal weakness and new Somaliland government more willing to accept controversial recognition",
            "position_shifts": ["UAE deepened Berbera investment, creating opening", "Ethiopia-Somaliland MOU normalized idea of engagement"],
            "constraints_relaxed": ["Arab League distracted by Gaza", "US focused elsewhere", "Traditional opposition muted"],
            "window_analysis": "Window opened by convergence of regional distraction and Somaliland's growing de facto relationships. Window may narrow if Somalia stabilizes.",
            "key_assessments": [
                "Timing is explicitly opportunistic—acting while attention is elsewhere",
                "Ethiopia's MOU created political cover for Israel's recognition",
            ],
            "confidence": 0.85,
        },
        "synthesis": {
            "primary_driver": "Structural imperative (Red Sea security) combined with institutional momentum (intelligence community's long cultivation) enabled by opportunistic timing (regional distraction).",
            "enabling_conditions": [
                "UAE's prior Berbera investment normalized Somaliland engagement",
                "Ethiopia's MOU provided political cover",
                "Arab League distraction reduced opposition",
                "Netanyahu's need for foreign policy wins aligned incentives",
            ],
            "alternative_explanations": [
                "Pure Abraham Accords expansion play (seeking domino effect)",
                "Counter-Turkey move (Turkey deeply invested in Somalia)",
                "UAE coordination (Israel as recognition proxy for Gulf ally)",
            ],
            "confidence_assessment": 0.82,
            "key_uncertainties": [
                "Extent of prior UAE-Israel coordination",
                "Whether additional recognitions are planned",
                "Intelligence-sharing arrangements (unpublicized)",
            ],
        },
    },
}

MOTIVATION_EXAMPLE_2 = {
    "input": {
        "headline": "Niger Junta Expels French Military, Welcomes Russian Wagner Forces",
        "summary": "Niger's military government has ordered French troops to leave within 30 days while signing a military cooperation agreement with Russia. Wagner Group forces have begun arriving in Niamey.",
    },
    "output": {
        "individual_layer": {
            "decision_maker": "General Abdourahamane Tchiani (junta leader)",
            "political_position": "New to power via coup, needs to consolidate legitimacy. Anti-French sentiment is popular; delivering French expulsion shores up public support.",
            "domestic_needs": "Coup legitimacy requires distinguishing from deposed government. French presence symbolized old order. Russia offers alternative patron without colonial baggage.",
            "key_assessments": [
                "Tchiani personally has limited prior relationship with Russia—this is opportunistic",
                "Anti-French move is genuinely popular, not manufactured",
                "Domestic consolidation is primary driver, external security secondary",
            ],
            "confidence": 0.75,
        },
        "institutional_layer": {
            "foreign_ministry_role": "Largely sidelined. Military controls external relations directly.",
            "military_intelligence_role": "Junior officers driving anti-French sentiment within ranks. Senior officers pragmatically seeking new patron.",
            "economic_actors": ["Mining interests uncertain", "Informal traders benefit from reduced enforcement"],
            "key_assessments": [
                "Military institutional interests diverge from economic interests",
                "No strong institutional voice for maintaining French ties",
            ],
            "confidence": 0.70,
        },
        "structural_layer": {
            "systemic_position": "Landlocked Sahelian state dependent on external security assistance. Cannot defeat jihadist insurgency alone. Must have a security patron.",
            "threat_environment": "JNIM and ISGS insurgency is existential threat. French counterterrorism (Operation Barkhane) failed to eliminate threat despite decade of presence.",
            "economic_structure": "Uranium exports, limited other resources. France is major buyer. Economic structure constrains full break.",
            "geographic_imperatives": "Landlocked, surrounded by coup governments (Mali, Burkina Faso) or weak states (Chad, Libya). Regional isolation limits options.",
            "key_assessments": [
                "Structural need for security patron is immutable—question is which patron",
                "French failure to defeat insurgency delegitimizes their presence",
                "Geographic isolation means Sahel Alliance (Mali, Burkina) is natural partner",
            ],
            "confidence": 0.85,
        },
        "opportunistic_layer": {
            "what_changed": "Coup removed pro-French government. Wagner demonstrated capability in Mali. ECOWAS threats united public against external intervention.",
            "position_shifts": ["Mali and Burkina Faso already pivoted to Russia—Niger follows pattern", "France's African position collapsed rapidly in 2022-23"],
            "constraints_relaxed": ["ECOWAS military intervention failed to materialize", "US initially tried engagement, then withdrew"],
            "window_analysis": "Window opened by Mali/Burkina precedent and ECOWAS failure to intervene. Window is wide—no external force willing/able to reverse coup.",
            "key_assessments": [
                "Niger is following established Sahel template, not innovating",
                "ECOWAS credibility collapse was enabling condition",
            ],
            "confidence": 0.80,
        },
        "synthesis": {
            "primary_driver": "Structural failure of French counterterrorism (decade of presence, no victory) combined with coup dynamics requiring external legitimacy source and regional precedent (Mali/Burkina template).",
            "enabling_conditions": [
                "Mali/Burkina Faso demonstrated Russia pivot was feasible",
                "ECOWAS failed to intervene, removing constraint",
                "Popular anti-French sentiment made expulsion politically costless",
                "Wagner available and willing to deploy",
            ],
            "alternative_explanations": [
                "Russian active measures successfully cultivated coup plotters",
                "Genuine security calculation (Wagner more effective than France)",
                "Personal enrichment opportunity for junta via Russian deals",
            ],
            "confidence_assessment": 0.78,
            "key_uncertainties": [
                "Extent of pre-coup Russian contacts with military",
                "Whether Wagner can actually improve security situation",
                "Economic arrangements (mining concessions) not yet public",
            ],
        },
    },
}


# ============================================================================
# CHAIN MAPPING EXAMPLES
# ============================================================================

CHAIN_EXAMPLE_1 = {
    "input": {
        "event": "Israel recognizes Somaliland",
        "context": "First major power recognition of Somaliland since its 1991 declaration of independence",
    },
    "output": {
        "forward_chains": [
            {
                "order": 1,
                "actor": "Somalia",
                "response": "Recalls ambassador from Israel, seeks Arab League condemnation, deepens ties with Israel's regional rivals",
                "confidence": 0.95,
            },
            {
                "order": 1,
                "actor": "Somaliland",
                "response": "Announces reciprocal recognition of Israel, opens diplomatic mission, signs defense agreements",
                "confidence": 0.95,
            },
            {
                "order": 2,
                "actor": "Ethiopia",
                "response": "Accelerates own Somaliland MOU implementation, emboldened by Israeli precedent",
                "confidence": 0.85,
            },
            {
                "order": 2,
                "actor": "Turkey",
                "response": "Deepens Somalia commitment to counter Israeli move, potential military expansion in Mogadishu",
                "confidence": 0.75,
            },
            {
                "order": 3,
                "actor": "Djibouti",
                "response": "Signals alarm to France/US about Berbera competition, seeks to reinforce own strategic value",
                "confidence": 0.70,
            },
            {
                "order": 3,
                "actor": "African Union",
                "response": "Issues statement reaffirming territorial integrity, but takes no action (precedent: South Sudan)",
                "confidence": 0.80,
            },
            {
                "order": 4,
                "actor": "Taiwan",
                "response": "Studies Somaliland recognition pathway as potential template, considers similar arrangement",
                "confidence": 0.60,
            },
            {
                "order": 4,
                "actor": "Other breakaway regions",
                "response": "Kosovo, Transnistria, Kurdistan observe precedent—'good governance' path to recognition gains credibility",
                "confidence": 0.65,
            },
            {
                "order": 5,
                "actor": "International system",
                "response": "Territorial integrity norm further erodes. Recognition becomes tradeable commodity in great power competition.",
                "confidence": 0.55,
            },
        ],
        "backward_chains": [
            {
                "beneficiary": "UAE",
                "order": 3,
                "benefit": "Berbera port investment secured and legitimized. UAE gains partner in Red Sea network without having to recognize Somaliland itself.",
                "likely_influence": True,
                "evidence": "UAE's years of Berbera investment preceded and enabled this recognition",
            },
            {
                "beneficiary": "Saudi Arabia",
                "order": 3,
                "benefit": "Watches Abraham Accords expand without having to move first. Can calibrate own normalization timing.",
                "likely_influence": False,
                "evidence": "Saudi benefits but no evidence of active encouragement",
            },
            {
                "beneficiary": "China",
                "order": 4,
                "benefit": "Observes Western norm erosion, files away for Taiwan precedent debates",
                "likely_influence": False,
                "evidence": "Passive beneficiary only",
            },
        ],
        "synthesis": {
            "primary_chain_logic": "Recognition triggers Somalia-Israel rupture and Turkey-Israel proxy competition in Horn, while emboldening Ethiopia and alarming Djibouti. Longer-term, erodes territorial integrity norm globally.",
            "hidden_game_hypothesis": "The primary game may not be Horn of Africa at all—this is a move in the Red Sea security chess match, with Houthi threats creating urgency. UAE is the key enabler, Israel the recognition vehicle.",
            "key_tipping_points": [
                "Whether 2+ additional countries recognize Somaliland (tipping point for de facto statehood)",
                "Ethiopia's MOU implementation timeline",
                "Turkey's military response in Somalia",
            ],
            "recommended_monitoring": [
                "UAE-Israel coordination signals",
                "Ethiopian port access negotiations",
                "Somaliland's next recognition targets",
                "Taiwan-Somaliland relationship development",
            ],
            "confidence": 0.75,
        },
    },
}


# ============================================================================
# SUBTLETY ANALYSIS EXAMPLES
# ============================================================================

SUBTLETY_EXAMPLE_1 = {
    "input": {
        "event": "US issues statement on Israel-Somaliland recognition",
        "statement": "The United States notes Israel's decision regarding Somaliland. We continue to support Somalia's sovereignty and territorial integrity as defined by the African Union.",
    },
    "output": {
        "signals_in_action": {
            "intended_audience": "Primary: Israel and UAE (tacit approval signal). Secondary: African Union (reassurance). Tertiary: Somalia (managing relationship).",
            "norm_invoked": "Territorial integrity is stated but not enforced—classic diplomatic hedge.",
            "capability_demonstrated": "None. Deliberate passivity.",
            "commitment_signaled": "Minimal. 'Notes' is diplomatic term for 'acknowledges without endorsing or opposing.'",
            "analysis": "The US is permitting this by not opposing it. The statement's weakness IS the message—stronger language was available and not used.",
        },
        "eloquent_silences": {
            "who_hasnt_commented": ["Saudi Arabia", "Egypt", "Most EU states"],
            "missing_from_framing": "No criticism of Israel. No call to reverse. No mention of consequences.",
            "questions_deflected": "State Department briefing avoided direct questions on whether US supports the recognition.",
            "what_didnt_happen": "No emergency UN Security Council session. No US pressure on Israel to reconsider.",
            "analysis": "The silence from Saudi Arabia is particularly notable—suggests prior coordination or at minimum tacit acceptance in Abraham Accords context.",
        },
        "timing_message": {
            "what_preceded": "Statement came 48 hours after recognition—enough time to coordinate language, not urgent response.",
            "calendar_context": "During Gaza ceasefire negotiations—US has leverage over Israel it chose not to use.",
            "sequence_position": "Reactive, not proactive. US following events, not shaping them.",
            "analysis": "The 48-hour delay signals careful calibration, not surprise. The timing during Gaza talks—when US could apply pressure—makes inaction more meaningful.",
        },
        "choreography": {
            "who_appeared": "Junior State Department spokesperson, not Secretary of State.",
            "protocol_level": "Minimal. Buried in daily briefing, not standalone statement.",
            "visual_arrangement": "No visual—written statement only.",
            "analysis": "The low protocol level is deliberate downgrading. If US wanted to signal concern, Secretary would speak. Press release level signals 'we're required to comment but don't want to make this a thing.'",
        },
        "deniable_communication": {
            "trial_balloons": "None observed.",
            "sympathetic_media": "US-aligned outlets (Al-Monitor, etc.) framing recognition as 'bold move' not 'destabilizing.'",
            "back_channels": "Qatar likely informed given their Somalia mediation role. Oman possibly consulted.",
            "analysis": "The sympathetic media framing suggests this was pre-briefed to friendly journalists. The narrative was shaped before public announcement.",
        },
        "synthesis": {
            "overall_assessment": "The US is providing tacit approval through deliberate passivity. The combination of: (1) weak language ('notes'), (2) junior spokesperson, (3) 48-hour delay, (4) no pressure despite Gaza leverage, and (5) pre-shaped media narrative indicates this was coordinated or at minimum pre-cleared with Washington.",
            "confidence": 0.80,
        },
    },
}


# ============================================================================
# EXPORT FOR USE IN AGENTS
# ============================================================================

FEW_SHOT_EXAMPLES = {
    "motivation": [MOTIVATION_EXAMPLE_1, MOTIVATION_EXAMPLE_2],
    "chains": [CHAIN_EXAMPLE_1],
    "subtlety": [SUBTLETY_EXAMPLE_1],
}


def get_few_shot_examples(agent_type: str, count: int = 1) -> list[dict]:
    """Get few-shot examples for an agent type."""
    examples = FEW_SHOT_EXAMPLES.get(agent_type, [])
    return examples[:count]


def format_few_shot_prompt(agent_type: str, count: int = 1) -> str:
    """Format few-shot examples as prompt text."""
    examples = get_few_shot_examples(agent_type, count)

    if not examples:
        return ""

    import json

    parts = ["## EXAMPLES\n"]

    for i, ex in enumerate(examples, 1):
        parts.append(f"### Example {i}\n")
        parts.append(f"**Input:**\n```json\n{json.dumps(ex['input'], indent=2)}\n```\n")
        parts.append(f"**Output:**\n```json\n{json.dumps(ex['output'], indent=2)}\n```\n")

    return "\n".join(parts)

