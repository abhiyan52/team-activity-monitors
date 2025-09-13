# Test Suite for Team Activity Monitor

This directory contains comprehensive test cases for the JIRA and GitHub clients.

## Overview

The test suite includes:
- **JIRA Client Tests** (`test_jira_client.py`) - Tests all JIRA SDK functionality
- **GitHub Client Tests** (`test_github_client.py`) - Tests all GitHub SDK functionality

## Prerequisites

1. **Environment Configuration**: Create a `.env` file in the backend directory with:
   ```
   # JIRA Configuration
   JIRA_SERVER_URL=https://your-domain.atlassian.net
   JIRA_EMAIL=your-email@example.com
   JIRA_API_TOKEN=your-jira-api-token
   
   # GitHub Configuration
   GITHUB_TOKEN=your-github-personal-access-token
   GITHUB_ORGANIZATION=your-org-name  # Optional
   ```

2. **Dependencies**: Install test dependencies:
   ```bash
   pip install pytest pytest-asyncio
   ```

## Running Tests

### Using the Test Runner (Recommended)

```bash
# Run all tests
python run_tests.py

# Run only JIRA tests
python run_tests.py jira

# Run only GitHub tests
python run_tests.py github
```

### Using pytest directly

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_jira_client.py -v
pytest tests/test_github_client.py -v

# Run with detailed output
pytest tests/ -v -s
```

## Test Categories

### JIRA Client Tests

- **Configuration & Connection**: Validates JIRA setup and connectivity
- **Projects**: Tests project listing and details
- **Users**: Tests user search and project user listing
- **Issues**: Tests issue search with various filters
- **Recent Activity**: Tests activity tracking functionality
- **Issue Details**: Tests detailed issue information retrieval

### GitHub Client Tests

- **Configuration & Connection**: Validates GitHub setup and connectivity
- **User Information**: Tests user profile and organization data
- **Repositories**: Tests repository listing and detailed information
- **Commits**: Tests commit retrieval with filtering
- **Pull Requests**: Tests PR retrieval and filtering
- **Recent Activity**: Tests activity aggregation
- **Contributors**: Tests repository contributor analysis
- **Issues**: Tests GitHub issue tracking

## Test Output

The tests provide detailed output including:
- Configuration status for both services
- Connection test results
- Sample data from API calls
- Performance metrics (number of items found)
- Validation of data structures

## Troubleshooting

### Common Issues

1. **Configuration Errors**:
   - Ensure `.env` file is in the backend directory
   - Verify all required environment variables are set
   - Check that credentials are valid

2. **Connection Failures**:
   - Verify network connectivity
   - Check firewall settings
   - Ensure API tokens have proper permissions

3. **API Rate Limiting**:
   - Tests are designed to respect rate limits
   - If you encounter rate limiting, wait a few minutes and retry

4. **Empty Results**:
   - Some tests may show empty results if your account has no data
   - This is normal for new accounts or accounts with limited activity

### Getting Help

If tests fail:
1. Check the detailed error messages in the console output
2. Verify your credentials in the respective services
3. Ensure your tokens have the necessary permissions:
   - JIRA: Read access to projects and issues
   - GitHub: `repo` scope for private repositories, `public_repo` for public only

## Test Reports

Tests generate JUnit XML reports:
- `test-results-jira.xml` - JIRA test results
- `test-results-github.xml` - GitHub test results
- `test-results-all.xml` - Combined test results

These can be used for CI/CD integration or detailed analysis.
