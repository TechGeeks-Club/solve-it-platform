# Seed Data Enhancement Guide

## Summary of Changes

The `init_data.json` file has been enhanced with:

1. **Test Cases (TaskTest)** - Multiple test cases for each task with different scenarios
2. **Initial Code Templates** - Proper C language boilerplate code with input handling
3. **Enhanced Problem Descriptions** - Clear input/output specifications

## What Has Been Added

### Tasks with Complete Test Cases

The following tasks now have complete test cases and proper initial code:

- **Task 8 - Parity Check**: 5 test cases (2 sample, 3 hidden)
- **Task 9 - Natural Number Summation**: 4 test cases (2 sample, 2 hidden)
- **Task 10 - Prime Number Check**: 5 test cases (2 sample, 3 hidden)
- **Task 13 - Factorial Finder**: 4 test cases (2 sample, 2 hidden)
- **Task 16 - Array Element Finder**: 4 test cases (2 sample, 2 hidden)
- **Task 17 - Vowel Counter**: 5 test cases (2 sample, 3 hidden)
- **Task 18 - Array Reversal**: 4 test cases (2 sample, 2 hidden)

## Test Case Structure

Each test case follows this structure:

```json
{
    "model": "tasks.tasktest",
    "pk": <unique_id>,
    "fields": {
        "task": <task_id>,
        "input": "<input_data>",
        "output": "<expected_output>",
        "display": true/false,      // true for sample cases
        "weight": 1 or 2,            // weighted scoring
        "is_sample": true/false,     // mark sample cases
        "order": <execution_order>   // order of test execution
    }
}
```

### Test Case Best Practices

1. **Sample Tests** (`is_sample: true`, `display: true`)
   - At least 2 per task
   - Show basic functionality
   - Visible to students for testing

2. **Hidden Tests** (`is_sample: false`, `display: false`)
   - Edge cases (empty input, zero, negative numbers, etc.)
   - Large values
   - Complex scenarios
   - Higher weight for difficult cases

3. **Test Weights**
   - Basic tests: `weight: 1`
   - Complex/Edge cases: `weight: 2`
   - Used for weighted scoring calculation

## Initial Code Template Pattern

All tasks now use proper C templates:

```c
#include <stdio.h>

int main() {
    int n;
    scanf("%d", &n);
    
    // Your code here
    
    return 0;
}
```

For array problems:
```c
#include <stdio.h>

int main() {
    int n;
    scanf("%d", &n);
    int arr[n];
    
    for(int i = 0; i < n; i++) {
        scanf("%d", &arr[i]);
    }
    
    // Your code here
    
    return 0;
}
```

For string problems:
```c
#include <stdio.h>
#include <string.h>

int main() {
    char str[101];
    scanf("%s", str);
    
    // Your code here
    
    return 0;
}
```

## Pattern for Remaining Tasks

To add test cases for remaining tasks, follow this pattern:

### 1. Update Task Context
Add clear input/output specifications:
```
Input: <description of input format>
Output: <description of expected output>
```

### 2. Add Initial Code
Replace `"// Enter code here"` with proper C template based on problem type.

### 3. Create Test Cases
Add at least 4-5 test cases:
- 2 sample cases (basic scenarios)
- 2-3 hidden cases (edge cases, complex scenarios)

### Example for Task 20 (Maximum sum for consecutive pairs):

```json
{
    "model": "tasks.Task",
    "pk": 20,
    "fields": {
        "category": 2,
        "context": "Given an array A of 8 integers, Write a program in c for entering the array A, calculating, and display the greatest sum of two consecutive elements in A.\r\n\r\nInput: 8 integers separated by spaces\r\nOutput: The maximum sum of two consecutive elements",
        "initialCode": "#include <stdio.h>\n\nint main() {\n    int arr[8];\n    for(int i = 0; i < 8; i++) {\n        scanf(\"%d\", &arr[i]);\n    }\n    \n    // Your code here\n    \n    return 0;\n}",
        // ... rest of fields
    }
},
{
    "model": "tasks.tasktest",
    "pk": 32,
    "fields": {
        "task": 20,
        "input": "1 2 3 4 5 6 7 8",
        "output": "15",
        "display": true,
        "weight": 1,
        "is_sample": true,
        "order": 1
    }
},
// ... more test cases
```

