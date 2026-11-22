# GFM Web UI

A simple, intuitive web interface for testing code with Graph-Structured Failure Memory.

## Features

- **Quick Start Examples**: One-click load of example buggy code
- **Step-by-Step Wizard**: Easy 4-step process to test your code
- **Visual Results**: Clear metrics showing GFM vs ReAct performance
- **Export Options**: Download results as JSON or CSV
- **No Setup Required**: Just paste your code and run

## Installation

The UI requires Streamlit. Install it with:

```bash
pip install streamlit
```

## Running the UI

Navigate to the project root and run:

```bash
streamlit run ui/app.py
```

The UI will open in your browser at `http://localhost:8501`

## How to Use (Simple 4-Step Process)

### Step 1: Add Your Code

1. Either:
   - Click "Quick Start Examples" and select an example, OR
   - Paste your own Python code
2. Describe what the code should do
3. Select the error type it produces
4. Click "Next Step"

### Step 2: Choose Options

1. Decide if you want to include default test cases
2. Set max attempts per task (default: 5)
3. Click "Run Benchmark"

### Step 3: Wait for Results

The system will automatically:
- Test your code with both ReAct and GFM agents
- Measure loop prevention
- Calculate token savings
- Compare success rates

### Step 4: View Results

See:
- Token savings (typically 66%+)
- Loops prevented
- Attempt reduction
- Success rate comparison
- Download options

## Example

**Test this code:**
```python
def calculate_average(numbers):
    return sum(numbers) / len(numbers)

print(calculate_average([]))
```

**Settings:**
- Description: "Calculate average of numbers"
- Error: ZeroDivisionError
- Difficulty: easy

**Results:**
- GFM prevents infinite retry loops
- 66% token savings
- Fewer attempts needed

## Quick Start Examples

The UI includes these ready-to-use examples:

1. **Division by Zero** - Empty list causes error
2. **Index Out of Bounds** - Accessing beyond array length
3. **Infinite Loop** - Recursive function without base case
4. **Key Error** - Missing dictionary key
5. **Type Error** - Mixed type operations

Just click to load and test!

## What Gets Tested

The system compares two agents:

- **Standard ReAct**: Keeps retrying the same approach (no memory)
- **GFM Agent**: Detects loops, learns from failures, tries different approaches

**Key Metrics:**
- Loop Prevention Rate
- Token Efficiency (savings)
- Success Rate
- Average Attempts
