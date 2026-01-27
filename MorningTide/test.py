"""
MorningTide Comprehensive Test Runner

A single Python file that handles all testing requirements: 
- Unit tests
- Integration tests
- Coverage analysis
- Performance metrics
- Linting checks
- Manual testing simulation

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Unit tests only
    python run_tests.py --integration      # Integration tests only
    python run_tests.py --coverage         # With coverage report
    python run_tests.py --performance      # Performance analysis
    python run_tests. py --full             # Everything
    python run_tests.py --lint             # Linting only
    python run_tests.py --manual           # Manual API tests
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple
import argparse
from datetime import datetime
from enum import Enum


# ==================== Setup Python Path ====================

def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).parent.absolute()


def setup_environment() -> Dict[str, str]:
    """Setup environment variables for testing"""
    project_root = get_project_root()
    
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    env['TESTING'] = 'True'
    env['FLASK_ENV'] = 'testing'
    
    return env


PROJECT_ROOT = get_project_root()
TEST_ENV = setup_environment()


# ==================== ANSI Color Codes ====================

class Colors(Enum):
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[0;37m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


# ==================== Utility Functions ====================

def print_header(text: str, char: str = "=") -> None:
    """Print a formatted header"""
    width = 80
    print(f"{Colors.CYAN. value}{Colors.BOLD.value}{char * width}{Colors.END.value}")
    print(f"{Colors. CYAN.value}{Colors.BOLD.value}{text. center(width)}{Colors.END.value}")
    print(f"{Colors.CYAN.value}{Colors.BOLD.value}{char * width}{Colors.END. value}\n")


def print_success(text: str) -> None:
    """Print success message"""
    print(f"{Colors.GREEN. value}✓ {text}{Colors. END.value}")


def print_error(text: str) -> None:
    """Print error message"""
    print(f"{Colors.RED.value}✗ {text}{Colors.END.value}")


def print_warning(text: str) -> None:
    """Print warning message"""
    print(f"{Colors.YELLOW.value}⚠ {text}{Colors.END.value}")


def print_info(text: str) -> None:
    """Print info message"""
    print(f"{Colors. BLUE.value}ℹ {text}{Colors.END.value}")


def print_section(text: str) -> None:
    """Print section header"""
    print(f"\n{Colors.MAGENTA.value}{Colors.BOLD.value}>>> {text}{Colors.END.value}\n")


def run_command(
    cmd: List[str],
    description: str = "",
    capture_output: bool = False,
    verbose: bool = True,
    cwd: Path = None
) -> Tuple[int, str, str]:
    """
    Run a command and return exit code, stdout, stderr
    
    Args:
        cmd: Command to run as list
        description: Description of what the command does
        capture_output: Whether to capture output
        verbose: Whether to print output
        cwd: Working directory for command
        
    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    if description and verbose:
        print_info(description)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=True,
            timeout=300,
            env=TEST_ENV,
            cwd=str(cwd or PROJECT_ROOT)
        )
        
        if result.returncode == 0 and verbose and description:
            print_success(f"{description} passed")
        elif result.returncode != 0 and verbose and description:
            print_error(f"{description} failed")
        
        return result.returncode, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        if verbose:
            print_error(f"{description} timed out")
        return 1, "", "Timeout"
    except Exception as e:
        if verbose:
            print_error(f"Error running command: {e}")
        return 1, "", str(e)


# ==================== Test Runners ====================

