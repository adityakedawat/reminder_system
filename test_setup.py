#!/usr/bin/env python3
"""
Test script to verify the reminder system setup
"""

import os
import sys

def test_environment_variables():
    """Test if all required environment variables are set"""
    print("🔍 Testing environment variables...")
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SECRET_KEY',
        'RESEND_API_KEY',
        'RESEND_FROM_EMAIL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def test_database_connection():
    """Test database connection"""
    print("\n🔍 Testing database connection...")
    
    try:
        from reminder_system.db import DBAdapter
        db = DBAdapter()
        
        # Test a simple query
        result = db.client.table('clients').select('count').execute()
        print("✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def test_mailersend_config():
    """Test MailerSend configuration"""
    print("\n🔍 Testing MailerSend configuration...")
    
    try:
        from reminder_system.reminder_service import MailerSendService
        mailer = MailerSendService()
        print("✅ MailerSend configuration is valid")
        return True
        
    except Exception as e:
        print(f"❌ MailerSend configuration failed: {str(e)}")
        return False

def test_reminder_service():
    """Test reminder service initialization"""
    print("\n🔍 Testing reminder service...")
    
    try:
        from reminder_system.reminder_service import ReminderService
        service = ReminderService()
        print("✅ Reminder service initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Reminder service initialization failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Reminder System Setup\n")
    
    tests = [
        test_environment_variables,
        test_database_connection,
        test_mailersend_config,
        test_reminder_service
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your reminder system is ready to use.")
        print("\nNext steps:")
        print("1. Add some test data to your database")
        print("2. Run: reminder-system")
        print("3. Check GitHub Actions workflow for automated runs")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 