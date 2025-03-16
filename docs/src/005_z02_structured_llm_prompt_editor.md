This can be a Typescript app which allows for adding a `StructuredLLMCall`.
- Input type and schema
- Output type and schema
- Prompt
- Default Model

Then it gives a slug based url which can be called with the input, and the model type.

We can also save all the invocations, making it easier to debug.

#### Template Editor
We have a lot of prompts and we need to regularly update them. We should have some configurable way to update the prompts

The prompts take a input object and then return a string. Handlebars can be used to populate the string with the object.
There is also good support for handlebars in react online editors and we can use one of them to edit the prompts via a UI.

See these examples & libraries
- https://medium.com/@jacksbridger/building-a-handlebars-email-previewer-df83d346e2e2
- https://github.com/suren-atoyan/monaco-react && https://github.com/react-monaco-editor/react-monaco-editor

More Information
- This editor can be a standalone lambda app or can be a vercel app.
- We can save the prompts in a json file and then load them in the editor or in the DB
- We can also have a versioning system for the prompts
- We can write a simple python script to make it easy to use the prompts in python code.


#### JSON schema editor.
We also use a JSON schema for getting a structured response. We should also be able to create the JSON schema via a UI.

We can use
- https://github.com/Open-Federation/json-schema-editor-visual
- https://github.com/ginkgobioworks/react-json-schema-form-builder
- https://github.com/Optum/jsonschema-editor-react
- https://github.com/lin-mt/json-schema-editor-antd

----
```typescript
interface Prompt {
  id: string;
  inputJsonSchemaId: string;
  outputJsonSchemaId: string;
  promptTemplate: string;
  sampleInput: string;   
  defaultModel: string;
  version: number;
  commitMessage: string;
  isLive: boolean;
}

interface StructuredLLMCall {
  input: any;
  modelType: string;
  promptId: string;
}

```

```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model Schema {
  id          String           @id @default(uuid())
  name        String           @unique
  description String?
  createdAt   DateTime         @default(now())
  versions    SchemaVersion[]  @relation(onDelete: Cascade) // Cascade delete versions when Schema is deleted
  activeVersion SchemaVersion? @relation("ActiveVersion")   // Track active version
}

model SchemaVersion {
  id         String         @id @default(uuid())
  version    Int
  content    Json
  createdAt  DateTime       @default(now())
  schema     Schema         @relation(fields: [schemaId], references: [id], onDelete: Cascade)
  schemaId   String
  isActive   Boolean        @default(false) // Indicates if this version is active
  referencesFrom SchemaReference[] @relation("SourceReferences")
  referencesTo   SchemaReference[] @relation("TargetReferences")
  prompts    Prompt[]       // Prompts using this schema version

  @@unique([schemaId, version])
  @@index([schemaId, isActive]) // For efficient active version lookup
}

model SchemaReference {
  id              String         @id @default(uuid())
  fromVersionId   String
  fromVersion     SchemaVersion  @relation("SourceReferences", fields: [fromVersionId], references: [id], onDelete: Cascade)
  toVersionId     String
  toVersion       SchemaVersion  @relation("TargetReferences", fields: [toVersionId], references: [id], onDelete: Restrict) // Prevent deletion of referenced versions
  description     String?
  referenceType   String?        // Type of reference (e.g., "dependency", "extension")
  createdAt       DateTime       @default(now())
}

model Prompt {
  id                 String         @id @default(cuid())
  inputSchemaVersion SchemaVersion  @relation(fields: [inputSchemaVersionId], references: [id], name: "InputSchemaVersion")
  inputSchemaVersionId String
  outputSchemaVersion SchemaVersion @relation(fields: [outputSchemaVersionId], references: [id], name: "OutputSchemaVersion")
  outputSchemaVersionId String
  promptTemplate     String
  sampleInput        String
  defaultModel       String
  version            Int
  commitMessage      String
  isLive             Boolean       @default(false)
  createdAt          DateTime      @default(now())
  updatedAt          DateTime      @updatedAt

  @@unique([inputSchemaVersionId, outputSchemaVersionId, version]) // Unique prompt version per schema versions
}

model StructuredLLMCall {
  id        String   @id @default(cuid())
  input     Json     
  modelType String   
  prompt    Prompt   @relation(fields: [promptId], references: [id], onDelete: Cascade)
  promptId  String   
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```
### Schema Management - Cases Handled

1. **Creating a New Schema:**
    - The `Schema` model holds the overall metadata (name, description) for a JSON schema.
    - The `name` field is unique to ensure no duplicates.

2. **Maintaining Multiple Versions:**
    - The `SchemaVersion` model stores each version’s JSON content along with a version number.
    - A composite unique index (`@@unique([schemaId, version])`) guarantees that a given schema cannot have duplicate version numbers.

