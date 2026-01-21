# MeroGhar Documentation Structure

This documentation follows the software development lifecycle phases with comprehensive diagrams using Mermaid.js.

## 📁 Documentation Structure

### 1. Requirements Phase
- **[requirements.md](requirements/requirements.md)** - Requirements document with functional and non-functional requirements
- **[user_stories.md](requirements/user_stories.md)** - User stories and journey maps

### 2. Analysis Phase
- **[use_case_diagram.md](analysis/use_case_diagram.md)** - System use cases and actors
- **[use_case_descriptions.md](analysis/use_case_descriptions.md)** - Detailed use case descriptions with flows
- **[system_context_diagram.md](analysis/system_context_diagram.md)** - System boundaries and external dependencies
- **[activity_diagram.md](analysis/activity_diagram.md)** - Business process flows
- **[swimlane_diagram.md](analysis/swimlane_diagram.md)** - Cross-department workflows

### 3. High-Level Design Phase
- **[system_sequence_diagram.md](high_level_design/system_sequence_diagram.md)** - Black-box system interactions
- **[domain_model.md](high_level_design/domain_model.md)** - Domain entities and relationships
- **[data_flow_diagram.md](high_level_design/data_flow_diagram.md)** - Data movement through the system
- **[architecture_diagram.md](high_level_design/architecture_diagram.md)** - High-level system architecture
- **[c4_context_container.md](high_level_design/c4_context_container.md)** - C4 context and container diagrams

### 4. Detailed Design Phase
- **[class_diagram.md](detailed_design/class_diagram.md)** - Detailed class structures
- **[sequence_diagram.md](detailed_design/sequence_diagram.md)** - Internal object interactions
- **[state_machine_diagram.md](detailed_design/state_machine_diagram.md)** - Object state transitions
- **[erd_schema.md](detailed_design/erd_schema.md)** - Database schema and relationships
- **[component_diagram.md](detailed_design/component_diagram.md)** - Software modules and dependencies
- **[api_design.md](detailed_design/api_design.md)** - API endpoints and integration
- **[c4_component.md](detailed_design/c4_component.md)** - C4 component diagram

### 5. Infrastructure Phase
- **[deployment_diagram.md](infrastructure/deployment_diagram.md)** - Software to hardware mapping
- **[network_diagram.md](infrastructure/network_diagram.md)** - Network and infrastructure layout
- **[cloud_architecture.md](infrastructure/cloud_architecture.md)** - AWS cloud architecture

### 6. Implementation Phase
- **[c4_code_diagram.md](implementation/c4_code_diagram.md)** - Code-level class diagrams

## 🎯 Quick Navigation

### By Concern
- **System Overview**: Start with [system_context_diagram.md](analysis/system_context_diagram.md) and [architecture_diagram.md](high_level_design/architecture_diagram.md)
- **User Flows**: Check [user_stories.md](requirements/user_stories.md) and [activity_diagram.md](analysis/activity_diagram.md)
- **Database Design**: See [erd_schema.md](detailed_design/erd_schema.md) and [domain_model.md](high_level_design/domain_model.md)
- **API Reference**: Review [api_design.md](detailed_design/api_design.md)
- **Deployment Guide**: Visit [deployment_diagram.md](infrastructure/deployment_diagram.md) and [cloud_architecture.md](infrastructure/cloud_architecture.md)

### By Role
- **Business Analysts**: requirements/ and analysis/ folders
- **Architects**: high_level_design/ folder
- **Developers**: detailed_design/ and implementation/ folders
- **DevOps**: infrastructure/ folder

## 📊 Diagram Types Used

All diagrams are created using [Mermaid.js](https://mermaid.js.org/) for easy rendering and version control.

- Flowcharts and Activity Diagrams
- Sequence Diagrams
- State Diagrams
- Entity Relationship Diagrams
- Class Diagrams
- Component Diagrams
- Deployment Diagrams
- C4 Model Diagrams (Context, Container, Component, Code)

## 🔄 Viewing Diagrams

Mermaid diagrams can be viewed directly in:
- GitHub
- GitLab
- VS Code (with Mermaid extension)
- Any Markdown editor with Mermaid support
- [Mermaid Live Editor](https://mermaid.live/)

## 📝 Contributing

When updating diagrams:
1. Follow Mermaid.js syntax
2. Keep diagrams clear and concise
3. Update related documentation
4. Maintain consistency across diagrams
