# Deployment Diagram

## Production Deployment Architecture

```mermaid
graph TB
    subgraph "User Devices"
        Browser[Web Browser]
        Mobile[Mobile App]
    end
    
    subgraph "CDN Layer"
        CloudFront[CloudFront CDN]
    end
    
    subgraph "Load Balancer"
        ALB[Application Load Balancer]
    end
    
    subgraph "Web Servers - EC2 Instances"
        Web1[Web Server 1<br/>Nginx]
        Web2[Web Server 2<br/>Nginx]
    end
    
    subgraph "Application Servers - EC2 Instances"
        App1[App Server 1<br/>Django/Gunicorn]
        App2[App Server 2<br/>Django/Gunicorn]
        App3[App Server 3<br/>Django/Gunicorn]
    end
    
    subgraph "Data Tier"
        RDS[(RDS PostgreSQL<br/>Primary)]
        RDSReplica[(RDS PostgreSQL<br/>Read Replica)]
        Redis[(ElastiCache<br/>Redis)]
        S3[(S3 Bucket<br/>File Storage)]
    end
    
    subgraph "Background Services"
        Worker1[Celery Worker 1]
        Worker2[Celery Worker 2]
        Queue[Redis Queue]
    end
    
    Browser & Mobile --> CloudFront
    CloudFront --> ALB
    ALB --> Web1 & Web2
    Web1 & Web2 --> App1 & App2 & App3
    
    App1 & App2 & App3 --> RDS
    App1 & App2 & App3 --> RDSReplica
    App1 & App2 & App3 --> Redis
    App1 & App2 & App3 --> S3
    
    App1 & App2 & App3 --> Queue
    Queue --> Worker1 & Worker2
    Worker1 & Worker2 --> RDS
```

## Container Deployment (Docker)

```mermaid
graph TB
    subgraph "Docker Host"
        subgraph "Frontend Container"
            NextJS[Next.js App<br/>Port 3000]
        end
        
        subgraph "Backend Container"
            Django[Django API<br/>Port 8000]
        end
        
        subgraph "Database Container"
            Postgres[(PostgreSQL<br/>Port 5432)]
        end
        
        subgraph "Cache Container"
            RedisC[(Redis<br/>Port 6379)]
        end
        
        subgraph "Nginx Container"
            Nginx[Nginx<br/>Port 80/443]
        end
    end
    
    Nginx --> NextJS
    Nginx --> Django
    Django --> Postgres
    Django --> RedisC
```

## Kubernetes Deployment

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Ingress"
            Ingress[Ingress Controller<br/>nginx-ingress]
        end
        
        subgraph "Frontend Deployment"
            FrontPod1[Frontend Pod 1]
            FrontPod2[Frontend Pod 2]
            FrontSvc[Frontend Service]
        end
        
        subgraph "Backend Deployment"
            BackPod1[Backend Pod 1]
            BackPod2[Backend Pod 2]
            BackPod3[Backend Pod 3]
            BackSvc[Backend Service]
        end
        
        subgraph "Worker Deployment"
            WorkerPod1[Worker Pod 1]
            WorkerPod2[Worker Pod 2]
        end
        
        subgraph "StatefulSet"
            DB[(Database<br/>StatefulSet)]
            RedisSet[(Redis<br/>StatefulSet)]
        end
        
        subgraph "External"
            RDSPG[(RDS PostgreSQL)]
            ElastiCache[(ElastiCache)]
            S3Storage[(S3)]
        end
    end
    
    Ingress --> FrontSvc
    Ingress --> BackSvc
    FrontSvc --> FrontPod1 & FrontPod2
    BackSvc --> BackPod1 & BackPod2 & BackPod3
    
    BackPod1 & BackPod2 & BackPod3 --> RDSPG
    BackPod1 & BackPod2 & BackPod3 --> ElastiCache
    BackPod1 & BackPod2 & BackPod3 --> S3Storage
    WorkerPod1 & WorkerPod2 --> ElastiCache
```
