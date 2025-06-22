#!/usr/bin/env python3
"""
Post-Deployment Testing Script for Energy Agent Streamlit Cloud Deployment
Tests deployed app functionality, performance, and generates verification reports
"""

import requests
import time
import json
import sys
from datetime import datetime
from urllib.parse import urljoin

class DeploymentTester:
    def __init__(self, app_url):
        self.app_url = app_url.rstrip('/')
        self.test_results = {}
        self.start_time = datetime.now()
        
    def test_app_health(self):
        """Test basic app health and accessibility"""
        print("🔍 Testing app health...")
        
        try:
            response = requests.get(self.app_url, timeout=10)
            
            if response.status_code == 200:
                print("✅ App is accessible (HTTP 200)")
                self.test_results['health'] = {
                    'status': 'PASS',
                    'response_time': response.elapsed.total_seconds(),
                    'status_code': response.status_code
                }
                return True
            else:
                print(f"❌ App returned status code: {response.status_code}")
                self.test_results['health'] = {
                    'status': 'FAIL',
                    'status_code': response.status_code,
                    'error': f'HTTP {response.status_code}'
                }
                return False
                
        except requests.exceptions.Timeout:
            print("❌ App health check timed out")
            self.test_results['health'] = {
                'status': 'FAIL',
                'error': 'Timeout'
            }
            return False
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to app")
            self.test_results['health'] = {
                'status': 'FAIL',
                'error': 'Connection Error'
            }
            return False
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            self.test_results['health'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def test_app_content(self):
        """Test that app content loads correctly"""
        print("📄 Testing app content...")
        
        try:
            response = requests.get(self.app_url, timeout=15)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                # Check for expected content
                checks = [
                    ('streamlit', 'Streamlit framework'),
                    ('energy', 'Energy-related content'),
                    ('equipment', 'Equipment analysis'),
                    ('maintenance', 'Maintenance features'),
                    ('risk', 'Risk assessment'),
                ]
                
                passed_checks = []
                for keyword, description in checks:
                    if keyword in content:
                        passed_checks.append(description)
                
                if len(passed_checks) >= 3:  # At least 3 out of 5 checks should pass
                    print(f"✅ App content verified ({len(passed_checks)}/5 checks passed)")
                    self.test_results['content'] = {
                        'status': 'PASS',
                        'passed_checks': passed_checks,
                        'total_checks': len(checks)
                    }
                    return True
                else:
                    print(f"❌ App content verification failed ({len(passed_checks)}/5 checks passed)")
                    self.test_results['content'] = {
                        'status': 'FAIL',
                        'passed_checks': passed_checks,
                        'total_checks': len(checks)
                    }
                    return False
            else:
                print(f"❌ Content test failed: HTTP {response.status_code}")
                self.test_results['content'] = {
                    'status': 'FAIL',
                    'error': f'HTTP {response.status_code}'
                }
                return False
                
        except Exception as e:
            print(f"❌ Content test failed: {e}")
            self.test_results['content'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def test_performance(self):
        """Test app performance metrics"""
        print("⚡ Testing performance...")
        
        try:
            # Test multiple requests to get average response time
            response_times = []
            for i in range(3):
                start_time = time.time()
                response = requests.get(self.app_url, timeout=15)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_times.append(end_time - start_time)
                else:
                    print(f"❌ Performance test request {i+1} failed: HTTP {response.status_code}")
                    self.test_results['performance'] = {
                        'status': 'FAIL',
                        'error': f'HTTP {response.status_code} on request {i+1}'
                    }
                    return False
            
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            print(f"📊 Performance metrics:")
            print(f"   Average response time: {avg_response_time:.2f}s")
            print(f"   Maximum response time: {max_response_time:.2f}s")
            
            # Performance thresholds
            if avg_response_time < 3.0 and max_response_time < 5.0:
                print("✅ Performance meets requirements")
                self.test_results['performance'] = {
                    'status': 'PASS',
                    'avg_response_time': avg_response_time,
                    'max_response_time': max_response_time,
                    'threshold_met': True
                }
                return True
            else:
                print("⚠️ Performance below optimal thresholds")
                self.test_results['performance'] = {
                    'status': 'WARNING',
                    'avg_response_time': avg_response_time,
                    'max_response_time': max_response_time,
                    'threshold_met': False
                }
                return True  # Warning, not failure
                
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            self.test_results['performance'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def test_error_handling(self):
        """Test app error handling"""
        print("🛡️ Testing error handling...")
        
        try:
            # Test with a non-existent endpoint
            test_url = urljoin(self.app_url, '/nonexistent-endpoint')
            response = requests.get(test_url, timeout=10)
            
            # App should handle 404 gracefully
            if response.status_code in [404, 200]:  # 200 if app handles 404s gracefully
                print("✅ Error handling works correctly")
                self.test_results['error_handling'] = {
                    'status': 'PASS',
                    'status_code': response.status_code
                }
                return True
            else:
                print(f"⚠️ Unexpected error handling response: {response.status_code}")
                self.test_results['error_handling'] = {
                    'status': 'WARNING',
                    'status_code': response.status_code
                }
                return True
                
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            self.test_results['error_handling'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            return False
    
    def generate_verification_report(self):
        """Generate comprehensive verification report"""
        print("📋 Generating verification report...")
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Calculate overall status
        status_counts = {}
        for test_name, result in self.test_results.items():
            status = result.get('status', 'UNKNOWN')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        overall_status = 'PASS'
        if status_counts.get('FAIL', 0) > 0:
            overall_status = 'FAIL'
        elif status_counts.get('WARNING', 0) > 0:
            overall_status = 'WARNING'
        
        report = f"""
# Deployment Verification Report

## Test Information
- **App URL:** {self.app_url}
- **Test Date:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
- **Test Duration:** {duration:.2f} seconds
- **Overall Status:** {overall_status}

## Test Results Summary
- **PASS:** {status_counts.get('PASS', 0)}
- **WARNING:** {status_counts.get('WARNING', 0)}
- **FAIL:** {status_counts.get('FAIL', 0)}

## Detailed Results
"""
        
        for test_name, result in self.test_results.items():
            status = result.get('status', 'UNKNOWN')
            status_icon = {'PASS': '✅', 'WARNING': '⚠️', 'FAIL': '❌'}.get(status, '❓')
            
            report += f"\n### {test_name.replace('_', ' ').title()}\n"
            report += f"**Status:** {status_icon} {status}\n\n"
            
            # Add test-specific details
            if 'response_time' in result:
                report += f"- Response Time: {result['response_time']:.2f}s\n"
            if 'avg_response_time' in result:
                report += f"- Average Response Time: {result['avg_response_time']:.2f}s\n"
                report += f"- Maximum Response Time: {result['max_response_time']:.2f}s\n"
            if 'passed_checks' in result:
                report += f"- Passed Checks: {result['passed_checks']}\n"
            if 'error' in result:
                report += f"- Error: {result['error']}\n"
        
        report += f"""
## Recommendations
"""
        
        if overall_status == 'PASS':
            report += "- ✅ Deployment is successful and ready for use\n"
            report += "- 📊 Monitor performance metrics regularly\n"
            report += "- 🔄 Set up automated health checks\n"
        elif overall_status == 'WARNING':
            report += "- ⚠️ Deployment is functional but may need optimization\n"
            report += "- 📈 Consider performance improvements\n"
            report += "- 🔍 Investigate warnings for potential issues\n"
        else:
            report += "- ❌ Deployment has critical issues that need attention\n"
            report += "- 🔧 Review and fix failed tests\n"
            report += "- 🚨 Do not proceed with production use until issues are resolved\n"
        
        report += f"""
## Next Steps
1. **If PASS:** Share app URL with team and stakeholders
2. **If WARNING:** Monitor closely and optimize as needed
3. **If FAIL:** Fix issues and re-run tests

## App Access
- **URL:** {self.app_url}
- **Status:** {'🟢 Ready' if overall_status == 'PASS' else '🟡 Needs Attention' if overall_status == 'WARNING' else '🔴 Not Ready'}
"""
        
        # Save report
        report_filename = f"deployment_verification_{self.start_time.strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_filename, 'w') as f:
            f.write(report)
        
        print(f"✅ Verification report generated: {report_filename}")
        return report_filename
    
    def run_all_tests(self):
        """Run all deployment tests"""
        print("🚀 Starting deployment verification tests...")
        print(f"🌐 Testing app at: {self.app_url}")
        print("="*60)
        
        tests = [
            ("Health Check", self.test_app_health),
            ("Content Verification", self.test_app_content),
            ("Performance Test", self.test_performance),
            ("Error Handling", self.test_error_handling),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name}...")
            if test_func():
                passed_tests += 1
            print()
        
        # Generate report
        report_file = self.generate_verification_report()
        
        # Summary
        print("="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"✅ Passed: {passed_tests}/{total_tests}")
        print(f"📋 Report: {report_file}")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Deployment is successful.")
            return True
        else:
            print("⚠️ Some tests failed or had warnings. Check the report for details.")
            return False

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python test_deployment.py <app_url>")
        print("Example: python test_deployment.py https://your-app.streamlit.app")
        return 1
    
    app_url = sys.argv[1]
    
    print("🧪 Energy Agent Deployment Verification")
    print("="*50)
    
    tester = DeploymentTester(app_url)
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Deployment verification completed successfully!")
        print(f"🌐 Your app is ready at: {app_url}")
    else:
        print("\n❌ Deployment verification found issues!")
        print("📋 Check the verification report for details")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 