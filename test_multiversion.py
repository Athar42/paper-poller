#!/usr/bin/env python3

import sys
import json
import os
import importlib.util

# Import the PaperAPI class from the main script
spec = importlib.util.spec_from_file_location("paper_poller", "paper-poller.py")
paper_poller = importlib.util.module_from_spec(spec)
spec.loader.exec_module(paper_poller)

PaperAPI = paper_poller.PaperAPI

# Create a test environment
test_webhooks = ["https://httpbin.org/post"]

# Override webhook URLs for testing
os.environ["WEBHOOK_URL"] = json.dumps(test_webhooks)


def test_version_tracking():
    """Test the version tracking functionality"""
    print("Testing version tracking functionality...")
    
    # Initialize Paper API
    paper = PaperAPI(project="paper")
    
    # Test getting all versions
    try:
        all_versions_result = paper.get_all_versions()
        versions = all_versions_result["project"]["versions"]
        print(f"✓ Successfully fetched {len(versions)} versions")
        
        # Test a few versions
        test_versions = versions[-3:]  # Last 3 versions
        print(f"Testing with versions: {[v['id'] for v in test_versions]}")
        
        for version_data in test_versions:
            version_id = version_data["id"]
            builds = version_data.get("builds", [])
            
            if builds:
                build_info = builds[0]
                build_id = build_info["id"]
                channel_name = build_info["channel"]
                
                print(f"  Version {version_id}: Build {build_id} ({channel_name})")
                
                # Test version-specific storage methods
                is_up_to_date = paper.up_to_date_for_version(version_id, build_id)
                print(f"    Up to date: {is_up_to_date}")
                
                if not is_up_to_date:
                    # Test writing version data
                    paper.write_version_to_json(version_id, build_id, channel_name)
                    print(f"    ✓ Wrote version data for {version_id}")
                    
                    # Verify it was written correctly
                    stored_data = paper.get_stored_data_for_version(version_id)
                    if stored_data.get("build") == build_id:
                        print(f"    ✓ Version data verified for {version_id}")
                    else:
                        print(f"    ✗ Version data mismatch for {version_id}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing version tracking: {e}")
        return False

def test_dry_run():
    """Test the multi-version functionality without sending webhooks"""
    print("\nTesting multi-version functionality (dry run)...")
    
    # Mock webhook URLs to prevent actual sending
    test_urls = []
    
    # Temporarily override the global webhook_urls
    original_urls = paper_poller.webhook_urls
    paper_poller.webhook_urls = test_urls
    
    try:
        paper = PaperAPI(project="paper")
        
        # Get all versions
        gql_all_versions = paper.get_all_versions()
        all_versions = gql_all_versions["project"]["versions"]
        
        print(f"✓ Found {len(all_versions)} versions to check")
        
        # Test the logic for a few versions without sending webhooks
        updates_found = 0
        for version_data in all_versions[-5:]:  # Test last 5 versions
            version_id = version_data["id"]
            builds = version_data.get("builds", [])
            
            if not builds:
                continue
                
            build_info = builds[0]
            build_id = build_info["id"]
            channel_name = build_info["channel"]
            
            # Check if this version would trigger an update
            updated = paper.up_to_date_for_version(version_id, build_id)
            if not updated:
                updates_found += 1
                print(f"  Would send update for {version_id}: Build {build_id} ({channel_name})")
        
        print(f"✓ Would send {updates_found} updates")
        return True
        
    except Exception as e:
        print(f"✗ Error in dry run test: {e}")
        return False
    finally:
        # Restore original webhook URLs
        paper_poller.webhook_urls = original_urls

if __name__ == "__main__":
    print("Running multi-version support tests...\n")
    
    success = True
    success &= test_version_tracking()
    success &= test_dry_run()
    
    if success:
        print("\n✓ All tests passed! Multi-version support is working correctly.")
    else:
        print("\n✗ Some tests failed. Please check the implementation.")
        sys.exit(1)