class TestRunner:
    """Orchestrate all testing tasks"""
    
    def __init__(self, project_root: Path = None, verbose: bool = True):
        """Initialize test runner"""
        self. project_root = project_root or PROJECT_ROOT
        self.verbose = verbose
        self.results:  Dict[str, Dict] = {}
        self.start_time = time.time()
        
        print_info(f"Project root: {self.project_root}")
        print_info(f"PYTHONPATH: {TEST_ENV. get('PYTHONPATH')}")
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are installed"""
        print_section("Checking Prerequisites")
        
        prerequisites = {
            'pytest': 'pytest',
            'pytest-cov': 'pytest coverage',
            'pytest-mock': 'pytest mocking',
            'black': 'code formatter',
            'flake8': 'linter',
        }
        
        all_good = True
        for package, name in prerequisites.items():
            exit_code, _, _ = run_command(
                ['python', '-m', 'pip', 'show', package],
                f"Checking {name}",
                capture_output=True,
                verbose=self.verbose
            )
            
            if exit_code != 0:
                print_error(f"{name} ({package}) not installed")
                all_good = False
            else:
                print_success(f"{name} is installed")
        
        if not all_good:
            print_warning("Some prerequisites missing. Install with:")
            print(f"  pip install -r requirements-dev.txt")
            return False
        
        return True
    
    def check_app_structure(self) -> bool:
        """Check if app structure exists"""
        print_section("Checking Application Structure")
        
        required_paths = [
            'app/__init__.py',
            'app/config.py',
            'app/main.py',
            'app/api/rag.py',
            'app/ml/rag/runner.py',
            'tests/conftest.py',
            'tests/test_rag_unit.py',
            'tests/test_rag_integration.py',
        ]
        
        all_good = True
        for path in required_paths:
            full_path = self.project_root / path
            if full_path.exists():
                print_success(f"Found {path}")
            else:
                print_warning(f"Not found: {path}")
        
        # Check that app module can be imported
        print_info("Checking if app module can be imported...")
        exit_code, stdout, stderr = run_command(
            ['python', '-c', 'import app; print("App imported successfully")'],
            "Import app module",
            capture_output=True,
            verbose=False
        )
        
        if exit_code == 0:
            print_success("App module can be imported")
            return True
        else:
            print_error("Cannot import app module")
            print_error(f"Error: {stderr}")
            return False
    
    def run_unit_tests(self) -> bool:
        """Run unit tests"""
        print_section("Running Unit Tests")
        
        cmd = [
            'python', '-m', 'pytest',
            'tests/test_rag_unit. py',
            '-v',
            '--tb=short',
            '--color=yes',
            '-p', 'no:cacheprovider'  # Disable cache
        ]
        
        exit_code, stdout, stderr = run_command(
            cmd,
            "Unit tests",
            capture_output=True,
            verbose=self. verbose,
            cwd=self.project_root
        )
        
        self.results['unit_tests'] = {
            'passed': exit_code == 0,
            'exit_code': exit_code,
            'output': stdout
        }
        
        if exit_code == 0:
            print_success("All unit tests passed")
            # Count tests
            for line in stdout.split('\n'):
                if 'passed' in line. lower():
                    print_info(line. strip())
        else:
            print_error("Some unit tests failed")
            if self.verbose:
                print("\n--- Test Output ---")
                print(stdout)
                if stderr:
                    print("\n--- Errors ---")
                    print(stderr)
        
        return exit_code == 0
    
    def run_integration_tests(self) -> bool:
        """Run integration tests"""
        print_section("Running Integration Tests")
        
        cmd = [
            'python', '-m', 'pytest',
            'tests/test_rag_integration.py',
            '-v',
            '--tb=short',
            '--color=yes',
            '-p', 'no:cacheprovider'
        ]
        
        exit_code, stdout, stderr = run_command(
            cmd,
            "Integration tests",
            capture_output=True,
            verbose=self.verbose,
            cwd=self.project_root
        )
        
        self.results['integration_tests'] = {
            'passed': exit_code == 0,
            'exit_code': exit_code,
            'output': stdout
        }
        
        if exit_code == 0:
            print_success("All integration tests passed")
            for line in stdout.split('\n'):
                if 'passed' in line.lower():
                    print_info(line.strip())
        else:
            print_error("Some integration tests failed")
            if self.verbose:
                print("\n--- Test Output ---")
                print(stdout)
                if stderr:
                    print("\n--- Errors ---")
                    print(stderr)
        
        return exit_code == 0
    
    def run_all_tests(self) -> bool:
        """Run all tests"""
        print_section("Running All Tests")
        
        cmd = [
            'python', '-m', 'pytest',
            'tests/',
            '-v',
            '--tb=short',
            '--color=yes',
            '-p', 'no:cacheprovider'
        ]
        
        exit_code, stdout, stderr = run_command(
            cmd,
            "All tests",
            capture_output=True,
            verbose=self.verbose,
            cwd=self. project_root
        )
        
        self.results['all_tests'] = {
            'passed': exit_code == 0,
            'exit_code': exit_code,
            'output':  stdout
        }
        
        if exit_code == 0:
            print_success("All tests passed!")
            for line in stdout.split('\n'):
                if 'passed' in line.lower():
                    print_info(line.strip())
        else:
            print_error("Some tests failed")
            if self.verbose:
                print("\n--- Test Output (first 3000 chars) ---")
                print(stdout[:3000])
        
        return exit_code == 0
    
    def run_coverage(self) -> bool:
        """Run tests with coverage analysis"""
        print_section("Running Coverage Analysis")
        
        cmd = [
            'python', '-m', 'pytest',
            'tests/',
            '--cov=app',
            '--cov-report=html',
            '--cov-report=term-missing',
            '-v',
            '--tb=short',
            '-p', 'no:cacheprovider'
        ]
        
        exit_code, stdout, stderr = run_command(
            cmd,
            "Coverage analysis",
            capture_output=True,
            verbose=self.verbose,
            cwd=self.project_root
        )
        
        self.results['coverage'] = {
            'passed': exit_code == 0,
            'exit_code': exit_code,
            'output': stdout,
            'report_location': 'htmlcov/index.html'
        }
        
        if exit_code == 0:
            print_success("Coverage report generated")
            report_path = self.project_root / 'htmlcov' / 'index.html'
            if report_path.exists():
                print_info(f"View report:  {report_path}")
            
            # Extract coverage percentage
            for line in stdout.split('\n'):
                if 'TOTAL' in line:
                    print_info(f"Coverage: {line.strip()}")
        else:
            print_error("Coverage analysis failed")
            if self.verbose:
                print("\n--- Output ---")
                print(stdout[: 2000])
        
        return exit_code == 0
    
    def run_performance_analysis(self) -> bool:
        """Run performance analysis"""
        print_section("Running Performance Analysis")
        
        cmd = [
            'python', '-m', 'pytest',
            'tests/',
            '--durations=10',
            '-v',
            '--tb=short',
            '-p', 'no:cacheprovider'
        ]
        
        exit_code, stdout, stderr = run_command(
            cmd,
            "Performance analysis",
            capture_output=True,
            verbose=self.verbose,
            cwd=self.project_root
        )
        
        self.results['performance'] = {
            'passed': exit_code == 0,
            'exit_code':  exit_code,
            'output': stdout
        }
        
        if exit_code == 0:
            print_success("Performance analysis complete")
            # Print slowest tests
            lines = stdout.split('\n')
            printing = False
            for line in lines:
                if 'slowest' in line.lower() or 'durations' in line.lower():
                    printing = True
                if printing and line.strip():
                    print_info(line.strip())
        else:
            print_error("Performance analysis failed")
        
        return exit_code == 0
    
    def run_linting(self) -> bool:
        """Run code linting checks"""
        print_section("Running Linting Checks")
        
        all_passed = True
        
        # Check with Black
        print_info("Checking code formatting with Black...")
        cmd = ['python', '-m', 'black', '--check', 'app/', 'tests/']
        exit_code, stdout, stderr = run_command(
            cmd,
            "Black check",
            capture_output=True,
            verbose=False,
            cwd=self. project_root
        )
        
        if exit_code == 0:
            print_success("Black formatting check passed")
            self.results['black'] = {'passed': True}
        else:
            print_warning("Black formatting issues found.  Run:  black app/ tests/")
            self.results['black'] = {'passed':  False}
            all_passed = False
        
        # Check with Flake8
        print_info("Checking code style with Flake8...")
        cmd = ['python', '-m', 'flake8', 'app/', 'tests/', '--max-line-length=100', '--ignore=E501,W503']
        exit_code, stdout, stderr = run_command(
            cmd,
            "Flake8 check",
            capture_output=True,
            verbose=False,
            cwd=self.project_root
        )
        
        if exit_code == 0:
            print_success("Flake8 style check passed")
            self.results['flake8'] = {'passed': True}
        else: 
            print_warning("Flake8 issues found")
            self.results['flake8'] = {'passed': False}
            if stdout:
                print(stdout[: 1000])
            all_passed = False
        
        return all_passed
    
    def run_manual_api_tests(self) -> bool:
        """Simulate manual API testing with curl"""
        print_section("Running Manual API Tests")
        
        base_url = "http://localhost:8000"
        
        # Check if server is running
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_running = sock.connect_ex(('localhost', 8000)) == 0
        sock.close()
        
        if not server_running:
            print_warning("Flask server not running on http://localhost:8000")
            print_info("Start server with: python -m flask run")
            return False
        
        print_success("Flask server is running")
        
        tests = [
            {
                'name': 'Root Endpoint',
                'method': 'GET',
                'url': f'{base_url}/',
                'data': None
            },
            {
                'name': 'Health Check',
                'method': 'GET',
                'url': f'{base_url}/health',
                'data': None
            },
            {
                'name':  'RAG Health',
                'method': 'GET',
                'url': f'{base_url}/api/rag/health',
                'data': None
            },
            {
                'name': 'Index Stats',
                'method': 'GET',
                'url': f'{base_url}/api/rag/index-stats',
                'data':  None
            },
        ]
        
        all_passed = True
        for test in tests:
            cmd = ['curl', '-s', '-X', test['method'], test['url']]
            
            exit_code, stdout, stderr = run_command(
                cmd,
                f"Testing {test['name']}",
                capture_output=True,
                verbose=False,
                cwd=self.project_root
            )
            
            try:
                response = json.loads(stdout)
                print_success(f"{test['name']}: OK")
            except (json.JSONDecodeError, ValueError):
                print_error(f"{test['name']}: Invalid response")
                all_passed = False
        
        return all_passed
    
    def run_specific_test(self, test_path: str) -> bool:
        """Run a specific test"""
        print_section(f"Running {test_path}")
        
        cmd = [
            'python', '-m', 'pytest',
            test_path,
            '-v',
            '--tb=short',
            '-p', 'no: cacheprovider'
        ]
        
        exit_code, stdout, stderr = run_command(
            cmd,
            f"Test:  {test_path}",
            capture_output=True,
            verbose=self.verbose,
            cwd=self.project_root
        )
        
        if exit_code == 0:
            print_success(f"{test_path} passed")
        else:
            print_error(f"{test_path} failed")
            if self.verbose:
                print("\n--- Output ---")
                print(stdout)
        
        return exit_code == 0
    
    def generate_report(self) -> None:
        """Generate comprehensive test report"""
        print_section("Test Report")
        
        elapsed_time = time.time() - self.start_time
        
        print(f"\n{Colors.BOLD. value}Test Execution Report{Colors.END.value}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {elapsed_time:.2f} seconds\n")
        
        # Results summary
        print(f"{Colors.BOLD.value}Results Summary:{Colors.END.value}")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self. results.values() if r.get('passed', False))
        
        for test_name, result in self. results.items():
            status = "PASS" if result. get('passed') else "FAIL"
            symbol = "✓" if result. get('passed') else "✗"
            color = Colors.GREEN.value if result.get('passed') else Colors.RED.value
            
            print(f"{color}{symbol} {test_name}:  {status}{Colors.END.value}")
        
        # Overall result
        if total_tests > 0:
            print(f"\n{Colors.BOLD.value}Overall:  {passed_tests}/{total_tests} passed{Colors.END.value}")
            
            if passed_tests == total_tests:
                print(f"{Colors.GREEN.value}{Colors.BOLD.value}✓ All tests passed!{Colors.END.value}")
            else:
                print(f"{Colors.RED.value}{Colors.BOLD.value}✗ Some tests failed{Colors.END.value}")
    
    def run_full_suite(self) -> bool:
        """Run complete test suite"""
        print_header("MorningTide RAG - Full Test Suite")
        
        if not self.check_prerequisites():
            return False
        
        if not self.check_app_structure():
            return False
        
        # Run tests
        unit_passed = self.run_unit_tests()
        integration_passed = self.run_integration_tests()
        
        # Run analysis
        coverage_passed = self.run_coverage()
        perf_passed = self.run_performance_analysis()
        lint_passed = self.run_linting()
        
        # Try manual tests if server is running
        manual_passed = self.run_manual_api_tests()
        
        # Generate report
        self.generate_report()
        
        # Return overall result
        return all([unit_passed, integration_passed, coverage_passed])


# ==================== CLI Interface ====================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='MorningTide Comprehensive Test Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --unit              Run unit tests only
  python run_tests.py --full              Run all tests with coverage
  python run_tests. py --coverage          Run with coverage report
  python run_tests.py --test tests/test_rag_unit.py:: TestGenerateSuggestions
        """
    )
    
    parser.add_argument(
        '--unit',
        action='store_true',
        help='Run unit tests only'
    )
    parser.add_argument(
        '--integration',
        action='store_true',
        help='Run integration tests only'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all tests'
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run tests with coverage analysis'
    )
    parser.add_argument(
        '--performance',
        action='store_true',
        help='Run performance analysis'
    )
    parser.add_argument(
        '--lint',
        action='store_true',
        help='Run linting checks only'
    )
    parser.add_argument(
        '--manual',
        action='store_true',
        help='Run manual API tests'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run complete test suite (everything)'
    )
    parser.add_argument(
        '--test',
        type=str,
        help='Run specific test'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output'
    )
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not any(vars(args).values()):
        parser.print_help()
        print("\n" + "="*80)
        print("Running full test suite by default.. .\n")
        args. full = True
    
    # Create test runner
    runner = TestRunner(verbose=not args.quiet)
    
    # Run requested tests
    success = True
    
    if args.unit:
        success = runner.run_unit_tests() and success
    
    if args.integration:
        success = runner.run_integration_tests() and success
    
    if args. all:
        success = runner.run_all_tests() and success
    
    if args.coverage:
        success = runner.run_coverage() and success
    
    if args.performance:
        success = runner.run_performance_analysis() and success
    
    if args. lint:
        success = runner. run_linting() and success
    
    if args.manual:
        success = runner.run_manual_api_tests() and success
    
    if args.test:
        success = runner.run_specific_test(args.test) and success
    
    if args.full:
        success = runner.run_full_suite() and success
    
    # Generate report
    runner.generate_report()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()