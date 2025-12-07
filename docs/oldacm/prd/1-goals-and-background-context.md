# 1. Goals and Background Context

## Goals

- **Solve a compliance bottleneck**: Eliminate manual data entry and reduce errors in creating asbestos registers.
- **Boost trust and adoption**: Provide click-through citations from structured data back to the raw PDF source, ensuring transparency.
- **Increase independence**: Shift from reliance on cloud APIs to local models for OCR, layout analysis, embeddings, and LLM chat.
- **Unify workflows**: Provide both structured database outputs for regulatory needs and semantic chat/search for daily operational use.

## Background Context

The project is addressing a critical compliance and data-usability gap in asbestos and building management. Current reports, such as SSAMPs and Asbestos Registers, are often inconsistent and incomplete in their PDF format. This makes it difficult to reliably and accurately populate mandatory regulatory templates like the Bar Replacement and ACM Register, leading to manual data entry, potential errors, and compliance risks.

The original Supabase and n8n pipeline provided a baseline for data ingestion, but new client requirements necessitate a more advanced, secure, and transparent solution. This enhancement will evolve the system from a simple data pipeline into a sophisticated, local-first AI platform. It aims to unify the workflow for both regulators who need structured, verifiable data and daily users (like facility managers) who need fast, conversational access to query project information.
