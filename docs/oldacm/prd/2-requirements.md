# 2. Requirements

## Functional Requirements

1. The system must provide an interface for users to upload PDF, PNG, JPG, and TIFF reports.
2. The system must perform OCR (Tesseract) on uploaded documents to extract raw text content.
3. The system must use a layout analysis model (e.g., LayoutLMv3) to identify and structure the extracted text from the semi-structured documents.
4. The system must generate vector embeddings from the document content and store them to power conversational queries.
5. The system must automatically populate structured data tables, specifically the Bar Replacement and ACM Register templates, from the analyzed document content.
6. The system must feature a "Provenance Viewer" where a user can click a field in the structured data and be shown the exact source location highlighted within the original PDF document.
7. The system must provide an interactive, conversational chat interface allowing end-users to query asbestos and building data using natural language.
8. The system must allow users to export the populated and standardized regulatory templates.

## Non-Functional Requirements

1. **Data Privacy and Security**: All AI models for OCR, layout analysis, embeddings, and chat must run locally within the user's environment and must not send project data to external, third-party cloud APIs.
2. **Performance**: The system's interactive features, including the provenance viewer and conversational chat, must provide a responsive user experience with minimal latency.
3. **Data Accuracy and Provenance**: The system must ensure a high degree of data accuracy and provide transparent, auditable links between every piece of extracted data and its precise source (including page and bounding box) in the original document.
4. **Maintainability**: The local AI environment, including the configuration, management, and updating of models, must be maintainable by the client's technical team.
