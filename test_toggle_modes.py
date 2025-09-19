#!/usr/bin/env python3

import sys
import json
import os
import importlib.util

def test_mode(check_all_versions: bool, mode_name: str):
    """Test a specific mode (single or multi-version)"""
    print(f"\n=== Testing {mode_name} ===")
    
    # Set environment variable
    os.environ["PAPER_POLLER_CHECK_ALL_VERSIONS"] = str(check_all_versions).lower()
    os.environ["WEBHOOK_URL"] = json.dumps([])  # Empty to prevent actual sends
    
    # Import the script fresh to pick up env var changes
    spec = importlib.util.spec_from_file_location("paper_poller", "paper-poller.py")
    paper_poller = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(paper_poller)
    
    PaperAPI = paper_poller.PaperAPI
    CHECK_ALL_VERSIONS = paper_poller.CHECK_ALL_VERSIONS
    
    print(f"CHECK_ALL_VERSIONS = {CHECK_ALL_VERSIONS}")
    
    # Test with a small project to avoid too much output
    try:
        api = PaperAPI(project="velocity")
        
        # Check which methods are called by mocking them
        original_single = api._run_single_version_mode
        original_multi = api._run_multi_version_mode
        
        single_called = False
        multi_called = False
        
        def mock_single():
            nonlocal single_called
            single_called = True
            print(f"  ✓ Single version mode called")
            
        def mock_multi():
            nonlocal multi_called
            multi_called = True
            print(f"  ✓ Multi version mode called")
        
        api._run_single_version_mode = mock_single
        api._run_multi_version_mode = mock_multi
        
        # Call run to see which mode is used
        api.run()
        
        # Verify correct mode was called
        if check_all_versions and multi_called:
            print(f"  ✓ {mode_name} working correctly")
            return True
        elif not check_all_versions and single_called:
            print(f"  ✓ {mode_name} working correctly")
            return True
        else:
            print(f"  ✗ {mode_name} failed - wrong mode called")
            return False
            
    except Exception as e:
        print(f"  ✗ Error testing {mode_name}: {e}")
        return False

def test_actual_functionality():
    """Test that both modes can actually fetch data"""
    print(f"\n=== Testing Actual Functionality ===")
    
    # Test single version mode
    os.environ["PAPER_POLLER_CHECK_ALL_VERSIONS"] = "false"
    os.environ["WEBHOOK_URL"] = json.dumps([])
    
    spec = importlib.util.spec_from_file_location("paper_poller", "paper-poller.py")
    paper_poller = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(paper_poller)
    
    try:
        api = paper_poller.PaperAPI(project="velocity")
        
        # Test single version mode can get latest build
        latest_result = api.get_latest_build()
        if latest_result and "project" in latest_result:
            print("  ✓ Single version mode can fetch latest build")
        else:
            print("  ✗ Single version mode failed to fetch latest build")
            return False
            
        # Test multi version mode can get all versions
        all_result = api.get_all_versions()
        if all_result and "project" in all_result and len(all_result["project"]["versions"]) > 0:
            version_count = len(all_result["project"]["versions"])
            print(f"  ✓ Multi version mode can fetch all {version_count} versions")
        else:
            print("  ✗ Multi version mode failed to fetch versions")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ✗ Error testing functionality: {e}")
        return False

if __name__ == "__main__":
    print("Testing environment variable toggle functionality...\n")
    
    success = True
    
    # Test both modes
    success &= test_mode(False, "Single Version Mode (default)")
    success &= test_mode(True, "Multi Version Mode")
    success &= test_actual_functionality()
    
    if success:
        print("\n✓ All toggle tests passed!")
        print("\nUsage:")
        print("  Default (single version): python paper-poller.py")
        print("  Multi version: PAPER_POLLER_CHECK_ALL_VERSIONS=true python paper-poller.py")
    else:
        print("\n✗ Some toggle tests failed!")
        sys.exit(1)