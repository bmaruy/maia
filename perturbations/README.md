# MAIA Perturbation System

A framework for testing MAIA's robustness by perturbing prompts in controlled ways.

## Quick Start

### 1. Apply Perturbations

```python
from perturbations import apply_perturbations

# Apply a perturbation config
apply_perturbations('perturbations/configs/test_simple.yaml')
```

### 2. Run MAIA Experiment

Run MAIA normally - it will use the perturbed prompts:

```bash
python main.py --agent local-google/gemma-3-27b-it --model resnet152 --device 0 --unit 42 --layer layer4
```

### 3. Restore Original Prompts

```python
from perturbations import restore_originals

# Restore all files to original state
restore_originals()
```

### 4. Clean Backups (optional)

```python
from perturbations import clean_backups

# Remove backup files
clean_backups()
```

## Available Configs

### Basic Tests

- **`test_simple.yaml`** - Adds a visible marker to verify perturbations work
- **`typo_injection.yaml`** - Adds 5% typo rate to test LLM robustness

### MAIA Workflow Tests

- **`iteration_control.yaml`** - Forces fixed number of iterations (default: 3)
- **`hypothesis_reduction.yaml`** - Forces single hypothesis instead of multiple
- **`output_format_change.yaml`** - Changes output format markers
- **`remove_tool.yaml`** - Removes a tool from API documentation

### Stress Tests

- **`combined_stress.yaml`** - Multiple simultaneous perturbations

## Creating Custom Configs

Config files are YAML (or JSON) with this structure:

```yaml
description: "What this test does"

perturbations:
  - file: "prompts/open/final.txt"      # Relative to maia_fork/
    type: "exact"                        # exact | regex | full
    find: "iterate until confident"     # For type: exact
    replace: "run exactly 3 iterations"
    description: "Why this change matters"

  - file: "prompts/open/api.txt"
    type: "full"                         # Apply to entire file
    strategy: "inject_typos"             # Strategy name from strategies.py
    rate: 0.05                           # Strategy-specific params
    seed: 42
    description: "Add typos to API"
```

### Perturbation Types

1. **`exact`** - Simple find/replace
   ```yaml
   type: "exact"
   find: "some text"
   replace: "new text"
   ```

2. **`regex`** - Pattern-based replacement
   ```yaml
   type: "regex"
   pattern: "neuron\\s+\\d+"
   replace: "unit \\1"
   ```

3. **`full`** - Apply strategy to entire file
   ```yaml
   type: "full"
   strategy: "inject_typos"
   rate: 0.05
   ```

### Available Strategies

See [strategies.py](strategies.py) for full list:

#### Basic
- `replace_text` - Replace entire content
- `append_text` - Add text to end
- `prepend_text` - Add text to beginning

#### Noise
- `append_random` - Add random words
- `remove_random_word` - Remove random word
- `inject_typos` - Add keyboard typos

#### Structural
- `shuffle_sentences` - Randomize sentence order
- `remove_section` - Remove marked section

#### MAIA-Specific
- `change_iteration_count` - Force fixed iterations
- `change_hypothesis_count` - Limit hypotheses
- `corrupt_output_format` - Change format markers
- `remove_tool_documentation` - Remove tool from API
- `swap_tool_names` - Swap two tool names

## Workflow Example

```python
from perturbations import apply_perturbations, restore_originals

# Test 1: Baseline (no perturbations)
# Run MAIA normally...

# Test 2: Limited iterations
apply_perturbations('perturbations/configs/iteration_control.yaml')
# Run MAIA...
# Compare results to baseline

# Test 3: Single hypothesis
restore_originals()
apply_perturbations('perturbations/configs/hypothesis_reduction.yaml')
# Run MAIA...
# Compare results

# Restore when done
restore_originals()
```

## File Locations

- **Strategies**: `perturbations/strategies.py`
- **Core logic**: `perturbations/perturber.py`
- **Configs**: `perturbations/configs/*.yaml`
- **Backups**: `.perturbation_backups/` (auto-created)

## Tips

1. **Always backup first** - The system auto-backs up before modifying
2. **Test incrementally** - Start with simple perturbations
3. **Check the diff** - After applying, manually verify changes:
   ```bash
   diff prompts/open/final.txt .perturbation_backups/final.txt.*.bak
   ```
4. **Restore between tests** - Don't stack perturbations unless intended
5. **Name configs clearly** - Use descriptive names for reproducibility

## Advanced: Creating New Strategies

Add to `strategies.py`:

```python
def my_custom_strategy(text: str, my_param: str = "default", **_) -> str:
    """What this strategy does."""
    # Your logic here
    return modified_text

# Register it
STRATEGIES["my_custom_strategy"] = my_custom_strategy
```

Then use in configs:

```yaml
perturbations:
  - file: "prompts/open/api.txt"
    type: "full"
    strategy: "my_custom_strategy"
    my_param: "custom value"
```