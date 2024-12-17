# Fenrir

Welcome to the **Fenrir Data Platform** — a modern data infrastructure stack designed for real-time data ingestion, processing, and visualization. Built with **Docker Swarm** and powered by some of the most robust open-source data tools available, this platform aims to simplify complex data workflows while remaining flexible, modular, and easy to deploy.

## 📦 **Technologies Used**

This platform integrates the following open-source technologies:

- **Docker Swarm**: Orchestrates and manages multiple containers across nodes.
- **Tailscale**: Secure, private network overlay to enable secure remote access.
- **Portainer**: Simple, visual container management.
- **Airflow**: Workflow orchestration and scheduling.
- **Kafka**: Real-time event streaming and message brokering.
- **Kafka Connect**: Enables data integration between Kafka and external systems.
- **Kafka Registry**: Manages and enforces schema versions for Kafka topics.
- **Kafdrop**: A web-based UI for visualizing and monitoring Kafka topics.
- **Scrapy**: Web scraping framework used to ingest data.
- **Spark**: Distributed big data processing and analytics.
- **PostgreSQL**: Relational database for persistent storage.
- **Metabase**: Business intelligence and analytics dashboard for visualizing data.

## 🌐 **What Does This Platform Do?**

This platform is a full-featured **data infrastructure stack** that can:

- **Ingest data** from web scrapers (Scrapy), relational databases (PostgreSQL via Debezium, etc.), and other third-party systems using Kafka Connect.
- **Process data** in real-time using Kafka, Spark, and streaming workflows.
- **Schedule workflows** using Airflow, enabling batch and continuous processing.
- **Manage infrastructure** using Docker Swarm for orchestration and Portainer for visual container management.
- **Visualize data** with Metabase, providing a no-code way to explore and visualize processed data.

Whether you need to scrape, ingest, process, or visualize data, this platform is ready to support modern data engineering needs.

### **Prerequisites**
- Docker-ce Engine
- Tailscale if you want secure remote access, otherwise, please modify setup.sh for advertised address of docker swarm manager node.

### **Deploy the Platform**
```bash
# Clone the repository
git clone https://github.com/Aragonski97/fenrir-infra.git ~/.fenrir

# Navigate to the project directory
cd ~/.fenrir

# Deploy the platform
source setup.sh
```
