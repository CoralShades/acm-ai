# Tool Creation Template

Custom tools are TypeScript/JavaScript functions that extend AI capabilities.

## File Structure

Tools are defined in `.opencode/tool/<tool-name>.ts`

## Basic Template

```typescript
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Brief description of what this tool does",
  args: {
    param1: tool.schema.string()
      .describe("Description of parameter 1"),
    param2: tool.schema.number()
      .describe("Description of parameter 2")
      .optional(),
    param3: tool.schema.enum(["option1", "option2"])
      .describe("Enum parameter")
      .default("option1")
  },
  async execute({ param1, param2, param3 }) {
    try {
      // Tool implementation
      const result = await doSomething(param1, param2, param3)

      return {
        success: true,
        message: "Operation completed",
        data: result
      }
    } catch (error) {
      return {
        success: false,
        message: `Operation failed: ${error.message}`,
        hint: "Suggestion for resolving the issue"
      }
    }
  }
})
```

## Schema Types

```typescript
// String
tool.schema.string()
  .describe("Description")
  .optional()
  .default("default value")

// Number
tool.schema.number()
  .describe("Description")
  .min(0)
  .max(100)

// Boolean
tool.schema.boolean()
  .describe("Description")
  .default(false)

// Enum
tool.schema.enum(["option1", "option2", "option3"])
  .describe("Description")
  .default("option1")

// Array
tool.schema.array(tool.schema.string())
  .describe("Array of strings")

// Object
tool.schema.object({
  field1: tool.schema.string(),
  field2: tool.schema.number()
})
```

## Example: Service Status Tool

```typescript
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Check the health and status of all AI stack services",
  args: {},
  async execute() {
    const { $ } = await import("bun")

    try {
      const result = await $`docker compose -p localai ps --format json`.quiet()
      const output = result.stdout.toString()

      if (!output.trim()) {
        return {
          status: "stopped",
          message: "No containers running",
          containers: []
        }
      }

      const containers = output.trim().split('\n')
        .map(line => JSON.parse(line))
        .filter(Boolean)

      return {
        status: "running",
        message: `${containers.length} containers running`,
        containers: containers.map(c => ({
          name: c.Name,
          state: c.State,
          ports: c.Ports
        }))
      }
    } catch (error) {
      return {
        status: "error",
        message: `Failed to check status: ${error.message}`
      }
    }
  }
})
```

## Example: HTTP Request Tool

```typescript
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Make HTTP requests to APIs",
  args: {
    url: tool.schema.string().describe("URL to request"),
    method: tool.schema.enum(["GET", "POST", "PUT", "DELETE"])
      .describe("HTTP method")
      .default("GET"),
    body: tool.schema.string()
      .describe("Request body (JSON)")
      .optional()
  },
  async execute({ url, method, body }) {
    try {
      const options: RequestInit = { method }

      if (body && method !== "GET") {
        options.headers = { "Content-Type": "application/json" }
        options.body = body
      }

      const response = await fetch(url, options)
      const data = await response.json()

      return {
        success: response.ok,
        status: response.status,
        data
      }
    } catch (error) {
      return {
        success: false,
        message: error.message
      }
    }
  }
})
```

## Example: File Operations Tool

```typescript
import { tool } from "@opencode-ai/plugin"
import { readFile, writeFile } from "fs/promises"

export default tool({
  description: "Read or write files",
  args: {
    operation: tool.schema.enum(["read", "write"])
      .describe("Operation type"),
    path: tool.schema.string()
      .describe("File path"),
    content: tool.schema.string()
      .describe("Content to write")
      .optional()
  },
  async execute({ operation, path, content }) {
    try {
      if (operation === "read") {
        const data = await readFile(path, "utf-8")
        return { success: true, content: data }
      } else {
        if (!content) {
          return { success: false, message: "Content required for write" }
        }
        await writeFile(path, content)
        return { success: true, message: "File written" }
      }
    } catch (error) {
      return { success: false, message: error.message }
    }
  }
})
```

## Best Practices

1. **Clear Descriptions** - Write detailed descriptions for tool and parameters
2. **Error Handling** - Always catch errors and return helpful messages
3. **Return Structure** - Use consistent return objects with success/message/data
4. **Type Safety** - Use proper schema types for validation
5. **Async Operations** - Tools should be async for I/O operations
6. **Security** - Validate inputs and avoid command injection
