"""Integration test for LookupSubjects ("who can view this document?"). Part 4c.

Requires live SpiceDB + setup_environment. No LLM needed.
"""
import pytest
from examples.who_can_view import who_can_view


@pytest.mark.integration
def test_who_can_view_cross_department_doc():
    # hr-policy-001 is viewable by the hr department (hr_manager) and, via the
    # cross-department share, the finance department (finance_manager).
    assert set(who_can_view("hr-policy-001")) == {"hr_manager", "finance_manager"}


@pytest.mark.integration
def test_who_can_view_excludes_unprivileged():
    assert "bob" not in set(who_can_view("hr-policy-001"))  # sales has no path
