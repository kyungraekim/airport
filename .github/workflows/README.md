# GitHub Workflows for Model Commands

This directory contains GitHub Action workflows that are triggered when slash commands are posted in Issues. The bot server parses these commands and triggers the appropriate workflows.

## Available Workflows

### 0. Help Command (`help-command.yml`)
**Triggered by:** `/help` commands in Issues and Pull Requests
**Purpose:** Provide comprehensive documentation about all available commands

**Command Examples:**
```bash
/help                    # Show all commands overview
/help train              # Get detailed help for training
/help eval               # Get help for evaluation commands
```

**Workflow Features:**
- Context-aware help responses
- Detailed parameter explanations
- Interactive examples and use cases
- Command-specific documentation
- Automatic posting to Issues/PRs

### 1. Train Model (`train-model.yml`)
**Triggered by:** `/train` commands in Issues
**Purpose:** Train ML models with specified parameters

**Command Examples:**
```bash
/train --config=new --epochs=10 --lr=0.001
/train --epochs=50 --gpu=2 --batch_size=32
```

**Workflow Features:**
- Configurable training parameters
- Progress simulation with realistic metrics
- Model artifact generation
- Comprehensive training reports

### 2. Evaluate Model (`evaluate-model.yml`)
**Triggered by:** `/eval` commands in Issues  
**Purpose:** Evaluate and compare model performance

**Command Examples:**
```bash
/eval --model=baseline,incoming --metrics=accuracy,f1
/eval --model=latest --metrics=all
```

**Workflow Features:**
- Multi-model comparison
- Customizable metrics computation
- Visual comparison charts
- Performance analysis reports

### 3. Test Model (`test-model.yml`)
**Triggered by:** `/test` commands in Pull Requests
**Purpose:** Run comprehensive model testing

**Command Examples:**
```bash
/test --type=smoke --samples=100
/test --type=integration
/test --type=performance --samples=1000
```

**Workflow Features:**
- Multiple test types (smoke, integration, performance)
- Configurable test sample sizes
- Detailed test reporting
- Failure analysis

### 4. Model Pipeline (`model-pipeline.yml`)
**Triggered by:** `/pipeline` commands in Issues
**Purpose:** Execute multi-step ML pipelines

**Command Examples:**
```bash
/pipeline --steps=train,eval --skip=test
/pipeline --steps=all
/pipeline --steps=train,eval,test,validate
```

**Workflow Features:**
- Flexible step configuration
- Step dependency handling
- Comprehensive pipeline reporting
- Failure recovery and validation

## Workflow Inputs

All workflows accept these common inputs:

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `job_id` | Unique job identifier from bot | No | - |
| `command` | Original slash command | No | - |
| `user` | User who triggered the command | No | - |

### Command-Specific Inputs

**Training Workflows:**
- `config`: Training configuration name
- `epochs`: Number of training epochs
- `learning_rate` / `lr`: Learning rate
- `gpu`: Number of GPUs to use
- `batch_size`: Training batch size

**Evaluation Workflows:**
- `model`: Comma-separated list of models to evaluate
- `metrics`: Comma-separated list of metrics to compute
- `batch_size`: Evaluation batch size

**Testing Workflows:**
- `test_type`: Type of tests (`smoke`, `integration`, `performance`, `all`)
- `samples`: Number of test samples
- `model_path`: Path to model for testing

**Pipeline Workflows:**
- `steps`: Pipeline steps to execute (`train,eval,test,validate`)
- `skip`: Steps to skip
- `config`: Pipeline configuration

## Help System

The help system (`help-command.yml`) provides comprehensive documentation and responds to `/help` commands:

### Help Command Usage

- **`/help`** - Shows complete overview of all available commands
- **`/help <command>`** - Shows detailed help for specific command
- **Examples:**
  - `/help train` - Detailed training command help
  - `/help eval` - Model evaluation help  
  - `/help test` - Testing command help
  - `/help pipeline` - Pipeline command help

### Demo System

Use the `demo-help.yml` workflow to test the help system:

1. Go to Actions → Demo Help System
2. Click "Run workflow"
3. Select demo type (general-help, train-help, etc.)
4. Enable "Create demo issue" 
5. The workflow will create an issue and demonstrate the help response

## Manual Workflow Triggering

You can manually trigger workflows using GitHub's workflow dispatch feature:

1. Go to your repository's Actions tab
2. Select the desired workflow
3. Click "Run workflow"
4. Fill in the input parameters
5. Click "Run workflow"

### Using GitHub CLI

```bash
# Train a model
gh workflow run train-model.yml \
  -f config=production \
  -f epochs=20 \
  -f learning_rate=0.001 \
  -f job_id=manual-001

# Evaluate models
gh workflow run evaluate-model.yml \
  -f model="baseline,candidate" \
  -f metrics="accuracy,f1,precision,recall" \
  -f job_id=manual-002

# Run tests
gh workflow run test-model.yml \
  -f test_type=smoke \
  -f samples=100 \
  -f job_id=manual-003

# Execute pipeline
gh workflow run model-pipeline.yml \
  -f steps="train,eval,test" \
  -f epochs=15 \
  -f job_id=manual-004
```

## Artifacts Generated

Each workflow generates artifacts that include:

- **JSON result files** with detailed metrics and outcomes
- **Markdown reports** with human-readable summaries
- **Configuration files** used during execution
- **Log files** for debugging and analysis
- **Visualization charts** (for evaluation workflows)

Artifacts are automatically uploaded and can be downloaded from the workflow run page.

## Integration with Bot Server

The bot server integrates with these workflows by:

1. **Parsing Commands:** Extracting parameters from Issue comments
2. **Triggering Workflows:** Using GitHub's workflow dispatch API
3. **Tracking Progress:** Monitoring workflow status (future enhancement)
4. **Updating Comments:** Posting workflow results back to Issues

## Development and Testing

### Local Testing

You can test the Python logic locally:

```bash
cd /path/to/your/repo

# Test training simulation
python -c "
import json
import time
epochs = 5
for epoch in range(1, epochs + 1):
    print(f'Epoch {epoch}/{epochs}')
    time.sleep(1)
print('Training completed!')
"
```

### Workflow Testing

1. Create test Issues with slash commands
2. Observe workflow triggers in Actions tab
3. Download artifacts to verify outputs
4. Check workflow logs for debugging

## Configuration

### Environment Variables

Set these in your repository secrets for production:

- `GITHUB_TOKEN`: For workflow dispatch (automatically provided)
- `ML_CONFIG_PATH`: Path to ML configurations
- `ARTIFACT_STORAGE_URL`: External artifact storage (optional)

### Customization

To customize workflows for your specific use case:

1. **Modify Python Scripts:** Update the embedded Python code for your ML framework
2. **Add Dependencies:** Update the `pip install` commands
3. **Change Parameters:** Modify workflow inputs and defaults
4. **Add Steps:** Include additional workflow steps as needed

## Troubleshooting

### Common Issues

1. **Workflow not triggering:** Check repository permissions and GitHub token
2. **Python errors:** Verify dependencies and script syntax
3. **Artifact upload failures:** Check file paths and permissions
4. **Missing inputs:** Ensure all required parameters are provided

### Debugging

- Check workflow logs in GitHub Actions
- Download artifacts to examine output files
- Test Python scripts locally before deployment
- Use workflow dispatch for manual testing

## Future Enhancements

- **Real ML Integration:** Replace simulation with actual ML frameworks
- **Status Callbacks:** Report progress back to GitHub Issues
- **Resource Management:** Add GPU/CPU resource allocation
- **Distributed Execution:** Support for multi-node training
- **Model Registry:** Integration with model versioning systems