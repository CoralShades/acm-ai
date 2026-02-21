"""A2A Agent Card definitions for ACM-AI agents.

These cards describe the capabilities of each agent for A2A discovery.
They are used by the CopilotKit A2AMiddlewareAgent to discover and
route to the appropriate agent.
"""

# Agent card metadata (simplified for initial implementation)
# Full A2A protocol integration can be added later with the a2a-sdk

ACM_ANALYST_CARD = {
    "name": "ACM Analyst",
    "description": "Queries structured ACM register data from school building assessments. "
    "Specializes in risk analysis, building/room lookups, material searches, and statistics.",
    "skills": [
        {
            "id": "risk_analysis",
            "name": "ACM Risk Analysis",
            "description": "Search and analyze ACM records by risk level (High, Medium, Low)",
            "examples": [
                "What rooms have high-risk ACM?",
                "Show me all medium-risk materials",
                "Which buildings have the most dangerous asbestos?",
            ],
        },
        {
            "id": "building_lookup",
            "name": "Building/Room Lookup",
            "description": "Find ACM records for specific buildings, rooms, or locations",
            "examples": [
                "What ACM is in Building A?",
                "Show records for Room 5",
                "List all materials in the main building",
            ],
        },
        {
            "id": "material_search",
            "name": "Material Search",
            "description": "Search for specific ACM material types",
            "examples": [
                "Find all vinyl floor tiles",
                "Where is cement sheeting installed?",
                "Search for pipe insulation records",
            ],
        },
        {
            "id": "statistics",
            "name": "ACM Statistics",
            "description": "Get summary statistics and overviews of ACM data",
            "examples": [
                "How many ACM records are there?",
                "Give me a risk summary",
                "How many buildings are affected?",
            ],
        },
    ],
    "capabilities": {
        "streaming": True,
        "tool_calling": True,
    },
}

DOC_SEARCH_CARD = {
    "name": "Document Search",
    "description": "Searches PDF document content, source text, and AI-generated insights. "
    "Uses both semantic similarity and keyword search to find relevant passages.",
    "skills": [
        {
            "id": "semantic_search",
            "name": "Semantic Document Search",
            "description": "Find relevant passages using natural language similarity",
            "examples": [
                "What does the report say about removal procedures?",
                "Find information about asbestos management policies",
                "What are the recommendations for Building A?",
            ],
        },
        {
            "id": "keyword_search",
            "name": "Keyword Document Search",
            "description": "Find exact terms, phrases, or reference numbers in documents",
            "examples": [
                "Search for 'encapsulation' in the document",
                "Find references to sample number S123",
                "Look for the term 'non-friable'",
            ],
        },
    ],
    "capabilities": {
        "streaming": True,
        "tool_calling": True,
    },
}

SUPERVISOR_CARD = {
    "name": "ACM-AI Supervisor",
    "description": "Orchestrates ACM Analyst and Document Search agents to answer complex questions "
    "about asbestos containing materials in school buildings. Routes queries to the "
    "appropriate specialist and synthesizes responses.",
    "skills": [
        {
            "id": "acm_query",
            "name": "ACM Data Query",
            "description": "Answer questions about structured ACM register data",
        },
        {
            "id": "document_query",
            "name": "Document Content Query",
            "description": "Find and retrieve information from uploaded documents",
        },
        {
            "id": "hybrid_query",
            "name": "Hybrid Analysis",
            "description": "Combine structured data and document content for comprehensive answers",
        },
    ],
    "capabilities": {
        "streaming": True,
        "tool_calling": True,
        "multi_agent": True,
    },
}
