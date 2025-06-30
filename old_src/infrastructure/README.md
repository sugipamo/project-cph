# Infrastructure Layer Architecture

## Current Structure

```
infrastructure/
├── domain/                    # Domain Layer (Business Logic)
│   ├── requests/             # Request objects and operations
│   ├── results/              # Result objects and data structures
│   ├── types/                # Domain types and enums
│   └── constants/            # Domain constants
│
├── application/              # Application Layer (Use Cases)
│   ├── orchestration/        # Execution orchestration and control
│   ├── factory/              # Object creation and factories
│   └── formatters/           # Output formatting and presentation
│
├── infra/                    # Infrastructure Layer (External Systems)
│   ├── drivers/              # External system drivers
│   ├── persistence/          # Data persistence (SQLite, JSON)
│   └── environment/          # Environment management
│
└── shared/                   # Shared Components
    ├── utils/                # Utility functions and helpers
    ├── exceptions/           # Common exceptions
    ├── mock/                 # Test doubles and mocks
    └── di_container.py       # Dependency injection container
```

## Layer Responsibilities

### Domain Layer (`requests/`, `results/`, `types/`, `constants/`)
- **Purpose**: Core business logic and domain models
- **Dependencies**: Should not depend on external frameworks or infrastructure
- **Contents**: Request/Response objects, domain types, business constants

### Application Layer (`orchestration/`, `factory/`, `formatters/`)
- **Purpose**: Application use cases and coordination
- **Dependencies**: Can depend on domain layer, should not depend on infrastructure details
- **Contents**: Workflow orchestration, object factories, output formatting

### Infrastructure Layer (`drivers/`, `persistence/`, `environment/`)
- **Purpose**: External system integration and technical concerns
- **Dependencies**: Can depend on domain and application layers
- **Contents**: Database access, file system operations, external API calls

### Shared Layer (`utils/`, `exceptions/`, `mock/`, `di_container.py`)
- **Purpose**: Common utilities and cross-cutting concerns
- **Dependencies**: Should be dependency-free or minimal dependencies
- **Contents**: Utility functions, common exceptions, test infrastructure

## Current Implementation Notes

⚠️ **Known Issues:**
1. Layer boundaries are not strictly enforced in the current codebase
2. Some circular dependencies may exist between layers
3. The current structure mixes layers within the same directory

📋 **Future Improvements:**
1. Consider reorganizing into explicit layer directories
2. Implement dependency rules to prevent layer violations
3. Extract pure domain logic from infrastructure concerns

## Usage Guidelines

1. **Importing**: Always import from the most specific module possible
2. **Dependencies**: Follow the dependency rule (outer layers depend on inner layers)
3. **Testing**: Use mock implementations from the `mock/` directory for testing
4. **Extensions**: Add new functionality in the appropriate layer based on its responsibility