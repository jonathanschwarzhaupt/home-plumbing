# Home Plumbing

## 1. Overview / Background
**What problem are you solving?**

Managing my personal finances through the Comdirect banking app has proven frustrating due to the lack of a detailed, customizable spending overview.I aim to solve that gap by independently extracting, integrating, and analyzing financial data to build a richer, tailored spending dashboard.

Beyond solving a personal need, the project also serves as a playground to integrate multiple data sources, explore (emerging) technologies like Apache Airflow 3.0, Apache Iceberg and Project Nessie, and apply modern data engineering best practices such as the Write-Audit-Publish (WAP) pattern.

Scope: This is a personal Proof of Concept (PoC) designed to validate the technical setup and workflows. The project may later evolve into a more polished, production-grade solution as features and robustness improve. 

Goal: The goal is to have a Airflow installation running in my Kubernetes [homelab](https://github.com/jonathanschwarzhaupt/homelab).

## 2. Project Structure
- Core code is separated from orchestration code, ensuring portability of the key components
  ```
  TBD
  ```

## 3. Tasks / TODOs

  - [ ] Write comdirect source module
  - [ ] Write Iceberg destination module
  - [ ] Create docker compose for local testing
  - [ ] Write basic unit tests


## 4. Setup Instructions

TBD


## 5. Notes / Considerations
 Any design decisions worth recording

TBD

## 6. Future Improvements (Optional, but Valuable)
Ideas that aren't immediate tasks

TBD
