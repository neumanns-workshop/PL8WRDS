#!/usr/bin/env python3
"""
Comprehensive test runner for PL8WRDS application.

This script provides various test running options and configurations
for different testing scenarios.
"""

import argparse
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional


def run_command(cmd: List[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False


def run_unit_tests(verbose: bool = False, coverage: bool = True) -> bool:
    """Run unit tests."""
    cmd = ["python", "-m", "pytest", "-m", "unit"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])
    
    cmd.append("tests/unit/")
    
    return run_command(cmd, "Unit Tests")


def run_integration_tests(verbose: bool = False) -> bool:
    """Run integration tests."""
    cmd = ["python", "-m", "pytest", "-m", "integration"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.append("tests/integration/")
    
    return run_command(cmd, "Integration Tests")


def run_api_tests(verbose: bool = False) -> bool:
    """Run API tests."""
    cmd = ["python", "-m", "pytest", "-m", "api"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.append("tests/api/")
    
    return run_command(cmd, "API Tests")


def run_e2e_tests(verbose: bool = False) -> bool:
    """Run end-to-end tests."""
    cmd = ["python", "-m", "pytest", "-m", "e2e"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.append("tests/e2e/")
    
    return run_command(cmd, "End-to-End Tests")


def run_performance_tests(verbose: bool = False) -> bool:
    """Run performance tests."""
    cmd = ["python", "-m", "pytest", "-m", "performance"]
    
    if verbose:
        cmd.append("-v")
    
    # Performance tests might take longer
    cmd.extend(["--timeout=300"])
    
    cmd.append("tests/performance/")
    
    return run_command(cmd, "Performance Tests")


def run_all_tests(verbose: bool = False, coverage: bool = True, skip_slow: bool = False) -> bool:
    """Run all tests in sequence."""
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing", "--cov-report=html"])
    
    if skip_slow:
        cmd.extend(["-m", "not slow"])
    
    cmd.append("tests/")
    
    return run_command(cmd, "All Tests")


def run_fast_tests(verbose: bool = False) -> bool:
    """Run only fast tests (unit + api)."""
    cmd = ["python", "-m", "pytest", "-m", "unit or api"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend(["--cov=app", "--cov-report=term-missing"])
    cmd.append("tests/")
    
    return run_command(cmd, "Fast Tests (Unit + API)")


def run_linting() -> bool:
    """Run code linting."""
    success = True
    
    # Run flake8 if available
    if subprocess.run(["which", "flake8"], capture_output=True).returncode == 0:
        success &= run_command(
            ["flake8", "app/", "tests/", "--max-line-length=100", "--ignore=E501,W503"],
            "Flake8 Linting"
        )
    
    # Run black check if available
    if subprocess.run(["which", "black"], capture_output=True).returncode == 0:
        success &= run_command(
            ["black", "--check", "--diff", "app/", "tests/"],
            "Black Code Formatting Check"
        )
    
    # Run isort check if available
    if subprocess.run(["which", "isort"], capture_output=True).returncode == 0:
        success &= run_command(
            ["isort", "--check-only", "--diff", "app/", "tests/"],
            "isort Import Sorting Check"
        )
    
    return success


def run_type_checking() -> bool:
    """Run type checking with mypy."""
    if subprocess.run(["which", "mypy"], capture_output=True).returncode == 0:
        return run_command(
            ["mypy", "app/", "--ignore-missing-imports"],
            "MyPy Type Checking"
        )
    else:
        print("⚠️  MyPy not available, skipping type checking")
        return True


def run_security_checks() -> bool:
    """Run security checks."""
    success = True
    
    # Run bandit if available
    if subprocess.run(["which", "bandit"], capture_output=True).returncode == 0:
        success &= run_command(
            ["bandit", "-r", "app/", "-f", "json"],
            "Bandit Security Check"
        )
    
    # Run safety if available
    if subprocess.run(["which", "safety"], capture_output=True).returncode == 0:
        success &= run_command(
            ["safety", "check"],
            "Safety Dependency Check"
        )
    
    return success


def generate_coverage_report() -> bool:
    """Generate HTML coverage report."""
    return run_command(
        ["python", "-m", "pytest", "--cov=app", "--cov-report=html", "tests/"],
        "Coverage Report Generation"
    )


def clean_test_artifacts():
    """Clean test artifacts and cache files."""
    artifacts_to_clean = [
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        "__pycache__",
        "*.pyc",
        ".mypy_cache",
        "test-results.xml"
    ]
    
    print("\n🧹 Cleaning test artifacts...")
    
    for pattern in artifacts_to_clean:
        if pattern.startswith("."):
            # Handle hidden directories and files
            cmd = ["find", ".", "-name", pattern, "-exec", "rm", "-rf", "{}", "+"]
        else:
            # Handle patterns like *.pyc
            cmd = ["find", ".", "-name", pattern, "-delete"]
        
        subprocess.run(cmd, capture_output=True)
    
    print("✅ Test artifacts cleaned")


def setup_test_environment():
    """Set up the test environment."""
    print("🔧 Setting up test environment...")
    
    # Create test directories
    test_dirs = [
        "/tmp/test_pl8wrds",
        "/tmp/test_cache",
    ]
    
    for directory in test_dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Set environment variables for testing
    os.environ["TESTING"] = "1"
    os.environ["LOG_LEVEL"] = "WARNING"
    
    print("✅ Test environment set up")


def main():
    parser = argparse.ArgumentParser(
        description="PL8WRDS Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --all                    # Run all tests
  python run_tests.py --unit --verbose         # Run unit tests with verbose output
  python run_tests.py --fast                   # Run fast tests only
  python run_tests.py --performance            # Run performance tests
  python run_tests.py --lint --type-check      # Run code quality checks
  python run_tests.py --coverage               # Generate coverage report
  python run_tests.py --clean                  # Clean test artifacts
        """
    )
    
    # Test selection options
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--api", action="store_true", help="Run API tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--fast", action="store_true", help="Run fast tests (unit + api)")
    
    # Quality checks
    parser.add_argument("--lint", action="store_true", help="Run linting checks")
    parser.add_argument("--type-check", action="store_true", help="Run type checking")
    parser.add_argument("--security", action="store_true", help="Run security checks")
    
    # Options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--skip-slow", action="store_true", help="Skip slow tests")
    parser.add_argument("--coverage", action="store_true", help="Generate HTML coverage report")
    
    # Utility options
    parser.add_argument("--clean", action="store_true", help="Clean test artifacts")
    parser.add_argument("--setup", action="store_true", help="Set up test environment")
    
    args = parser.parse_args()
    
    # If no specific test type is selected, run all
    if not any([
        args.all, args.unit, args.integration, args.api, args.e2e, 
        args.performance, args.fast, args.lint, args.type_check, 
        args.security, args.coverage, args.clean, args.setup
    ]):
        args.all = True
    
    success = True
    
    # Set up test environment
    if args.setup or args.all:
        setup_test_environment()
    
    # Clean artifacts if requested
    if args.clean:
        clean_test_artifacts()
        return
    
    # Run quality checks
    if args.lint or args.all:
        success &= run_linting()
    
    if args.type_check or args.all:
        success &= run_type_checking()
    
    if args.security:
        success &= run_security_checks()
    
    # Run tests
    coverage = not args.no_coverage
    
    if args.unit:
        success &= run_unit_tests(args.verbose, coverage)
    
    if args.integration:
        success &= run_integration_tests(args.verbose)
    
    if args.api:
        success &= run_api_tests(args.verbose)
    
    if args.e2e:
        success &= run_e2e_tests(args.verbose)
    
    if args.performance:
        success &= run_performance_tests(args.verbose)
    
    if args.fast:
        success &= run_fast_tests(args.verbose)
    
    if args.all:
        success &= run_all_tests(args.verbose, coverage, args.skip_slow)
    
    if args.coverage:
        success &= generate_coverage_report()
    
    # Final summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()