#!/usr/bin/env python3
"""
Test runner script for GitHub and JIRA clients.

This script runs all test cases and provides a comprehensive report of the results.
It checks environment configuration and provides helpful feedback for setup issues.
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def check_environment():
    """Check if required environment variables are set"""
    load_dotenv()
    
    print("🔍 Checking Environment Configuration...")
    print("=" * 50)
    
    # Check JIRA configuration
    jira_server = os.getenv("JIRA_SERVER_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    
    print("JIRA Configuration:")
    print(f"  JIRA_SERVER_URL: {'✓ Set' if jira_server else '✗ Missing'}")
    print(f"  JIRA_EMAIL: {'✓ Set' if jira_email else '✗ Missing'}")
    print(f"  JIRA_API_TOKEN: {'✓ Set' if jira_token else '✗ Missing'}")
    
    jira_configured = bool(jira_server and jira_email and jira_token)
    print(f"  JIRA Overall: {'✓ Configured' if jira_configured else '✗ Not Configured'}")
    
    # Check GitHub configuration
    github_token = os.getenv("GITHUB_TOKEN")
    github_org = os.getenv("GITHUB_ORGANIZATION")
    
    print("\nGitHub Configuration:")
    print(f"  GITHUB_TOKEN: {'✓ Set' if github_token else '✗ Missing'}")
    print(f"  GITHUB_ORGANIZATION: {'✓ Set' if github_org else '○ Optional'} {f'({github_org})' if github_org else ''}")
    
    github_configured = bool(github_token)
    print(f"  GitHub Overall: {'✓ Configured' if github_configured else '✗ Not Configured'}")
    
    print("\n" + "=" * 50)
    
    if not jira_configured and not github_configured:
        print("❌ Neither JIRA nor GitHub is configured!")
        print("\nTo configure, create a .env file with:")
        print("  JIRA_SERVER_URL=https://your-domain.atlassian.net")
        print("  JIRA_EMAIL=your-email@example.com")
        print("  JIRA_API_TOKEN=your-jira-api-token")
        print("  GITHUB_TOKEN=your-github-personal-access-token")
        print("  GITHUB_ORGANIZATION=your-org-name  # Optional")
        return False
    elif not jira_configured:
        print("⚠️  JIRA is not configured - JIRA tests will be skipped")
    elif not github_configured:
        print("⚠️  GitHub is not configured - GitHub tests will be skipped")
    else:
        print("✅ Both JIRA and GitHub are configured!")
    
    return True

def run_specific_tests(test_file, service_name):
    """Run tests for a specific service"""
    print(f"\n🧪 Running {service_name} Tests...")
    print("=" * 50)
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            test_file, 
            "-v", "-s", 
            "--tb=short",
            f"--junit-xml=test-results-{service_name.lower()}.xml"
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print(f"✅ {service_name} tests completed successfully!")
        else:
            print(f"❌ {service_name} tests failed!")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running {service_name} tests: {e}")
        return False

def run_all_tests():
    """Run all test suites"""
    print("\n🚀 Running All Tests...")
    print("=" * 50)
    
    try:
        # Run all tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", "-s", 
            "--tb=short",
            "--junit-xml=test-results-all.xml"
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print("✅ All tests completed successfully!")
        else:
            print("❌ Some tests failed!")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def main():
    """Main test runner function"""
    print("🔬 Team Activity Monitor - Test Suite")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("tests").exists():
        print("❌ Tests directory not found. Please run this script from the backend directory.")
        sys.exit(1)
    
    # Check environment configuration
    if not check_environment():
        print("\n❌ Environment not properly configured. Please check your .env file.")
        sys.exit(1)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == "jira":
            success = run_specific_tests("tests/test_jira_client.py", "JIRA")
        elif test_type == "github":
            success = run_specific_tests("tests/test_github_client.py", "GitHub")
        elif test_type == "all":
            success = run_all_tests()
        else:
            print(f"❌ Unknown test type: {test_type}")
            print("Usage: python run_tests.py [jira|github|all]")
            sys.exit(1)
    else:
        # Run all tests by default
        success = run_all_tests()
    
    # Final summary
    print("\n" + "=" * 50)
    if success:
        print("🎉 Test execution completed successfully!")
        print("\n📊 Test Results:")
        print("  - Check the console output above for detailed results")
        print("  - JUnit XML reports are saved as test-results-*.xml files")
    else:
        print("💥 Test execution completed with failures!")
        print("\n🔧 Troubleshooting:")
        print("  1. Check your .env file configuration")
        print("  2. Verify your JIRA/GitHub credentials")
        print("  3. Check network connectivity")
        print("  4. Review the error messages above")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