3. **Storing JSON Content:**
    - The `content` field in `SchemaVersion` is of type `Json` so that you can store the full JSON schema (which may include nested entities and references).

4. **Version History/Audit:**
    - The `createdAt` timestamps in both `Schema` and `SchemaVersion` models allow you to track when a schema and its versions were created.

5. **Handling Schema References:**
    - The `SchemaReference` model enables one schema version to refer to another. This supports cases where one JSON schema (or a part of it) needs to reference definitions or entities defined in another schema version.
    - The model includes both `fromVersion` (the referring version) and `toVersion` (the referenced version).

6. **Relational Integrity:**
    - All relations (e.g., linking a version to its schema or a reference between versions) are enforced by Prisma’s relation fields.
    - This ensures consistency when you update or delete a record.

7. **Extensibility:**
    - Optional fields like `description` in both `Schema` and `SchemaReference` let you add additional metadata.
    - The structure can be extended if you later need to capture more granular details (for example, if you want to manage internal entities within a JSON schema).

This structure should cover all the essential cases for managing JSON schemas with version history and inter-schema (or inter-entity) references.


To ensure your Prisma schema comprehensively handles all use cases for managing JSON schemas with versioning and references, let's address the identified gaps and enhance the schema:

### Enhanced Prisma Schema with Annotations

### Addressed Use Cases and Enhancements
 `deletedAt` fields if soft deletion is required (not shown here).

### Complete List of Handled Use Cases

1. **Schema Management**
    - ✅ Create schemas with unique names.
    - ✅ Track active version per schema.
    - ✅ Cascade delete all versions when a schema is deleted.

2. **Version Control**
    - ✅ Immutable version history with incremental `version` numbers.
    - ✅ Enforce unique version numbers per schema (`@@unique([schemaId, version])`).
    - ✅ Track creation timestamps for auditing.

3. **References Between Schemas**
    - ✅ Cross-schema version references via `SchemaReference`.
    - ✅ Prevent accidental deletion of referenced versions (`onDelete: Restrict`).
    - ✅ Categorize references with `referenceType`.

4. **Data Integrity**
    - ✅ Foreign key constraints for all relationships (e.g., Prompt ↔ SchemaVersion).
    - ✅ Cascading deletes where appropriate (e.g., Schema → SchemaVersion).

5. **Prompt Management**
    - ✅ Link prompts to specific schema versions for input/output.
    - ✅ Unique prompt versions per input/output schema combination.

6. **Performance**
    - ✅ Indexes for frequent queries (active versions, schema-version pairs).

7. **Extensibility**
    - ✅ Optional fields (`description`, `referenceType`) for future needs.

8. **Audit and Compliance**
    - ✅ `createdAt`/`updatedAt` timestamps on all models.

### Unhandled Cases (Require Application Logic)


1. **Active Version Tracking**
    - `Schema.activeVersion`: Optional 1-1 relation to track the currently active version.
    - `SchemaVersion.isActive`: Boolean flag for quick filtering of active versions.

2. **Reference Integrity**
    - **Cascading Deletes**: Schema versions are deleted when their parent Schema is removed (`onDelete: Cascade`).
    - **Protected References**: Prevents deletion of `SchemaVersion` if referenced by others (`onDelete: Restrict` on `SchemaReference.toVersion`).

3. **Prompt-Schema Relationships**
    - Fixed relations in `Prompt` to use `SchemaVersion` via `inputSchemaVersionId` and `outputSchemaVersionId`, ensuring referential integrity.

4. **Reference Types**
    - Added `referenceType` in `SchemaReference` to categorize references (e.g., "dependency", "extension").

5. **Indexing for Performance**
    - Composite index on `[schemaId, isActive]` for efficient active version queries.

6. **Prompt Version Uniqueness**
    - `@@unique` constraint on `Prompt` ensures unique combinations of input/output schema versions and prompt version.

7. **Handling Deletion Propagation**
    - `StructuredLLMCall` cascades deletes when linked `Prompt` is removed.

8. **Soft Delete Support (Optional)**
    - Consider adding `isArchived` or
----
1. **Circular Reference Prevention**
    - Application must detect and prevent circular references during reference creation.

2. **Version Number Assignment**
    - App must auto-increment version numbers when adding new versions.

3. **Schema Validation**
    - Validate JSON `content` against JSON Schema standards on creation/update.

4. **Deprecation Workflow**
    - Use `isActive` to manage deprecation, but app logic needed to enforce only one active version.

5. **Data Migration**
    - Migration of existing data when schemas change must be handled in app logic.

This schema provides a robust foundation for your application, ensuring data integrity, version control, and flexible references while leaving business-specific logic to the application layer.
