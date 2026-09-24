# SamoGo

> A simple VK community automation platform — currently in development.

**SamoGo** is a platform for simplifying user-generated content management in VK communities.

The product is designed around one central idea: community management and everyday automation should be understandable even for people with no technical background.

After connecting a VK community, SamoGo is intended to bring routine content workflows into one simple interface:

- collecting user-generated content;
- creating and publishing posts;
- scheduling publications;
- conversational automation through a community bot.

## Product idea

Community automation tools can become complicated very quickly.

SamoGo takes the opposite approach: hide technical complexity behind a simple product experience.

The goal is not to make users learn automation systems, workflows or integrations. The goal is to let them configure what they need and let the platform handle the routine.

**Настроил. И само пошло.**

## Status

🚧 **SamoGo is currently in active development.**

The private repository contains the complete product implementation and ongoing experiments.

This public repository is a limited portfolio showcase. It contains selected implementation examples and intentionally excludes production credentials and configuration, complete VK integration details, unreleased product workflows, commercial logic, the internal roadmap and production infrastructure.

## Public code sample

The current public sample focuses on a self-contained authentication subsystem rather than SamoGo's unreleased product workflows.

It demonstrates:

- one-time login codes with expiration;
- invalidation of previous active codes;
- attempt limiting;
- hashed OTP and session-token storage;
- session expiration and revocation;
- normalized user identity;
- SQLite constraints and foreign keys;
- automated tests around security-sensitive behavior.

## What this repository demonstrates

- Python backend development;
- separation of application logic and persistence;
- authentication lifecycle design;
- state and expiry handling;
- SQLite persistence;
- automated backend testing;
- development of a commercial product from concept toward a working MVP.

## Stack

**Python 3.12 · FastAPI · SQLite · pytest/unittest · VK integration in the private product**

## Commercial project boundary

SamoGo is an independently developed commercial product.

The complete source code, unreleased product design, detailed VK integration, product roadmap and proprietary workflow logic remain private.

This repository exists to demonstrate selected engineering work without publishing the implementation that defines the product's competitive behavior.

No open-source license is granted by this repository.
