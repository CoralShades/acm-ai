# E35-S1 Verification: Sync Upload asyncio.run() Error

## Status: PASS

## Code Verification

### 1. commands/source_commands.py -- No asyncio.run() Present

The `process_source_command()` function at line 569 is declared as `async def` and uses `await` throughout:

- Line 569: `async def process_source_command(input_data: SourceProcessingInput) -> SourceProcessingOutput`
- Line 588: `transformation = await Transformation.get(trans_id)`
- Line 595: `source = await Source.get(input_data.source_id)`
- Line 605: `await source.save()`
- Line 627: `result = await source_graph.ainvoke(...)`
- Line 672: `merged_tables, _timings = await _run_dual_provider_extraction(...)`
- Line 678: `await _store_docling_tables(...)`

A grep for `asyncio.run` in the entire `commands/` directory returned **zero matches**, confirming the fix removed the problematic `asyncio.run()` call.

### 2. api/routers/sources.py -- Sync Upload Path Uses await Correctly

The sync upload path (line 508-605) uses `submit_command()` + `await wait_for_command()`:

- Line 537: `cmd_id = submit_command("open_notebook", "process_source", ...)` (sync submit)
- Line 542: `result = await wait_for_command(cmd_id, timeout=300)` (async wait)

This pattern correctly delegates processing to the worker via surreal-commands, avoiding the `asyncio.run()` nested event loop error that occurred when trying to call `asyncio.run()` inside an already-running FastAPI event loop.

A grep for `asyncio.run` in `api/routers/sources.py` returned **zero matches**.

### 3. Async Path Also Correct

The async upload path (line 433-506) uses `await CommandService.submit_command_job(...)` at line 462, which is fully async.

## Test Results

```
129 passed, 1993 deselected, 7 warnings in 16.87s
```

All 129 source-related tests pass. No failures.

## Evidence

Key code pattern confirming the fix:

```python
# api/routers/sources.py, lines 537-542 (sync path)
cmd_id = submit_command(
    "open_notebook",
    "process_source",
    command_input.model_dump(),
)
result = await wait_for_command(
    cmd_id,
    timeout=300,
)
```

```python
# commands/source_commands.py, line 569
async def process_source_command(
    input_data: SourceProcessingInput,
) -> SourceProcessingOutput:
```

## Notes

- No remaining `asyncio.run()` calls anywhere in the upload/processing pipeline
- The surreal-commands worker runs the async command handler in its own event loop, so there is no nested event loop conflict
- All 129 source-related tests pass cleanly
