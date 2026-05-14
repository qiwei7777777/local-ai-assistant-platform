# Project Spec

## Objective

Build a local-first AI assistant platform that can be presented as a complete software product, not just a model experiment.

## Users

- Developer or student demonstrating local AI engineering capability
- Project manager reviewing an AI product prototype
- Local-network user testing an assistant without cloud LLM credentials

## Core Requirements

- Run locally with Ollama
- Use `gemma4:e4b` as the default model
- Provide a polished chat workspace
- Persist sessions and messages
- Support streaming and non-streaming chat
- Support model switching
- Support file upload, parsing, knowledge bases, and retrieval
- Support explicit memory
- Provide backend diagnostics and OpenAPI docs
- Provide a Python SDK
- Include tests, scripts, and clear docs

## Non-goals

- Cloud-only deployment
- Hosted multi-tenant authentication
- Enterprise vector search
- Automatic hidden memory capture
- Replacing Ollama as the default local runtime
