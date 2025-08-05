"""Additional pytest configuration"""


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        '--run-external', action='store_true', default=False, help='Run tests that require external network access'
    )


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line('markers', 'external: mark test as requiring external network access')
