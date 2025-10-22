# MedCare HMS Test Runner
# Quick test execution script

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and print results"""
    print(f"\n{'='*70}")
    print(f"  {description}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=False)
    
    if result.returncode == 0:
        print(f"\n✅ {description} - PASSED")
    else:
        print(f"\n❌ {description} - FAILED")
        return False
    return True

def main():
    """Main test runner"""
    os.chdir('medcare_hms')
    
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║              MedCare HMS - Automated Test Suite              ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Test suites to run
    test_suites = [
        {
            'cmd': 'python manage.py test chat.tests.ChatModelTest --verbosity=2',
            'desc': 'Chat Module - Model Tests'
        },
        {
            'cmd': 'python manage.py test chat.tests.ChatViewsTest --verbosity=2',
            'desc': 'Chat Module - View Tests'
        },
        {
            'cmd': 'python manage.py test notifications.tests --verbosity=2',
            'desc': 'Notifications Module - All Tests'
        },
        {
            'cmd': 'python manage.py test billing.tests --verbosity=2',
            'desc': 'Billing Module - All Tests'
        },
        {
            'cmd': 'python manage.py test accounts.tests --verbosity=2',
            'desc': 'Accounts Module - All Tests'
        },
        {
            'cmd': 'python manage.py test patients.tests --verbosity=2',
            'desc': 'Patients Module - All Tests'
        },
    ]
    
    results = []
    
    # Run each test suite
    for suite in test_suites:
        passed = run_command(suite['cmd'], suite['desc'])
        results.append({
            'name': suite['desc'],
            'passed': passed
        })
    
    # Summary
    print(f"\n\n{'='*70}")
    print("                        TEST SUMMARY")
    print(f"{'='*70}\n")
    
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    
    for result in results:
        status = "✅ PASSED" if result['passed'] else "❌ FAILED"
        print(f"  {status:15} - {result['name']}")
    
    print(f"\n{'='*70}")
    print(f"  Total: {passed_count}/{total_count} test suites passed")
    print(f"{'='*70}\n")
    
    if passed_count == total_count:
        print("  🎉 All tests passed! Great job!")
        return 0
    else:
        print("  ⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
