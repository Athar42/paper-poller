#!/usr/bin/env python3

import sys
import json
import os
import importlib.util

def test_dry_run_mode():
    """Test that dry run mode processes updates but doesn't send webhooks"""
    print("=== Testing Dry Run Mode ===")
    
    # Set environment variables for dry run
    os.environ["PAPER_POLLER_DRY_RUN"] = "true"
    os.environ["PAPER_POLLER_CHECK_ALL_VERSIONS"] = "false"  # Use single version for simpler testing
    os.environ["WEBHOOK_URL"] = json.dumps(["https://httpbin.org/post"])  # Real webhook URL to test it's not called
    
    # Import the script fresh to pick up env var changes
    spec = importlib.util.spec_from_file_location("paper_poller", "paper-poller.py")
    paper_poller = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(paper_poller)
    
    PaperAPI = paper_poller.PaperAPI
    DRY_RUN = paper_poller.DRY_RUN
    
    print(f"DRY_RUN = {DRY_RUN}")
    
    try:
        # Test with velocity (smaller project)
        api = PaperAPI(project="velocity")
        
        # Mock the send_v2_webhook to detect if it gets called
        webhook_called = False
        original_send_webhook = api.send_v2_webhook
        
        def mock_send_webhook(*args, **kwargs):
            nonlocal webhook_called
            webhook_called = True
            print("  ✗ ERROR: Webhook was called in dry run mode!")
        
        api.send_v2_webhook = mock_send_webhook
        
        # Test the _process_and_send_update method directly
        fake_build_info = {
            "id": "999",
            "channel": "STABLE",
            "download": {"url": "https://example.com/test.jar"},
            "time": "2025-08-15T22:00:00.000Z",
            "commits": []
        }
        
        print("  Testing _process_and_send_update in dry run mode...")
        api._process_and_send_update("1.21.1", fake_build_info, False)
        
        if webhook_called:
            print("  ✗ Webhook was called - dry run mode failed!")
            return False
        else:
            print("  ✓ Webhook was NOT called - dry run mode working!")
            return True
            
    except Exception as e:
        print(f"  ✗ Error testing dry run: {e}")
        return False

def test_normal_mode():
    """Test that normal mode would call webhooks (mock them)"""
    print("\n=== Testing Normal Mode ===")
    
    # Set environment variables for normal mode
    os.environ["PAPER_POLLER_DRY_RUN"] = "false"
    os.environ["PAPER_POLLER_CHECK_ALL_VERSIONS"] = "false"
    os.environ["WEBHOOK_URL"] = json.dumps(["https://httpbin.org/post"])
    
    # Import the script fresh to pick up env var changes
    spec = importlib.util.spec_from_file_location("paper_poller", "paper-poller.py")
    paper_poller = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(paper_poller)
    
    PaperAPI = paper_poller.PaperAPI
    DRY_RUN = paper_poller.DRY_RUN
    
    print(f"DRY_RUN = {DRY_RUN}")
    
    try:
        api = PaperAPI(project="velocity")
        
        # Mock the send_v2_webhook to detect if it gets called
        webhook_called = False
        
        def mock_send_webhook(*args, **kwargs):
            nonlocal webhook_called
            webhook_called = True
            print("  ✓ Webhook was called in normal mode!")
        
        api.send_v2_webhook = mock_send_webhook
        
        # Test the _process_and_send_update method directly
        fake_build_info = {
            "id": "999",
            "channel": "STABLE",
            "download": {"url": "https://example.com/test.jar"},
            "time": "2025-08-15T22:00:00.000Z",
            "commits": []
        }
        
        print("  Testing _process_and_send_update in normal mode...")
        api._process_and_send_update("1.21.1", fake_build_info, False)
        
        if webhook_called:
            print("  ✓ Normal mode working - webhook was called!")
            return True
        else:
            print("  ✗ Webhook was NOT called - normal mode failed!")
            return False
            
    except Exception as e:
        print(f"  ✗ Error testing normal mode: {e}")
        return False

def test_configuration_display():
    """Test that configuration messages are displayed correctly"""
    print("\n=== Testing Configuration Display ===")
    
    # Test dry run + multi version
    os.environ["PAPER_POLLER_DRY_RUN"] = "true"
    os.environ["PAPER_POLLER_CHECK_ALL_VERSIONS"] = "true"
    
    spec = importlib.util.spec_from_file_location("paper_poller", "paper-poller.py")
    paper_poller = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(paper_poller)
    
    DRY_RUN = paper_poller.DRY_RUN
    CHECK_ALL_VERSIONS = paper_poller.CHECK_ALL_VERSIONS
    
    print(f"  DRY_RUN = {DRY_RUN}, CHECK_ALL_VERSIONS = {CHECK_ALL_VERSIONS}")
    
    if DRY_RUN and CHECK_ALL_VERSIONS:
        print("  ✓ Configuration variables set correctly")
        return True
    else:
        print("  ✗ Configuration variables not set correctly")
        return False

if __name__ == "__main__":
    print("Testing dry run functionality...\n")
    
    success = True
    success &= test_dry_run_mode()
    success &= test_normal_mode()
    success &= test_configuration_display()
    
    if success:
        print("\n✓ All dry run tests passed!")
        print("\nUsage:")
        print("  Normal mode: python paper-poller.py")
        print("  Dry run mode: PAPER_POLLER_DRY_RUN=true python paper-poller.py")
        print("  Dry run + multi-version: PAPER_POLLER_DRY_RUN=true PAPER_POLLER_CHECK_ALL_VERSIONS=true python paper-poller.py")
    else:
        print("\n✗ Some dry run tests failed!")
        sys.exit(1)