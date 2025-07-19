#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Tour Operator Application
Tests all validation, CRUD operations, and analytics endpoints
"""

import requests
import json
import uuid
import re
from datetime import datetime, date
import sys

# Get backend URL from environment
BACKEND_URL = "https://e6980f67-3251-4aaa-8ed4-7d7bd8002fa8.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.test_results = {
            "validation_tests": {},
            "tour_crud_tests": {},
            "customer_crud_tests": {},
            "dashboard_tests": {},
            "sample_data_tests": {},
            "overall_status": "UNKNOWN"
        }
        self.created_tour_id = None
        self.created_customer_id = None
        
    def log_test(self, category, test_name, status, message="", data=None):
        """Log test results"""
        self.test_results[category][test_name] = {
            "status": status,
            "message": message,
            "data": data
        }
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_symbol} {category.upper()}: {test_name} - {message}")
        
    def make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {"Content-Type": "application/json"}
            
            if method == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed for {method} {endpoint}: {str(e)}")
            return None

    def test_aadhaar_validation(self):
        """Test Aadhaar validation with Verhoeff algorithm"""
        print("\n🔍 Testing Aadhaar Validation with Verhoeff Algorithm...")
        
        # Test cases for Aadhaar validation
        test_cases = [
            # Valid Aadhaar numbers (these should pass Verhoeff checksum)
            {"number": "234123412346", "expected": True, "description": "Valid Aadhaar with correct checksum"},
            {"number": "123456789012", "expected": False, "description": "Invalid checksum"},
            
            # Invalid formats
            {"number": "12345678901", "expected": False, "description": "Too short (11 digits)"},
            {"number": "1234567890123", "expected": False, "description": "Too long (13 digits)"},
            {"number": "12345678901a", "expected": False, "description": "Contains non-digit"},
            {"number": "000000000000", "expected": False, "description": "All zeros"},
            {"number": "111111111111", "expected": False, "description": "All same digits"},
            {"number": "", "expected": False, "description": "Empty string"},
            {"number": None, "expected": False, "description": "None value"},
        ]
        
        passed = 0
        total = len(test_cases)
        
        for case in test_cases:
            data = {"aadhaar_number": case["number"]} if case["number"] is not None else {}
            response = self.make_request("POST", "/validate/aadhaar", data)
            
            if response and response.status_code == 200:
                result = response.json()
                is_valid = result.get("valid", False)
                
                if is_valid == case["expected"]:
                    self.log_test("validation_tests", f"aadhaar_{case['description']}", "PASS", 
                                f"Correctly validated {case['number']} as {is_valid}")
                    passed += 1
                else:
                    self.log_test("validation_tests", f"aadhaar_{case['description']}", "FAIL", 
                                f"Expected {case['expected']}, got {is_valid} for {case['number']}")
            else:
                self.log_test("validation_tests", f"aadhaar_{case['description']}", "FAIL", 
                            f"API request failed for {case['number']}")
        
        overall_status = "PASS" if passed == total else "FAIL"
        self.log_test("validation_tests", "aadhaar_overall", overall_status, 
                     f"Passed {passed}/{total} Aadhaar validation tests")

    def test_pan_validation(self):
        """Test PAN validation"""
        print("\n🔍 Testing PAN Validation...")
        
        test_cases = [
            {"number": "ABCDE1234F", "expected": True, "description": "Valid PAN format"},
            {"number": "ABCDE1234f", "expected": True, "description": "Valid PAN with lowercase (should be converted)"},
            {"number": "ABCD1234F", "expected": False, "description": "Too short"},
            {"number": "ABCDE12345", "expected": False, "description": "No letter at end"},
            {"number": "12345ABCDE", "expected": False, "description": "Wrong format"},
            {"number": "", "expected": False, "description": "Empty string"},
        ]
        
        passed = 0
        total = len(test_cases)
        
        for case in test_cases:
            data = {"pan_number": case["number"]}
            response = self.make_request("POST", "/validate/pan", data)
            
            if response and response.status_code == 200:
                result = response.json()
                is_valid = result.get("valid", False)
                
                if is_valid == case["expected"]:
                    self.log_test("validation_tests", f"pan_{case['description']}", "PASS", 
                                f"Correctly validated {case['number']} as {is_valid}")
                    passed += 1
                else:
                    self.log_test("validation_tests", f"pan_{case['description']}", "FAIL", 
                                f"Expected {case['expected']}, got {is_valid} for {case['number']}")
            else:
                self.log_test("validation_tests", f"pan_{case['description']}", "FAIL", 
                            f"API request failed for {case['number']}")
        
        overall_status = "PASS" if passed == total else "FAIL"
        self.log_test("validation_tests", "pan_overall", overall_status, 
                     f"Passed {passed}/{total} PAN validation tests")

    def test_mobile_validation(self):
        """Test mobile number validation"""
        print("\n🔍 Testing Mobile Number Validation...")
        
        test_cases = [
            {"number": "9876543210", "expected": True, "description": "Valid 10-digit mobile"},
            {"number": "8765432109", "expected": True, "description": "Valid mobile starting with 8"},
            {"number": "7654321098", "expected": True, "description": "Valid mobile starting with 7"},
            {"number": "6543210987", "expected": True, "description": "Valid mobile starting with 6"},
            {"number": "919876543210", "expected": True, "description": "Valid with country code 91"},
            {"number": "+919876543210", "expected": True, "description": "Valid with +91 prefix"},
            {"number": "5432109876", "expected": False, "description": "Invalid starting digit 5"},
            {"number": "98765432", "expected": False, "description": "Too short"},
            {"number": "98765432109", "expected": False, "description": "Too long without country code"},
            {"number": "", "expected": False, "description": "Empty string"},
        ]
        
        passed = 0
        total = len(test_cases)
        
        for case in test_cases:
            data = {"mobile": case["number"]}
            response = self.make_request("POST", "/validate/mobile", data)
            
            if response and response.status_code == 200:
                result = response.json()
                is_valid = result.get("valid", False)
                
                if is_valid == case["expected"]:
                    self.log_test("validation_tests", f"mobile_{case['description']}", "PASS", 
                                f"Correctly validated {case['number']} as {is_valid}")
                    passed += 1
                else:
                    self.log_test("validation_tests", f"mobile_{case['description']}", "FAIL", 
                                f"Expected {case['expected']}, got {is_valid} for {case['number']}")
            else:
                self.log_test("validation_tests", f"mobile_{case['description']}", "FAIL", 
                            f"API request failed for {case['number']}")
        
        overall_status = "PASS" if passed == total else "FAIL"
        self.log_test("validation_tests", "mobile_overall", overall_status, 
                     f"Passed {passed}/{total} mobile validation tests")

    def test_email_validation(self):
        """Test email validation"""
        print("\n🔍 Testing Email Validation...")
        
        test_cases = [
            {"email": "test@example.com", "expected": True, "description": "Valid email"},
            {"email": "user.name@domain.co.in", "expected": True, "description": "Valid email with dots"},
            {"email": "user+tag@example.org", "expected": True, "description": "Valid email with plus"},
            {"email": "invalid.email", "expected": False, "description": "Missing @ symbol"},
            {"email": "@example.com", "expected": False, "description": "Missing local part"},
            {"email": "test@", "expected": False, "description": "Missing domain"},
            {"email": "", "expected": False, "description": "Empty string"},
        ]
        
        passed = 0
        total = len(test_cases)
        
        for case in test_cases:
            data = {"email": case["email"]}
            response = self.make_request("POST", "/validate/email", data)
            
            if response and response.status_code == 200:
                result = response.json()
                is_valid = result.get("valid", False)
                
                if is_valid == case["expected"]:
                    self.log_test("validation_tests", f"email_{case['description']}", "PASS", 
                                f"Correctly validated {case['email']} as {is_valid}")
                    passed += 1
                else:
                    self.log_test("validation_tests", f"email_{case['description']}", "FAIL", 
                                f"Expected {case['expected']}, got {is_valid} for {case['email']}")
            else:
                self.log_test("validation_tests", f"email_{case['description']}", "FAIL", 
                            f"API request failed for {case['email']}")
        
        overall_status = "PASS" if passed == total else "FAIL"
        self.log_test("validation_tests", "email_overall", overall_status, 
                     f"Passed {passed}/{total} email validation tests")

    def test_sample_data_initialization(self):
        """Test that sample tours are created on startup"""
        print("\n🔍 Testing Sample Data Initialization...")
        
        response = self.make_request("GET", "/tours")
        
        if response and response.status_code == 200:
            tours = response.json()
            
            if len(tours) >= 2:
                # Check for Bhutan and Sri Lanka tours
                bhutan_tour = any("Bhutan" in tour.get("name", "") or "Bhutan" in tour.get("destination", "") for tour in tours)
                sri_lanka_tour = any("Sri Lanka" in tour.get("name", "") or "Sri Lanka" in tour.get("destination", "") for tour in tours)
                
                if bhutan_tour and sri_lanka_tour:
                    self.log_test("sample_data_tests", "sample_tours", "PASS", 
                                f"Found {len(tours)} tours including Bhutan and Sri Lanka tours")
                    
                    # Verify UUID format
                    uuid_valid = all(self.is_valid_uuid(tour.get("tour_id", "")) for tour in tours)
                    if uuid_valid:
                        self.log_test("sample_data_tests", "tour_uuid_format", "PASS", 
                                    "All tours have valid UUID format")
                    else:
                        self.log_test("sample_data_tests", "tour_uuid_format", "FAIL", 
                                    "Some tours have invalid UUID format")
                else:
                    self.log_test("sample_data_tests", "sample_tours", "FAIL", 
                                "Missing expected Bhutan or Sri Lanka tours")
            else:
                self.log_test("sample_data_tests", "sample_tours", "FAIL", 
                            f"Expected at least 2 sample tours, found {len(tours)}")
        else:
            self.log_test("sample_data_tests", "sample_tours", "FAIL", 
                        "Failed to retrieve tours")

    def test_tour_crud_operations(self):
        """Test Tour CRUD operations"""
        print("\n🔍 Testing Tour CRUD Operations...")
        
        # Test CREATE
        tour_data = {
            "name": "Test Adventure Tour",
            "destination": "Test Destination, India",
            "start_date": "2025-06-01",
            "end_date": "2025-06-07",
            "price": 45000.0,
            "transport_mode": "AC Bus",
            "description": "A test tour for API validation",
            "max_capacity": 20,
            "image_url": "https://example.com/test-image.jpg"
        }
        
        response = self.make_request("POST", "/tours", tour_data)
        
        if response and response.status_code == 200:
            created_tour = response.json()
            self.created_tour_id = created_tour.get("tour_id")
            
            if self.is_valid_uuid(self.created_tour_id):
                self.log_test("tour_crud_tests", "create_tour", "PASS", 
                            f"Successfully created tour with UUID: {self.created_tour_id}")
            else:
                self.log_test("tour_crud_tests", "create_tour", "FAIL", 
                            f"Created tour has invalid UUID: {self.created_tour_id}")
        else:
            self.log_test("tour_crud_tests", "create_tour", "FAIL", 
                        "Failed to create tour")
            return
        
        # Test READ (individual)
        response = self.make_request("GET", f"/tours/{self.created_tour_id}")
        
        if response and response.status_code == 200:
            tour = response.json()
            if tour.get("name") == tour_data["name"]:
                self.log_test("tour_crud_tests", "read_tour", "PASS", 
                            "Successfully retrieved individual tour")
            else:
                self.log_test("tour_crud_tests", "read_tour", "FAIL", 
                            "Retrieved tour data doesn't match")
        else:
            self.log_test("tour_crud_tests", "read_tour", "FAIL", 
                        "Failed to retrieve individual tour")
        
        # Test UPDATE
        update_data = tour_data.copy()
        update_data["name"] = "Updated Test Adventure Tour"
        update_data["price"] = 50000.0
        
        response = self.make_request("PUT", f"/tours/{self.created_tour_id}", update_data)
        
        if response and response.status_code == 200:
            updated_tour = response.json()
            if updated_tour.get("name") == "Updated Test Adventure Tour" and updated_tour.get("price") == 50000.0:
                self.log_test("tour_crud_tests", "update_tour", "PASS", 
                            "Successfully updated tour")
            else:
                self.log_test("tour_crud_tests", "update_tour", "FAIL", 
                            "Tour update didn't reflect changes")
        else:
            self.log_test("tour_crud_tests", "update_tour", "FAIL", 
                        "Failed to update tour")
        
        # Test READ ALL
        response = self.make_request("GET", "/tours")
        
        if response and response.status_code == 200:
            tours = response.json()
            test_tour_found = any(tour.get("tour_id") == self.created_tour_id for tour in tours)
            
            if test_tour_found:
                self.log_test("tour_crud_tests", "read_all_tours", "PASS", 
                            f"Successfully retrieved all tours ({len(tours)} total)")
            else:
                self.log_test("tour_crud_tests", "read_all_tours", "FAIL", 
                            "Created tour not found in all tours list")
        else:
            self.log_test("tour_crud_tests", "read_all_tours", "FAIL", 
                        "Failed to retrieve all tours")

    def test_customer_crud_operations(self):
        """Test Customer CRUD operations"""
        print("\n🔍 Testing Customer CRUD Operations...")
        
        if not self.created_tour_id:
            self.log_test("customer_crud_tests", "prerequisite", "FAIL", 
                        "No tour available for customer testing")
            return
        
        # Test CREATE with valid data
        customer_data = {
            "tour_id": self.created_tour_id,
            "first_name": "Rajesh",
            "last_name": "Sharma",
            "date_of_birth": "1985-03-15",
            "gender": "Male",
            "email": "rajesh.sharma@example.com",
            "mobile": "9876543210",
            "address": "123 MG Road",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "aadhaar_number": "234123412346",  # Valid Aadhaar with correct checksum
            "pan_number": "ABCDE1234F",
            "emergency_contact_name": "Priya Sharma",
            "emergency_contact_number": "9876543211",
            "special_requirements": "Vegetarian meals",
            "payment_method": "Credit Card"
        }
        
        response = self.make_request("POST", "/customers", customer_data)
        
        if response and response.status_code == 200:
            created_customer = response.json()
            self.created_customer_id = created_customer.get("customer_id")
            
            if self.is_valid_uuid(self.created_customer_id):
                self.log_test("customer_crud_tests", "create_customer", "PASS", 
                            f"Successfully created customer with UUID: {self.created_customer_id}")
            else:
                self.log_test("customer_crud_tests", "create_customer", "FAIL", 
                            f"Created customer has invalid UUID: {self.created_customer_id}")
        else:
            error_msg = response.json() if response else "No response"
            self.log_test("customer_crud_tests", "create_customer", "FAIL", 
                        f"Failed to create customer: {error_msg}")
            return
        
        # Test CREATE with invalid Aadhaar (should fail)
        invalid_customer_data = customer_data.copy()
        invalid_customer_data["aadhaar_number"] = "123456789012"  # Invalid checksum
        invalid_customer_data["email"] = "invalid.test@example.com"
        
        response = self.make_request("POST", "/customers", invalid_customer_data)
        
        if response and response.status_code == 422:  # Validation error expected
            self.log_test("customer_crud_tests", "invalid_aadhaar_rejection", "PASS", 
                        "Correctly rejected customer with invalid Aadhaar")
        else:
            self.log_test("customer_crud_tests", "invalid_aadhaar_rejection", "FAIL", 
                        "Should have rejected invalid Aadhaar number")
        
        # Test CREATE with invalid PAN (should fail)
        invalid_pan_data = customer_data.copy()
        invalid_pan_data["pan_number"] = "INVALID123"
        invalid_pan_data["email"] = "invalid.pan@example.com"
        
        response = self.make_request("POST", "/customers", invalid_pan_data)
        
        if response and response.status_code == 422:  # Validation error expected
            self.log_test("customer_crud_tests", "invalid_pan_rejection", "PASS", 
                        "Correctly rejected customer with invalid PAN")
        else:
            self.log_test("customer_crud_tests", "invalid_pan_rejection", "FAIL", 
                        "Should have rejected invalid PAN number")
        
        # Test READ (individual)
        response = self.make_request("GET", f"/customers/{self.created_customer_id}")
        
        if response and response.status_code == 200:
            customer = response.json()
            if customer.get("first_name") == customer_data["first_name"]:
                self.log_test("customer_crud_tests", "read_customer", "PASS", 
                            "Successfully retrieved individual customer")
            else:
                self.log_test("customer_crud_tests", "read_customer", "FAIL", 
                            "Retrieved customer data doesn't match")
        else:
            self.log_test("customer_crud_tests", "read_customer", "FAIL", 
                        "Failed to retrieve individual customer")
        
        # Test READ by tour_id filter
        response = self.make_request("GET", "/customers", params={"tour_id": self.created_tour_id})
        
        if response and response.status_code == 200:
            customers = response.json()
            test_customer_found = any(customer.get("customer_id") == self.created_customer_id for customer in customers)
            
            if test_customer_found:
                self.log_test("customer_crud_tests", "read_customers_by_tour", "PASS", 
                            f"Successfully retrieved customers by tour_id ({len(customers)} found)")
            else:
                self.log_test("customer_crud_tests", "read_customers_by_tour", "FAIL", 
                            "Created customer not found in tour filter")
        else:
            self.log_test("customer_crud_tests", "read_customers_by_tour", "FAIL", 
                        "Failed to retrieve customers by tour_id")
        
        # Test UPDATE
        update_data = customer_data.copy()
        update_data["first_name"] = "Updated Rajesh"
        update_data["special_requirements"] = "Vegetarian meals and wheelchair access"
        
        response = self.make_request("PUT", f"/customers/{self.created_customer_id}", update_data)
        
        if response and response.status_code == 200:
            updated_customer = response.json()
            if updated_customer.get("first_name") == "Updated Rajesh":
                self.log_test("customer_crud_tests", "update_customer", "PASS", 
                            "Successfully updated customer")
            else:
                self.log_test("customer_crud_tests", "update_customer", "FAIL", 
                            "Customer update didn't reflect changes")
        else:
            self.log_test("customer_crud_tests", "update_customer", "FAIL", 
                        "Failed to update customer")

    def test_dashboard_analytics(self):
        """Test dashboard analytics and statistics"""
        print("\n🔍 Testing Dashboard Analytics...")
        
        response = self.make_request("GET", "/dashboard/stats")
        
        if response and response.status_code == 200:
            stats = response.json()
            
            required_fields = ["total_tours", "total_customers", "total_revenue", "total_expenses", "profit", "tour_stats"]
            missing_fields = [field for field in required_fields if field not in stats]
            
            if not missing_fields:
                self.log_test("dashboard_tests", "stats_structure", "PASS", 
                            "Dashboard stats has all required fields")
                
                # Verify data types
                if (isinstance(stats["total_tours"], int) and 
                    isinstance(stats["total_customers"], int) and 
                    isinstance(stats["total_revenue"], (int, float)) and 
                    isinstance(stats["total_expenses"], (int, float)) and 
                    isinstance(stats["profit"], (int, float)) and 
                    isinstance(stats["tour_stats"], list)):
                    
                    self.log_test("dashboard_tests", "stats_data_types", "PASS", 
                                "All dashboard stats have correct data types")
                    
                    # Verify calculations
                    expected_profit = stats["total_revenue"] - stats["total_expenses"]
                    if abs(stats["profit"] - expected_profit) < 0.01:  # Allow for floating point precision
                        self.log_test("dashboard_tests", "profit_calculation", "PASS", 
                                    f"Profit calculation is correct: {stats['profit']}")
                    else:
                        self.log_test("dashboard_tests", "profit_calculation", "FAIL", 
                                    f"Profit calculation incorrect: expected {expected_profit}, got {stats['profit']}")
                else:
                    self.log_test("dashboard_tests", "stats_data_types", "FAIL", 
                                "Some dashboard stats have incorrect data types")
            else:
                self.log_test("dashboard_tests", "stats_structure", "FAIL", 
                            f"Missing required fields: {missing_fields}")
        else:
            self.log_test("dashboard_tests", "stats_retrieval", "FAIL", 
                        "Failed to retrieve dashboard stats")

    def test_tour_booking_count_update(self):
        """Test that tour booking counts update when customers are added/removed"""
        print("\n🔍 Testing Tour Booking Count Updates...")
        
        if not self.created_tour_id:
            self.log_test("tour_crud_tests", "booking_count_prerequisite", "FAIL", 
                        "No tour available for booking count testing")
            return
        
        # Get initial booking count
        response = self.make_request("GET", f"/tours/{self.created_tour_id}")
        
        if response and response.status_code == 200:
            initial_tour = response.json()
            initial_count = initial_tour.get("booked_count", 0)
            
            # Customer should have been created earlier, so count should be > 0
            if initial_count > 0:
                self.log_test("tour_crud_tests", "booking_count_increment", "PASS", 
                            f"Tour booking count correctly incremented to {initial_count}")
            else:
                self.log_test("tour_crud_tests", "booking_count_increment", "FAIL", 
                            f"Tour booking count not incremented: {initial_count}")
        else:
            self.log_test("tour_crud_tests", "booking_count_check", "FAIL", 
                        "Failed to retrieve tour for booking count check")

    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete test customer
        if self.created_customer_id:
            response = self.make_request("DELETE", f"/customers/{self.created_customer_id}")
            if response and response.status_code == 200:
                print(f"✅ Deleted test customer: {self.created_customer_id}")
            else:
                print(f"⚠️ Failed to delete test customer: {self.created_customer_id}")
        
        # Delete test tour
        if self.created_tour_id:
            response = self.make_request("DELETE", f"/tours/{self.created_tour_id}")
            if response and response.status_code == 200:
                print(f"✅ Deleted test tour: {self.created_tour_id}")
            else:
                print(f"⚠️ Failed to delete test tour: {self.created_tour_id}")

    def is_valid_uuid(self, uuid_string):
        """Check if string is a valid UUID"""
        try:
            uuid.UUID(uuid_string)
            return True
        except (ValueError, TypeError):
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print(f"🚀 Starting Comprehensive Backend API Testing")
        print(f"🌐 Backend URL: {self.base_url}")
        print("=" * 80)
        
        try:
            # Test validation endpoints
            self.test_aadhaar_validation()
            self.test_pan_validation()
            self.test_mobile_validation()
            self.test_email_validation()
            
            # Test sample data
            self.test_sample_data_initialization()
            
            # Test CRUD operations
            self.test_tour_crud_operations()
            self.test_customer_crud_operations()
            
            # Test analytics
            self.test_dashboard_analytics()
            
            # Test booking count updates
            self.test_tour_booking_count_update()
            
        finally:
            # Always cleanup
            self.cleanup_test_data()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for category, tests in self.test_results.items():
            if category == "overall_status":
                continue
                
            print(f"\n📋 {category.upper().replace('_', ' ')}:")
            category_passed = 0
            category_total = 0
            
            for test_name, result in tests.items():
                status = result["status"]
                message = result["message"]
                
                if status == "PASS":
                    print(f"  ✅ {test_name}: {message}")
                    passed_tests += 1
                    category_passed += 1
                elif status == "FAIL":
                    print(f"  ❌ {test_name}: {message}")
                    failed_tests += 1
                else:
                    print(f"  ⚠️ {test_name}: {message}")
                
                total_tests += 1
                category_total += 1
            
            if category_total > 0:
                category_percentage = (category_passed / category_total) * 100
                print(f"  📈 Category Score: {category_passed}/{category_total} ({category_percentage:.1f}%)")
        
        # Overall results
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests}")
        print(f"  Failed: {failed_tests}")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            print(f"  Success Rate: {success_rate:.1f}%")
            
            if success_rate >= 90:
                self.test_results["overall_status"] = "EXCELLENT"
                print(f"  🏆 Status: EXCELLENT - Backend is working very well!")
            elif success_rate >= 75:
                self.test_results["overall_status"] = "GOOD"
                print(f"  ✅ Status: GOOD - Backend is working well with minor issues")
            elif success_rate >= 50:
                self.test_results["overall_status"] = "FAIR"
                print(f"  ⚠️ Status: FAIR - Backend has some issues that need attention")
            else:
                self.test_results["overall_status"] = "POOR"
                print(f"  ❌ Status: POOR - Backend has significant issues")
        
        print("=" * 80)

if __name__ == "__main__":
    tester = BackendTester()
    tester.run_all_tests()