## Judge0 Integration

### Language ID
All C code uses Judge0 language ID: **50** (C GCC 9.2.0)

This is set in the TaskSolution model with:
```python
language_id = models.IntegerField(default=50)
```

### Test Execution Flow

1. Student submits code
2. Django sends to Kafka (`code-submissions` topic)
3. Judge microservice:
   - Fetches test cases from database
   - Executes code against each test case using Judge0
   - Calculates weighted score
   - Sends results to Kafka (`code-results` topic)
4. Django consumer updates TaskSolution with results

### Score Calculation

Score is weighted based on test case weights:

```
score = (sum of weights for passed tests / sum of all weights) * 100
```

Example:
- Test 1 (weight: 1) - Passed ✓
- Test 2 (weight: 1) - Passed ✓
- Test 3 (weight: 1) - Failed ✗
- Test 4 (weight: 2) - Passed ✓

Score = ((1 + 1 + 2) / (1 + 1 + 1 + 2)) * 100 = 80%

## Next Steps

### To Complete Seed Data

For each remaining task (1-7, 11-12, 14-15, 19-37, etc.):

1. **Update Context**: Add clear input/output format
2. **Update Initial Code**: Replace generic comments with proper C template
3. **Add Test Cases**: Create 4-5 test cases following the pattern above

### Test Case ID Sequence

Continue numbering from pk: 32 onwards for new test cases.

### To Load Seed Data

```bash
# Inside Docker container
docker-compose exec django python manage.py loaddata /app/../database/json_db/init_data.json

# Or use Django management command
python manage.py loaddata database/json_db/init_data.json
```

## Example: Complete Task Definition

```json
{
    "model": "tasks.Task",
    "pk": 9,
    "fields": {
        "category": 3,
        "context": "Sum of Natural Numbers\r\nProblem Statement:\r\nWrite a program to find the sum of the first  `n` natural numbers.\r\n\r\nInput: A positive integer n\r\nOutput: The sum of numbers from 1 to n",
        "initialCode": "#include <stdio.h>\n\nint main() {\n    int n;\n    scanf(\"%d\", &n);\n    \n    // Your code here\n    \n    return 0;\n}",
        "level": "easy",
        "nextTask": null,
        "openCode": null,
        "phase": 1,
        "points": 10,
        "title": "Natural Number Summation"
    }
},
{
    "model": "tasks.tasktest",
    "pk": 6,
    "fields": {
        "task": 9,
        "input": "5",
        "output": "15",
        "display": true,
        "weight": 1,
        "is_sample": true,
        "order": 1
    }
},
{
    "model": "tasks.tasktest",
    "pk": 7,
    "fields": {
        "task": 9,
        "input": "10",
        "output": "55",
        "display": true,
        "weight": 1,
        "is_sample": true,
        "order": 2
    }
},
{
    "model": "tasks.tasktest",
    "pk": 8,
    "fields": {
        "task": 9,
        "input": "1",
        "output": "1",
        "display": false,
        "weight": 1,
        "is_sample": false,
        "order": 3
    }
},
{
    "model": "tasks.tasktest",
    "pk": 9,
    "fields": {
        "task": 9,
        "input": "100",
        "output": "5050",
        "display": false,
        "weight": 2,
        "is_sample": false,
        "order": 4
    }
}
```

## Notes

- Test case `pk` must be unique across all test cases
- The `order` field determines execution sequence
- Multi-line input uses `\n` in the input field
- Output should match exactly (case-sensitive, no extra whitespace)
- For problems requiring multiple outputs, use space or newline separation consistently
