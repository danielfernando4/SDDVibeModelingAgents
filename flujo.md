graph TB
    START(["python main.py"]) --> MENU

    subgraph "TERMINAL INTERACTIVA"
        MENU{"Menú<br/>1.Producto 2.Requisitos 3.Diseño"}
        MENU -->|"elige fase"| CHECK{"¿Fase accesible?<br/>product: siempre<br/>req: necesita product<br/>design: necesita req"}
        CHECK -->|"NO"| ERR["✗ Error: dependencia faltante"]
        CHECK -->|"SÍ"| PROMPT["Usuario escribe prompt"]
        ERR --> MENU
    end

    PROMPT --> SELECTOR

    subgraph "NODO SELECTOR"
        SELECTOR{"¿Cola de<br/>redirecciones?"}
        SELECTOR -->|"SÍ (FIFO)"| IS_REDIR["es_redireccion = true<br/>current_redirection = {...}<br/>user_prompt = resumen"]
        SELECTOR -->|"NO"| IS_USER["es_redireccion = false<br/>user_prompt = prompt usuario"]
    end

    IS_REDIR --> DISPATCH
    IS_USER --> DISPATCH

    DISPATCH{"target_phase?"}
    DISPATCH -->|"product"| PRODUCT
    DISPATCH -->|"requirements"| REQUIREMENTS
    DISPATCH -->|"design"| DESIGN
    DISPATCH -->|""| END_NODE(["FIN"])

    subgraph "NODO DE FASE (Product / Requirements / Design)"
        direction TB
        CHECK_MODE{"¿Modo?"}
        CHECK_MODE -->|"!exists"| CREATE["CREACIÓN<br/>prompt: creator_create.md<br/>reviewer: reviewer_create.md"]
        CHECK_MODE -->|"exists + user"| MODIFY["MODIFICACIÓN<br/>prompt: creator_modify.md<br/>reviewer: reviewer_modify.md"]
        CHECK_MODE -->|"exists + redir"| REDIR["REDIRECCIÓN<br/>prompt: creator_modify_redirection.md<br/>reviewer: reviewer_modify.md"]

        CREATE --> CLARIFY
        MODIFY --> CLARIFY
        REDIR --> CLARIFY_PROMPT_REDIR["¿Prompt ambiguo?<br/>→ clarificar (solo user, no redir)"]

        CLARIFY_PROMPT_REDIR --> LOOP
        CLARIFY["¿Prompt ambiguo? → clarificar"] --> LOOP

        subgraph "BUCLE Creator ↔ Reviewer"
            LOOP{"iteración N / max"}
            CREATOR["Creator<br/>genera/refina documento"]
            REVIEWER["Reviewer<br/>evalúa calidad<br/>+ genera redirection_summary"]
            CREATOR -->|"draft"| REVIEWER
            REVIEWER -->|"NEEDS_REVISION<br/>+ issues + checklist"| CREATOR
            REVIEWER -->|"APPROVED"| SAVE
            LOOP --> CREATOR
        end

        SAVE["Guardar .md / .json en disco"]
        SAVE --> PROP

        PROP{"¿es_redireccion = false<br/>y redirection_summary<br/>tiene contenido?"}
        PROP -->|"SÍ"| ENQUEUE["Encolar redirección<br/>a cada fase existente"]
        PROP -->|"NO"| NO_PROP["No propagar cambios"]

        ENQUEUE --> DONE
        NO_PROP --> DONE
        DONE["target_phase = ''"]
    end

    PRODUCT --> SELECTOR
    REQUIREMENTS --> SELECTOR
    DESIGN --> SELECTOR

    subgraph "AGENTES (6 en total)"
        PC["ProductCreator<br/>genera/modifica product.md"]
        PR["ProductReviewer<br/>evalúa calidad + redirection_summary"]
        RC["RequirementsCreator<br/>genera/modifica requirements.md"]
        RR["RequirementsReviewer<br/>evalúa calidad EARS + redirection_summary"]
        DC["DesignCreator<br/>genera/modifica design.json"]
        DR["DesignReviewer<br/>evalúa schema BUML + redirection_summary"]
    end

    subgraph "REDIRECCIÓN"
        direction LR
        R1["Requisitos cambia<br/>→ redirection_summary:<br/>'Se agregó Req 7: Facturación'"]
        R2["Selector envía a Producto<br/>→ user_prompt = resumen"]
        R3["Producto recibe<br/>→ Creator decide si modificar"]
        R1 --> R2 --> R3
    end

    style START fill:#0f3460,stroke:#00ff88,color:#fff
    style END_NODE fill:#0f3460,stroke:#00ff88,color:#fff
    style MENU fill:#1a1a2e,stroke:#e94560,color:#fff
    style SELECTOR fill:#1a1a2e,stroke:#e94560,color:#fff
    style PRODUCT fill:#16213e,stroke:#0f3460,color:#fff
    style REQUIREMENTS fill:#16213e,stroke:#0f3460,color:#fff
    style DESIGN fill:#16213e,stroke:#0f3460,color:#fff
